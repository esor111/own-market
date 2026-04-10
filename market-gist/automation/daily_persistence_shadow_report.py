"""
Daily Persistence Shadow Report v1

Frozen policy (do not change for 10-15 trading sessions):

  CAUTION signals (downgrade weak cases):
    - w7 seller_persistence_score >= 1.0
    - w10 persistent_seller_count >= 4
    - NOTE: today_seller_is_persistent

  SUPPORTIVE signals (support already-good cases):
    - w15 seller_persistence_score <= 0.6
    - ONLY full SUPPORTIVE if close_position_60d >= 0.6 AND volume_ratio_5d >= 1.0
    - Otherwise downgraded to note-only

Scope:
  - Commercial banks (NABIL, EBL, SANIMA): active shadow-decision lane
  - Hydropower (AKPL, UPPER, API): parallel research logging only
  - Dev banks (JBBL, MNBBL): excluded

This is a CAUTION OVERLAY, not a buy engine.
It downgrades weak cases or supports already-good ones.

Usage:
    python daily_persistence_shadow_report.py --date 2026-04-01
"""

import argparse
import csv
import json
import os
import sys
import glob
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from broker_persistence_tracker import load_all_ledgers, compute_persistence

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
SHADOW_DIR = ROOT / "data" / "validation" / "persistence_shadow_reports"
SHADOW_DIR.mkdir(parents=True, exist_ok=True)

ACTIVE_SYMBOLS = ["NABIL", "EBL", "SANIMA"]
RESEARCH_SYMBOLS = ["AKPL", "UPPER", "API"]
EXCLUDED = ["JBBL", "MNBBL"]

POLICY_VERSION = "v1_frozen_2026-04-05"
DIVIDEND_ANNOTATION_VERSION = "dividend_family_bank_annotation_v2_draft_2026-04-09"

# Paths for looking up pos60 and VR
REPLAYS_DIR = ROOT / "data" / "replays"
DATASET_PATH = ROOT / "data" / "validation" / "learning_reviews" / "latest__entry_research_dataset_v1.json"
SYMBOLS_DIR = ROOT / "data" / "symbols"
EVENT_TABLE_PATH = ROOT.parent / "experiments" / "01-corporate-action" / "data" / "events.csv"
SHARESANSAR_DATA_DIR = ROOT.parent / "sharesansar_datascrape" / "data"
DIVIDEND_FAMILY_EVENT_TYPES = {
    "dividend_notice",
    "cash_dividend_notice",
    "cash_dividend",
    "bonus_and_cash_dividend",
}
DIVIDEND_ADMIN_PATTERNS = [
    "unclaim",
    "uncollect",
    "collect due",
    "collect remaining",
    "remaining return investment",
    "last five fiscal years",
    "last 5 fiscal years",
]

# Cache for dataset rows
_dataset_cache = None
_dividend_event_cache = None
_market_calendar_cache = None


def _load_dataset_rows():
    """Load the 526-row dataset for pos60/VR lookup. Cached."""
    global _dataset_cache
    if _dataset_cache is not None:
        return _dataset_cache
    if DATASET_PATH.exists():
        data = json.loads(DATASET_PATH.read_text())
        _dataset_cache = {(r["session_date"], r["symbol"]): r for r in data.get("rows", [])}
    else:
        _dataset_cache = {}
    return _dataset_cache


def _lookup_stock_features(symbol, target_date):
    """Look up close_position_60d and volume_ratio_5d for a (symbol, date).

    Tries three sources in order:
    1. The 526-row entry research dataset
    2. Replay frozen case files
    3. Returns (None, None) if not found
    """
    # Source 1: dataset
    ds = _load_dataset_rows()
    row = ds.get((target_date, symbol))
    if row:
        pos60 = row.get("close_position_60d")
        vr = row.get("volume_ratio_5d")
        if pos60 is not None and vr is not None:
            return pos60, vr

    # Source 2: replay frozen case
    for replay_dir in REPLAYS_DIR.glob("*/sessions"):
        fc_path = replay_dir / target_date / symbol / "normalized" / f"{target_date}__{symbol}__frozen_case_v1.json"
        if fc_path.exists():
            fc = json.loads(fc_path.read_text())
            m = fc.get("metrics", {})
            pos60 = m.get("close_position_60d")
            vr = m.get("volume_ratio_5d")
            if pos60 is not None and vr is not None:
                return pos60, vr

    return None, None


def _parse_iso_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _event_source_rank(source_table):
    return {
        "company-announcements": 1,
        "company-events": 2,
        "company-dividend": 3,
    }.get(source_table, 99)


def _is_dividend_admin_notice(event_label):
    text = (event_label or "").lower()
    return any(pattern in text for pattern in DIVIDEND_ADMIN_PATTERNS)


def _load_dividend_family_events():
    """Load deduped bank-only dividend-family announcement events from the experiment table."""
    global _dividend_event_cache
    if _dividend_event_cache is not None:
        return _dividend_event_cache

    grouped = {symbol: [] for symbol in ACTIVE_SYMBOLS}
    if not EVENT_TABLE_PATH.exists():
        print(
            f"WARNING: dividend-family event table not found at {EVENT_TABLE_PATH}. "
            "Dividend annotation will be disabled for this run. "
            "Verify experiments/01-corporate-action/data/events.csv exists.",
            file=sys.stderr,
        )
        _dividend_event_cache = grouped
        return grouped

    rows = []
    with EVENT_TABLE_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            symbol = str(raw.get("symbol", "")).upper().strip()
            announcement_date = (raw.get("announcement_date") or "").strip()
            event_type = (raw.get("event_type") or "").strip()
            if symbol not in ACTIVE_SYMBOLS:
                continue
            if event_type not in DIVIDEND_FAMILY_EVENT_TYPES:
                continue
            if not announcement_date:
                continue
            event_label = (raw.get("event_label") or "").strip()
            if _is_dividend_admin_notice(event_label):
                continue
            rows.append(
                {
                    "symbol": symbol,
                    "announcement_date": announcement_date,
                    "event_type": event_type,
                    "source_table": (raw.get("source_table") or "").strip(),
                    "event_label": event_label,
                }
            )

    rows.sort(
        key=lambda row: (
            row["symbol"],
            row["announcement_date"],
            _event_source_rank(row["source_table"]),
            row["event_type"],
        )
    )

    seen = set()
    deduped = []
    for row in rows:
        key = (row["symbol"], row["announcement_date"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    for row in deduped:
        grouped.setdefault(row["symbol"], []).append(row)

    _dividend_event_cache = grouped
    return grouped


CALENDAR_REFERENCE_SYMBOL = "NABIL"
CALENDAR_COMPARISON_COLUMNS = (
    "Open", "High", "Low", "Close", "LTP", "VWAP", "Vol", "Prev. Close",
    "Turnover", "Trans.", "Diff", "Diff %", "Range", "Range %", "VWAP %",
)


def _load_market_calendar():
    """Load a trading-session calendar by collapsing consecutive duplicate sessions
    using the same per-row dedup logic as the experiment framework's price_loader.

    Compares NABIL's daily row across all numeric columns. A non-trading day
    (weekend/holiday) clones the previous trading day's row exactly. We collapse
    those clones so a "10 trading day" window matches the validated experiment
    window. See L-007 in experiments/LEARNINGS.md for the rationale.
    """
    global _market_calendar_cache
    if _market_calendar_cache is not None:
        return _market_calendar_cache

    dates = []
    previous_signature = None
    if SHARESANSAR_DATA_DIR.exists():
        dated_paths = []
        for csv_path in SHARESANSAR_DATA_DIR.glob("*.csv"):
            try:
                current_date = datetime.strptime(csv_path.stem, "%m_%d_%Y").date()
            except ValueError:
                continue
            dated_paths.append((current_date, csv_path))

        for current_date, csv_path in sorted(dated_paths, key=lambda item: item[0]):
            signature = _read_reference_row_signature(csv_path)
            if signature is None:
                # No reference symbol row at all on this date — skip.
                continue
            if signature == previous_signature:
                continue
            previous_signature = signature
            dates.append(current_date)

    _market_calendar_cache = dates
    return _market_calendar_cache


def _read_reference_row_signature(csv_path):
    """Return a tuple of comparison-column values for the reference symbol row,
    or None if the row is missing. Used to detect cloned non-trading days."""
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for raw in reader:
                symbol = str(raw.get("Symbol") or "").strip().upper()
                if symbol != CALENDAR_REFERENCE_SYMBOL:
                    continue
                return tuple(
                    (raw.get(column) or "").strip()
                    for column in CALENDAR_COMPARISON_COLUMNS
                )
    except (OSError, csv.Error):
        return None
    return None


def _resolve_trading_anchor_index(sorted_dates, event_day, max_forward_gap_days=10):
    for idx, trading_day in enumerate(sorted_dates):
        if trading_day >= event_day:
            if (trading_day - event_day).days > max_forward_gap_days:
                return None
            return idx
    return None


def _active_dividend_annotations(symbol, target_date, ledgers):
    """Return bank-only dividend-family caution annotations active on target_date."""
    if symbol not in ACTIVE_SYMBOLS:
        return []

    target_day = _parse_iso_date(target_date)
    if target_day is None:
        return []

    trading_days = _load_market_calendar()
    if target_day not in trading_days:
        return []

    target_idx = trading_days.index(target_day)
    annotations = []
    for event in _load_dividend_family_events().get(symbol, []):
        event_day = _parse_iso_date(event["announcement_date"])
        if event_day is None:
            continue
        anchor_idx = _resolve_trading_anchor_index(trading_days, event_day, max_forward_gap_days=10)
        if anchor_idx is None:
            continue
        if target_idx < anchor_idx or target_idx > anchor_idx + 9:
            continue

        annotations.append(
            {
                "annotation_type": "dividend_family_caution",
                "annotation_version": DIVIDEND_ANNOTATION_VERSION,
                "announcement_date": event["announcement_date"],
                "event_type": event["event_type"],
                "source_table": event["source_table"],
                "event_label": event["event_label"],
                "window_day": target_idx - anchor_idx + 1,
                "window_total_days": 10,
            }
        )

    return annotations


def _find_common_latest_date(all_ledgers):
    """Find the latest date that ALL active symbols have data for."""
    date_sets = []
    for sym in ACTIVE_SYMBOLS:
        if sym in all_ledgers and all_ledgers[sym]:
            date_sets.append(set(all_ledgers[sym].keys()))
    if not date_sets:
        return None
    common = date_sets[0]
    for ds in date_sets[1:]:
        common = common & ds
    if not common:
        # Fallback: use the latest date of the first symbol
        for sym in ACTIVE_SYMBOLS:
            if sym in all_ledgers and all_ledgers[sym]:
                return sorted(all_ledgers[sym].keys())[-1]
        return None
    return sorted(common)[-1]


def evaluate_signals(symbol, ledgers, target_date):
    """Evaluate the frozen v1 persistence policy for a symbol on a date."""
    w7 = compute_persistence(ledgers, target_date, 7)
    w10 = compute_persistence(ledgers, target_date, 10)
    w15 = compute_persistence(ledgers, target_date, 15)

    if not w7:
        return None

    # Look up stock features for SUPPORTIVE strength check
    pos60, vr = _lookup_stock_features(symbol, target_date)

    result = {
        "symbol": symbol,
        "date": target_date,
        "policy_version": POLICY_VERSION,
        "signals": {},
        "caution_flags": [],
        "supportive_flags": [],
        "event_annotations": [],
        "notes": [],
        "verdict": "NO_SIGNAL",
    }

    # Raw values
    result["signals"]["w7_seller_persist"] = w7["seller_persistence_score"]
    result["signals"]["w7_buyer_persist"] = w7["buyer_persistence_score"]
    result["signals"]["w7_net_bias"] = w7["net_persistence_bias"]
    result["signals"]["w10_persistent_seller_count"] = w10["persistent_seller_count"] if w10 else None
    result["signals"]["w15_seller_persist"] = w15["seller_persistence_score"] if w15 else None
    result["signals"]["today_seller_is_persistent"] = w7["today_seller_is_persistent"]
    result["signals"]["today_buyer_is_persistent"] = w7["today_buyer_is_persistent"]
    result["signals"]["close_position_60d"] = pos60
    result["signals"]["volume_ratio_5d"] = vr

    # === CAUTION SIGNALS ===
    if w7["seller_persistence_score"] >= 1.0:
        result["caution_flags"].append(
            "w7_seller_persist=1.0: same broker selling every day for 7 straight days"
        )

    if w10 and w10["persistent_seller_count"] >= 4:
        result["caution_flags"].append(
            f"w10_persistent_sellers={w10['persistent_seller_count']}: "
            f"4+ different brokers persistently selling over 10 days"
        )

    if w7["today_seller_is_persistent"]:
        result["notes"].append(
            "today_seller_is_persistent: today's top seller has been selling consistently"
        )

    # === SUPPORTIVE SIGNALS ===
    # w15 seller persistence <= 0.6 (no persistent seller for 15 days)
    # FIX 2: Only full SUPPORTIVE if pos60 >= 0.6 AND VR >= 1.0
    if w15 and w15["seller_persistence_score"] <= 0.6:
        has_strength = (pos60 is not None and pos60 >= 0.6
                        and vr is not None and vr >= 1.0)
        if has_strength:
            result["supportive_flags"].append(
                f"w15_seller_persist<=0.6 + pos60={pos60:.2f} + VR={vr:.2f}: "
                f"no persistent seller, confirmed by strong position and volume"
            )
        else:
            # Downgrade to note-only
            pos60_str = f"{pos60:.2f}" if pos60 is not None else "unknown"
            vr_str = f"{vr:.2f}" if vr is not None else "unknown"
            result["notes"].append(
                f"w15_seller_persist<=0.6 but pos60={pos60_str}, VR={vr_str}: "
                f"no persistent seller, but stock features do not confirm strength "
                f"(need pos60>=0.6 AND VR>=1.0 for full SUPPORTIVE)"
            )

    # === CORPORATE EVENT ANNOTATION (research only, no verdict change) ===
    result["event_annotations"] = _active_dividend_annotations(symbol, target_date, ledgers)

    # === VERDICT ===
    if result["caution_flags"]:
        result["verdict"] = "CAUTION"
    elif result["supportive_flags"]:
        result["verdict"] = "SUPPORTIVE"
    else:
        result["verdict"] = "NO_SIGNAL"

    return result


def format_report(results, report_date):
    """Format the shadow report as readable text."""
    lines = [
        f"=== PERSISTENCE SHADOW REPORT: {report_date} ===",
        f"Policy: {POLICY_VERSION}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "--- COMMERCIAL BANKS (active shadow lane) ---",
        "",
    ]

    for r in results:
        if r["symbol"] not in ACTIVE_SYMBOLS:
            continue
        if r is None:
            continue

        sym = r["symbol"]
        v = r["verdict"]
        s = r["signals"]

        w7s = s.get("w7_seller_persist", "?")
        w15s = s.get("w15_seller_persist", "?")
        w7s_str = f"{w7s:.2f}" if isinstance(w7s, float) else str(w7s)
        w15s_str = f"{w15s:.2f}" if isinstance(w15s, float) else str(w15s)

        lines.append(f"  {sym:8s} | sell_w7={w7s_str} sell_w15={w15s_str} | {v}")

        for flag in r["caution_flags"]:
            lines.append(f"           | CAUTION: {flag}")
        for flag in r["supportive_flags"]:
            lines.append(f"           | SUPPORT: {flag}")
        for annotation in r.get("event_annotations", []):
            lines.append(
                "           | EVENT: bank dividend caution active "
                f"(day {annotation['window_day']}/{annotation['window_total_days']}, "
                f"{annotation['event_type']} on {annotation['announcement_date']})"
            )
            lines.append(f"           | event: {annotation['event_label']}")
        for note in r["notes"]:
            lines.append(f"           | note: {note}")
        lines.append("")

    lines.append("--- HYDROPOWER (research logging only) ---")
    lines.append("")

    for r in results:
        if r["symbol"] not in RESEARCH_SYMBOLS:
            continue
        if r is None:
            continue

        sym = r["symbol"]
        v = r["verdict"]
        s = r["signals"]
        w7s = s.get("w7_seller_persist", "?")
        w7s_str = f"{w7s:.2f}" if isinstance(w7s, float) else str(w7s)

        lines.append(f"  {sym:8s} | sell_w7={w7s_str} | {v} (research only)")
        lines.append("")

    lines.extend([
        "--- EXCLUDED ---",
        "  JBBL, MNBBL: insufficient data, excluded from persistence signals",
        "",
        "--- HOW TO READ ---",
        "  CAUTION: persistence suggests downside risk. Do not enter weak setups.",
        "  SUPPORTIVE: no persistent seller + strong stock position. Supports good setups.",
        "  NO_SIGNAL: persistence is neutral. Use other analysis.",
        "  EVENT annotation: bank-only dividend research note; housekeeping notices filtered; does not change verdict.",
        "",
        "  This is a SHADOW report. Record the verdict. Do NOT trade on it alone.",
        "  Score after 10 trading days. Batch-score after 10-15 reports accumulate.",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True,
                        help="Target date (YYYY-MM-DD). Use the current trading session date.")
    args = parser.parse_args()

    target_date = args.date

    # Load all ledgers once
    all_ledgers = {}
    all_symbols = ACTIVE_SYMBOLS + RESEARCH_SYMBOLS
    for sym in all_symbols:
        all_ledgers[sym] = load_all_ledgers(sym)

    results = []
    skipped = {"no_ledger": [], "no_data_for_date": [], "evaluate_returned_none": []}
    for sym in all_symbols:
        ledgers = all_ledgers.get(sym, {})
        if not ledgers:
            print(f"  {sym}: no broker flow data")
            skipped["no_ledger"].append(sym)
            continue

        if target_date not in ledgers:
            print(f"  {sym}: no data for {target_date}")
            skipped["no_data_for_date"].append(sym)
            continue

        result = evaluate_signals(sym, ledgers, target_date)
        if result:
            results.append(result)
        else:
            skipped["evaluate_returned_none"].append(sym)

    # End-of-run sanity check: every ACTIVE symbol should produce a row.
    produced_symbols = {r["symbol"] for r in results}
    missing_active = [s for s in ACTIVE_SYMBOLS if s not in produced_symbols]
    missing_research = [s for s in RESEARCH_SYMBOLS if s not in produced_symbols]
    if missing_active:
        print(
            f"WARNING: missing ACTIVE symbols on {target_date}: {missing_active}. "
            "Active-lane CAUTION/SUPPORTIVE coverage is incomplete for this report.",
            file=sys.stderr,
        )
    if missing_research:
        print(
            f"NOTE: missing RESEARCH symbols on {target_date}: {missing_research}. "
            "Research-lane logging is incomplete (this is informational, not blocking).",
            file=sys.stderr,
        )
    if any(skipped[k] for k in skipped):
        print(f"  skipped detail: {skipped}", file=sys.stderr)

    if not results:
        print(f"No results for {target_date}. Check broker flow data for that date.")
        return

    report_text = format_report(results, target_date)

    # Print to console
    print(report_text)

    # Save JSON
    json_path = SHADOW_DIR / f"{target_date}__persistence_shadow_v1.json"
    with open(json_path, "w") as f:
        json.dump({
            "report_date": target_date,
            "policy_version": POLICY_VERSION,
            "generated_at": datetime.now().isoformat(),
            "results": results,
        }, f, indent=2)

    # Save text
    txt_path = SHADOW_DIR / f"{target_date}__persistence_shadow_v1.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\nSaved: {json_path}")
    print(f"Saved: {txt_path}")


if __name__ == "__main__":
    main()
