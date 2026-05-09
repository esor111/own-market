"""
Complete daily refresh workflow for NEPSE trading research lab.

This is the master daily refresh script that orchestrates all three data collection tasks:
1. Broker-flow data (Merolagani floorsheet scraping)
2. Intraday tape data (nepsealpha.com minute/hourly volume)
3. Price data (ShareSansar CSV archive) - MANUAL STEP

Usage:
    # Full daily refresh for today's trading session
    python run_daily_refresh_all.py --date 2026-04-30

    # Dry run to see what would be executed
    python run_daily_refresh_all.py --date 2026-04-30 --dry-run

    # Skip intraday collection (if already done)
    python run_daily_refresh_all.py --date 2026-04-30 --skip-intraday

    # Skip broker-flow collection (if already done)
    python run_daily_refresh_all.py --date 2026-04-30 --skip-broker-flow

What it does:
    1. Validates the target date is a trading day
    2. Runs broker-flow scrape for all tracked symbols (run_daily_scrape.py)
    3. Runs intraday tape collection for all 7 core symbols (PowerShell script)
    4. Runs persistence shadow report generation (run_persistence_shadow_daily.py)
    5. Prints a comprehensive summary of what was collected

What it does NOT do:
    - Scrape ShareSansar price data (must be done manually or via separate script)
    - Update psychology engine signals (separate task after backfill)
    - Modify any frozen policy or live trading decisions

Daily workflow (run after market close at 3:00 PM Nepal time):
    1. Wait 30 minutes for data to settle (3:30 PM Nepal time)
    2. Run: python run_daily_refresh_all.py --date <TODAY>
    3. Manually verify ShareSansar CSV was updated (check ../sharesansar_datascrape/data/)
    4. Review the summary output for any failures

Recommended schedule:
    - Manual: Run this script each evening after 3:30 PM Nepal time
    - Automated: Windows Task Scheduler at 3:30 PM Nepal time daily
    - Cloud: GitHub Actions workflow (requires setup)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

# Import trading calendar
sys.path.insert(0, str(SCRIPT_DIR))
from nepse_trading_calendar import is_trading_weekday

# Scripts to orchestrate
RUN_DAILY_SCRAPE = SCRIPT_DIR / "run_daily_scrape.py"
RUN_PERSISTENCE_SHADOW = SCRIPT_DIR / "run_persistence_shadow_daily.py"

# Intraday collection
INTRADAY_SCRIPT = ROOT.parent / "refresh_upper_data.ps1"
INTRADAY_SYMBOLS = ["UPPER", "AKPL", "API", "AHPC", "RADHI", "RHPL", "BHCL"]

# Price data location (for verification)
PRICE_DATA_DIR = ROOT.parent / "sharesansar_datascrape" / "data"


def main() -> int:
    args = parse_args()
    target_date = args.date

    print("=" * 80)
    print(f"NEPSE DAILY REFRESH — {target_date}")
    print(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Step 0: Validate trading day
    if not is_trading_weekday(target_date):
        print(f"\n⚠️  WARNING: {target_date} is not a trading weekday.")
        print("   The scraper may return empty results.")
        if not args.force:
            print("   Use --force to proceed anyway.")
            return 1

    # Step 1: Broker-flow scrape
    if not args.skip_broker_flow:
        print("\n" + "=" * 80)
        print("[STEP 1/4] BROKER-FLOW SCRAPE (Merolagani floorsheet)")
        print("=" * 80)
        if args.dry_run:
            print("[DRY RUN] Would run: python run_daily_scrape.py --date", target_date)
        else:
            result = run_broker_flow_scrape(target_date, args.headed)
            if result != 0:
                print(f"\n❌ FAILED: Broker-flow scrape exited with code {result}")
                if not args.continue_on_error:
                    return result
    else:
        print("\n[STEP 1/4] BROKER-FLOW SCRAPE — SKIPPED (--skip-broker-flow)")

    # Step 2: Intraday tape collection
    if not args.skip_intraday:
        print("\n" + "=" * 80)
        print("[STEP 2/4] INTRADAY TAPE COLLECTION (nepsealpha.com)")
        print("=" * 80)
        if args.dry_run:
            print(f"[DRY RUN] Would scrape {len(INTRADAY_SYMBOLS)} symbols: {', '.join(INTRADAY_SYMBOLS)}")
        else:
            result = run_intraday_collection(args.intraday_days)
            if result != 0:
                print(f"\n❌ FAILED: Intraday collection exited with code {result}")
                if not args.continue_on_error:
                    return result
    else:
        print("\n[STEP 2/4] INTRADAY TAPE COLLECTION — SKIPPED (--skip-intraday)")

    # Step 3: Price data verification
    print("\n" + "=" * 80)
    print("[STEP 3/4] PRICE DATA VERIFICATION (ShareSansar CSV)")
    print("=" * 80)
    price_status = verify_price_data(target_date)
    if not price_status["exists"]:
        print(f"\n⚠️  WARNING: ShareSansar CSV for {target_date} not found.")
        print(f"   Expected location: {price_status['expected_path']}")
        print("   This must be scraped manually or via separate script:")
        print(f"   python sharesansar_datascrape/scrape_nepse.py --start-date {target_date} --end-date {target_date}")
        if not args.continue_on_error:
            print("\n   Use --continue-on-error to proceed anyway.")
            return 2
    else:
        print(f"✅ Price data found: {price_status['path']}")

    # Step 4: Persistence shadow report
    if not args.skip_shadow_report:
        print("\n" + "=" * 80)
        print("[STEP 4/4] PERSISTENCE SHADOW REPORT")
        print("=" * 80)
        if args.dry_run:
            print("[DRY RUN] Would run: python run_persistence_shadow_daily.py --date", target_date)
        else:
            result = run_persistence_shadow_report(target_date)
            if result != 0:
                print(f"\n❌ FAILED: Shadow report exited with code {result}")
                if not args.continue_on_error:
                    return result
    else:
        print("\n[STEP 4/4] PERSISTENCE SHADOW REPORT — SKIPPED (--skip-shadow-report)")

    # Final summary
    print("\n" + "=" * 80)
    print("✅ DAILY REFRESH COMPLETE")
    print("=" * 80)
    print(f"Date: {target_date}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nData collected:")
    print(f"  ✅ Broker-flow: {'SKIPPED' if args.skip_broker_flow else 'DONE'}")
    print(f"  ✅ Intraday tape: {'SKIPPED' if args.skip_intraday else 'DONE'}")
    print(f"  {'✅' if price_status.get('exists') else '⚠️ '} Price data: {'FOUND' if price_status.get('exists') else 'MISSING'}")
    print(f"  ✅ Shadow report: {'SKIPPED' if args.skip_shadow_report else 'DONE'}")
    print("\nNext steps:")
    print("  1. Review shadow report: market-gist/data/validation/persistence_shadow_reports/")
    print("  2. Check for any failed scrapes in the logs above")
    if not price_status.get("exists"):
        print(f"  3. ⚠️  MANUAL: Scrape ShareSansar price data for {target_date}")
    print("=" * 80)
    return 0


def run_broker_flow_scrape(target_date: str, headed: bool = False) -> int:
    """Run the daily broker-flow scrape script."""
    cmd = [sys.executable, str(RUN_DAILY_SCRAPE), "--date", target_date]
    if headed:
        cmd.append("--headed")
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(SCRIPT_DIR))
    return result.returncode


def run_intraday_collection(days: int = 31) -> int:
    """Run the intraday tape collection for all symbols."""
    if not INTRADAY_SCRIPT.exists():
        print(f"⚠️  WARNING: Intraday script not found: {INTRADAY_SCRIPT}")
        print("   Skipping intraday collection.")
        return 0

    print(f"Collecting intraday data for {len(INTRADAY_SYMBOLS)} symbols...")
    print(f"Days to collect: {days}")
    
    failed = []
    for i, symbol in enumerate(INTRADAY_SYMBOLS, 1):
        print(f"\n[{i}/{len(INTRADAY_SYMBOLS)}] Scraping {symbol}...")
        cmd = [
            "powershell.exe",
            "-ExecutionPolicy", "Bypass",
            "-File", str(INTRADAY_SCRIPT),
            "-Symbol", symbol,
            "-Days", str(days)
        ]
        result = subprocess.run(cmd, cwd=str(INTRADAY_SCRIPT.parent))
        if result.returncode != 0:
            print(f"❌ FAILED: {symbol}")
            failed.append(symbol)
        else:
            print(f"✅ SUCCESS: {symbol}")
        
        # Brief pause between symbols to avoid rate limiting
        if i < len(INTRADAY_SYMBOLS):
            import time
            time.sleep(5)
    
    if failed:
        print(f"\n⚠️  {len(failed)} symbols failed: {', '.join(failed)}")
        return 1
    
    print(f"\n✅ All {len(INTRADAY_SYMBOLS)} symbols collected successfully")
    return 0


def verify_price_data(target_date: str) -> dict:
    """Check if ShareSansar CSV exists for the target date."""
    # ShareSansar uses MM_DD_YYYY format
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    filename = dt.strftime("%m_%d_%Y.csv")
    expected_path = PRICE_DATA_DIR / filename
    
    return {
        "exists": expected_path.exists(),
        "path": expected_path if expected_path.exists() else None,
        "expected_path": expected_path,
    }


def run_persistence_shadow_report(target_date: str) -> int:
    """Run the persistence shadow report generation."""
    cmd = [sys.executable, str(RUN_PERSISTENCE_SHADOW), "--date", target_date]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(SCRIPT_DIR))
    return result.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Complete daily refresh workflow for NEPSE trading research lab.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full daily refresh for today
  python run_daily_refresh_all.py --date 2026-04-30

  # Dry run to see what would be executed
  python run_daily_refresh_all.py --date 2026-04-30 --dry-run

  # Skip intraday collection (if already done)
  python run_daily_refresh_all.py --date 2026-04-30 --skip-intraday

  # Continue even if some steps fail
  python run_daily_refresh_all.py --date 2026-04-30 --continue-on-error
        """
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Trading session date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be executed without running",
    )
    parser.add_argument(
        "--skip-broker-flow",
        action="store_true",
        help="Skip broker-flow scraping (if already done)",
    )
    parser.add_argument(
        "--skip-intraday",
        action="store_true",
        help="Skip intraday tape collection (if already done)",
    )
    parser.add_argument(
        "--skip-shadow-report",
        action="store_true",
        help="Skip persistence shadow report generation",
    )
    parser.add_argument(
        "--intraday-days",
        type=int,
        default=31,
        help="Number of days to collect for intraday data (default: 31)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser headed instead of headless (for debugging)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Proceed even if target date is not a trading weekday",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue to next step even if current step fails",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
