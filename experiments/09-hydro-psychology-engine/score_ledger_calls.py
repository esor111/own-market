"""Score pending paper-trade ledger calls when their forward window has elapsed.

For each unresolved row, look up:
    - the trading session N forward sessions after signal_date
    - the close price on that session
    - the average peer return over the same window
Then mark the row as resolved with hit/miss against pattern direction.

Reads:
    data/paper_trade_ledger.csv
    sharesansar_datascrape/data/<MM_DD_YYYY>.csv

Writes:
    data/paper_trade_ledger.csv  (in-place)
    results/paper_trade_scorecard.md

Research only.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]
LEDGER_PATH = SCRIPT_DIR / "data" / "paper_trade_ledger.csv"
SCORECARD_PATH = SCRIPT_DIR / "results" / "paper_trade_scorecard.md"
PRICE_DIR = ROOT_DIR / "sharesansar_datascrape" / "data"
CONFIG_PATH = SCRIPT_DIR / "config.json"


LEDGER_FIELDS = [
    "recorded_at",
    "signal_date",
    "symbol",
    "decision",
    "horizon_days",
    "state",
    "robustness_grade",
    "expected_excess_peer_return_pct",
    "historical_peer_hit_rate_pct",
    "pattern_n",
    "invalidation_level",
    "quality_flags",
    "entry_close_price",
    "resolution_status",
    "target_session_date",
    "resolved_close_price",
    "actual_return_pct",
    "actual_peer_return_pct",
    "actual_excess_peer_return_pct",
    "decision_correct",
    "scored_at",
]


def main() -> int:
    if not LEDGER_PATH.exists():
        print(f"No ledger at {LEDGER_PATH}. Run append_watchlist_to_ledger.py first.")
        return 1

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    universe = [s.upper() for s in config.get("symbols", [])]

    trading_dates = load_trading_dates()
    if not trading_dates:
        print("No price data found. Cannot score.")
        return 1
    last_trading_date = trading_dates[-1]

    rows = read_ledger(LEDGER_PATH)
    now_iso = datetime.now().isoformat(timespec="seconds")
    newly_scored = 0

    for row in rows:
        if row.get("resolution_status") == "resolved":
            continue
        signal_date = row.get("signal_date", "").strip()
        symbol = row.get("symbol", "").strip().upper()
        try:
            horizon = int(row.get("horizon_days", ""))
        except (ValueError, TypeError):
            continue
        target = forward_session(trading_dates, signal_date, horizon)
        if not target:
            continue
        if target > last_trading_date:
            row["resolution_status"] = "pending"
            row["target_session_date"] = target
            continue

        entry_close = parse_number(row.get("entry_close_price"))
        if entry_close is None:
            entry_close = lookup_close(symbol, signal_date)
            if entry_close is not None:
                row["entry_close_price"] = entry_close
        resolved_close = lookup_close(symbol, target)
        if entry_close is None or resolved_close is None:
            row["resolution_status"] = "insufficient_data"
            row["target_session_date"] = target
            row["scored_at"] = now_iso
            newly_scored += 1
            continue

        actual_return_pct = ((resolved_close - entry_close) / entry_close) * 100

        peer_returns: list[float] = []
        for peer in universe:
            if peer == symbol:
                continue
            peer_entry = lookup_close(peer, signal_date)
            peer_exit = lookup_close(peer, target)
            if peer_entry and peer_exit:
                peer_returns.append(((peer_exit - peer_entry) / peer_entry) * 100)
        peer_avg = sum(peer_returns) / len(peer_returns) if peer_returns else None
        excess = actual_return_pct - peer_avg if peer_avg is not None else None

        decision = row.get("decision", "").strip().lower()
        correct: int | str = ""
        if excess is not None:
            if decision == "long":
                correct = 1 if excess > 0 else 0
            elif decision == "avoid":
                correct = 1 if excess < 0 else 0

        row["target_session_date"] = target
        row["resolved_close_price"] = round(resolved_close, 4)
        row["actual_return_pct"] = round(actual_return_pct, 4)
        row["actual_peer_return_pct"] = round(peer_avg, 4) if peer_avg is not None else ""
        row["actual_excess_peer_return_pct"] = round(excess, 4) if excess is not None else ""
        row["decision_correct"] = correct
        row["resolution_status"] = "resolved"
        row["scored_at"] = now_iso
        newly_scored += 1

    write_ledger(LEDGER_PATH, rows)
    write_scorecard(rows)

    print(f"Scored {newly_scored} new rows. Ledger has {len(rows)} total. Last trading date: {last_trading_date}.")
    return 0


def load_trading_dates() -> list[str]:
    """Return sorted list of trading-date strings (YYYY-MM-DD) from the price archive."""
    dates: list[str] = []
    for path in PRICE_DIR.glob("*.csv"):
        try:
            d = datetime.strptime(path.stem, "%m_%d_%Y").date()
        except ValueError:
            continue
        dates.append(d.isoformat())
    return sorted(dates)


def forward_session(trading_dates: list[str], signal_date: str, n: int) -> str | None:
    """Return the trading-date string n sessions after signal_date, or None."""
    try:
        idx = trading_dates.index(signal_date)
    except ValueError:
        # find first trading date strictly after signal_date
        idx = -1
        for i, d in enumerate(trading_dates):
            if d > signal_date:
                idx = i - 1
                break
        if idx < 0:
            return None
    target_idx = idx + n
    if target_idx >= len(trading_dates):
        return None
    return trading_dates[target_idx]


def lookup_close(symbol: str, iso_date: str) -> float | None:
    try:
        d = datetime.strptime(iso_date, "%Y-%m-%d").date()
    except ValueError:
        return None
    csv_path = PRICE_DIR / f"{d.strftime('%m_%d_%Y')}.csv"
    if not csv_path.exists():
        return None
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            if str(raw.get("Symbol", "")).strip().upper() == symbol:
                close = parse_number(raw.get("Close")) or parse_number(raw.get("LTP"))
                return close
    return None


def write_scorecard(rows: list[dict[str, Any]]) -> None:
    SCORECARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    resolved = [r for r in rows if r.get("resolution_status") == "resolved" and r.get("decision_correct") in (0, 1, "0", "1")]
    pending = [r for r in rows if r.get("resolution_status") == "pending"]
    insufficient = [r for r in rows if r.get("resolution_status") == "insufficient_data"]

    lines = [
        "# Paper-Trade Scorecard",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Forward evidence collection for experiment 09 robust-pattern watchlist.",
        "Research only. Not financial advice.",
        "",
        "## Headline Numbers",
        "",
        f"- Ledger rows: {len(rows)}",
        f"- Resolved: {len(resolved)}",
        f"- Pending: {len(pending)}",
        f"- Insufficient data: {len(insufficient)}",
        "",
    ]

    if not resolved:
        lines.append("No resolved calls yet. Wait for forward sessions to elapse.")
    else:
        correct = sum(1 for r in resolved if str(r.get("decision_correct")) == "1")
        hit_rate = correct / len(resolved) * 100
        excesses = [parse_number(r.get("actual_excess_peer_return_pct")) for r in resolved]
        excesses = [e for e in excesses if e is not None]
        avg_excess = sum(excesses) / len(excesses) if excesses else None
        lines.extend([
            "## Aggregate Result",
            "",
            f"- Hit rate: {correct}/{len(resolved)} = {hit_rate:.1f}%",
            f"- Avg excess vs peers: {avg_excess:.4f}%" if avg_excess is not None else "- Avg excess vs peers: n/a",
            "",
            "## By Decision",
            "",
            "| Decision | N | Hit rate | Avg excess vs peers |",
            "|---|---:|---:|---:|",
        ])
        by_decision: dict[str, list[dict]] = {}
        for r in resolved:
            by_decision.setdefault(r.get("decision", ""), []).append(r)
        for dec, group in sorted(by_decision.items()):
            grp_correct = sum(1 for r in group if str(r.get("decision_correct")) == "1")
            grp_hit = grp_correct / len(group) * 100
            grp_excesses = [parse_number(r.get("actual_excess_peer_return_pct")) for r in group]
            grp_excesses = [e for e in grp_excesses if e is not None]
            grp_avg = sum(grp_excesses) / len(grp_excesses) if grp_excesses else None
            avg_str = f"{grp_avg:.4f}%" if grp_avg is not None else "n/a"
            lines.append(f"| {dec} | {len(group)} | {grp_hit:.1f}% | {avg_str} |")

        lines.extend([
            "",
            "## By Horizon",
            "",
            "| Horizon | N | Hit rate | Avg excess vs peers |",
            "|---:|---:|---:|---:|",
        ])
        by_horizon: dict[str, list[dict]] = {}
        for r in resolved:
            by_horizon.setdefault(r.get("horizon_days", ""), []).append(r)
        for h, group in sorted(by_horizon.items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 999):
            grp_correct = sum(1 for r in group if str(r.get("decision_correct")) == "1")
            grp_hit = grp_correct / len(group) * 100
            grp_excesses = [parse_number(r.get("actual_excess_peer_return_pct")) for r in group]
            grp_excesses = [e for e in grp_excesses if e is not None]
            grp_avg = sum(grp_excesses) / len(grp_excesses) if grp_excesses else None
            avg_str = f"{grp_avg:.4f}%" if grp_avg is not None else "n/a"
            lines.append(f"| {h} | {len(group)} | {grp_hit:.1f}% | {avg_str} |")

    if pending:
        lines.extend([
            "",
            "## Pending Calls (awaiting forward data)",
            "",
            "| Symbol | Decision | H | Signal date | Target session |",
            "|---|---|---:|---|---|",
        ])
        for r in sorted(pending, key=lambda x: (x.get("signal_date", ""), x.get("horizon_days", ""))):
            lines.append(
                f"| {r.get('symbol','')} | {r.get('decision','')} | {r.get('horizon_days','')} "
                f"| {r.get('signal_date','')} | {r.get('target_session_date','') or 'tbd'} |"
            )

    SCORECARD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {SCORECARD_PATH}")


def read_ledger(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_ledger(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    text = str(value).replace(",", "").strip()
    if not text or text == "-":
        return None
    try:
        return float(text)
    except ValueError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
