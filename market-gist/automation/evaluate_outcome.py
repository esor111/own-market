"""
Evaluate the realized outcome of a prior stored decision using later bars.
Usage: python evaluate_outcome.py SMHL 2026-03-18 1W
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from datetime import time as dt_time

from browser_actions import BrowserAutomation
from config import DEFAULT_TRUTH_SOURCE, get_decision_filename, get_run_directories, get_session_id
from data_sources import get_truth_source
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


def to_close_time_ms(business_date):
    """Convert YYYY-MM-DD to an end-of-day millisecond timestamp."""
    if not business_date:
        return None
    try:
        value = datetime.strptime(str(business_date), "%Y-%m-%d")
    except ValueError:
        return None
    value = datetime.combine(value.date(), dt_time(23, 59, 59))
    return int(value.timestamp() * 1000)


def normalize_history_rows(history_payload):
    """Convert provider history rows into the bar format used by OutcomeTracker."""
    if not history_payload:
        return []

    container = history_payload.get("history", history_payload)
    rows = container.get("content", []) if isinstance(container, dict) else []
    bars = []
    for row in rows:
        close_time_ms = to_close_time_ms(row.get("businessDate"))
        bars.append({
            "time": row.get("businessDate"),
            "open": row.get("openPrice"),
            "high": row.get("highPrice"),
            "low": row.get("lowPrice"),
            "close": row.get("closePrice"),
            "volume": row.get("totalTradedQuantity"),
            "close_time_ms": close_time_ms,
        })

    bars.sort(key=lambda item: item.get("close_time_ms") or 0)
    return bars


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
    evidence_refs = [
        os.path.relpath(decision_path, run_dirs["base"]).replace("\\", "/"),
        os.path.relpath(bars_path, run_dirs["base"]).replace("\\", "/"),
    ]

    future_bars = []
    evaluation_extract_path = None
    outcome_source = "none"

    truth_bundle_path = os.path.join(
        run_dirs["raw_tables"],
        f"{run_date}__{symbol}__api_truth_bundle.json"
    )
    truth_bundle = load_json(truth_bundle_path).get("data", {}) if os.path.exists(truth_bundle_path) else None

    if not truth_bundle:
        try:
            truth_source = get_truth_source(DEFAULT_TRUTH_SOURCE, verify_ssl=False)
            truth_bundle = truth_source.build_truth_bundle(symbol)
            evaluation_extract_path = os.path.join(
                run_dirs["raw_tables"],
                f"{run_date}__{symbol}__{timeframe}__outcome_eval_truth.json"
            )
            with open(evaluation_extract_path, "w", encoding="utf-8") as f:
                json.dump(truth_bundle, f, indent=2)
            evidence_refs.append(os.path.relpath(evaluation_extract_path, run_dirs["base"]).replace("\\", "/"))
        except Exception:
            truth_bundle = None

    if truth_bundle:
        history_payload = truth_bundle.get("history", {})
        latest_bars = normalize_history_rows(history_payload)
        if last_reference_time is not None:
            future_bars = [bar for bar in latest_bars if (bar.get("close_time_ms") or 0) > last_reference_time]
        else:
            future_bars = latest_bars
        outcome_source = "truth_history"

    browser_error = None
    if not truth_bundle:
        browser = BrowserAutomation()
        try:
            await browser.start()
            await browser.search_and_load_symbol(symbol)
            await asyncio.sleep(2)
            await browser.set_timeframe(timeframe)
            await asyncio.sleep(2)
            latest_bars_payload = await browser.extract_recent_bars(limit=120)
            evaluation_extract_path = os.path.join(
                run_dirs["raw_tables"],
                f"{run_date}__{symbol}__{timeframe}__outcome_eval_bars.json"
            )
            with open(evaluation_extract_path, "w", encoding="utf-8") as f:
                json.dump(latest_bars_payload, f, indent=2)
            evidence_refs.append(os.path.relpath(evaluation_extract_path, run_dirs["base"]).replace("\\", "/"))
            latest_bars = latest_bars_payload.get("bars", [])
            if last_reference_time is not None:
                future_bars = [bar for bar in latest_bars if (bar.get("close_time_ms") or 0) > last_reference_time]
            else:
                future_bars = latest_bars
            outcome_source = "browser_bars"
        except Exception as exc:
            browser_error = str(exc)
        finally:
            await browser.close()

    tracker = OutcomeTracker()
    outcome_data = tracker.evaluate(decision_record, future_bars, evaluation_date, timeframe)
    note_prefix = f"Outcome source: {outcome_source}."
    if browser_error:
        note_prefix += f" Browser fallback unavailable: {browser_error}."
    if outcome_data.get("notes"):
        outcome_data["notes"] = f"{note_prefix} {outcome_data['notes']}"
    else:
        outcome_data["notes"] = note_prefix

    file_gen = FileGenerator(get_session_id(symbol, timeframe, run_date), run_date, run_dirs)
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
