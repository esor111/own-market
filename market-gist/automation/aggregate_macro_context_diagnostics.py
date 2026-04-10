"""
Aggregate macro-context diagnostics across multiple replay runs.

Usage:
    python aggregate_macro_context_diagnostics.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from datetime import datetime

from config import VALIDATION_DIR
from replay_macro_context_diagnostics import (
    collect_macro_context_records,
    save_json,
    save_text,
    summarize_macro_context_records,
)


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")


def _render_markdown(summary):
    lines = [
        "# Aggregate Replay Macro Context Diagnostics",
        "",
        f"- aggregate_id: `{summary['replay_id']}`",
        f"- built_at: `{summary['built_at']}`",
        f"- comparison_count: `{summary['comparison_count']}`",
        f"- records_with_macro_context: `{summary['records_with_macro_context']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in summary.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")

    lines.extend(["", "## Notes", ""])
    for note in summary.get("notes", []):
        lines.append(f"- {note}")

    lines.extend(["", "## Calendar Phase Profiles", ""])
    for item in summary.get("calendar_phase_profiles", []):
        lines.append(
            f"- `{item['calendar_phase']}`: count `{item['count']}`, actionable `{item['actionable_count']}`, "
            f"good_call_rate `{item['good_call_rate']}`, bad_or_mixed_call_rate `{item['bad_or_mixed_call_rate']}`, "
            f"missed_opportunity_rate `{item['missed_opportunity_rate']}`, good_avoid_rate `{item['good_avoid_rate']}`"
        )

    lines.extend(["", "## Macro Metric Buckets", ""])
    for metric_summary in summary.get("macro_metric_summaries", []):
        lines.append(f"### `{metric_summary['metric']}`")
        lines.append("")
        lines.append(f"- distinct replay values: `{metric_summary.get('distinct_value_count')}`")
        lines.append(f"- bucket boundaries: `{metric_summary['bucket_boundaries']}`")
        for bucket in metric_summary.get("buckets", []):
            lines.append(
                f"- `{bucket['bucket']}`: count `{bucket['count']}`, value_range `[{bucket['value_min']}, {bucket['value_max']}]`, "
                f"good_call_rate `{bucket['good_call_rate']}`, bad_or_mixed_call_rate `{bucket['bad_or_mixed_call_rate']}`, "
                f"missed_opportunity_rate `{bucket['missed_opportunity_rate']}`, good_avoid_rate `{bucket['good_avoid_rate']}`"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def build_aggregate_macro_context_diagnostics(replay_ids):
    all_records = []
    for replay_id in replay_ids:
        all_records.extend(collect_macro_context_records(replay_id))

    aggregate_id = f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_macro_context_diagnostics_v1"
    notes = [
        "this is an aggregate descriptive review across multiple replay runs",
        "aggregate macro diagnostics are more meaningful than single-month replays because macro snapshots vary mostly across months, not within one month",
        "this remains context-only and does not change any replay rule",
    ]
    summary = summarize_macro_context_records(all_records, aggregate_id, notes=notes)
    summary["replay_ids"] = replay_ids
    summary["aggregate_type"] = "multi_replay_review"

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_macro_context_diagnostics_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_macro_context_diagnostics_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_macro_context_diagnostics_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_macro_context_diagnostics_v1.md")

    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python aggregate_macro_context_diagnostics.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    replay_ids = sys.argv[1:]
    summary, latest_json_path, latest_md_path = build_aggregate_macro_context_diagnostics(replay_ids)
    print(json.dumps({
        "replay_id_count": len(replay_ids),
        "comparison_count": summary["comparison_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
