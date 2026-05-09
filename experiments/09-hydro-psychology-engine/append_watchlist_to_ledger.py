"""Append today's robust-pattern watchlist calls to the master paper-trade ledger.

Idempotent: re-running on the same (signal_date, symbol, decision, horizon_days)
will not create duplicates.

Reads:
    results/latest_robust_pattern_watchlist.csv
    sharesansar_datascrape/data/<MM_DD_YYYY>.csv  (for entry close price)

Writes/updates:
    data/paper_trade_ledger.csv

Research only. Forward evidence collection layer for experiment 09.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, date
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]
WATCHLIST_PATH = SCRIPT_DIR / "results" / "latest_robust_pattern_watchlist.csv"
LEDGER_PATH = SCRIPT_DIR / "data" / "paper_trade_ledger.csv"
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
    if not WATCHLIST_PATH.exists():
        print(f"No watchlist at {WATCHLIST_PATH}. Run the refresh pipeline first.")
        return 1

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    universe = [s.upper() for s in config.get("symbols", [])]

    watchlist_rows = list(csv.DictReader(WATCHLIST_PATH.open("r", encoding="utf-8")))
    if not watchlist_rows:
        print("Watchlist is empty. Nothing to append.")
        return 0

    existing = read_ledger(LEDGER_PATH)
    existing_keys = {dedup_key(r) for r in existing}

    now_iso = datetime.now().isoformat(timespec="seconds")
    appended = 0

    for row in watchlist_rows:
        signal_date = row.get("signal_date", "").strip()
        symbol = row.get("symbol", "").strip().upper()
        decision = row.get("decision", "").strip().lower()
        horizon = row.get("horizon_days", "").strip()
        if not (signal_date and symbol and decision and horizon):
            continue
        key = (signal_date, symbol, decision, horizon)
        if key in existing_keys:
            continue

        entry_close = lookup_close(symbol, signal_date)
        ledger_row = {
            "recorded_at": now_iso,
            "signal_date": signal_date,
            "symbol": symbol,
            "decision": decision,
            "horizon_days": horizon,
            "state": row.get("state", ""),
            "robustness_grade": row.get("robustness_grade", ""),
            "expected_excess_peer_return_pct": row.get("expected_excess_peer_return_pct", ""),
            "historical_peer_hit_rate_pct": row.get("historical_peer_hit_rate_pct", ""),
            "pattern_n": row.get("pattern_n", ""),
            "invalidation_level": row.get("invalidation_level", ""),
            "quality_flags": row.get("quality_flags", ""),
            "entry_close_price": entry_close if entry_close is not None else "",
            "resolution_status": "pending",
            "target_session_date": "",
            "resolved_close_price": "",
            "actual_return_pct": "",
            "actual_peer_return_pct": "",
            "actual_excess_peer_return_pct": "",
            "decision_correct": "",
            "scored_at": "",
        }
        existing.append(ledger_row)
        existing_keys.add(key)
        appended += 1

    write_ledger(LEDGER_PATH, existing)
    print(f"Appended {appended} new calls. Ledger now has {len(existing)} rows at {LEDGER_PATH}.")
    return 0


def dedup_key(row: dict[str, Any]) -> tuple:
    return (
        row.get("signal_date", "").strip(),
        row.get("symbol", "").strip().upper(),
        row.get("decision", "").strip().lower(),
        str(row.get("horizon_days", "")).strip(),
    )


def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_ledger(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def lookup_close(symbol: str, iso_date: str) -> float | None:
    """Look up close (or LTP fallback) for a symbol on a given trading date."""
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


def parse_number(value: Any) -> float | None:
    if value is None:
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
