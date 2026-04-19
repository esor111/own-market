"""
Reversal Specialist — Step 1: Build Trigger Events Table (Revision 4 of pre-reg)

Scans all symbols in the 26-symbol scrape universe for single-day return events
that satisfy the sharp-move definition in PRE_REGISTRATION.md revision 4.

Revision 4 fixes per Romeo's 2026-04-18 third review (small consistency items
after measurement issues from rev 3 were integrated):
- `baseline_obs_count` now counts "last N prior trading observations" (capped
  at 120), not "trading rows within 120 calendar days." Aligns Gate 1's baseline
  universe with L-003 and future H1. Romeo preference: use the same baseline
  method H1 will use, not a proxy.
- Pre-reg's Layer B wording updated to match code (active-symbol denominator).
- Gate-drift diagnostic now emitted by check_gate1.py (how many rows are
  include_in_primary but not h1_eligible, split by reason).
- Stale "revision 1" text in check_gate1.py docstring + markdown output bumped.

Revision 3 fixes (prior pass):
- `has_forward_5d`, `baseline_obs_count`, `active_symbol_count_that_date`,
  `h1_eligible` fields added. Gate 1 counts h1_eligible only.
- Layer B denominator uses per-date active-symbol count (volume > 0), not fixed 26.

Revision 2 fixes (earlier pass):
- Trading-day regime-exclusion windowing via nepse_trading_calendar.
- Layer B data-driven market-wide-shock filter.
- Corporate-action ex-date hard-drop (±2 trading days, L-001 events.csv).
- Circuit-limit exclusion numerical (9.5% pre-2026-04-17 / 14.5% post).
- 5-day median volume threshold.

Reads: price data via load_symbol_prices(); L-001 events.csv (cross-experiment
dependency disclosed in CONTRACT.md).

Writes: experiments/reversal-specialist/data/trigger_events.csv

DOES NOT RUN UNTIL ROMEO SIGNS OFF ON PRE_REGISTRATION revision 4.

Usage (after sign-off):
    python experiments/reversal-specialist/build_trigger_events.py
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
AUTOMATION_DIR = REPO_ROOT / "market-gist" / "automation"
sys.path.insert(0, str(AUTOMATION_DIR))
from nepse_trading_calendar import is_trading_weekday  # noqa: E402
from price_data_integrity import IntegrityError, check_data_dir  # noqa: E402
from score_persistence_shadow_reports import load_symbol_prices  # noqa: E402

OUTPUT_DIR = SCRIPT_DIR / "data"
OUTPUT_CSV = OUTPUT_DIR / "trigger_events.csv"
SYMBOL_LIST_JSON = AUTOMATION_DIR / "scrape_symbol_list.json"
L001_EVENTS_CSV = REPO_ROOT / "experiments" / "01-corporate-action" / "data" / "events.csv"

# Pre-reg revision 4 thresholds (unchanged from rev 2, retained for continuity)
SHARP_DOWN_THRESHOLD = -0.05  # −5.0%
SHARP_UP_THRESHOLD = 0.05     # +5.0%

# Circuit-limit thresholds (hard-drop triggers near price limits)
CIRCUIT_LIMIT_PRE = 0.095   # ±9.5% before April 17, 2026 (NEPSE 10% regime)
CIRCUIT_LIMIT_POST = 0.145  # ±14.5% from April 17, 2026 (NEPSE 15% regime)
CIRCUIT_REGIME_CUTOVER = date(2026, 4, 17)  # widened from 10% to 15% this day

# Layer A — hand-picked documented regime dates (±5 trading days)
REGIME_EXCLUSION_DATES = {
    date(2026, 2, 18),  # Gyalpo Lhosar
    date(2026, 2, 19),  # Democracy Day
    date(2026, 3, 5),   # General Election (non-trading)
    date(2026, 3, 9),   # Post-election triple circuit-breaker +6%
    date(2026, 4, 14),  # Nepali New Year
}
REGIME_EXCLUSION_TRADING_DAYS = 5

# Layer B — data-driven market-wide shock thresholds
MARKET_WIDE_CO_TRIGGER_FRACTION = 0.30   # ≥30% of *active* symbols (volume>0 that date) also triggered
MARKET_WIDE_PROXY_RETURN = 0.03          # |market proxy mean return| ≥ 3%

# Corporate-action ex-date hard-drop window (trading days)
CORP_ACTION_OVERLAP_WINDOW = 2
CORP_ACTION_EVENT_TYPES = {
    "bonus_share",
    "bonus_and_cash_dividend",
    "right_share",
    "cash_dividend",
}

# Volume threshold
VOLUME_LOOKBACK_DAYS = 5

# H1 eligibility requirements (revision 3)
H1_REQUIRED_FORWARD_TRADING_DAYS = 5     # need T+1..T+5 closes available
H1_MIN_BASELINE_OBS = 30                 # L-003 convention: min 30 prior observations for baseline


def trading_days_between(a: date, b: date) -> int:
    """Count trading days between a and b per nepse_trading_calendar.
    Positive if b > a, negative if b < a, zero if equal.

    Counts actual trading sessions, not calendar days.
    """
    if a == b:
        return 0
    step = timedelta(days=1) if b > a else timedelta(days=-1)
    sign = 1 if b > a else -1
    count = 0
    cursor = a
    safety = 0
    while cursor != b:
        cursor = cursor + step
        safety += 1
        if safety > 5000:
            raise RuntimeError(f"trading_days_between safety exceeded: {a} -> {b}")
        if is_trading_weekday(cursor):
            count += 1
    return sign * count


def circuit_limit_for_date(d: date) -> float:
    """Return the absolute-value circuit-limit threshold applicable on date d."""
    return CIRCUIT_LIMIT_POST if d >= CIRCUIT_REGIME_CUTOVER else CIRCUIT_LIMIT_PRE


def near_layer_a_regime_date(trigger_date: date) -> bool:
    """Layer A: within ±REGIME_EXCLUSION_TRADING_DAYS trading days of a hand-picked regime date."""
    for rd in REGIME_EXCLUSION_DATES:
        try:
            gap = trading_days_between(rd, trigger_date)
        except RuntimeError:
            continue
        if abs(gap) <= REGIME_EXCLUSION_TRADING_DAYS:
            return True
    return False


def load_symbols() -> list[str]:
    with SYMBOL_LIST_JSON.open("r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    symbols: list[str] = []
    for sector_symbols in cfg["sectors"].values():
        symbols.extend(sector_symbols)
    seen: set[str] = set()
    unique = []
    for s in symbols:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


def load_corp_action_dates() -> dict[str, list[date]]:
    """Load same-symbol ex-date anchors from L-001 events.csv.

    Returns {symbol: [book_close_dates...]} for hard-drop overlap checking.
    """
    if not L001_EVENTS_CSV.exists():
        print(f"WARNING: L-001 events.csv not found at {L001_EVENTS_CSV} — "
              "corporate-action overlap filter will be a no-op.", file=sys.stderr)
        return {}

    result: dict[str, list[date]] = defaultdict(list)
    with L001_EVENTS_CSV.open("r", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("event_type") not in CORP_ACTION_EVENT_TYPES:
                continue
            bcd_str = row.get("book_close_date", "").strip()
            if not bcd_str:
                continue
            try:
                bcd = datetime.strptime(bcd_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            sym = row.get("symbol", "").strip().upper()
            if sym:
                result[sym].append(bcd)
    return dict(result)


def overlaps_corp_action(
    symbol: str, trigger_date: date, corp_action_map: dict[str, list[date]]
) -> bool:
    """True if any same-symbol corporate action ex-date is within ±CORP_ACTION_OVERLAP_WINDOW trading days."""
    dates = corp_action_map.get(symbol, [])
    for d in dates:
        try:
            gap = trading_days_between(d, trigger_date)
        except RuntimeError:
            continue
        if abs(gap) <= CORP_ACTION_OVERLAP_WINDOW:
            return True
    return False


def detect_raw_moves(symbol: str) -> list[dict]:
    """Return every ≥5% single-day move for one symbol, tagged with all flags EXCEPT
    Layer B (market-wide shock) which can only be computed after all symbols are scanned.
    """
    prices = load_symbol_prices(symbol)
    if prices.empty:
        return []

    # Pre-compute recent-volume window
    volumes = list(prices["volume"]) if "volume" in prices.columns else []

    moves: list[dict] = []
    prior = None
    prices_list = list(prices.itertuples(index=False))
    for i, row in enumerate(prices_list):
        close = getattr(row, "close", None)
        volume = getattr(row, "volume", None)
        event_date = getattr(row, "date", None)
        if close is None or volume is None or event_date is None:
            prior = row
            continue
        if prior is None or getattr(prior, "close", None) in (None, 0):
            prior = row
            continue

        prior_close = float(prior.close)
        if prior_close == 0:
            prior = row
            continue
        daily_ret = (float(close) - prior_close) / prior_close

        d = event_date.date() if hasattr(event_date, "date") else event_date
        if not is_trading_weekday(d):
            prior = row
            continue

        try:
            vol_val = float(volume) if volume is not None else 0.0
        except (TypeError, ValueError):
            vol_val = 0.0

        direction = None
        if daily_ret <= SHARP_DOWN_THRESHOLD:
            direction = "down"
        elif daily_ret >= SHARP_UP_THRESHOLD:
            direction = "up"

        if direction is None:
            prior = row
            continue

        # Volume threshold: require non-zero AND ≥ 5-day median
        if vol_val <= 0:
            prior = row
            continue
        lookback_start = max(0, i - VOLUME_LOOKBACK_DAYS)
        recent_vols = [
            float(getattr(r, "volume", 0) or 0)
            for r in prices_list[lookback_start:i]
            if getattr(r, "volume", None) is not None
        ]
        recent_vols = [v for v in recent_vols if v > 0]
        if recent_vols:
            median_recent = statistics.median(recent_vols)
        else:
            median_recent = 0.0
        passes_volume = vol_val >= median_recent  # 0 when no prior history, still OK

        # Circuit-limit check
        limit = circuit_limit_for_date(d)
        near_price_limit = abs(daily_ret) > limit

        # Layer A regime check
        layer_a_regime = near_layer_a_regime_date(d)

        # H1-eligibility checks (rev 3): forward window + baseline observation count.
        forward_count = 0
        for j in range(i + 1, len(prices_list)):
            fwd = prices_list[j]
            fwd_date = getattr(fwd, "date", None)
            if fwd_date is None:
                continue
            fd = fwd_date.date() if hasattr(fwd_date, "date") else fwd_date
            if is_trading_weekday(fd):
                forward_count += 1
            if forward_count >= H1_REQUIRED_FORWARD_TRADING_DAYS:
                break
        has_forward_5d = forward_count >= H1_REQUIRED_FORWARD_TRADING_DAYS

        # Baseline observation count (Revision 4, per Romeo's preference to match H1):
        # The L-003 rolling baseline uses the last 120 prior return observations, not
        # 120 calendar days of observations. Gate 1 now matches H1's future method so
        # gate and test use the same baseline universe.
        #
        # `i` is the index of the current (trigger) row within this symbol's deduped
        # price frame. `prices_list[0..i-1]` are the prior trading sessions. We want
        # the last 120 of them (if available); Gate 1 requires at least 30.
        baseline_obs = min(i, 120)

        moves.append({
            "symbol": symbol,
            "trigger_date": d.isoformat(),
            "trigger_date_obj": d,
            "direction": direction,
            "close": float(close),
            "prior_close": prior_close,
            "daily_return_pct": round(daily_ret * 100, 3),
            "daily_return_abs": abs(daily_ret),
            "volume": vol_val,
            "volume_median_5d_prior": round(median_recent, 2),
            "passes_volume_threshold": passes_volume,
            "near_price_limit": near_price_limit,
            "layer_a_regime_excluded": layer_a_regime,
            "has_forward_5d": has_forward_5d,
            "baseline_obs_count": baseline_obs,
            # Layer B, corp-action, and h1_eligible filled in later
        })
        prior = row
    return moves


def apply_layer_b_market_shock(all_moves: list[dict], symbols: list[str]) -> None:
    """Compute Layer B flags IN PLACE on every trigger.

    A trigger day t is market-wide-shock if:
      - ≥30% of **active symbols** (those that actually traded on day t, volume > 0)
        trigger on day t — denominator is per-date active count, not fixed 26, OR
      - equal-weighted market proxy (mean daily return across symbols that had volume > 0 on day t)
        satisfies |proxy| ≥ 3.0%.

    Reuses per-symbol price data via load_symbol_prices; cached implicitly by the scorer.
    """
    # Collect co-trigger date counts (any direction)
    co_trigger_by_date: dict[date, set[str]] = defaultdict(set)
    for m in all_moves:
        co_trigger_by_date[m["trigger_date_obj"]].add(m["symbol"])

    # Build per-symbol return tables for proxy computation. Reload, since caching isn't guaranteed here.
    sym_returns: dict[str, dict[date, float]] = {}
    sym_volumes: dict[str, dict[date, float]] = {}
    for sym in symbols:
        prices = load_symbol_prices(sym)
        if prices.empty:
            continue
        returns_by_date: dict[date, float] = {}
        volumes_by_date: dict[date, float] = {}
        prior_close = None
        for row in prices.itertuples(index=False):
            close = getattr(row, "close", None)
            volume = getattr(row, "volume", None)
            event_date = getattr(row, "date", None)
            if close is None or event_date is None:
                continue
            d = event_date.date() if hasattr(event_date, "date") else event_date
            if prior_close is None or prior_close in (0, 0.0):
                prior_close = float(close)
                continue
            ret = (float(close) - prior_close) / prior_close
            returns_by_date[d] = ret
            try:
                volumes_by_date[d] = float(volume or 0)
            except (TypeError, ValueError):
                volumes_by_date[d] = 0.0
            prior_close = float(close)
        sym_returns[sym] = returns_by_date
        sym_volumes[sym] = volumes_by_date

    # Revision 3 fix: co_trigger denominator is active symbols THAT TRADED that date
    # (volume > 0), not fixed 26. Historical dates where fewer symbols existed / traded
    # were being under-flagged with the fixed-26 denominator.

    for m in all_moves:
        d = m["trigger_date_obj"]

        # Count how many of the 26 symbols actually traded that date
        active_symbol_count = 0
        for sym in symbols:
            vol = sym_volumes.get(sym, {}).get(d, 0.0)
            if vol > 0:
                active_symbol_count += 1

        co_trigger_count = len(co_trigger_by_date[d])
        co_trigger_share = (
            co_trigger_count / active_symbol_count
            if active_symbol_count > 0 else 0.0
        )

        # Equal-weighted market proxy: mean daily return across symbols with non-zero volume on d
        traded_returns = []
        for sym in symbols:
            if sym not in sym_returns:
                continue
            if d not in sym_returns[sym]:
                continue
            vol = sym_volumes.get(sym, {}).get(d, 0.0)
            if vol > 0:
                traded_returns.append(sym_returns[sym][d])
        if traded_returns:
            market_proxy = sum(traded_returns) / len(traded_returns)
        else:
            market_proxy = 0.0

        # Safeguard: when active_symbol_count is too small, the co-trigger share is noisy.
        # Require at least 5 active symbols before co-trigger flag can fire.
        # The proxy flag is separately valid for any non-empty traded_returns.
        MIN_ACTIVE_FOR_CO_TRIGGER = 5
        market_wide_by_co_trigger = (
            active_symbol_count >= MIN_ACTIVE_FOR_CO_TRIGGER
            and co_trigger_share >= MARKET_WIDE_CO_TRIGGER_FRACTION
        )
        market_wide_by_proxy = abs(market_proxy) >= MARKET_WIDE_PROXY_RETURN
        layer_b_excluded = market_wide_by_co_trigger or market_wide_by_proxy

        m["active_symbol_count_that_date"] = active_symbol_count
        m["co_trigger_count_that_date"] = co_trigger_count
        m["co_trigger_share"] = round(co_trigger_share, 3)
        m["market_proxy_return_pct"] = round(market_proxy * 100, 3)
        m["layer_b_market_wide_excluded"] = layer_b_excluded


def apply_corp_action_filter(all_moves: list[dict], corp_action_map: dict[str, list[date]]) -> None:
    for m in all_moves:
        m["corp_action_overlap_excluded"] = overlaps_corp_action(
            m["symbol"], m["trigger_date_obj"], corp_action_map
        )


def finalize_inclusion(all_moves: list[dict]) -> None:
    for m in all_moves:
        m["include_in_primary"] = (
            m["passes_volume_threshold"]
            and not m["near_price_limit"]
            and not m["layer_a_regime_excluded"]
            and not m["layer_b_market_wide_excluded"]
            and not m["corp_action_overlap_excluded"]
        )
        # Revision 3 addition: Gate 1 counts only rows that can actually enter H1.
        # "include_in_primary" is the filter-passing flag. "h1_eligible" also requires
        # sufficient forward data and enough baseline observations. Gate 1 must count
        # h1_eligible to prevent gate-drift (passing Gate 1 with rows that H1 later drops).
        m["h1_eligible"] = (
            m["include_in_primary"]
            and m.get("has_forward_5d", False)
            and m.get("baseline_obs_count", 0) >= H1_MIN_BASELINE_OBS
        )


def main() -> int:
    # Integrity guard
    try:
        check_data_dir(raise_on_corrupt=True)
    except IntegrityError as exc:
        print(f"FAILED: price data integrity check: {exc}", file=sys.stderr)
        return 1

    symbols = load_symbols()
    print(f"Scanning {len(symbols)} symbols for sharp-move candidates (Revision 4 pre-reg)...")

    all_moves: list[dict] = []
    for s in symbols:
        ms = detect_raw_moves(s)
        all_moves.extend(ms)
        print(f"  {s}: {len(ms)} raw candidate(s)")

    print(f"\nTotal raw candidates: {len(all_moves)}")

    # Layer B market-wide shock filter (needs full cross-symbol view)
    print("Computing Layer B (data-driven market-wide shock) flags...")
    apply_layer_b_market_shock(all_moves, symbols)

    # Corporate-action ex-date filter
    print("Loading L-001 corporate-action dates for ex-date filter...")
    corp_action_map = load_corp_action_dates()
    total_ca = sum(len(v) for v in corp_action_map.values())
    print(f"  Loaded {total_ca} corporate-action anchor dates across {len(corp_action_map)} symbols")
    apply_corp_action_filter(all_moves, corp_action_map)

    finalize_inclusion(all_moves)

    # Summary
    def count_dir(flag_key: str, want_true: bool, direction: str | None = None) -> int:
        out = 0
        for m in all_moves:
            if direction and m["direction"] != direction:
                continue
            if m[flag_key] is want_true:
                out += 1
        return out

    print()
    print("=== Filter impact (sharp-down primary) ===")
    print(f"Raw sharp-down candidates: {sum(1 for m in all_moves if m['direction']=='down')}")
    print(f"  Fails volume threshold: {count_dir('passes_volume_threshold', False, 'down')}")
    print(f"  Near price-limit (circuit): {count_dir('near_price_limit', True, 'down')}")
    print(f"  Layer A regime-excluded: {count_dir('layer_a_regime_excluded', True, 'down')}")
    print(f"  Layer B market-wide-excluded: {count_dir('layer_b_market_wide_excluded', True, 'down')}")
    print(f"  Corporate-action overlap: {count_dir('corp_action_overlap_excluded', True, 'down')}")
    print(f"  Included in primary (passed filters): {count_dir('include_in_primary', True, 'down')}")
    print(f"  No forward [T+1,T+5] window: {count_dir('has_forward_5d', False, 'down')}")
    baseline_fails_down = sum(
        1 for m in all_moves
        if m['direction'] == 'down' and m.get('baseline_obs_count', 0) < H1_MIN_BASELINE_OBS
    )
    print(f"  Insufficient baseline (<{H1_MIN_BASELINE_OBS} prior obs): {baseline_fails_down}")
    print(f"  H1-eligible (Gate 1 counts this): {count_dir('h1_eligible', True, 'down')}")

    print()
    print("=== Filter impact (sharp-up secondary) ===")
    print(f"Raw sharp-up candidates: {sum(1 for m in all_moves if m['direction']=='up')}")
    print(f"  Included in primary: {count_dir('include_in_primary', True, 'up')}")
    print(f"  H1-eligible: {count_dir('h1_eligible', True, 'up')}")

    # Remove temporary objects before writing
    rows_out = []
    for m in all_moves:
        m2 = {k: v for k, v in m.items() if k != "trigger_date_obj"}
        rows_out.append(m2)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not rows_out:
        print(f"\nNo moves detected. Writing empty file to {OUTPUT_CSV}")
        OUTPUT_CSV.write_text("", encoding="utf-8")
        return 0

    fieldnames = list(rows_out[0].keys())
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows_out:
            writer.writerow(r)
    print(f"\nWrote {len(rows_out)} rows to {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
