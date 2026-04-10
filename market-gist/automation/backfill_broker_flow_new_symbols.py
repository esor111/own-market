"""
Backfill broker flow for 5 new symbols: JBBL, MNBBL, AKPL, UPPER, API.

This covers dates where we have scored outcomes PLUS a 15-day lookback buffer
for persistence window computation.

Usage:
    python backfill_broker_flow_new_symbols.py --dry-run
    python backfill_broker_flow_new_symbols.py --run --headed
    python backfill_broker_flow_new_symbols.py --run --symbol AKPL --headed
"""

import argparse
import json
import os
import glob
import subprocess
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
SCORES_DIR = ROOT / "data" / "predictions" / "replay_scores"
DATASET_PATH = ROOT / "data" / "validation" / "learning_reviews" / "latest__entry_research_dataset_v1.json"
LEDGER_ROOT = ROOT / "broker_flow_ledger"
BACKFILL_SCRIPT = BASE / "backfill_merolagani_floorsheet.py"

TARGET_SYMBOLS = ["JBBL", "MNBBL", "AKPL", "UPPER", "API"]
TRADING_WEEKDAYS = {6, 0, 1, 2, 3}  # Sun=6, Mon=0, Tue=1, Wed=2, Thu=3


def collect_outcome_dates():
    """Dates where we have scored outcomes."""
    dates = {s: set() for s in TARGET_SYMBOLS}

    for sf in SCORES_DIR.glob("*.json"):
        s = json.loads(sf.read_text())
        pid = s.get("prediction_id", "")
        parts = pid.split("__")
        if len(parts) >= 3 and parts[2] in dates:
            dates[parts[2]].add(parts[1])

    if DATASET_PATH.exists():
        data = json.loads(DATASET_PATH.read_text())
        for row in data.get("rows", []):
            sym = row.get("symbol")
            dt = row.get("session_date")
            if sym in dates and dt:
                dates[sym].add(dt)

    return dates


def expand_with_lookback(outcome_dates, lookback_calendar_days=25):
    """Add lookback days before each outcome date for persistence computation."""
    all_dates = {s: set() for s in TARGET_SYMBOLS}

    for sym, dates in outcome_dates.items():
        for date_str in dates:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            all_dates[sym].add(date_str)
            for offset in range(1, lookback_calendar_days + 1):
                prior = dt - timedelta(days=offset)
                if prior.weekday() in TRADING_WEEKDAYS:
                    all_dates[sym].add(prior.strftime("%Y-%m-%d"))

    return all_dates


def check_existing(all_dates):
    """Check what already exists."""
    missing = {s: set() for s in TARGET_SYMBOLS}
    existing = {s: set() for s in TARGET_SYMBOLS}

    for sym, dates in all_dates.items():
        sym_dir = LEDGER_ROOT / sym
        raw_dir = LEDGER_ROOT / "raw_merolagani" / sym
        for d in dates:
            if (sym_dir / f"{d}.json").exists() or (raw_dir / f"{d}.json").exists():
                existing[sym].add(d)
            else:
                missing[sym].add(d)

    return existing, missing


def build_month_ranges(dates):
    """Group dates by month for efficient backfill."""
    by_month = defaultdict(list)
    for d in sorted(dates):
        by_month[d[:7]].append(d)

    ranges = []
    for ym in sorted(by_month.keys()):
        month_dates = sorted(by_month[ym])
        ranges.append((month_dates[0], month_dates[-1]))
    return ranges


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--symbol", help="Only backfill one symbol")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and not args.run:
        args.dry_run = True

    outcome_dates = collect_outcome_dates()
    all_dates = expand_with_lookback(outcome_dates)
    existing, missing = check_existing(all_dates)

    total_needed = sum(len(d) for d in all_dates.values())
    total_existing = sum(len(d) for d in existing.values())
    total_missing = sum(len(d) for d in missing.values())

    print("=" * 60)
    print("BROKER FLOW BACKFILL: NEW SYMBOLS")
    print("=" * 60)
    print(f"Symbols: {', '.join(TARGET_SYMBOLS)}")
    print(f"Total dates needed:  {total_needed}")
    print(f"Already have:        {total_existing}")
    print(f"Need to backfill:    {total_missing}")
    print()

    for sym in TARGET_SYMBOLS:
        o = len(outcome_dates.get(sym, set()))
        n = len(all_dates[sym])
        e = len(existing[sym])
        m = len(missing[sym])
        print(f"  {sym:8s}: {o:3d} outcome dates, {n:3d} total (w/ lookback), {e:3d} have, {m:3d} missing")
    print()

    if total_missing == 0:
        print("All data exists. Nothing to backfill.")
        return

    symbols_to_run = [args.symbol.upper()] if args.symbol else TARGET_SYMBOLS
    commands = []

    for sym in symbols_to_run:
        if not missing.get(sym):
            continue
        ranges = build_month_ranges(missing[sym])
        for start, end in ranges:
            count = len([d for d in missing[sym] if start <= d <= end])
            cmd = [sys.executable, str(BACKFILL_SCRIPT),
                   "--symbol", sym, "--start-date", start, "--end-date", end]
            if args.headed:
                cmd.append("--headed")
            commands.append((sym, start, end, count, cmd))

    if args.dry_run:
        print(f"DRY RUN: {len(commands)} commands\n")
        for sym, start, end, count, cmd in commands:
            print(f"  # {sym} {start} to {end} ({count} dates)")
            print(f"  {' '.join(cmd)}")
            print()
        print(f"Total commands: {len(commands)}")
        print()
        print("To run:")
        print("  python backfill_broker_flow_new_symbols.py --run --headed")
        print("  python backfill_broker_flow_new_symbols.py --run --symbol AKPL --headed")
        return

    if args.run:
        print(f"Running {len(commands)} commands...\n")
        success, failed = 0, 0
        for i, (sym, start, end, count, cmd) in enumerate(commands, 1):
            print(f"[{i}/{len(commands)}] {sym} {start} to {end} ({count} dates)...", end=" ", flush=True)
            try:
                result = subprocess.run(cmd, capture_output=True, text=True,
                                       timeout=600, cwd=str(BASE))
                if result.returncode == 0:
                    success += 1
                    print("OK")
                else:
                    failed += 1
                    print(f"FAIL ({result.returncode})")
                    if result.stderr:
                        print(f"  {result.stderr[:150]}")
            except subprocess.TimeoutExpired:
                failed += 1
                print("TIMEOUT")
            except Exception as e:
                failed += 1
                print(f"ERROR: {e}")

        print(f"\nDone. Success: {success}, Failed: {failed}")
        _, still_missing = check_existing(all_dates)
        sm = sum(len(d) for d in still_missing.values())
        print(f"Still missing: {sm}" if sm else "All covered!")


if __name__ == "__main__":
    main()
