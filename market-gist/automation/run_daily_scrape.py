"""
Daily broker-flow scrape for all tracked symbols.

Usage:
    python run_daily_scrape.py --date 2026-04-10
    python run_daily_scrape.py --date 2026-04-10 --tier active_shadow --tier research
    python run_daily_scrape.py --date 2026-04-10 --sector hydropower
    python run_daily_scrape.py --date 2026-04-10 --symbol NBB --symbol NICA
    python run_daily_scrape.py --date 2026-04-10 --dry-run

What it does:
    1. Reads scrape_symbol_list.json to resolve which symbols to scrape
    2. Skips symbols that already have a ledger file for the target date
    3. Calls backfill_merolagani_floorsheet.py once with all pending symbols
    4. Prints a summary of results

What it does NOT do:
    - Run the persistence shadow report (use run_persistence_shadow_daily.py)
    - Score any signals
    - Modify any frozen policy

Daily workflow:
    python run_daily_scrape.py --date <DATE>
    python run_persistence_shadow_daily.py --date <DATE>
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from nepse_trading_calendar import is_trading_weekday


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
CONFIG_PATH = SCRIPT_DIR / "scrape_symbol_list.json"
BACKFILL_SCRIPT = SCRIPT_DIR / "backfill_merolagani_floorsheet.py"
LEDGER_ROOT = ROOT / "broker_flow_ledger"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_symbols(config: dict, tiers: list[str] | None, sectors: list[str] | None, explicit: list[str] | None) -> list[str]:
    """Resolve which symbols to scrape based on CLI filters."""
    if explicit:
        return [s.upper().strip() for s in explicit]

    all_symbols: list[str] = []

    if tiers:
        for tier_name in tiers:
            tier = config["tiers"].get(tier_name)
            if tier is None:
                print(f"WARNING: unknown tier '{tier_name}', skipping", file=sys.stderr)
                continue
            all_symbols.extend(tier["symbols"])
    elif sectors:
        for sector_name in sectors:
            sector_syms = config["sectors"].get(sector_name)
            if sector_syms is None:
                print(f"WARNING: unknown sector '{sector_name}', skipping", file=sys.stderr)
                continue
            all_symbols.extend(sector_syms)
    else:
        for tier in config["tiers"].values():
            all_symbols.extend(tier["symbols"])

    seen: set[str] = set()
    unique: list[str] = []
    for sym in all_symbols:
        s = sym.upper().strip()
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


def check_existing(symbols: list[str], target_date: str) -> tuple[list[str], list[str]]:
    """Split symbols into (need_scrape, already_have)."""
    need, have = [], []
    for sym in symbols:
        ledger_path = LEDGER_ROOT / sym / f"{target_date}.json"
        if ledger_path.exists():
            have.append(sym)
        else:
            need.append(sym)
    return need, have


def main() -> int:
    args = parse_args()
    target_date = args.date

    if not is_trading_weekday(target_date):
        print(f"NOTE: {target_date} is not a trading weekday. Scraper may return empty results.")

    config = load_config()
    symbols = resolve_symbols(config, args.tiers, args.sectors, args.symbols)

    if not symbols:
        print("No symbols resolved. Check your filters.")
        return 1

    need_scrape, already_have = check_existing(symbols, target_date)

    print("=" * 70)
    print(f"Daily Broker Flow Scrape — {target_date}")
    print(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"\nTotal symbols: {len(symbols)}")
    print(f"Already have ledger: {len(already_have)} ({', '.join(already_have) if already_have else 'none'})")
    print(f"Need scraping: {len(need_scrape)} ({', '.join(need_scrape) if need_scrape else 'none'})")

    if not need_scrape:
        print("\nNothing to scrape. All symbols already have data for this date.")
        return 0

    if args.dry_run:
        print(f"\n[DRY RUN] Would scrape {len(need_scrape)} symbols: {', '.join(need_scrape)}")
        print(f"[DRY RUN] Command: python backfill_merolagani_floorsheet.py", end="")
        for s in need_scrape:
            print(f" --symbol {s}", end="")
        print(f" --start-date {target_date} --end-date {target_date}")
        return 0

    print(f"\nScraping {len(need_scrape)} symbols...")
    cmd = [sys.executable, str(BACKFILL_SCRIPT)]
    for sym in need_scrape:
        cmd.extend(["--symbol", sym])
    cmd.extend(["--start-date", target_date, "--end-date", target_date])
    if args.headed:
        cmd.append("--headed")

    result = subprocess.run(cmd, cwd=str(SCRIPT_DIR))

    # Post-scrape check
    scraped, failed = [], []
    for sym in need_scrape:
        ledger_path = LEDGER_ROOT / sym / f"{target_date}.json"
        if ledger_path.exists():
            scraped.append(sym)
        else:
            raw_path = LEDGER_ROOT / "raw_merolagani" / sym / f"{target_date}.json"
            if raw_path.exists():
                scraped.append(sym)
            else:
                failed.append(sym)

    print("\n" + "=" * 70)
    print(f"DONE. Daily scrape for {target_date}.")
    print(f"  Scraped: {len(scraped)} ({', '.join(scraped[:10])}{'...' if len(scraped) > 10 else ''})")
    print(f"  Skipped (already had data): {len(already_have)}")
    if failed:
        print(f"  No data produced: {len(failed)} ({', '.join(failed)})")
        print(f"  (May be non-trading day, holiday, or symbol with no floorsheet activity)")
    print(f"Finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    return result.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Daily broker-flow scrape for all tracked symbols."
    )
    parser.add_argument(
        "--date", required=True,
        help="Trading session date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--tier", action="append", dest="tiers",
        help="Filter to specific tier(s): active_shadow, research, shadow_excluded, data_collection_only",
    )
    parser.add_argument(
        "--sector", action="append", dest="sectors",
        help="Filter to specific sector(s): commercial_banks, hydropower, etc.",
    )
    parser.add_argument(
        "--symbol", action="append", dest="symbols",
        help="Override: scrape only these specific symbol(s)",
    )
    parser.add_argument(
        "--headed", action="store_true",
        help="Run Chrome headed instead of headless",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be scraped without executing",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
