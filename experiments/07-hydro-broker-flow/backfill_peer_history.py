from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]
PRICE_DIR = ROOT_DIR / "sharesansar_datascrape" / "data"
RUN_DAILY_SCRAPE = ROOT_DIR / "market-gist" / "automation" / "run_daily_scrape.py"
LEDGER_ROOT = ROOT_DIR / "market-gist" / "broker_flow_ledger"
AUTOMATION_DIR = ROOT_DIR / "market-gist" / "automation"

if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))

from nepse_trading_calendar import is_trading_weekday  # noqa: E402

DEFAULT_SYMBOLS = ["UPPER", "API", "AKPL", "AHPC", "BHCL", "RADHI", "RHPL"]


def main() -> int:
    args = parse_args()
    symbols = [symbol.upper().strip() for symbol in (args.symbols or DEFAULT_SYMBOLS)]
    dates = available_price_dates(args.start_date, args.end_date)
    if args.max_dates:
        dates = dates[: args.max_dates]

    print(f"Hydro broker-flow peer backfill")
    print(f"  symbols: {', '.join(symbols)}")
    print(f"  dates: {len(dates)}")
    print(f"  range: {dates[0] if dates else 'none'} to {dates[-1] if dates else 'none'}")
    print(f"  dry_run: {args.dry_run}")
    print()

    total_needed = 0
    total_already = 0
    status_counts: Counter[str] = Counter()
    failures: list[str] = []

    for business_date in dates:
        statuses = {symbol: existing_status(symbol, business_date) for symbol in symbols}
        needed = [symbol for symbol in symbols if statuses[symbol] == "missing"]
        already = [symbol for symbol in symbols if symbol not in needed]
        total_needed += len(needed)
        total_already += len(already)
        status_counts.update(statuses.values())

        print(f"[DATE] {business_date}: need={len(needed)} already={len(already)}")
        if already:
            existing = ", ".join(f"{symbol}({statuses[symbol]})" for symbol in already)
            print(f"       already: {existing}")
        if needed:
            print(f"       scrape:  {', '.join(needed)}")
        else:
            continue

        if args.dry_run:
            continue

        cmd = [sys.executable, str(RUN_DAILY_SCRAPE), "--date", business_date]
        for symbol in symbols:
            cmd.extend(["--symbol", symbol])
        if args.headed:
            cmd.append("--headed")

        result = subprocess.run(cmd, cwd=str(RUN_DAILY_SCRAPE.parent))
        if result.returncode != 0:
            failures.append(business_date)
            if args.stop_on_failure:
                break

    print()
    print("Summary")
    print(f"  symbol-date already present: {total_already}")
    print(f"  symbol-date needed at start: {total_needed}")
    print(f"  status counts: {format_status_counts(status_counts)}")
    print(f"  failed dates: {', '.join(failures) if failures else 'none'}")
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Controlled hydro broker-flow peer backfill for experiment 07.")
    parser.add_argument("--start-date", required=True, help="Inclusive YYYY-MM-DD.")
    parser.add_argument("--end-date", required=True, help="Inclusive YYYY-MM-DD.")
    parser.add_argument("--symbols", nargs="*", help="Optional symbol override.")
    parser.add_argument("--max-dates", type=int, help="Only process the first N eligible price dates.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without scraping.")
    parser.add_argument("--headed", action="store_true", help="Run browser headed.")
    parser.add_argument("--stop-on-failure", action="store_true", help="Stop after first failed scrape date.")
    return parser.parse_args()


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def available_price_dates(start_text: str, end_text: str) -> list[str]:
    start = parse_date(start_text)
    end = parse_date(end_text)
    values: list[date] = []
    for path in PRICE_DIR.glob("*.csv"):
        try:
            current = datetime.strptime(path.stem, "%m_%d_%Y").date()
        except ValueError:
            continue
        if start <= current <= end and is_trading_weekday(current.isoformat()):
            values.append(current)
    return [value.isoformat() for value in sorted(values)]


def existing_status(symbol: str, business_date: str) -> str:
    ledger_path = LEDGER_ROOT / symbol / f"{business_date}.json"
    raw_path = LEDGER_ROOT / "raw_merolagani" / symbol / f"{business_date}.json"
    if ledger_path.exists():
        return "ledger"
    if raw_path.exists():
        return "raw" if raw_has_rows(raw_path) else "raw_empty"
    return "missing"


def raw_has_rows(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(payload.get("rows"))


def format_status_counts(status_counts: Counter[str]) -> str:
    ordered = ["ledger", "raw", "raw_empty", "missing"]
    parts = [f"{key}={status_counts.get(key, 0)}" for key in ordered if status_counts.get(key, 0)]
    return ", ".join(parts) if parts else "none"


if __name__ == "__main__":
    raise SystemExit(main())
