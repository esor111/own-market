"""
Aggregate replay summary and replay review outputs across multiple replay runs.

Usage:
    python aggregate_replay_validation.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import REPLAYS_DIR, VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _load_replay_pair(replay_id):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    replay_summary_path = os.path.join(replay_root, "summaries", "latest__replay_summary_v1.json")
    review_summary_path = os.path.join(replay_root, "summaries", "latest__replay_review_summary_v1.json")
    if not os.path.exists(replay_summary_path):
        raise FileNotFoundError(f"Replay summary not found: {replay_summary_path}")
    if not os.path.exists(review_summary_path):
        raise FileNotFoundError(f"Replay review summary not found: {review_summary_path}")
    return load_json(replay_summary_path), load_json(review_summary_path)


def _month_row(replay_summary, review_summary):
    action_counts = replay_summary.get("action_counts") or {}
    verdict_counts = review_summary.get("verdict_counts") or {}
    actionable_count = int(action_counts.get("buy", 0)) + int(action_counts.get("watch_only", 0))
    avoid_count = int(action_counts.get("avoid", 0))
    good_call_count = int(verdict_counts.get("good_call", 0))
    bad_or_mixed_count = int(verdict_counts.get("bad_call", 0)) + int(verdict_counts.get("mixed_call", 0))
    good_avoid_count = int(verdict_counts.get("good_avoid", 0))
    missed_opportunity_count = int(verdict_counts.get("missed_opportunity", 0))
    return {
        "replay_id": replay_summary.get("replay_id"),
        "start_date": replay_summary.get("start_date"),
        "end_date": replay_summary.get("end_date"),
        "session_count": replay_summary.get("session_count"),
        "case_count": replay_summary.get("case_count"),
        "action_counts": action_counts,
        "comparison_verdict_counts": replay_summary.get("comparison_verdict_counts") or {},
        "top_reason_codes": review_summary.get("top_reason_codes") or [],
        "top_proposals": review_summary.get("top_proposals") or [],
        "actionable_count": actionable_count,
        "avoid_count": avoid_count,
        "good_call_count": good_call_count,
        "bad_or_mixed_count": bad_or_mixed_count,
        "good_avoid_count": good_avoid_count,
        "missed_opportunity_count": missed_opportunity_count,
        "actionable_good_call_rate": _rate(good_call_count, actionable_count),
        "actionable_bad_or_mixed_rate": _rate(bad_or_mixed_count, actionable_count),
        "avoid_good_avoid_rate": _rate(good_avoid_count, avoid_count),
        "avoid_missed_opportunity_rate": _rate(missed_opportunity_count, avoid_count),
    }


def _render_markdown(summary):
    lines = [
        "# Aggregate Replay Validation Summary",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- replay_id_count: `{summary['replay_id_count']}`",
        f"- total_sessions: `{summary['total_sessions']}`",
        f"- total_cases: `{summary['total_cases']}`",
        "",
        "## Notes",
        "",
    ]
    for note in summary.get("notes", []):
        lines.append(f"- {note}")

    lines.extend(["", "## Replay Inputs", ""])
    for replay_id in summary.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")

    lines.extend(["", "## Aggregate Actions", ""])
    for action, count in summary.get("action_counts", {}).items():
        lines.append(f"- `{action}`: `{count}`")

    lines.extend(["", "## Aggregate Verdicts", ""])
    for verdict, count in summary.get("verdict_counts", {}).items():
        lines.append(f"- `{verdict}`: `{count}`")

    lines.extend(["", "## Aggregate Quality Rates", ""])
    rates = summary.get("aggregate_rates") or {}
    lines.append(f"- actionable_good_call_rate: `{rates.get('actionable_good_call_rate')}`")
    lines.append(f"- actionable_bad_or_mixed_rate: `{rates.get('actionable_bad_or_mixed_rate')}`")
    lines.append(f"- avoid_good_avoid_rate: `{rates.get('avoid_good_avoid_rate')}`")
    lines.append(f"- avoid_missed_opportunity_rate: `{rates.get('avoid_missed_opportunity_rate')}`")

    lines.extend(["", "## Top Reason Codes", ""])
    for reason, count in summary.get("top_reason_codes", []):
        lines.append(f"- `{reason}`: `{count}`")

    lines.extend(["", "## Top Proposals", ""])
    for proposal, count in summary.get("top_proposals", []):
        lines.append(f"- {proposal}: `{count}`")

    lines.extend(["", "## Month Breakdown", ""])
    for item in summary.get("month_rows", []):
        lines.append(
            f"- `{item['start_date']} to {item['end_date']}`: cases `{item['case_count']}`, "
            f"actions `{item['action_counts']}`, verdicts `{item['comparison_verdict_counts']}`, "
            f"actionable_good_call_rate `{item['actionable_good_call_rate']}`, "
            f"avoid_good_avoid_rate `{item['avoid_good_avoid_rate']}`"
        )
    return "\n".join(lines) + "\n"


def build_aggregate_replay_validation(replay_ids):
    month_rows = []
    total_sessions = 0
    total_cases = 0
    action_counter = Counter()
    verdict_counter = Counter()
    reason_counter = Counter()
    proposal_counter = Counter()

    for replay_id in replay_ids:
        replay_summary, review_summary = _load_replay_pair(replay_id)
        month_row = _month_row(replay_summary, review_summary)
        month_rows.append(month_row)

        total_sessions += int(replay_summary.get("session_count") or 0)
        total_cases += int(replay_summary.get("case_count") or 0)
        action_counter.update(replay_summary.get("action_counts") or {})
        verdict_counter.update(review_summary.get("verdict_counts") or {})
        reason_counter.update(review_summary.get("reason_code_counts") or {})
        proposal_counter.update(review_summary.get("proposal_counts") or {})

    month_rows.sort(key=lambda item: (item.get("start_date") or "", item.get("replay_id") or ""))

    actionable_count = int(action_counter.get("buy", 0)) + int(action_counter.get("watch_only", 0))
    avoid_count = int(action_counter.get("avoid", 0))
    good_call_count = int(verdict_counter.get("good_call", 0))
    bad_or_mixed_count = int(verdict_counter.get("bad_call", 0)) + int(verdict_counter.get("mixed_call", 0))
    good_avoid_count = int(verdict_counter.get("good_avoid", 0))
    missed_opportunity_count = int(verdict_counter.get("missed_opportunity", 0))

    summary = {
        "schema_version": "1.0",
        "aggregate_id": f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_replay_validation_v1",
        "built_at": datetime.now().isoformat(),
        "replay_id_count": len(replay_ids),
        "replay_ids": replay_ids,
        "notes": [
            "this is a review-layer aggregate across already completed replay runs",
            "it avoids another giant opaque replay run by reusing existing frozen month outputs",
            "the replay inputs include one broad Q1 run plus current monthly champion runs for April through December 2025",
            "confidence calibration is tracked separately and should be interpreted beside, not instead of, these action and verdict counts",
        ],
        "total_sessions": total_sessions,
        "total_cases": total_cases,
        "action_counts": dict(action_counter),
        "verdict_counts": dict(verdict_counter),
        "reason_code_counts": dict(reason_counter),
        "proposal_counts": dict(proposal_counter),
        "top_reason_codes": reason_counter.most_common(10),
        "top_proposals": proposal_counter.most_common(10),
        "aggregate_rates": {
            "actionable_good_call_rate": _rate(good_call_count, actionable_count),
            "actionable_bad_or_mixed_rate": _rate(bad_or_mixed_count, actionable_count),
            "avoid_good_avoid_rate": _rate(good_avoid_count, avoid_count),
            "avoid_missed_opportunity_rate": _rate(missed_opportunity_count, avoid_count),
        },
        "month_rows": month_rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_replay_validation_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_replay_validation_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_replay_validation_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_replay_validation_v1.md")
    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python aggregate_replay_validation.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    replay_ids = sys.argv[1:]
    summary, latest_json_path, latest_md_path = build_aggregate_replay_validation(replay_ids)
    print(json.dumps({
        "replay_id_count": len(replay_ids),
        "total_cases": summary["total_cases"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
