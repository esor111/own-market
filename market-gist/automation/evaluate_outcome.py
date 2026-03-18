"""
Evaluate the realized outcome of a prior stored decision using later bars.
Usage: python evaluate_outcome.py SMHL 2026-03-18 1W
"""
import asyncio
import json
import os
import sys
from datetime import datetime

from browser_actions import BrowserAutomation
from config import get_decision_filename, get_run_directories, get_session_id
from file_generator import FileGenerator
from outcome_tracker import OutcomeTracker

for stream_name in ("stdout", "stderr"):
    stream = getattr(sys, stream_name, None)
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def evaluate_outcome_for_run(symbol, run_date, timeframe="1W", evaluation_date=None):
    symbol = symbol.upper()
    evaluation_date = evaluation_date or datetime.now().strftime("%Y-%m-%d")
    run_dirs = get_run_directories(symbol, run_date)
    decision_path = os.path.join(
        run_dirs["normalized_decisions"],
        get_decision_filename(symbol, timeframe, run_date)
    )
    bars_path = os.path.join(run_dirs["raw_tables"], f"{run_date}__{symbol}__{timeframe}__bar_extract.json")

    if not os.path.exists(decision_path):
        raise FileNotFoundError(f"Decision record not found: {decision_path}")
    if not os.path.exists(bars_path):
        raise FileNotFoundError(f"Bar extract not found: {bars_path}")

    decision_record = load_json(decision_path)
    original_bars_payload = load_json(bars_path)
    original_bars = original_bars_payload.get("data", {}).get("bars", [])
    last_reference_time = original_bars[-1].get("close_time_ms") if original_bars else None

    browser = BrowserAutomation()
    try:
        await browser.start()
        await browser.search_and_load_symbol(symbol)
        await asyncio.sleep(2)
        await browser.set_timeframe(timeframe)
        await asyncio.sleep(2)

        latest_bars_payload = await browser.extract_recent_bars(limit=120)
    finally:
        await browser.close()

    evaluation_extract_path = os.path.join(
        run_dirs["raw_tables"],
        f"{run_date}__{symbol}__{timeframe}__outcome_eval_bars.json"
    )
    with open(evaluation_extract_path, "w", encoding="utf-8") as f:
        json.dump(latest_bars_payload, f, indent=2)

    latest_bars = latest_bars_payload.get("bars", [])
    future_bars = []
    if last_reference_time is not None:
        future_bars = [bar for bar in latest_bars if (bar.get("close_time_ms") or 0) > last_reference_time]

    tracker = OutcomeTracker()
    outcome_data = tracker.evaluate(decision_record, future_bars, evaluation_date, timeframe)

    file_gen = FileGenerator(get_session_id(symbol, timeframe, run_date), run_date, run_dirs)
    evidence_refs = [
        os.path.relpath(decision_path, run_dirs["base"]).replace("\\", "/"),
        os.path.relpath(bars_path, run_dirs["base"]).replace("\\", "/"),
        os.path.relpath(evaluation_extract_path, run_dirs["base"]).replace("\\", "/")
    ]
    outcome_path = file_gen.generate_outcome_record(symbol, timeframe, outcome_data, evidence_refs)

    return {
        "outcome_path": outcome_path,
        "outcome_data": outcome_data,
        "decision_path": decision_path,
        "bars_path": bars_path
    }


async def main():
    if len(sys.argv) < 3:
        print("Usage: python evaluate_outcome.py SYMBOL RUN_DATE [TIMEFRAME]")
        sys.exit(1)

    symbol = sys.argv[1].upper()
    run_date = sys.argv[2]
    timeframe = sys.argv[3] if len(sys.argv) > 3 else "1W"

    result = await evaluate_outcome_for_run(symbol, run_date, timeframe)
    print(f"Outcome evaluated for {symbol} {timeframe} ({run_date})")
    print(json.dumps(result["outcome_data"], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
