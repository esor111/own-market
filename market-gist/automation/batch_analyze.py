"""
Run analysis for multiple symbols and write a batch validation summary.
Usage: python batch_analyze.py 1W SMHL NABIL
   or: python batch_analyze.py 1W @core_reliability
"""
import asyncio
import json
import os
import sys
from datetime import datetime

from analyze_stock import StockAnalysisAutomation
from config import (
    VALIDATION_DIR,
    get_decision_filename,
    get_run_directories,
    get_session_filename,
    resolve_symbols,
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def run_symbol(symbol, timeframe, run_date):
    automation = StockAnalysisAutomation(symbol, timeframe, run_date=run_date)
    await automation.run()

    run_dirs = get_run_directories(symbol, run_date)
    decision_path = os.path.join(
        run_dirs["normalized_decisions"],
        get_decision_filename(symbol, timeframe, run_date)
    )
    session_path = os.path.join(
        run_dirs["normalized_sessions"],
        get_session_filename(symbol, timeframe, run_date)
    )
    qc_path = os.path.join(run_dirs["raw_tables"], f"{run_date}__{symbol}__{timeframe}__decision_qc.json")

    decision = load_json(decision_path) if os.path.exists(decision_path) else {}
    session = load_json(session_path) if os.path.exists(session_path) else {}
    qc = load_json(qc_path).get("data", {}) if os.path.exists(qc_path) else {}

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "action": decision.get("action"),
        "setup_type": decision.get("setup_type"),
        "score": decision.get("score"),
        "confidence": decision.get("confidence"),
        "qc_status": qc.get("status"),
        "qc_findings": qc.get("findings", []),
        "session_notes": session.get("notes")
    }


async def main():
    if len(sys.argv) < 3:
        print("Usage: python batch_analyze.py TIMEFRAME SYMBOL_OR_LIST [SYMBOL_OR_LIST ...]")
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

    summary = {
        "run_date": run_date,
        "timeframe": timeframe,
        "symbols": symbols,
        "results": results,
        "action_counts": {},
        "qc_fail_count": 0
    }

    for result in results:
        action = result.get("action") or "unknown"
        summary["action_counts"][action] = summary["action_counts"].get(action, 0) + 1
        if result.get("qc_status") == "fail":
            summary["qc_fail_count"] += 1

    os.makedirs(VALIDATION_DIR, exist_ok=True)
    output_path = os.path.join(VALIDATION_DIR, f"{run_date}__{timeframe}__batch_validation.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Batch validation saved: {output_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
