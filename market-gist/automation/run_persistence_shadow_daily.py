"""
One-command daily routine for the persistence shadow lane.

Usage:
    python run_persistence_shadow_daily.py --date 2026-04-09

What it does (in order):
    1. Verify required input directories exist
    2. Verify broker_flow_ledger has data for the target date
    3. Run daily_persistence_shadow_report.py for the date
    4. Run score_persistence_shadow_reports.py to refresh forward outcomes
    5. Print a clear summary: success / partial / failed

What it does NOT do:
    - Scrape Merolagani floorsheet (run backfill_merolagani_floorsheet.py separately)
    - Promote any signal to live trading
    - Touch the experiment lab

This is the persistence-shadow daily entrypoint. Other workflows have their
own runners (run_monitoring_cycle.py, run_system_program_cycle.py).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

REQUIRED_DIRS = [
    ROOT / "broker_flow_ledger",
    ROOT.parent / "sharesansar_datascrape" / "data",
    ROOT / "data" / "validation" / "persistence_shadow_reports",
]

ACTIVE_SYMBOLS = ["NABIL", "EBL", "SANIMA"]
RESEARCH_SYMBOLS = ["AKPL", "UPPER", "API"]

SHADOW_REPORT_SCRIPT = SCRIPT_DIR / "daily_persistence_shadow_report.py"
SCORER_SCRIPT = SCRIPT_DIR / "score_persistence_shadow_reports.py"


def main() -> int:
    args = parse_args()
    target_date = args.date

    print("=" * 70)
    print(f"Persistence Shadow Daily Routine — {target_date}")
    print(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Step 1: input directory check
    print("\n[1/4] Checking required input directories...")
    missing_dirs = [d for d in REQUIRED_DIRS if not d.exists()]
    if missing_dirs:
        print("FAILED: Missing required directories:", file=sys.stderr)
        for d in missing_dirs:
            print(f"  - {d}", file=sys.stderr)
        return 2
    print("OK")

    # Step 2: ledger coverage check for target date
    print(f"\n[2/4] Checking broker flow ledger coverage for {target_date}...")
    ledger_root = ROOT / "broker_flow_ledger"
    coverage = check_ledger_coverage(ledger_root, target_date)
    if not coverage["any_active_present"]:
        print(
            "FAILED: No active-symbol broker flow data for "
            f"{target_date}. Run the floorsheet scraper first.",
            file=sys.stderr,
        )
        print(f"  active symbols missing: {coverage['active_missing']}", file=sys.stderr)
        return 3
    if coverage["active_missing"]:
        print(
            f"WARNING: some active symbols missing for {target_date}: "
            f"{coverage['active_missing']}",
            file=sys.stderr,
        )
    if coverage["research_missing"]:
        print(
            f"NOTE: research symbols missing for {target_date}: "
            f"{coverage['research_missing']} (informational)"
        )
    print(f"OK ({coverage['active_present']} active + {coverage['research_present']} research)")

    # Step 3: run shadow report
    print(f"\n[3/4] Running daily_persistence_shadow_report.py for {target_date}...")
    report_result = run_subprocess([
        sys.executable,
        str(SHADOW_REPORT_SCRIPT),
        "--date", target_date,
    ])
    if report_result != 0:
        print(f"FAILED: shadow report exited with code {report_result}", file=sys.stderr)
        return 4
    print("OK")

    # Step 4: run scorer to refresh forward outcomes
    print("\n[4/4] Running score_persistence_shadow_reports.py to refresh outcomes...")
    scorer_result = run_subprocess([sys.executable, str(SCORER_SCRIPT)])
    if scorer_result != 0:
        print(f"WARNING: scorer exited with code {scorer_result} (non-blocking)", file=sys.stderr)
    else:
        print("OK")

    # Final summary
    print("\n" + "=" * 70)
    print(f"DONE. Persistence shadow report for {target_date} written.")
    print(f"Finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    return 0


def check_ledger_coverage(ledger_root: Path, target_date: str) -> dict:
    """Check which active and research symbols have a ledger file for the date."""
    active_present, active_missing = [], []
    for sym in ACTIVE_SYMBOLS:
        ledger_path = ledger_root / sym / f"{target_date}.json"
        (active_present if ledger_path.exists() else active_missing).append(sym)
    research_present, research_missing = [], []
    for sym in RESEARCH_SYMBOLS:
        ledger_path = ledger_root / sym / f"{target_date}.json"
        (research_present if ledger_path.exists() else research_missing).append(sym)
    return {
        "active_present": active_present,
        "active_missing": active_missing,
        "research_present": research_present,
        "research_missing": research_missing,
        "any_active_present": bool(active_present),
    }


def run_subprocess(cmd: list[str]) -> int:
    """Run a child script and stream its output. Returns exit code."""
    try:
        proc = subprocess.run(cmd, cwd=str(SCRIPT_DIR))
        return proc.returncode
    except FileNotFoundError as exc:
        print(f"FAILED: could not run {cmd}: {exc}", file=sys.stderr)
        return 9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="One-command daily routine for the persistence shadow lane."
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Trading session date in YYYY-MM-DD. Use today's session date.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
