"""
Build an action-aware calibration summary from replay champion runs.

Usage:
    python replay_calibration_report.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from glob import glob
from statistics import mean

from config import REPLAYS_DIR, VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
ACTIONABLE_ACTIONS = {"buy", "watch_only"}


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


def confidence_bucket(confidence):
    if confidence is None:
        return "unknown"
    start = int(confidence // 10) * 10
    end = min(start + 9, 100)
    return f"{start}-{end}"


def score_bucket(score):
    if score is None:
        return "unknown"
    start = int(score // 10) * 10
    end = min(start + 9, 100)
    return f"{start}-{end}"


def _success_from_replay(action, comparison_verdict):
    if action in ACTIONABLE_ACTIONS:
        if comparison_verdict == "good_call":
            return True
        if comparison_verdict == "bad_call":
            return False
        return None
    if action == "avoid":
        if comparison_verdict == "good_avoid":
            return True
        if comparison_verdict == "missed_opportunity":
            return False
        return None
    return None


def _rate(true_count, total_count):
    if not total_count:
        return None
    return round((true_count / total_count) * 100, 2)


def _summarize_bucket_records(records, bucket_key):
    grouped = defaultdict(list)
    for record in records:
        grouped[record.get(bucket_key) or "unknown"].append(record)

    summary = {}
    for bucket_name, items in sorted(grouped.items()):
        usable = [item for item in items if item["success"] is not None]
        success_count = sum(1 for item in usable if item["success"] is True)
        avg_confidence = mean(item["confidence"] for item in items if item["confidence"] is not None) if items else None
        avg_score = mean(item["score"] for item in items if item["score"] is not None) if items else None
        observed_hit_rate = _rate(success_count, len(usable))
        calibration_gap = None
        if observed_hit_rate is not None and avg_confidence is not None:
            calibration_gap = round(observed_hit_rate - avg_confidence, 2)

        summary[bucket_name] = {
            "count": len(items),
            "usable_outcomes": len(usable),
            "success_count": success_count,
            "average_confidence": round(avg_confidence, 2) if avg_confidence is not None else None,
            "average_score": round(avg_score, 2) if avg_score is not None else None,
            "observed_hit_rate_pct": observed_hit_rate,
            "calibration_gap_pct": calibration_gap,
        }
    return summary


def _group_name(action):
    if action in ACTIONABLE_ACTIONS:
        return "actionable"
    if action == "avoid":
        return "avoid"
    return "other"


def collect_replay_calibration_records(replay_ids):
    records = []
    for replay_id in replay_ids:
        replay_root = os.path.join(REPLAYS_DIR, replay_id)
        comparison_paths = glob(os.path.join(replay_root, "sessions", "*", "*", "comparisons", "*__comparison_v1.json"))
        for comparison_path in sorted(comparison_paths):
            comparison = load_json(comparison_path)
            decision_path = comparison_path.replace(f"{os.sep}comparisons{os.sep}", f"{os.sep}derived{os.sep}").replace(
                "__comparison_v1.json", "__replay_decision_v1.json"
            )
            frozen_case_path = comparison_path.replace(f"{os.sep}comparisons{os.sep}", f"{os.sep}normalized{os.sep}").replace(
                "__comparison_v1.json", "__frozen_case_v1.json"
            )
            if not os.path.exists(decision_path) or not os.path.exists(frozen_case_path):
                continue

            decision = load_json(decision_path)
            frozen_case = load_json(frozen_case_path)
            action = decision.get("action")
            comparison_verdict = comparison.get("comparison_verdict")
            success = _success_from_replay(action, comparison_verdict)

            records.append({
                "replay_id": replay_id,
                "replay_month": replay_id[:7],
                "session_id": comparison.get("session_id"),
                "session_date": comparison.get("session_date"),
                "symbol": comparison.get("symbol"),
                "sector_name": frozen_case.get("sector_name") or "UNKNOWN",
                "action": action,
                "action_group": _group_name(action),
                "setup_type": decision.get("setup_type"),
                "score": decision.get("score"),
                "confidence": decision.get("confidence"),
                "confidence_bucket": confidence_bucket(decision.get("confidence")),
                "score_bucket": score_bucket(decision.get("score")),
                "comparison_verdict": comparison_verdict,
                "success": success,
            })
    return records


def _summarize_group(records, action_filter=None):
    group_records = [record for record in records if action_filter(record)]
    usable = [record for record in group_records if record["success"] is not None]
    success_count = sum(1 for record in usable if record["success"] is True)
    return {
        "count": len(group_records),
        "usable_outcomes": len(usable),
        "excluded_ambiguous": len(group_records) - len(usable),
        "observed_hit_rate_pct": _rate(success_count, len(usable)),
        "confidence_buckets": _summarize_bucket_records(group_records, "confidence_bucket"),
        "score_buckets": _summarize_bucket_records(group_records, "score_bucket"),
    }


def _render_markdown(summary):
    lines = [
        "# Replay Champion Calibration Report",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- replay_id_count: `{summary['replay_id_count']}`",
        f"- total_records: `{summary['total_records']}`",
        f"- usable_records: `{summary['usable_records']}`",
        f"- excluded_ambiguous_records: `{summary['excluded_ambiguous_records']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in summary.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")

    lines.extend(["", "## Action Groups", ""])
    for group_name, group_summary in summary.get("action_groups", {}).items():
        lines.append(
            f"- `{group_name}`: count `{group_summary['count']}`, usable `{group_summary['usable_outcomes']}`, "
            f"excluded `{group_summary['excluded_ambiguous']}`, observed_hit_rate `{group_summary['observed_hit_rate_pct']}`"
        )

    lines.extend(["", "## Actionable Confidence Buckets", ""])
    for bucket_name, bucket_summary in summary.get("action_groups", {}).get("actionable", {}).get("confidence_buckets", {}).items():
        lines.append(
            f"- `{bucket_name}`: count `{bucket_summary['count']}`, usable `{bucket_summary['usable_outcomes']}`, "
            f"avg_confidence `{bucket_summary['average_confidence']}`, observed_hit_rate `{bucket_summary['observed_hit_rate_pct']}`, "
            f"gap `{bucket_summary['calibration_gap_pct']}`"
        )

    lines.extend(["", "## Avoid Confidence Buckets", ""])
    for bucket_name, bucket_summary in summary.get("action_groups", {}).get("avoid", {}).get("confidence_buckets", {}).items():
        lines.append(
            f"- `{bucket_name}`: count `{bucket_summary['count']}`, usable `{bucket_summary['usable_outcomes']}`, "
            f"avg_confidence `{bucket_summary['average_confidence']}`, observed_hit_rate `{bucket_summary['observed_hit_rate_pct']}`, "
            f"gap `{bucket_summary['calibration_gap_pct']}`"
        )

    return "\n".join(lines) + "\n"


def build_replay_calibration_report(replay_ids):
    records = collect_replay_calibration_records(replay_ids)
    usable = [record for record in records if record["success"] is not None]

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_id_count": len(replay_ids),
        "replay_ids": replay_ids,
        "total_records": len(records),
        "usable_records": len(usable),
        "excluded_ambiguous_records": len(records) - len(usable),
        "minimum_sample_warning": len(usable) < 50,
        "action_groups": {
            "actionable": _summarize_group(records, action_filter=lambda record: record["action_group"] == "actionable"),
            "avoid": _summarize_group(records, action_filter=lambda record: record["action_group"] == "avoid"),
            "buy": _summarize_group(records, action_filter=lambda record: record["action"] == "buy"),
            "watch_only": _summarize_group(records, action_filter=lambda record: record["action"] == "watch_only"),
        },
        "records": records,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__replay_champion_calibration_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__replay_champion_calibration_v1.json",
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")

    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_calibration_report.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    summary, latest_json_path, latest_md_path = build_replay_calibration_report(sys.argv[1:])
    print(json.dumps({
        "replay_id_count": summary["replay_id_count"],
        "total_records": summary["total_records"],
        "usable_records": summary["usable_records"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
