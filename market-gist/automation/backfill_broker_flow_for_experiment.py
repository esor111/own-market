"""
Backfill broker flow data for all dates needed by the Layer 2 experiment.

This script generates the exact commands to run the Merolagani floorsheet
backfill for NABIL, EBL, and SANIMA across all dates where we have
scored predictions or entry research dataset rows.

Total: ~206 (date, symbol) pairs across 2023-07 to 2025-12.

Usage:
    # Dry run — show what would be backfilled:
    python backfill_broker_flow_for_experiment.py --dry-run

    # Run the actual backfill (requires Chrome, takes ~2-5 min per symbol range):
    python backfill_broker_flow_for_experiment.py --run

    # Run for a single symbol:
    python backfill_broker_flow_for_experiment.py --run --symbol NABIL

    # Run headed (visible browser):
    python backfill_broker_flow_for_experiment.py --run --headed
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_ROOT = BASE.parent if (BASE.parent / "data").exists() else BASE / ".."
SCORES_DIR = DATA_ROOT / "data" / "predictions" / "replay_scores"
DATASET_PATH = DATA_ROOT / "data" / "validation" / "learning_reviews" / "latest__entry_research_dataset_v1.json"
LEDGER_ROOT = DATA_ROOT / "broker_flow_ledger"
BACKFILL_SCRIPT = BASE / "backfill_merolagani_floorsheet.py"

TARGET_SYMBOLS = ["NABIL", "EBL", "SANIMA"]


def collect_needed_dates():
    """Collect all dates we need broker flow for, from both data sources."""
    dates_by_sym = {sym: set() for sym in TARGET_SYMBOLS}

    # Source 1: scored replay predictions
    if SCORES_DIR.exists():
        for sf in SCORES_DIR.glob("*.json"):
            with open(sf) as f:
                s = json.load(f)
            pid = s.get("prediction_id", "")
            parts = pid.split("__")
            if len(parts) >= 3:
                date, sym = parts[1], parts[2]
                if sym in dates_by_sym:
                    dates_by_sym[sym].add(date)

    # Source 2: 526-row entry research dataset
    if DATASET_PATH.exists():
        with open(DATASET_PATH) as f:
            data = json.load(f)
        for row in data.get("rows", []):
            sym = row.get("symbol")
            date = row.get("session_date")
            if sym in dates_by_sym and date:
                dates_by_sym[sym].add(date)

    return dates_by_sym


def check_existing(dates_by_sym):
    """Check which dates already have broker flow data."""
    missing = {sym: set() for sym in TARGET_SYMBOLS}
    existing = {sym: set() for sym in TARGET_SYMBOLS}

    for sym, dates in dates_by_sym.items():
        for date in dates:
            # Check both ledger and raw_merolagani
            ledger_file = LEDGER_ROOT / sym / f"{date}.json"
            raw_file = LEDGER_ROOT / "raw_merolagani" / sym / f"{date}.json"
            if ledger_file.exists() or raw_file.exists():
                existing[sym].add(date)
            else:
                missing[sym].add(date)

    return existing, missing


def build_date_ranges(dates):
    """Group consecutive dates into ranges for efficient backfill.
    Merolagani backfill script takes --start-date and --end-date,
    so grouping by month is more efficient than individual dates."""
    if not dates:
        return []

    sorted_dates = sorted(dates)
    ranges = []

    # Group by year-month for manageable batches
    from collections import defaultdict
    by_month = defaultdict(list)
    for d in sorted_dates:
        ym = d[:7]  # YYYY-MM
        by_month[ym].append(d)

    for ym in sorted(by_month.keys()):
        month_dates = sorted(by_month[ym])
        # Use first and last date of the month as range
        # The backfill script will skip non-trading days automatically
        ranges.append((month_dates[0], month_dates[-1]))

    return ranges


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Show what would be backfilled")
    parser.add_argument("--run", action="store_true", help="Actually run the backfill")
    parser.add_argument("--symbol", help="Only backfill one symbol")
    parser.add_argument("--headed", action="store_true", help="Run browser headed (visible)")
    args = parser.parse_args()

    if not args.dry_run and not args.run:
        args.dry_run = True

    dates_by_sym = collect_needed_dates()
    existing, missing = check_existing(dates_by_sym)

    # Summary
    print("=" * 60)
    print("BROKER FLOW BACKFILL FOR LAYER 2 EXPERIMENT")
    print("=" * 60)
    print()

    total_needed = sum(len(d) for d in dates_by_sym.values())
    total_existing = sum(len(d) for d in existing.values())
    total_missing = sum(len(d) for d in missing.values())

    print(f"Total dates needed:   {total_needed}")
    print(f"Already have:         {total_existing}")
    print(f"Need to backfill:     {total_missing}")
    print()

    for sym in TARGET_SYMBOLS:
        n = len(dates_by_sym[sym])
        e = len(existing[sym])
        m = len(missing[sym])
        print(f"  {sym:8s}: {n:3d} needed, {e:3d} have, {m:3d} missing")
    print()

    if total_missing == 0:
        print("All broker flow data already exists. Nothing to backfill.")
        return

    # Build commands
    symbols_to_run = [args.symbol.upper()] if args.symbol else TARGET_SYMBOLS
    commands = []

    for sym in symbols_to_run:
        if sym not in missing or not missing[sym]:
            continue

        ranges = build_date_ranges(missing[sym])
        for start, end in ranges:
            cmd = [
                sys.executable,
                str(BACKFILL_SCRIPT),
                "--symbol", sym,
                "--start-date", start,
                "--end-date", end,
            ]
            if args.headed:
                cmd.append("--headed")
            commands.append((sym, start, end, cmd))

    if args.dry_run:
        print("DRY RUN — commands that would be executed:")
        print()
        for sym, start, end, cmd in commands:
            date_count = len([d for d in missing[sym] if start <= d <= end])
            print(f"  # {sym} {start} to {end} ({date_count} dates)")
            print(f"  {' '.join(cmd)}")
            print()

        print(f"Total commands: {len(commands)}")
        print()
        print("To run for real:")
        print("  python backfill_broker_flow_for_experiment.py --run")
        print("  python backfill_broker_flow_for_experiment.py --run --symbol NABIL")
        print("  python backfill_broker_flow_for_experiment.py --run --headed  # visible browser")
        return

    if args.run:
        print(f"Running {len(commands)} backfill commands...")
        print()

        success = 0
        failed = 0

        for i, (sym, start, end, cmd) in enumerate(commands, 1):
            date_count = len([d for d in missing[sym] if start <= d <= end])
            print(f"[{i}/{len(commands)}] {sym} {start} to {end} ({date_count} dates)...")

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 min max per range
                    cwd=str(BASE),
                )
                if result.returncode == 0:
                    success += 1
                    print(f"  OK")
                else:
                    failed += 1
                    print(f"  FAILED (exit {result.returncode})")
                    if result.stderr:
                        print(f"  {result.stderr[:200]}")
            except subprocess.TimeoutExpired:
                failed += 1
                print(f"  TIMEOUT (>5 min)")
            except Exception as e:
                failed += 1
                print(f"  ERROR: {e}")

        print()
        print(f"Done. Success: {success}, Failed: {failed}")

        # Recheck coverage
        _, still_missing = check_existing(dates_by_sym)
        total_still_missing = sum(len(d) for d in still_missing.values())
        if total_still_missing > 0:
            print(f"Still missing: {total_still_missing} dates")
        else:
            print("All dates now covered!")


if __name__ == "__main__":
    main()
