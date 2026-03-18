"""
Build a simple follow-up queue from an existing reliability cycle.
Usage: python followup_queue.py 2026-03-18 1W
"""
import json
import os
import sys

from config import VALIDATION_DIR


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sort_key(item):
    return (
        0 if item.get("action") == "buy" else 1 if item.get("action") == "watch_only" else 2,
        -(item.get("confidence") or 0),
        -(item.get("score") or 0),
        item.get("symbol") or ""
    )


def build_queue(run_date, timeframe):
    cycle_path = os.path.join(VALIDATION_DIR, f"{run_date}__{timeframe}__reliability_cycle.json")
    if not os.path.exists(cycle_path):
        raise FileNotFoundError(f"Reliability cycle not found: {cycle_path}")

    cycle = load_json(cycle_path)
    results = cycle.get("results", [])

    actionable_pending = []
    pending = []
    closed_or_ignored = []

    for result in results:
        row = {
            "symbol": result.get("symbol"),
            "action": result.get("action"),
            "score": result.get("score"),
            "confidence": result.get("confidence"),
            "outcome_label": result.get("outcome_label"),
            "decision_path": result.get("decision_path"),
            "outcome_path": result.get("outcome_path"),
        }

        if row["outcome_label"] == "pending" and row["action"] in {"buy", "watch_only"}:
            actionable_pending.append(row)
        elif row["outcome_label"] == "pending":
            pending.append(row)
        else:
            closed_or_ignored.append(row)

    actionable_pending.sort(key=sort_key)
    pending.sort(key=sort_key)
    closed_or_ignored.sort(key=sort_key)

    return {
        "run_date": run_date,
        "timeframe": timeframe,
        "source_cycle_path": cycle_path,
        "actionable_pending": actionable_pending,
        "pending_non_actionable": pending,
        "closed_or_ignored": closed_or_ignored,
        "counts": {
            "actionable_pending": len(actionable_pending),
            "pending_non_actionable": len(pending),
            "closed_or_ignored": len(closed_or_ignored),
        }
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python followup_queue.py RUN_DATE [TIMEFRAME]")
        sys.exit(1)

    run_date = sys.argv[1]
    timeframe = sys.argv[2] if len(sys.argv) > 2 else "1W"

    queue = build_queue(run_date, timeframe)
    output_path = os.path.join(VALIDATION_DIR, f"{run_date}__{timeframe}__followup_queue.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2)

    print(f"Follow-up queue saved: {output_path}")
    print(json.dumps(queue, indent=2))


if __name__ == "__main__":
    main()
