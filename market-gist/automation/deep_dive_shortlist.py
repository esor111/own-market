"""
Run the full browser deep-dive on symbols shortlisted by the latest light scan.
Usage:
    python deep_dive_shortlist.py 1W @expanded_reliability
    python deep_dive_shortlist.py 1W @dev_fast
"""
import asyncio
import json
import os
import sys
from datetime import datetime

from batch_analyze import build_summary, run_symbol, write_summary
from config import (
    VALIDATION_DIR,
    build_run_label,
    get_latest_validation_filename,
    resolve_symbols,
)


def load_light_scan_summary(timeframe, raw_symbol_args):
    """Load the latest light-scan summary for the provided label."""
    resolved_symbols = resolve_symbols(raw_symbol_args)
    run_label = build_run_label(raw_symbol_args, resolved_symbols)
    latest_filename = get_latest_validation_filename("light_scan", timeframe, run_label)
    latest_path = os.path.join(VALIDATION_DIR, latest_filename)

    if not os.path.exists(latest_path):
        raise FileNotFoundError(
            f"Light scan summary not found for {run_label}. Run light_scan.py first."
        )

    with open(latest_path, "r", encoding="utf-8") as handle:
        return json.load(handle), run_label


def extract_shortlist(summary):
    """Return shortlist symbols from the saved light scan."""
    shortlist = summary.get("shortlist") or []
    if shortlist:
        return shortlist

    results = summary.get("results") or []
    return [item.get("symbol") for item in results if item.get("action") == "shortlist" and item.get("symbol")]


async def main():
    if len(sys.argv) < 3:
        print("Usage: python deep_dive_shortlist.py TIMEFRAME SYMBOL_OR_LIST [SYMBOL_OR_LIST ...]")
        sys.exit(1)

    timeframe = sys.argv[1]
    raw_symbol_args = sys.argv[2:]

    try:
        summary, run_label = load_light_scan_summary(timeframe, raw_symbol_args)
    except (ValueError, FileNotFoundError) as exc:
        print(str(exc))
        sys.exit(1)

    shortlist = extract_shortlist(summary)
    if not shortlist:
        print(f"No shortlisted symbols found for {run_label}. Nothing to deep-dive.")
        return

    print(f"Using shortlist from {run_label}: {', '.join(shortlist)}")
    run_date = datetime.now().strftime("%Y-%m-%d")
    deep_dive_results = []
    for symbol in shortlist:
        deep_dive_results.append(await run_symbol(symbol, timeframe, run_date))

    deep_dive_label = f"{run_label}__shortlist"
    combined_summary = build_summary(run_date, timeframe, deep_dive_label, shortlist, deep_dive_results)
    combined_summary["source_light_scan_run_label"] = run_label
    combined_summary["source_light_scan_file"] = get_latest_validation_filename("light_scan", timeframe, run_label)
    combined_summary["scan_shortlist"] = shortlist

    output_path, latest_path = write_summary(combined_summary, "batch_validation")
    print(f"Shortlist deep-dive batch saved: {output_path}")
    print(f"Latest shortlist deep-dive pointer saved: {latest_path}")
    print(json.dumps(combined_summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
