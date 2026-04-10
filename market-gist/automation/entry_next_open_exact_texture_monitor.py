"""
Monitor future evidence for the current best exact next-open entry texture.

Usage:
    python entry_next_open_exact_texture_monitor.py
    python entry_next_open_exact_texture_monitor.py DATASET_JSON_PATH
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import VALIDATION_DIR
from entry_next_open_branch_readiness_queue import DEFAULT_DATASET_PATH, load_json
from entry_next_open_commercial_bank_texture_validation import TARGET_SLICE, _bucket_key, _texture_match


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
TEXTURE_VALIDATION_PATH = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__entry_next_open_commercial_bank_texture_validation_v1.json",
)
TRIGGER_SHEET_PATH = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__entry_next_open_trigger_sheet_v1.json",
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
        "leadership": _counts(rows, "leadership_label"),
    }


def _top_symbol_share_from_summary(summary):
    symbols = summary.get("symbols") or {}
    total = summary.get("count") or 0
    if not total or not symbols:
        return None
    top_count = max(symbols.values())
    return _rate(top_count, total)


def _future_state(future_exact_summary):
    min_count = 3
    min_month_count = 2
    min_positive_rate = 0.67
    symbol_share_max = 0.70

    rows_count = future_exact_summary.get("count") or 0
    positive_rate = future_exact_summary.get("positive_rate")
    month_count = len(future_exact_summary.get("months") or {})
    symbol_share = _top_symbol_share_from_summary(future_exact_summary)

    if rows_count == 0:
        return "waiting_for_new_exact_matches"
    if positive_rate is not None and positive_rate < min_positive_rate:
        return "weakened"
    if rows_count >= min_count and month_count >= min_month_count and positive_rate is not None and positive_rate >= min_positive_rate and (symbol_share is None or symbol_share < symbol_share_max):
        return "strengthened"
    return "still_guarded"


def _render_markdown(payload):
    lines = [
        "# Entry Next-Open Exact Texture Monitor",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- texture_description: `{payload['texture_description']}`",
        f"- reference_boundary_month: `{payload['reference_boundary_month']}`",
        f"- future_signal_state: `{payload['future_signal_state']}`",
        "",
        "## Reference Exact Texture",
        "",
        f"- count: `{payload['reference_exact_summary']['count']}`",
        f"- positive_rate: `{payload['reference_exact_summary']['positive_rate']}`",
        f"- months: `{payload['reference_exact_summary']['months']}`",
        f"- symbols: `{payload['reference_exact_summary']['symbols']}`",
        "",
        "## Future Exact Texture",
        "",
        f"- count: `{payload['future_exact_summary']['count']}`",
        f"- positive_rate: `{payload['future_exact_summary']['positive_rate']}`",
        f"- months: `{payload['future_exact_summary']['months']}`",
        f"- symbols: `{payload['future_exact_summary']['symbols']}`",
        "",
        "## Future Same-Structure Neighbors",
        "",
        f"- count: `{payload['future_neighbor_summary']['count']}`",
        f"- positive_rate: `{payload['future_neighbor_summary']['positive_rate']}`",
        f"- months: `{payload['future_neighbor_summary']['months']}`",
        f"- symbols: `{payload['future_neighbor_summary']['symbols']}`",
        "",
        "## What It Means Now",
        "",
    ]
    for item in payload.get("current_action") or []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_entry_next_open_exact_texture_monitor(dataset_path):
    dataset = load_json(dataset_path)
    texture_validation = load_json(TEXTURE_VALIDATION_PATH)
    trigger_sheet = load_json(TRIGGER_SHEET_PATH)

    reference_months = set()
    reference_months.update((texture_validation.get("summaries") or {}).get("exact_slice_discovery", {}).get("months", {}).keys())
    reference_months.update((texture_validation.get("summaries") or {}).get("exact_slice_validation", {}).get("months", {}).keys())
    reference_boundary_month = max(reference_months) if reference_months else None

    rows = [row for row in (dataset.get("rows") or []) if row.get("entry_executed")]
    exact_rows = [row for row in rows if _bucket_key(row) == TARGET_SLICE and _texture_match(row)]
    reference_exact_rows = [row for row in exact_rows if row.get("month_key") in reference_months]
    future_exact_rows = [row for row in exact_rows if reference_boundary_month and str(row.get("month_key") or "") > reference_boundary_month]

    future_neighbor_rows = [
        row for row in rows
        if reference_boundary_month
        and str(row.get("month_key") or "") > reference_boundary_month
        and row.get("sector_name") == "COMMERCIAL BANKS"
        and row.get("calendar_phase") == "no_named_phase"
        and row.get("event_state") == "no_symbol_event_match"
        and row.get("action") == "watch_only"
        and _texture_match(row)
    ]

    reference_exact_summary = _subset_summary("reference_exact", reference_exact_rows)
    future_exact_summary = _subset_summary("future_exact", future_exact_rows)
    future_neighbor_summary = _subset_summary("future_neighbors", future_neighbor_rows)
    future_signal_state = _future_state(future_exact_summary)

    current_action = {
        "waiting_for_new_exact_matches": [
            "no new exact future texture has appeared yet",
            "keep the commercial-bank next-open texture on watch",
            "do not increase trust from silence alone",
        ],
        "still_guarded": [
            "new future exact matches exist, but not enough to increase trust yet",
            "keep the candidate guarded and wait for broader future evidence",
        ],
        "strengthened": [
            "future exact texture evidence is now strengthening the candidate",
            "open a fresh untouched validation review before any promotion language",
        ],
        "weakened": [
            "future exact texture evidence is weakening the candidate",
            "do not promote and re-check whether the texture was regime-specific",
        ],
    }[future_signal_state]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "texture_description": texture_validation.get("texture_description"),
        "reference_boundary_month": reference_boundary_month,
        "reference_months": sorted(reference_months),
        "future_signal_state": future_signal_state,
        "reference_exact_summary": reference_exact_summary,
        "future_exact_summary": future_exact_summary,
        "future_neighbor_summary": future_neighbor_summary,
        "future_must_prove": trigger_sheet.get("future_must_prove") or [],
        "current_action": current_action,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_exact_texture_monitor_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_exact_texture_monitor_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_next_open_exact_texture_monitor(dataset_path)
    print(json.dumps({
        "future_signal_state": payload["future_signal_state"],
        "reference_boundary_month": payload["reference_boundary_month"],
        "future_exact_count": payload["future_exact_summary"]["count"],
        "future_neighbor_count": payload["future_neighbor_summary"]["count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
