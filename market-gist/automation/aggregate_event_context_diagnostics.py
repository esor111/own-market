"""
Aggregate event-context diagnostics across multiple replay runs.

Usage:
    python aggregate_event_context_diagnostics.py '@replay_basket_v1' REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from datetime import datetime

from config import VALIDATION_DIR
from replay_event_context_diagnostics import save_json, save_text, collect_event_context_records, summarize_event_context_records


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")


def _render_markdown(summary):
    lines = [
        "# Aggregate Replay Event Context Diagnostics",
        "",
        f"- aggregate_id: `{summary['replay_id']}`",
        f"- replay_list_name: `{summary['replay_list_name']}`",
        f"- built_at: `{summary['built_at']}`",
        f"- comparison_count: `{summary['comparison_count']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in summary.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")
    lines.extend(["", "## Notes", ""])
    for note in summary.get("notes", []):
        lines.append(f"- {note}")
    lines.extend(["", "## Event State Buckets", ""])
    for key, value in summary.get("event_state_buckets", {}).items():
        lines.append(
            f"- `{key}`: count `{value['count']}`, actionable `{value['actionable_count']}`, "
            f"good_call_rate `{value['good_call_rate']}`, bad_or_mixed_call_rate `{value['bad_or_mixed_call_rate']}`, "
            f"missed_opportunity_rate `{value['missed_opportunity_rate']}`, good_avoid_rate `{value['good_avoid_rate']}`"
        )
    lines.extend(["", "## Event Type Profiles", ""])
    for item in summary.get("event_type_profiles", []):
        lines.append(
            f"- `{item['event_type']}`: count `{item['count']}`, active_count `{item['active_count']}`, "
            f"good_call_rate `{item['good_call_rate']}`, bad_or_mixed_call_rate `{item['bad_or_mixed_call_rate']}`, "
            f"missed_opportunity_rate `{item['missed_opportunity_rate']}`, good_avoid_rate `{item['good_avoid_rate']}`"
        )
    return "\n".join(lines) + "\n"


def build_aggregate_event_context_diagnostics(replay_ids, replay_list_name):
    all_records = []
    for replay_id in replay_ids:
        _, records = collect_event_context_records(replay_id, replay_list_name)
        all_records.extend(records)

    aggregate_id = f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_event_context_diagnostics_v1"
    notes = [
        "this is an aggregate descriptive review across existing replay runs",
        "it is useful for signal discovery but less pure than a single frozen full-year replay because the source runs may span different replay variants",
        "event_date currently uses the replay-safe publication date for the historical disclosure sources",
    ]
    summary = summarize_event_context_records(all_records, aggregate_id, replay_list_name, notes=notes)
    summary["replay_ids"] = replay_ids
    summary["aggregate_type"] = "multi_replay_review"

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_event_context_diagnostics_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_event_context_diagnostics_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_event_context_diagnostics_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_event_context_diagnostics_v1.md")
    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) < 3:
        print("Usage: python aggregate_event_context_diagnostics.py '@replay_basket_v1' REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    replay_list_name = sys.argv[1]
    replay_ids = sys.argv[2:]
    summary, latest_json_path, latest_md_path = build_aggregate_event_context_diagnostics(replay_ids, replay_list_name)
    print(json.dumps({
        "replay_list_name": replay_list_name,
        "replay_id_count": len(replay_ids),
        "comparison_count": summary["comparison_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
