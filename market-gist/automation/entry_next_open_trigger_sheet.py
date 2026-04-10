"""
Build an explicit trigger sheet for the current best next-open entry candidate.

This converts the current queue + texture validation into:
- what future exact-slice evidence must appear
- what would increase trust
- what would invalidate the current guarded-candidate framing

Usage:
    python entry_next_open_trigger_sheet.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
QUEUE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_branch_readiness_queue_v1.json")
TEXTURE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_commercial_bank_texture_validation_v1.json")
DECISION_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_decision_study_v1.json")

FUTURE_EXACT_MATCH_COUNT_MIN = 3
FUTURE_EXACT_MONTH_COUNT_MIN = 2
FUTURE_EXACT_POSITIVE_RATE_MIN = 0.67
SYMBOL_SHARE_MAX = 0.70


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


def _render_markdown(payload):
    lines = [
        "# Entry Next-Open Trigger Sheet",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- current_top_candidate: `{payload['current_top_candidate']}`",
        f"- current_candidate_status: `{payload['current_candidate_status']}`",
        f"- current_exact_texture_rate: `{payload['current_exact_texture_rate']}`",
        "",
        "## What Future Data Must Prove",
        "",
    ]
    for item in payload.get("future_must_prove") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## What Would Increase Trust",
        "",
    ])
    for item in payload.get("trust_increase_signals") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## What Would Reduce Trust",
        "",
    ])
    for item in payload.get("trust_reduction_signals") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Current Decision",
        "",
        "- keep `Risk Engine v1` frozen",
        "- keep the commercial-bank next-open texture as a guarded candidate",
        "- do not promote an entry rule until future exact-slice evidence arrives",
    ])
    return "\n".join(lines) + "\n"


def build_entry_next_open_trigger_sheet():
    queue = load_json(QUEUE_PATH)
    texture = load_json(TEXTURE_PATH)
    decision = load_json(DECISION_PATH)

    top_row = (queue.get("queue_rows") or [{}])[0]
    exact = ((texture.get("summaries") or {}).get("exact_slice_all") or {})
    neighbor = ((texture.get("summaries") or {}).get("neighbor_same_structure_all_confidence") or {})
    future_probe = ((texture.get("summaries") or {}).get("future_neighbor_probe") or {})
    enterable_base = ((decision.get("ranker_rows") or [{}])[0] or {})

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "current_top_candidate": top_row.get("slice"),
        "current_candidate_status": texture.get("interpretation", {}).get("verdict"),
        "current_exact_texture_rate": exact.get("positive_rate"),
        "future_must_prove": [
            f"at least {FUTURE_EXACT_MATCH_COUNT_MIN} new exact-texture matches across at least {FUTURE_EXACT_MONTH_COUNT_MIN} future months",
            f"future exact-texture positive rate stays at or above {FUTURE_EXACT_POSITIVE_RATE_MIN}",
            "future exact-texture cases should not collapse back into one symbol only",
            f"top symbol share should stay below {SYMBOL_SHARE_MAX}",
        ],
        "trust_increase_signals": [
            "the first new future exact-texture match is positive",
            "a second future month produces the same exact texture",
            "the texture appears in more than one bank without adding negatives",
            f"the exact texture continues to outperform the current next-open enterable baseline of {enterable_base.get('positive_rate')}",
            f"neighboring same-structure rows stay near the current {neighbor.get('positive_rate')} level instead of softening sharply",
        ],
        "trust_reduction_signals": [
            "the next future exact-texture match is negative",
            "all new exact matches come from only one symbol again",
            "future evidence appears only as loose neighbors and not as the exact texture",
            "neighboring same-structure rows start leaking multiple new negatives",
            f"future exact-texture rate falls materially below {FUTURE_EXACT_POSITIVE_RATE_MIN}",
        ],
        "current_context": {
            "exact_texture_count": exact.get("count"),
            "exact_texture_positive_count": exact.get("positive_count"),
            "neighbor_probe_count": neighbor.get("count"),
            "neighbor_probe_positive_rate": neighbor.get("positive_rate"),
            "future_probe_count": future_probe.get("count"),
        },
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_trigger_sheet_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_trigger_sheet_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_next_open_trigger_sheet()
    print(json.dumps({
        "current_top_candidate": payload["current_top_candidate"],
        "current_candidate_status": payload["current_candidate_status"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
