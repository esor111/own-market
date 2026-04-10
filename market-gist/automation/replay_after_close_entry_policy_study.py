"""
Research-only study for after-close next-open entry policy candidates.

Usage:
    python replay_after_close_entry_policy_study.py
"""
import json
import os
import sys
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
LATEST_TRADABILITY_STUDY_PATH = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__replay_next_open_tradability_study_v1.json",
)
TARGET_DISTANCE_THRESHOLDS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 4.8, 5.0, 5.5, 6.0]
RR_THRESHOLDS = [0.5, 0.75, 1.0, 1.1, 1.2, 1.36, 1.5, 1.75, 2.0]


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


def _split_name(record):
    month = str(record.get("session_date") or "")[:7]
    return "discovery" if month <= "2025-06" else "validation"


def _policy_allows(record, target_distance_min, rr_min):
    target_distance = record.get("target_distance_close_pct")
    rr = record.get("risk_reward_ratio")
    if target_distance is None or rr is None:
        return False
    return float(target_distance) >= float(target_distance_min) and float(rr) >= float(rr_min)


def _evaluate_policy(records, target_distance_min, rr_min):
    positives = [record for record in records if record.get("next_open_label") == "tradable_positive_gross"]
    negatives = [record for record in records if record.get("next_open_label") != "tradable_positive_gross"]
    original_good_calls = [record for record in records if record.get("comparison_verdict") == "good_call"]
    goodcall_tradable = [record for record in original_good_calls if record.get("next_open_label") == "tradable_positive_gross"]
    goodcall_gap_above = [record for record in original_good_calls if record.get("next_open_label") == "gap_above_target"]

    allowed = [record for record in records if _policy_allows(record, target_distance_min, rr_min)]
    blocked = [record for record in records if not _policy_allows(record, target_distance_min, rr_min)]

    allowed_positive = [record for record in allowed if record.get("next_open_label") == "tradable_positive_gross"]
    blocked_negative = [record for record in blocked if record.get("next_open_label") != "tradable_positive_gross"]

    tpr = _rate(len(allowed_positive), len(positives))
    tnr = _rate(len(blocked_negative), len(negatives))
    balanced_accuracy = None
    if tpr is not None and tnr is not None:
        balanced_accuracy = round((tpr + tnr) / 2, 4)

    allowed_goodcall_tradable = [record for record in goodcall_tradable if _policy_allows(record, target_distance_min, rr_min)]
    blocked_goodcall_gap_above = [record for record in goodcall_gap_above if not _policy_allows(record, target_distance_min, rr_min)]

    return {
        "target_distance_min": target_distance_min,
        "rr_min": rr_min,
        "record_count": len(records),
        "allowed_count": len(allowed),
        "blocked_count": len(blocked),
        "tradable_positive_total": len(positives),
        "tradable_positive_allowed": len(allowed_positive),
        "tradable_positive_recall": tpr,
        "nonpositive_total": len(negatives),
        "nonpositive_blocked": len(blocked_negative),
        "nonpositive_block_rate": tnr,
        "allow_precision": _rate(len(allowed_positive), len(allowed)),
        "balanced_accuracy": balanced_accuracy,
        "good_call_total": len(original_good_calls),
        "good_call_tradable_positive_total": len(goodcall_tradable),
        "good_call_tradable_positive_allowed": len(allowed_goodcall_tradable),
        "good_call_tradable_positive_recall": _rate(len(allowed_goodcall_tradable), len(goodcall_tradable)),
        "good_call_gap_above_total": len(goodcall_gap_above),
        "good_call_gap_above_blocked": len(blocked_goodcall_gap_above),
        "good_call_gap_above_block_rate": _rate(len(blocked_goodcall_gap_above), len(goodcall_gap_above)),
    }


def _candidate_sort_key(row):
    return (
        row.get("balanced_accuracy") if row.get("balanced_accuracy") is not None else -1,
        row.get("allow_precision") if row.get("allow_precision") is not None else -1,
        row.get("good_call_gap_above_block_rate") if row.get("good_call_gap_above_block_rate") is not None else -1,
        row.get("good_call_tradable_positive_recall") if row.get("good_call_tradable_positive_recall") is not None else -1,
    )


def _render_markdown(summary):
    lines = [
        "# Replay After-Close Entry Policy Study",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- total_record_count: `{summary['total_record_count']}`",
        f"- discovery_record_count: `{summary['discovery_record_count']}`",
        f"- validation_record_count: `{summary['validation_record_count']}`",
        "",
        "## Policy Shape",
        "",
        "- allow next-day trade only if both are true:",
        "  - target_distance_close_pct >= threshold",
        "  - risk_reward_ratio >= threshold",
        "",
        "## Top Discovery Candidates",
        "",
    ]

    for row in summary.get("top_discovery_candidates", []):
        lines.append(
            f"- `target_distance >= {row['target_distance_min']}` and `rr >= {row['rr_min']}`: "
            f"balanced_accuracy `{row['balanced_accuracy']}`, allow_precision `{row['allow_precision']}`, "
            f"tradable_positive_recall `{row['tradable_positive_recall']}`, nonpositive_block_rate `{row['nonpositive_block_rate']}`, "
            f"good_call_gap_block `{row['good_call_gap_above_block_rate']}`, good_call_tradable_keep `{row['good_call_tradable_positive_recall']}`"
        )

    lines.extend(["", "## Validation Of Top Discovery Candidates", ""])
    for row in summary.get("validated_top_candidates", []):
        lines.append(
            f"- `target_distance >= {row['target_distance_min']}` and `rr >= {row['rr_min']}`: "
            f"discovery_bal_acc `{row['discovery_balanced_accuracy']}`, validation_bal_acc `{row['validation_balanced_accuracy']}`, "
            f"validation_allow_precision `{row['validation_allow_precision']}`, validation_good_call_gap_block `{row['validation_good_call_gap_above_block_rate']}`, "
            f"validation_good_call_tradable_keep `{row['validation_good_call_tradable_positive_recall']}`"
        )

    if summary.get("best_validated_candidate"):
        row = summary["best_validated_candidate"]
        lines.extend([
            "",
            "## Best Current Validated Candidate",
            "",
            f"- `target_distance >= {row['target_distance_min']}` and `rr >= {row['rr_min']}`",
            f"- discovery_balanced_accuracy: `{row['discovery_balanced_accuracy']}`",
            f"- validation_balanced_accuracy: `{row['validation_balanced_accuracy']}`",
            f"- validation_allow_precision: `{row['validation_allow_precision']}`",
            f"- validation_good_call_gap_block_rate: `{row['validation_good_call_gap_above_block_rate']}`",
            f"- validation_good_call_tradable_positive_recall: `{row['validation_good_call_tradable_positive_recall']}`",
        ])

    return "\n".join(lines) + "\n"


def build_after_close_entry_policy_study():
    payload = load_json(LATEST_TRADABILITY_STUDY_PATH)
    records = payload.get("records") or []
    discovery_records = [record for record in records if _split_name(record) == "discovery"]
    validation_records = [record for record in records if _split_name(record) == "validation"]

    discovery_rows = []
    for target_distance_min in TARGET_DISTANCE_THRESHOLDS:
        for rr_min in RR_THRESHOLDS:
            row = _evaluate_policy(discovery_records, target_distance_min, rr_min)
            discovery_rows.append(row)

    discovery_rows.sort(key=_candidate_sort_key, reverse=True)
    top_discovery = discovery_rows[:12]

    validated = []
    for row in top_discovery:
        validation_row = _evaluate_policy(validation_records, row["target_distance_min"], row["rr_min"])
        validated.append({
            "target_distance_min": row["target_distance_min"],
            "rr_min": row["rr_min"],
            "discovery_balanced_accuracy": row["balanced_accuracy"],
            "discovery_allow_precision": row["allow_precision"],
            "discovery_good_call_gap_above_block_rate": row["good_call_gap_above_block_rate"],
            "discovery_good_call_tradable_positive_recall": row["good_call_tradable_positive_recall"],
            "validation_balanced_accuracy": validation_row["balanced_accuracy"],
            "validation_allow_precision": validation_row["allow_precision"],
            "validation_nonpositive_block_rate": validation_row["nonpositive_block_rate"],
            "validation_tradable_positive_recall": validation_row["tradable_positive_recall"],
            "validation_good_call_gap_above_block_rate": validation_row["good_call_gap_above_block_rate"],
            "validation_good_call_tradable_positive_recall": validation_row["good_call_tradable_positive_recall"],
        })

    validated.sort(
        key=lambda row: (
            row.get("validation_balanced_accuracy") if row.get("validation_balanced_accuracy") is not None else -1,
            row.get("validation_allow_precision") if row.get("validation_allow_precision") is not None else -1,
            row.get("validation_good_call_gap_above_block_rate") if row.get("validation_good_call_gap_above_block_rate") is not None else -1,
            row.get("validation_good_call_tradable_positive_recall") if row.get("validation_good_call_tradable_positive_recall") is not None else -1,
        ),
        reverse=True,
    )

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_path": LATEST_TRADABILITY_STUDY_PATH,
        "total_record_count": len(records),
        "discovery_record_count": len(discovery_records),
        "validation_record_count": len(validation_records),
        "target_distance_thresholds": TARGET_DISTANCE_THRESHOLDS,
        "rr_thresholds": RR_THRESHOLDS,
        "top_discovery_candidates": top_discovery,
        "validated_top_candidates": validated[:12],
        "best_validated_candidate": validated[0] if validated else None,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__replay_after_close_entry_policy_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__replay_after_close_entry_policy_study_v1.json",
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
    if len(sys.argv) > 1 and sys.argv[1] != "--force":
        print("This study uses the latest next-open tradability study JSON and takes no positional arguments.")
        sys.exit(1)

    summary, latest_json_path, latest_md_path = build_after_close_entry_policy_study()
    print(json.dumps({
        "total_record_count": summary["total_record_count"],
        "discovery_record_count": summary["discovery_record_count"],
        "validation_record_count": summary["validation_record_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
