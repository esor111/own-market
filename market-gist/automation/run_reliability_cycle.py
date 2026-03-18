"""
Run analysis, outcome evaluation, and calibration in one repeatable cycle.
Usage: python run_reliability_cycle.py 1W SMHL NABIL
   or: python run_reliability_cycle.py 1W @core_reliability
"""
import asyncio
import json
import os
import sys
from datetime import datetime

from analyze_stock import StockAnalysisAutomation
from calibration_report import build_calibration_summary
from config import VALIDATION_DIR, get_decision_filename, get_run_directories, resolve_symbols
from evaluate_outcome import evaluate_outcome_for_run

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


async def run_symbol(symbol, timeframe, run_date):
    automation = StockAnalysisAutomation(symbol, timeframe, run_date=run_date)
    await automation.run()
    outcome_result = await evaluate_outcome_for_run(symbol, run_date, timeframe)

    run_dirs = get_run_directories(symbol, run_date)
    decision_path = os.path.join(
        run_dirs["normalized_decisions"],
        get_decision_filename(symbol, timeframe, run_date)
    )
    decision = load_json(decision_path)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "decision_path": decision_path,
        "action": decision.get("action"),
        "score": decision.get("score"),
        "confidence": decision.get("confidence"),
        "outcome_path": outcome_result["outcome_path"],
        "outcome_label": outcome_result["outcome_data"].get("outcome_label")
    }


async def main():
    if len(sys.argv) < 3:
        print("Usage: python run_reliability_cycle.py TIMEFRAME SYMBOL_OR_LIST [SYMBOL_OR_LIST ...]")
        sys.exit(1)

    timeframe = sys.argv[1]
    try:
        symbols = resolve_symbols(sys.argv[2:])
    except ValueError as exc:
        print(str(exc))
        sys.exit(1)
    run_date = datetime.now().strftime("%Y-%m-%d")

    results = []
    for symbol in symbols:
        results.append(await run_symbol(symbol, timeframe, run_date))

    calibration_path, calibration_summary = build_calibration_summary()
    cycle_summary = {
        "run_date": run_date,
        "timeframe": timeframe,
        "symbols": symbols,
        "results": results,
        "calibration_summary_path": calibration_path,
        "usable_calibration_samples": calibration_summary.get("decisions_with_usable_outcomes", 0)
    }

    os.makedirs(VALIDATION_DIR, exist_ok=True)
    cycle_path = os.path.join(VALIDATION_DIR, f"{run_date}__{timeframe}__reliability_cycle.json")
    with open(cycle_path, "w", encoding="utf-8") as f:
        json.dump(cycle_summary, f, indent=2)

    print(f"Reliability cycle saved: {cycle_path}")
    print(json.dumps(cycle_summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
