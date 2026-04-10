"""
Build a short executive summary for the current next-open entry lane.

Usage:
    python entry_next_open_executive_status.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
QUEUE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_branch_readiness_queue_v1.json")
TEXTURE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_commercial_bank_texture_validation_v1.json")
TRIGGER_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_trigger_sheet_v1.json")
DECISION_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_decision_study_v1.json")
ATTRIBUTION_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_commercial_bank_attribution_study_v1.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_json_optional(path, default):
    if not os.path.exists(path):
        return default
    return load_json(path)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _render_markdown(payload):
    lines = [
        "# Entry Next-Open Executive Status",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- current_entry_lane_status: `{payload['current_entry_lane_status']}`",
        f"- current_best_candidate: `{payload['current_best_candidate']}`",
        "",
        "## Rough Picture",
        "",
    ]
    for item in payload.get("rough_picture") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Best Current Truths",
        "",
    ])
    for item in payload.get("best_current_truths") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Main Blockers",
        "",
    ])
    for item in payload.get("main_blockers") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## What Future Data Must Prove",
        "",
    ])
    for item in payload.get("future_must_prove") or []:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def build_entry_next_open_executive_status():
    queue = load_json(QUEUE_PATH)
    texture = load_json(TEXTURE_PATH)
    trigger = load_json(TRIGGER_PATH)
    decision = load_json(DECISION_PATH)
    attribution = load_json_optional(ATTRIBUTION_PATH, {})

    top_row = (queue.get("queue_rows") or [{}])[0]
    exact = ((texture.get("summaries") or {}).get("exact_slice_all") or {})
    enterable_base = ((decision.get("ranker_rows") or [{}])[0] or {})
    attribution_interpretation = attribution.get("interpretation") or {}
    coverage = attribution.get("coverage") or {}
    residual_positive_symbols = attribution.get("residual_positive_symbols") or {}

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "current_entry_lane_status": "promising_but_not_ready",
        "current_best_candidate": top_row.get("slice"),
        "rough_picture": [
            "the close-based entry lane stayed weak",
            "the next-open decision shift is the first entry lane that looks alive",
            "the current best candidate is a commercial-bank next-open texture",
            "that texture is clean so far, but still sample-limited",
            f"broadening state: {attribution_interpretation.get('broadening_verdict', 'unknown')}",
        ],
        "best_current_truths": [
            f"next-open enterable baseline positive rate: {enterable_base.get('positive_rate')}",
            f"top next-open candidate queue status: {top_row.get('readiness_bucket')} / {top_row.get('quality_status')}",
            f"exact texture result: {exact.get('positive_count')} positives from {exact.get('count')} matches",
            f"exact texture positive share inside the candidate: {coverage.get('exact_texture_positive_share')}",
            f"residual positives by symbol: {residual_positive_symbols}",
        ],
        "main_blockers": [
            "the best exact texture still has too few total matches",
            "there are not yet enough untouched future exact-slice windows",
            "broadening beyond the exact texture is still symbol-dependent",
            "no entry rule should be promoted from one guarded candidate alone",
        ],
        "future_must_prove": trigger.get("future_must_prove") or [],
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_executive_status_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_executive_status_v1.json",
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")

    markdown = _render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_entry_next_open_executive_status()
    print(json.dumps({
        "current_entry_lane_status": payload["current_entry_lane_status"],
        "current_best_candidate": payload["current_best_candidate"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
