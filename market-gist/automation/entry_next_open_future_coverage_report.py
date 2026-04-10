"""
Report how much future coverage exists for the current best next-open entry texture.

Usage:
    python entry_next_open_future_coverage_report.py
    python entry_next_open_future_coverage_report.py DATASET_JSON_PATH
"""
import json
import os
import sys
from datetime import datetime

from config import VALIDATION_DIR
from entry_next_open_branch_readiness_queue import DEFAULT_DATASET_PATH, load_json
from entry_next_open_commercial_bank_texture_validation import TARGET_SLICE, _bucket_key, _texture_match


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


def _future_month_rows(rows, boundary_month):
    return [row for row in rows if str(row.get("month_key") or "") > boundary_month]


def _base_slice(row):
    return (
        row.get("sector_name") == "COMMERCIAL BANKS"
        and row.get("calendar_phase") == "no_named_phase"
        and row.get("event_state") == "no_symbol_event_match"
        and row.get("action") == "watch_only"
    )


def _target_slice(row):
    return _bucket_key(row) == TARGET_SLICE


def _month_summary(month_rows):
    enterable_rows = [row for row in month_rows if row.get("entry_executed")]
    base_rows = [row for row in month_rows if _base_slice(row)]
    target_rows = [row for row in month_rows if _target_slice(row)]
    exact_rows = [row for row in target_rows if _texture_match(row)]
    exact_positive_count = sum(1 for row in exact_rows if row.get("entry_outcome_family") == "strict_positive")
    exact_negative_count = len(exact_rows) - exact_positive_count
    return {
        "month_key": month_rows[0]["month_key"] if month_rows else None,
        "actionable_row_count": len(month_rows),
        "enterable_row_count": len(enterable_rows),
        "base_slice_count": len(base_rows),
        "target_slice_count": len(target_rows),
        "exact_texture_count": len(exact_rows),
        "exact_texture_positive_count": exact_positive_count,
        "exact_texture_negative_count": exact_negative_count,
        "exact_texture_positive_rate": _rate(exact_positive_count, len(exact_rows)),
    }


def _render_markdown(payload):
    lines = [
        "# Entry Next-Open Future Coverage Report",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- reference_boundary_month: `{payload['reference_boundary_month']}`",
        f"- coverage_state: `{payload['coverage_state']}`",
        f"- future_month_count: `{payload['future_month_count']}`",
        "",
        "## Future Coverage Totals",
        "",
        f"- future_actionable_row_count: `{payload['future_actionable_row_count']}`",
        f"- future_enterable_row_count: `{payload['future_enterable_row_count']}`",
        f"- future_base_slice_month_count: `{payload['future_base_slice_month_count']}`",
        f"- future_target_slice_month_count: `{payload['future_target_slice_month_count']}`",
        f"- future_exact_texture_month_count: `{payload['future_exact_texture_month_count']}`",
        "",
        "## Future Month Rows",
        "",
    ]
    for row in payload.get("future_month_rows") or []:
        lines.append(
            f"- `{row['month_key']}`: actionable `{row['actionable_row_count']}`, enterable `{row['enterable_row_count']}`, base `{row['base_slice_count']}`, target `{row['target_slice_count']}`, exact `{row['exact_texture_count']}`, exact_positive_rate `{row['exact_texture_positive_rate']}`"
        )

    lines.extend(["", "## What It Means Now", ""])
    for item in payload.get("current_action") or []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_entry_next_open_future_coverage_report(dataset_path):
    dataset = load_json(dataset_path)
    texture_validation = load_json(TEXTURE_VALIDATION_PATH)

    reference_months = set()
    reference_months.update((texture_validation.get("summaries") or {}).get("exact_slice_discovery", {}).get("months", {}).keys())
    reference_months.update((texture_validation.get("summaries") or {}).get("exact_slice_validation", {}).get("months", {}).keys())
    reference_boundary_month = max(reference_months) if reference_months else None

    rows = dataset.get("rows") or []
    future_rows = _future_month_rows(rows, reference_boundary_month)
    future_month_keys = sorted({row["month_key"] for row in future_rows})
    future_month_rows = []
    for month_key in future_month_keys:
        month_rows = [row for row in future_rows if row.get("month_key") == month_key]
        future_month_rows.append(_month_summary(month_rows))

    future_base_slice_month_count = sum(1 for row in future_month_rows if row["base_slice_count"] > 0)
    future_target_slice_month_count = sum(1 for row in future_month_rows if row["target_slice_count"] > 0)
    future_exact_texture_month_count = sum(1 for row in future_month_rows if row["exact_texture_count"] > 0)

    if future_exact_texture_month_count > 0:
        coverage_state = "future_exact_texture_present"
        current_action = [
            "future exact-texture rows now exist",
            "use the exact-texture monitor to judge whether trust should increase or stay guarded",
        ]
    elif future_target_slice_month_count > 0:
        coverage_state = "future_target_slice_present_but_exact_absent"
        current_action = [
            "future months contain the commercial-bank target slice, but not the full exact texture",
            "treat this as useful negative coverage, not as extra positive proof",
        ]
    elif future_base_slice_month_count > 0:
        coverage_state = "future_base_slice_present_but_target_absent"
        current_action = [
            "future months contain the broader commercial-bank base slice, but not the strongly-overconfident target slice",
            "the candidate is still waiting for relevant exact-texture coverage",
        ]
    else:
        coverage_state = "future_relevant_structure_absent"
        current_action = [
            "future months currently contain no relevant commercial-bank base structure for this candidate",
            "lack of exact matches here is not yet informative enough to increase trust",
        ]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "reference_boundary_month": reference_boundary_month,
        "coverage_state": coverage_state,
        "future_month_count": len(future_month_rows),
        "future_actionable_row_count": len(future_rows),
        "future_enterable_row_count": sum(1 for row in future_rows if row.get("entry_executed")),
        "future_base_slice_month_count": future_base_slice_month_count,
        "future_target_slice_month_count": future_target_slice_month_count,
        "future_exact_texture_month_count": future_exact_texture_month_count,
        "future_month_rows": future_month_rows,
        "current_action": current_action,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_future_coverage_report_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_future_coverage_report_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_next_open_future_coverage_report(dataset_path)
    print(json.dumps({
        "coverage_state": payload["coverage_state"],
        "future_month_count": payload["future_month_count"],
        "future_exact_texture_month_count": payload["future_exact_texture_month_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
