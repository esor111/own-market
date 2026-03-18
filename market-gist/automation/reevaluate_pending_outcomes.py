"""
Re-evaluate only pending outcomes for an existing run, then refresh calibration.
Usage: python reevaluate_pending_outcomes.py 2026-03-18 1W
   or: python reevaluate_pending_outcomes.py 2026-03-18 1W @expanded_reliability
"""
import asyncio
import json
import os
import sys
from glob import glob

from calibration_report import build_calibration_summary
from config import (
    VALIDATION_DIR,
    SYMBOLS_DIR,
    get_decision_filename,
    get_run_directories,
    resolve_symbols,
)
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


def discover_symbols_for_run(run_date, timeframe):
    pattern = os.path.join(
        SYMBOLS_DIR,
        "*",
        run_date,
        "normalized",
        "decisions",
        f"{run_date}__*__{timeframe.upper()}__decision_v2.json"
    )
    symbols = []
    for path in glob(pattern):
        try:
            payload = load_json(path)
        except Exception:
            continue
        symbol = payload.get("symbol")
        if symbol:
            symbols.append(str(symbol).upper())

    unique_symbols = []
    seen = set()
    for symbol in sorted(symbols):
        if symbol not in seen:
            seen.add(symbol)
            unique_symbols.append(symbol)
    return unique_symbols


def find_pending_symbols(symbols, run_date, timeframe):
    pending = []
    for symbol in symbols:
        run_dirs = get_run_directories(symbol, run_date)
        outcome_path = os.path.join(
            run_dirs["outcomes_realized_results"],
            f"{run_date}__{symbol}__{timeframe}__outcome_v1.json"
        )
        if not os.path.exists(outcome_path):
            pending.append(symbol)
            continue

        try:
            outcome_data = load_json(outcome_path)
        except Exception:
            pending.append(symbol)
            continue

        if outcome_data.get("outcome_label") == "pending":
            pending.append(symbol)

    return pending


def build_cycle_summary(run_date, timeframe, symbols, calibration_path, calibration_summary):
    results = []
    for symbol in symbols:
        run_dirs = get_run_directories(symbol, run_date)
        decision_path = os.path.join(
            run_dirs["normalized_decisions"],
            get_decision_filename(symbol, timeframe, run_date)
        )
        outcome_path = os.path.join(
            run_dirs["outcomes_realized_results"],
            f"{run_date}__{symbol}__{timeframe}__outcome_v1.json"
        )

        decision = load_json(decision_path) if os.path.exists(decision_path) else {}
        outcome = load_json(outcome_path) if os.path.exists(outcome_path) else {}

        results.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "decision_path": decision_path if os.path.exists(decision_path) else None,
            "action": decision.get("action"),
            "score": decision.get("score"),
            "confidence": decision.get("confidence"),
            "outcome_path": outcome_path if os.path.exists(outcome_path) else None,
            "outcome_label": outcome.get("outcome_label")
        })

    return {
        "run_date": run_date,
        "timeframe": timeframe,
        "symbols": symbols,
        "results": results,
        "calibration_summary_path": calibration_path,
        "usable_calibration_samples": calibration_summary.get("decisions_with_usable_outcomes", 0)
    }


async def main():
    if len(sys.argv) < 2:
        print("Usage: python reevaluate_pending_outcomes.py RUN_DATE [TIMEFRAME] [SYMBOL_OR_LIST ...]")
        sys.exit(1)

    run_date = sys.argv[1]
    timeframe = sys.argv[2] if len(sys.argv) >= 3 else "1W"

    if len(sys.argv) >= 4:
        try:
            symbols = resolve_symbols(sys.argv[3:])
        except ValueError as exc:
            print(str(exc))
            sys.exit(1)
    else:
        symbols = discover_symbols_for_run(run_date, timeframe)

    if not symbols:
        print(f"No symbols found for run_date={run_date} timeframe={timeframe}")
        sys.exit(1)

    pending_symbols = find_pending_symbols(symbols, run_date, timeframe)

    reevaluated = []
    for symbol in pending_symbols:
        result = await evaluate_outcome_for_run(symbol, run_date, timeframe)
        reevaluated.append({
            "symbol": symbol,
            "outcome_path": result["outcome_path"],
            "outcome_label": result["outcome_data"].get("outcome_label")
        })

    calibration_path, calibration_summary = build_calibration_summary()
    cycle_summary = build_cycle_summary(run_date, timeframe, symbols, calibration_path, calibration_summary)

    os.makedirs(VALIDATION_DIR, exist_ok=True)
    cycle_path = os.path.join(VALIDATION_DIR, f"{run_date}__{timeframe}__reliability_cycle.json")
    with open(cycle_path, "w", encoding="utf-8") as f:
        json.dump(cycle_summary, f, indent=2)

    print(json.dumps({
        "run_date": run_date,
        "timeframe": timeframe,
        "symbols_checked": symbols,
        "pending_symbols_found": pending_symbols,
        "reevaluated": reevaluated,
        "calibration_summary_path": calibration_path,
        "reliability_cycle_path": cycle_path,
        "usable_calibration_samples": cycle_summary["usable_calibration_samples"]
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
