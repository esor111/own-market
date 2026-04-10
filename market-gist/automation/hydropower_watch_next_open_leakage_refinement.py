"""
Follow-up refinement study for the hydropower watch next-open policy.

This tests whether adding a minimum recomputed RR at the next open removes the
known negative-probe leakage without breaking the earlier positive subset.
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR
from hydropower_watch_next_open_policy_study import (
    DEFAULT_REPLAY_IDS,
    DISCOVERY_MONTHS,
    FUTURE_STRESS_MONTHS,
    NEGATIVE_PROBE_MONTHS,
    POSITIVE_PROBE_MONTHS,
    VALIDATION_MONTHS,
    _assemble_rows,
    _evaluate_candidate,
)


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
SOURCE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__hydropower_watch_next_open_policy_study_v1.json")
MIN_RR_CANDIDATES = [0.04, 0.05, 0.06, 0.07, 0.0709, 0.08, 0.1]


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _load_source_candidate():
    with open(SOURCE_PATH, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    candidate = payload.get("best_candidate") or {}
    return payload, {
        "gap_min": candidate.get("gap_min"),
        "rr_max": candidate.get("rr_max"),
    }


def _evaluate_with_rr_min(rows, base_candidate, rr_min):
    filtered_rows = [
        row for row in rows
        if row.get("recomputed_rr_at_entry") is None or row["recomputed_rr_at_entry"] >= rr_min
    ]
    candidate = dict(base_candidate)
    candidate["rr_min"] = rr_min
    return _evaluate_candidate(filtered_rows, candidate)


def _render_markdown(payload):
    lines = [
        "# Hydropower Watch Next-Open Leakage Refinement",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- source_path: `{payload['source_path']}`",
        f"- base_gap_min: `{payload['base_candidate']['gap_min']}`",
        f"- base_rr_max: `{payload['base_candidate']['rr_max']}`",
        "",
        "## Top RR-Min Refinements",
        "",
    ]
    for item in payload.get("top_refinements", []):
        lines.extend([
            f"### `rr_min >= {item['rr_min']}`",
            f"- validation_allow_success_count: `{item['validation_metrics']['allow_success_count']}`",
            f"- validation_allow_other_count: `{item['validation_metrics']['allow_other_count']}`",
            f"- validation_success_recall: `{item['validation_metrics']['success_recall']}`",
            f"- positive_probe_allow_success_count: `{item['positive_probe_metrics']['allow_success_count']}`",
            f"- negative_probe_allow_other_count: `{item['negative_probe_metrics']['allow_other_count']}`",
            f"- future_stress_allow_other_count: `{item['future_stress_metrics']['allow_other_count']}`",
            "",
        ])

    best = payload.get("best_refinement") or {}
    if best:
        lines.extend([
            "## Best Refinement",
            "",
            f"- rr_min: `{best['rr_min']}`",
            "",
            "### Discovery",
            f"- allow_success_count: `{best['discovery_metrics']['allow_success_count']}`",
            f"- allow_other_count: `{best['discovery_metrics']['allow_other_count']}`",
            f"- success_recall: `{best['discovery_metrics']['success_recall']}`",
            "",
            "### Validation",
            f"- allow_success_count: `{best['validation_metrics']['allow_success_count']}`",
            f"- allow_other_count: `{best['validation_metrics']['allow_other_count']}`",
            f"- success_recall: `{best['validation_metrics']['success_recall']}`",
            "",
            "### Positive Probe",
            f"- allow_success_count: `{best['positive_probe_metrics']['allow_success_count']}`",
            f"- allow_other_count: `{best['positive_probe_metrics']['allow_other_count']}`",
            f"- success_recall: `{best['positive_probe_metrics']['success_recall']}`",
            "",
            "### Negative Probe",
            f"- allow_success_count: `{best['negative_probe_metrics']['allow_success_count']}`",
            f"- allow_other_count: `{best['negative_probe_metrics']['allow_other_count']}`",
            f"- other_block_rate: `{best['negative_probe_metrics']['other_block_rate']}`",
            "",
            "### Future Stress",
            f"- allow_other_count: `{best['future_stress_metrics']['allow_other_count']}`",
            f"- other_block_rate: `{best['future_stress_metrics']['other_block_rate']}`",
            "",
        ])
    return "\n".join(lines) + "\n"


def build_leakage_refinement():
    source_payload, base_candidate = _load_source_candidate()
    rows = _assemble_rows(DEFAULT_REPLAY_IDS)
    discovery_rows = [row for row in rows if row["month_key"] in DISCOVERY_MONTHS]
    validation_rows = [row for row in rows if row["month_key"] in VALIDATION_MONTHS]
    future_stress_rows = [row for row in rows if row["month_key"] in FUTURE_STRESS_MONTHS]
    positive_probe_rows = [row for row in rows if row["month_key"] in POSITIVE_PROBE_MONTHS]
    negative_probe_rows = [row for row in rows if row["month_key"] in NEGATIVE_PROBE_MONTHS]

    refinements = []
    for rr_min in MIN_RR_CANDIDATES:
        entry = {
            "rr_min": rr_min,
            "discovery_metrics": _evaluate_with_rr_min(discovery_rows, base_candidate, rr_min),
            "validation_metrics": _evaluate_with_rr_min(validation_rows, base_candidate, rr_min),
            "future_stress_metrics": _evaluate_with_rr_min(future_stress_rows, base_candidate, rr_min),
            "positive_probe_metrics": _evaluate_with_rr_min(positive_probe_rows, base_candidate, rr_min),
            "negative_probe_metrics": _evaluate_with_rr_min(negative_probe_rows, base_candidate, rr_min),
        }
        refinements.append(entry)

    refinements.sort(
        key=lambda item: (
            item["negative_probe_metrics"]["other_block_rate"] or -1,
            item["validation_metrics"]["allow_success_count"],
            item["positive_probe_metrics"]["allow_success_count"],
            item["discovery_metrics"]["allow_success_count"],
        ),
        reverse=True,
    )
    best_refinement = refinements[0] if refinements else None

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_path": SOURCE_PATH,
        "base_candidate": base_candidate,
        "source_replay_ids": source_payload.get("replay_ids") or [],
        "top_refinements": refinements[:10],
        "best_refinement": best_refinement,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__hydropower_watch_next_open_leakage_refinement_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__hydropower_watch_next_open_leakage_refinement_v1.json",
    )
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__hydropower_watch_next_open_leakage_refinement_v1.md",
    )
    latest_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__hydropower_watch_next_open_leakage_refinement_v1.md",
    )

    markdown = _render_markdown(payload)
    for path in (dated_json_path, latest_json_path):
        save_json(path, payload)
    for path in (dated_md_path, latest_md_path):
        save_text(path, markdown)

    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_leakage_refinement()
    print(json.dumps({
        "best_refinement": payload.get("best_refinement"),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
