"""
Fetch NEPSE API truth data and compare it against an existing browser run.

Usage:
    python compare_nepse_truth.py EBL 2026-03-18 1W
    python compare_nepse_truth.py EBL 2026-03-18 1W nepse_scraper
"""
import json
import os
import sys

from config import get_run_directories
from data_sources import get_truth_source
from truth_comparison import build_truth_comparison


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

    
def maybe_load(path):
    if not os.path.exists(path):
        return None
    return load_json(path)


def build_browser_snapshot(symbol, run_date, timeframe, run_dirs):
    """Load browser-side records from disk for comparison."""
    symbol = symbol.upper()
    browser_daily_path = os.path.join(
        run_dirs["normalized_stocks"],
        f"{run_date}__{symbol}__1D__stock_chart_v2.json"
    )
    browser_primary_path = os.path.join(
        run_dirs["normalized_stocks"],
        f"{run_date}__{symbol}__{timeframe}__stock_chart_v2.json"
    )
    browser_indicator_daily_path = os.path.join(
        run_dirs["normalized_indicators"],
        f"{run_date}__{symbol}__1D__indicator_v2.json"
    )
    browser_market_path = os.path.join(
        run_dirs["normalized_market"],
        f"{run_date}__NEPSE__1D__market_v2.json"
    )
    browser_sector = None
    for filename in os.listdir(run_dirs["normalized_sectors"]):
        if filename.endswith("__sector_v2.json"):
            browser_sector = maybe_load(os.path.join(run_dirs["normalized_sectors"], filename))
            break

    return {
        "daily_stock": maybe_load(browser_daily_path),
        "primary_stock": maybe_load(browser_primary_path),
        "daily_indicator": maybe_load(browser_indicator_daily_path),
        "market": maybe_load(browser_market_path),
        "sector": browser_sector,
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_nepse_truth.py SYMBOL RUN_DATE [TIMEFRAME] [TRUTH_SOURCE]")
        sys.exit(1)

    symbol = sys.argv[1].upper()
    run_date = sys.argv[2]
    timeframe = sys.argv[3] if len(sys.argv) > 3 else "1W"
    truth_source_name = sys.argv[4] if len(sys.argv) > 4 else "nepse_scraper"

    run_dirs = get_run_directories(symbol, run_date)
    adapter = get_truth_source(truth_source_name, verify_ssl=False)

    truth_bundle = adapter.build_truth_bundle(symbol)
    comparison = build_truth_comparison(
        symbol,
        run_date,
        timeframe,
        truth_bundle,
        build_browser_snapshot(symbol, run_date, timeframe, run_dirs)
    )

    truth_path = os.path.join(
        run_dirs["raw_tables"],
        f"{run_date}__{symbol}__api_truth_bundle.json"
    )
    comparison_path = os.path.join(
        run_dirs["raw_tables"],
        f"{run_date}__{symbol}__{timeframe}__api_truth_comparison.json"
    )

    adapter.save_json(truth_path, truth_bundle)
    adapter.save_json(comparison_path, comparison)

    print(json.dumps({
        "truth_bundle_path": truth_path,
        "comparison_path": comparison_path,
        "comparison_summary": {
            "symbol": symbol,
            "timeframe": timeframe,
            "truth_source": truth_source_name,
            "api_business_date": comparison.get("api_business_date"),
            "daily_close_diff": comparison.get("api_vs_browser_daily", {}).get("close_diff"),
            "browser_files_found": comparison.get("browser_files_found"),
        }
    }, indent=2))


if __name__ == "__main__":
    main()
