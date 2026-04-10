"""
Explain why future commercial-bank rows miss the current exact next-open texture.

Usage:
    python entry_next_open_future_near_miss_report.py
    python entry_next_open_future_near_miss_report.py DATASET_JSON_PATH
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import VALIDATION_DIR
from entry_next_open_branch_readiness_queue import DEFAULT_DATASET_PATH, load_json
from entry_next_open_commercial_bank_texture_validation import TARGET_SLICE, _bucket_key, _texture_match
from entry_next_open_future_coverage_report import _base_slice


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
TEXTURE_VALIDATION_PATH = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__entry_next_open_commercial_bank_texture_validation_v1.json",
)


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


def _counts(rows, key):
    return dict(Counter(str(row.get(key) or "UNKNOWN") for row in rows).most_common(10))


def _subset_summary(name, rows):
    positive_count = sum(1 for row in rows if row.get("entry_outcome_family") == "strict_positive")
    return {
        "name": name,
        "count": len(rows),
        "positive_count": positive_count,
        "negative_count": len(rows) - positive_count,
        "positive_rate": _rate(positive_count, len(rows)),
        "months": _counts(rows, "month_key"),
        "symbols": _counts(rows, "symbol"),
        "confidence": _counts(rows, "confidence_label"),
        "leadership": _counts(rows, "leadership_label"),
        "next_open_labels": _counts(rows, "next_open_label"),
        "executable_labels": _counts(rows, "executable_entry_label"),
    }


def _target_miss_reason(row):
    reasons = []
    rr = row.get("risk_reward_ratio")
    if not isinstance(rr, (int, float)) or rr > 0.78:
        reasons.append("rr_above_0.78")
    if row.get("leadership_label") == "both_leader":
        reasons.append("leadership_both_leader")
    if not reasons:
        reasons.append("other")
    return "+".join(reasons)


def _base_miss_reason(row):
    if row.get("confidence_label") != "strongly_overconfident":
        return "confidence_below_strongly_overconfident"
    return "other"


def _render_markdown(payload):
    lines = [
        "# Entry Next-Open Future Near-Miss Report",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- reference_boundary_month: `{payload['reference_boundary_month']}`",
        f"- near_miss_state: `{payload['near_miss_state']}`",
        "",
        "## Future Base Slice",
        "",
        f"- count: `{payload['future_base_summary']['count']}`",
        f"- positive_rate: `{payload['future_base_summary']['positive_rate']}`",
        f"- confidence: `{payload['future_base_summary']['confidence']}`",
        f"- symbols: `{payload['future_base_summary']['symbols']}`",
        "",
        "## Future Target Slice Near Misses",
        "",
        f"- count: `{payload['future_target_near_miss_summary']['count']}`",
        f"- positive_rate: `{payload['future_target_near_miss_summary']['positive_rate']}`",
        f"- symbols: `{payload['future_target_near_miss_summary']['symbols']}`",
        f"- leadership: `{payload['future_target_near_miss_summary']['leadership']}`",
        f"- executable_labels: `{payload['future_target_near_miss_summary']['executable_labels']}`",
        f"- miss_reason_counts: `{payload['future_target_miss_reason_counts']}`",
        "",
        "## Future Base-Only Near Misses",
        "",
        f"- count: `{payload['future_base_only_near_miss_summary']['count']}`",
        f"- positive_rate: `{payload['future_base_only_near_miss_summary']['positive_rate']}`",
        f"- symbols: `{payload['future_base_only_near_miss_summary']['symbols']}`",
        f"- confidence: `{payload['future_base_only_near_miss_summary']['confidence']}`",
        f"- executable_labels: `{payload['future_base_only_near_miss_summary']['executable_labels']}`",
        f"- miss_reason_counts: `{payload['future_base_miss_reason_counts']}`",
        "",
        "## What It Means Now",
        "",
    ]
    for item in payload.get("current_action") or []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_entry_next_open_future_near_miss_report(dataset_path):
    dataset = load_json(dataset_path)
    texture_validation = load_json(TEXTURE_VALIDATION_PATH)

    reference_months = set()
    reference_months.update((texture_validation.get("summaries") or {}).get("exact_slice_discovery", {}).get("months", {}).keys())
    reference_months.update((texture_validation.get("summaries") or {}).get("exact_slice_validation", {}).get("months", {}).keys())
    reference_boundary_month = max(reference_months) if reference_months else None

    rows = dataset.get("rows") or []
    future_rows = [row for row in rows if str(row.get("month_key") or "") > reference_boundary_month]

    future_base_rows = [row for row in future_rows if _base_slice(row)]
    future_target_rows = [row for row in future_rows if _bucket_key(row) == TARGET_SLICE]
    future_exact_rows = [row for row in future_target_rows if _texture_match(row)]
    future_target_near_miss_rows = [row for row in future_target_rows if not _texture_match(row)]
    future_base_only_near_miss_rows = [row for row in future_base_rows if _bucket_key(row) != TARGET_SLICE]

    future_target_reason_counts = dict(Counter(_target_miss_reason(row) for row in future_target_near_miss_rows))
    future_base_reason_counts = dict(Counter(_base_miss_reason(row) for row in future_base_only_near_miss_rows))

    if future_target_near_miss_rows and not future_exact_rows:
        near_miss_state = "future_target_near_misses_without_exact_repeat"
        current_action = [
            "future months are generating the target slice, but they miss the exact texture in a specific way",
            "treat those misses as useful evidence against premature promotion",
        ]
    elif future_base_only_near_miss_rows and not future_target_rows:
        near_miss_state = "future_base_only_near_misses"
        current_action = [
            "future months are reaching the broader commercial-bank base slice but not the target slice",
            "the candidate still needs more relevant future pressure before trust can increase",
        ]
    else:
        near_miss_state = "no_future_near_misses"
        current_action = [
            "future months have not yet produced informative near-miss rows for this candidate",
            "keep waiting for new exact-texture or near-miss evidence",
        ]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "reference_boundary_month": reference_boundary_month,
        "near_miss_state": near_miss_state,
        "future_base_summary": _subset_summary("future_base", future_base_rows),
        "future_target_summary": _subset_summary("future_target", future_target_rows),
        "future_exact_summary": _subset_summary("future_exact", future_exact_rows),
        "future_target_near_miss_summary": _subset_summary("future_target_near_miss", future_target_near_miss_rows),
        "future_base_only_near_miss_summary": _subset_summary("future_base_only_near_miss", future_base_only_near_miss_rows),
        "future_target_miss_reason_counts": future_target_reason_counts,
        "future_base_miss_reason_counts": future_base_reason_counts,
        "current_action": current_action,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_future_near_miss_report_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_future_near_miss_report_v1.json",
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")

    markdown = _render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main(argv=None):
    argv = argv or sys.argv[1:]
    dataset_path = argv[0] if argv else DEFAULT_DATASET_PATH
    payload, latest_json_path, latest_md_path = build_entry_next_open_future_near_miss_report(dataset_path)
    print(json.dumps({
        "near_miss_state": payload["near_miss_state"],
        "future_target_near_miss_count": payload["future_target_near_miss_summary"]["count"],
        "future_base_only_near_miss_count": payload["future_base_only_near_miss_summary"]["count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
