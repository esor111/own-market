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
    build_run_label,
    get_decision_filename,
    get_latest_validation_filename,
    get_validation_filename,
    get_run_directories,
    get_session_filename,
    resolve_symbols,
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_summary(run_date, timeframe, run_label, symbols, results):
    """Build the batch summary payload from symbol results."""
    summary = {
        "run_date": run_date,
        "timeframe": timeframe,
        "run_label": run_label,
        "symbols": symbols,
        "results": results,
        "action_counts": {},
        "qc_fail_count": 0,
        "watchlist_priority_counts": {}
    }

    for result in results:
        action = result.get("action") or "unknown"
        summary["action_counts"][action] = summary["action_counts"].get(action, 0) + 1
        if result.get("qc_status") == "fail":
            summary["qc_fail_count"] += 1
        tier = result.get("watchlist_tier") or "none"
        summary["watchlist_priority_counts"][tier] = summary["watchlist_priority_counts"].get(tier, 0) + 1

    results.sort(key=lambda item: (item.get("watchlist_priority") or 99, -(item.get("score") or 0), item.get("symbol") or ""))
    return summary


def write_summary(summary, report_name="batch_validation"):
    """Persist a validation summary and its latest pointer."""
    os.makedirs(VALIDATION_DIR, exist_ok=True)
    output_path = os.path.join(
        VALIDATION_DIR,
        get_validation_filename(
            report_name,
            summary["timeframe"],
            summary["run_date"],
            summary.get("run_label")
        )
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    latest_path = os.path.join(
        VALIDATION_DIR,
        get_latest_validation_filename(
            report_name,
            summary["timeframe"],
            summary.get("run_label")
        )
    )
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return output_path, latest_path


async def run_symbol(symbol, timeframe, run_date):
    automation = StockAnalysisAutomation(symbol, timeframe, run_date=run_date)
    success = await automation.run()

    if not success:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "action": "run_error",
            "setup_type": None,
            "score": None,
            "confidence": None,
            "watchlist_tier": None,
            "watchlist_priority": None,
            "risk_reward_ratio": None,
            "qc_status": "error",
            "qc_findings": ["analysis_run_failed"],
            "session_notes": "analysis_run_failed"
        }

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
        "watchlist_tier": decision.get("watchlist_tier"),
        "watchlist_priority": decision.get("watchlist_priority"),
        "risk_reward_ratio": decision.get("risk_reward_ratio"),
        "qc_status": qc.get("status"),
        "qc_findings": qc.get("findings", []),
        "session_notes": session.get("notes")
    }


async def main():
    if len(sys.argv) < 3:
        print("Usage: python batch_analyze.py TIMEFRAME SYMBOL_OR_LIST [SYMBOL_OR_LIST ...]")
        sys.exit(1)

    timeframe = sys.argv[1]
    raw_symbol_args = sys.argv[2:]
    try:
        symbols = resolve_symbols(raw_symbol_args)
    except ValueError as exc:
        print(str(exc))
        sys.exit(1)
    run_date = datetime.now().strftime("%Y-%m-%d")
    run_label = build_run_label(raw_symbol_args, symbols)

    results = []
    for symbol in symbols:
        results.append(await run_symbol(symbol, timeframe, run_date))

    summary = build_summary(run_date, timeframe, run_label, symbols, results)
    output_path, latest_path = write_summary(summary, "batch_validation")

    print(f"Batch validation saved: {output_path}")
    print(f"Latest batch pointer saved: {latest_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
