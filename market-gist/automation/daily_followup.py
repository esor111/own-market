    """
    Run the daily follow-up workflow for an existing run:
    - re-evaluate pending outcomes
    - refresh calibration and reliability cycle
    - rebuild the follow-up queue

    Usage: python daily_followup.py 2026-03-18 1W
    or: python daily_followup.py 2026-03-18 1W @expanded_reliability
    """
    import asyncio
    import json
    import os
    import sys

    from followup_queue import build_queue
    from config import VALIDATION_DIR, build_run_label, get_latest_validation_filename, get_validation_filename
    from reevaluate_pending_outcomes import (
        build_cycle_summary,
        discover_symbols_for_run,
        find_pending_symbols,
    )
    from calibration_report import build_calibration_summary
    from evaluate_outcome import evaluate_outcome_for_run

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


    async def main():
        if len(sys.argv) < 2:
            print("Usage: python daily_followup.py RUN_DATE [TIMEFRAME] [SYMBOL_OR_LIST ...]")
            sys.exit(1)

        run_date = sys.argv[1]
        timeframe = sys.argv[2] if len(sys.argv) >= 3 else "1W"

        if len(sys.argv) >= 4:
            from config import resolve_symbols
            raw_symbol_args = sys.argv[3:]
            try:
                symbols = resolve_symbols(raw_symbol_args)
            except ValueError as exc:
                print(str(exc))
                sys.exit(1)
            run_label = build_run_label(raw_symbol_args, symbols)
        else:
            symbols = discover_symbols_for_run(run_date, timeframe)
            run_label = build_run_label(symbols, symbols)

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
        cycle_summary["run_label"] = run_label

        os.makedirs(VALIDATION_DIR, exist_ok=True)
        cycle_path = os.path.join(
            VALIDATION_DIR,
            get_validation_filename("reliability_cycle", timeframe, run_date, run_label)
        )
        with open(cycle_path, "w", encoding="utf-8") as f:
            json.dump(cycle_summary, f, indent=2)

        latest_cycle_path = os.path.join(
            VALIDATION_DIR,
            get_latest_validation_filename("reliability_cycle", timeframe, run_label)
        )
        with open(latest_cycle_path, "w", encoding="utf-8") as f:
            json.dump(cycle_summary, f, indent=2)

        queue = build_queue(run_date, timeframe, run_label)
        queue_path = os.path.join(
            VALIDATION_DIR,
            get_validation_filename("followup_queue", timeframe, run_date, run_label)
        )
        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2)

        latest_queue_path = os.path.join(
            VALIDATION_DIR,
            get_latest_validation_filename("followup_queue", timeframe, run_label)
        )
        with open(latest_queue_path, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2)

        print(json.dumps({
            "run_date": run_date,
            "timeframe": timeframe,
            "run_label": run_label,
            "symbols_checked": symbols,
            "pending_symbols_found": pending_symbols,
            "reevaluated": reevaluated,
            "calibration_summary_path": calibration_path,
            "reliability_cycle_path": cycle_path,
            "latest_reliability_cycle_path": latest_cycle_path,
            "followup_queue_path": queue_path,
            "latest_followup_queue_path": latest_queue_path,
            "usable_calibration_samples": cycle_summary["usable_calibration_samples"],
            "actionable_pending_count": queue["counts"]["actionable_pending"]
        }, indent=2))


    if __name__ == "__main__":
        asyncio.run(main())
