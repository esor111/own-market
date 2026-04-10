"""
Validate the strongest next-open commercial-bank texture on exact and nearby windows.

Texture under test:
    COMMERCIAL BANKS
    no_named_phase
    no_symbol_event_match
    strongly_overconfident
    watch_only
    risk_reward_ratio <= 0.78
    leadership_label != both_leader

Goal:
    Distinguish between:
    - a weak texture that leaks badly
    - a clean texture that is still sample-limited
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import VALIDATION_DIR
from entry_next_open_branch_readiness_queue import DEFAULT_DATASET_PATH, load_json


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
TARGET_SLICE = "COMMERCIAL BANKS | no_named_phase | no_symbol_event_match | strongly_overconfident | watch_only"


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _bucket_key(row):
    return " | ".join([
        row.get("sector_name") or "UNKNOWN",
        row.get("calendar_phase") or "UNKNOWN",
        row.get("event_state") or "UNKNOWN",
        row.get("confidence_label") or "UNKNOWN",
        row.get("action") or "UNKNOWN",
    ])


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _counts(rows, key):
    return dict(Counter(str(row.get(key) or "UNKNOWN") for row in rows).most_common(10))


def _texture_match(row):
    rr = row.get("risk_reward_ratio")
    if not isinstance(rr, (int, float)):
        return False
    return rr <= 0.78 and (row.get("leadership_label") != "both_leader")


def _subset_summary(name, rows):
    positive_count = sum(1 for row in rows if row["entry_outcome_family"] == "strict_positive")
    return {
        "name": name,
        "count": len(rows),
        "positive_count": positive_count,
        "negative_count": len(rows) - positive_count,
        "positive_rate": _rate(positive_count, len(rows)),
        "symbols": _counts(rows, "symbol"),
        "months": _counts(rows, "month_key"),
        "confidence": _counts(rows, "confidence_label"),
        "events": _counts(rows, "event_state"),
        "leadership": _counts(rows, "leadership_label"),
    }


def _render_markdown(payload):
    lines = [
        "# Entry Next-Open Commercial Bank Texture Validation",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- dataset_path: `{payload['dataset_path']}`",
        f"- texture_description: `{payload['texture_description']}`",
        "",
    ]
    for key in (
        "exact_slice_all",
        "exact_slice_discovery",
        "exact_slice_validation",
        "neighbor_same_structure_all_confidence",
        "future_neighbor_probe",
    ):
        summary = payload["summaries"][key]
        lines.extend([
            f"## `{key}`",
            "",
            f"- count: `{summary['count']}`",
            f"- positive_count: `{summary['positive_count']}`",
            f"- negative_count: `{summary['negative_count']}`",
            f"- positive_rate: `{summary['positive_rate']}`",
            f"- symbols: `{summary['symbols']}`",
            f"- months: `{summary['months']}`",
            f"- confidence: `{summary['confidence']}`",
            f"- events: `{summary['events']}`",
            f"- leadership: `{summary['leadership']}`",
            "",
        ])

    lines.extend([
        "## Interpretation",
        "",
        f"- verdict: `{payload['interpretation']['verdict']}`",
        f"- reason: `{payload['interpretation']['reason']}`",
        "",
        "## Decision",
        "",
        "- keep `Risk Engine v1` frozen",
        "- do not promote an entry rule from this validation alone",
        "- treat the texture as a guarded next-open candidate until more untouched exact-slice months appear",
    ])
    return "\n".join(lines) + "\n"


def build_entry_next_open_commercial_bank_texture_validation(dataset_path):
    dataset = load_json(dataset_path)
    rows = [row for row in (dataset.get("rows") or []) if row.get("entry_executed")]

    exact_slice_rows = [row for row in rows if _bucket_key(row) == TARGET_SLICE]
    exact_texture_rows = [row for row in exact_slice_rows if _texture_match(row)]

    discovery_months = {"2023-12", "2025-05"}
    validation_months = {"2025-06"}
    future_probe_months = {"2025-09"}

    exact_texture_discovery = [row for row in exact_texture_rows if row["month_key"] in discovery_months]
    exact_texture_validation = [row for row in exact_texture_rows if row["month_key"] in validation_months]

    neighbor_same_structure_rows = [
        row for row in rows
        if row.get("entry_executed")
        and row.get("sector_name") == "COMMERCIAL BANKS"
        and row.get("calendar_phase") == "no_named_phase"
        and row.get("event_state") == "no_symbol_event_match"
        and row.get("action") == "watch_only"
        and _texture_match(row)
    ]

    future_neighbor_probe_rows = [
        row for row in neighbor_same_structure_rows
        if row["month_key"] in future_probe_months
    ]

    summaries = {
        "exact_slice_all": _subset_summary("exact_slice_all", exact_texture_rows),
        "exact_slice_discovery": _subset_summary("exact_slice_discovery", exact_texture_discovery),
        "exact_slice_validation": _subset_summary("exact_slice_validation", exact_texture_validation),
        "neighbor_same_structure_all_confidence": _subset_summary(
            "neighbor_same_structure_all_confidence",
            neighbor_same_structure_rows,
        ),
        "future_neighbor_probe": _subset_summary("future_neighbor_probe", future_neighbor_probe_rows),
    }

    exact_all = summaries["exact_slice_all"]
    neighbor_all = summaries["neighbor_same_structure_all_confidence"]
    future_probe = summaries["future_neighbor_probe"]

    if exact_all["count"] >= 5 and exact_all["negative_count"] == 0 and future_probe["count"] == 0:
        verdict = "clean_but_sample_limited"
        reason = "the texture stayed clean inside the exact slice and stayed silent in the nearest future neighbor month, but exact-slice future coverage is still too small"
    elif exact_all["positive_rate"] is not None and exact_all["positive_rate"] >= 0.6 and neighbor_all["positive_rate"] is not None and neighbor_all["positive_rate"] >= 0.5:
        verdict = "promising_but_guarded"
        reason = "the texture is real inside the exact slice, but nearby probes still need more future coverage before trust increases"
    else:
        verdict = "not_ready"
        reason = "the texture does not stay clean enough once neighboring structure is included"

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "texture_description": "COMMERCIAL BANKS | no_named_phase | no_symbol_event_match | strongly_overconfident | watch_only | risk_reward_ratio <= 0.78 | leadership != both_leader",
        "summaries": summaries,
        "interpretation": {
            "verdict": verdict,
            "reason": reason,
        },
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_commercial_bank_texture_validation_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_commercial_bank_texture_validation_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_next_open_commercial_bank_texture_validation(dataset_path)
    print(json.dumps({
        "verdict": payload["interpretation"]["verdict"],
        "exact_slice_positive_rate": payload["summaries"]["exact_slice_all"]["positive_rate"],
        "neighbor_positive_rate": payload["summaries"]["neighbor_same_structure_all_confidence"]["positive_rate"],
        "future_probe_count": payload["summaries"]["future_neighbor_probe"]["count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
