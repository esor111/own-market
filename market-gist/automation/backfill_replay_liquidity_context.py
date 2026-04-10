"""
Backfill missing replay-safe liquidity context into existing frozen replay cases.

This is a descriptive enrichment only:
- does not change replay decisions
- only fills missing `historical_context.liquidity_execution_context`
- uses point-in-time local symbol history already available to the replay

Usage:
    python backfill_replay_liquidity_context.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from datetime import datetime
from glob import glob

from config import REPLAYS_DIR
from replay_case_builder import _load_history_rows
from replay_liquidity_upgrade import build_replay_liquidity_execution_context


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _frozen_case_paths(replay_id):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    return sorted(glob(os.path.join(replay_root, "sessions", "*", "*", "normalized", "*__frozen_case_v1.json")))


def backfill_replay_liquidity_context(replay_id):
    updated = 0
    skipped_existing = 0
    missing_history = 0
    errors = []

    for path in _frozen_case_paths(replay_id):
        try:
            frozen_case = load_json(path)
            historical = frozen_case.get("historical_context") or {}
            if historical.get("liquidity_execution_context"):
                skipped_existing += 1
                continue

            symbol = frozen_case.get("symbol")
            session_date = frozen_case.get("session_date")
            truth_source = frozen_case.get("truth_source") or "sharesansar_local"
            history_rows = _load_history_rows(symbol, session_date, truth_source_name=truth_source)
            if not history_rows:
                missing_history += 1
                continue

            historical["liquidity_execution_context"] = build_replay_liquidity_execution_context(
                history_rows,
                session_date,
            )
            frozen_case["historical_context"] = historical
            save_json(path, frozen_case)
            updated += 1
        except Exception as exc:  # noqa: BLE001
            errors.append({
                "path": path,
                "error": str(exc),
            })

    return {
        "replay_id": replay_id,
        "built_at": datetime.now().isoformat(),
        "updated_count": updated,
        "skipped_existing_count": skipped_existing,
        "missing_history_count": missing_history,
        "error_count": len(errors),
        "errors": errors[:20],
    }


def main(argv=None):
    replay_ids = argv or sys.argv[1:]
    if not replay_ids:
        print("Usage: python backfill_replay_liquidity_context.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    summaries = [backfill_replay_liquidity_context(replay_id) for replay_id in replay_ids]
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
