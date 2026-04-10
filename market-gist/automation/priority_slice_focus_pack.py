"""
Build one focused inspection pack for the current top-priority slices.

This is the handoff artifact for the next replay refresh:
- primary buy-side focus
- secondary hostile-side focus

Usage:
    python priority_slice_focus_pack.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR
from monitoring_decision_gate import (
    BUY_POSITIVE_EMERGENT_SUCCESS_COUNT_MIN,
    BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN,
    HOSTILE_EMERGENT_FAILURE_COUNT_MIN,
    HOSTILE_EMERGENT_FAILURE_RATE_MIN,
)


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
BRANCH_PRIORITY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__branch_priority_queue_v1.json")
BUY_QUEUE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__buy_side_branch_readiness_queue_v1.json")
HOSTILE_WATCHLIST_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__hostile_watchlist_v1.json")


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


def _find_row(rows, slice_name):
    for row in rows:
        if row.get("slice") == slice_name:
            return row
    return None


def render_markdown(payload):
    lines = [
        "# Priority Slice Focus Pack",
        "",
        f"- built_at: `{payload['built_at']}`",
        "",
        "## Primary Buy-Side Focus",
        "",
        f"- slice: `{payload['primary_buy_focus']['slice']}`",
        f"- current_success_count: `{payload['primary_buy_focus']['success_count']}`",
        f"- current_failure_count: `{payload['primary_buy_focus']['failure_count']}`",
        f"- current_success_rate: `{payload['primary_buy_focus']['success_rate']}`",
        f"- additional_clean_successes_needed: `{payload['primary_buy_focus']['additional_clean_successes_needed']}`",
        f"- quality_status: `{payload['primary_buy_focus']['quality_status']}`",
        f"- quality_risks: `{payload['primary_buy_focus']['quality_risks']}`",
        f"- next_refresh_open_research_gate: `success_count >= {payload['primary_buy_focus']['gate']['success_count_min']}` and `success_rate >= {payload['primary_buy_focus']['gate']['success_rate_min']}`",
        "",
        "What to look for next refresh:",
        "",
    ]
    for item in payload["primary_buy_focus"]["watch_for"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Secondary Hostile-Side Focus",
        "",
        f"- slice: `{payload['secondary_hostile_focus']['slice']}`",
        f"- current_failure_count: `{payload['secondary_hostile_focus']['failure_count']}`",
        f"- current_failure_rate: `{payload['secondary_hostile_focus']['failure_rate']}`",
        f"- attention_bucket: `{payload['secondary_hostile_focus']['attention_bucket']}`",
        f"- quality_risks: `{payload['secondary_hostile_focus']['quality_risks']}`",
        f"- hostile_research_gate: `failure_count >= {payload['secondary_hostile_focus']['gate']['failure_count_min']}` and `failure_rate >= {payload['secondary_hostile_focus']['gate']['failure_rate_min']}`",
        "",
        "What to look for next refresh:",
        "",
    ])
    for item in payload["secondary_hostile_focus"]["watch_for"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Current Decision",
        "",
        "- champion stays frozen",
        "- no branch opens from this pack alone",
        "- on the next replay refresh, inspect the buy-side focus first, then the hostile-side focus",
    ])
    return "\n".join(lines) + "\n"


def build_focus_pack():
    branch_priority = load_json(BRANCH_PRIORITY_PATH)
    buy_queue = load_json(BUY_QUEUE_PATH)
    hostile_watchlist = load_json(HOSTILE_WATCHLIST_PATH)

    primary_buy_slice = ((branch_priority.get("primary_buy_focus") or {}).get("slice"))
    secondary_hostile_slice = ((branch_priority.get("secondary_hostile_focus") or {}).get("slice"))

    primary_buy_row = _find_row(buy_queue.get("queue_rows") or [], primary_buy_slice) or {}
    secondary_hostile_row = _find_row(hostile_watchlist.get("warning_slices") or [], secondary_hostile_slice) or {}

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "primary_buy_focus": {
            "slice": primary_buy_slice,
            "success_count": primary_buy_row.get("success_count"),
            "failure_count": primary_buy_row.get("failure_count"),
            "success_rate": primary_buy_row.get("success_rate"),
            "additional_clean_successes_needed": primary_buy_row.get("additional_clean_successes_needed"),
            "quality_status": primary_buy_row.get("quality_status"),
            "quality_risks": primary_buy_row.get("quality_risks") or [],
            "symbols": primary_buy_row.get("symbols") or [],
            "months": primary_buy_row.get("months") or [],
            "gate": {
                "success_count_min": BUY_POSITIVE_EMERGENT_SUCCESS_COUNT_MIN,
                "success_rate_min": BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN,
            },
            "watch_for": [
                "whether the next clean success comes without pushing symbol concentration higher",
                "whether success rate reaches or exceeds the current 0.50 gate",
                "whether a second symbol, not just the current leader, contributes to the next clean success",
            ],
        },
        "secondary_hostile_focus": {
            "slice": secondary_hostile_slice,
            "failure_count": secondary_hostile_row.get("failure_count"),
            "failure_rate": secondary_hostile_row.get("failure_rate"),
            "attention_bucket": _find_row(branch_priority.get("hostile_priority_rows") or [], secondary_hostile_slice).get("attention_bucket") if _find_row(branch_priority.get("hostile_priority_rows") or [], secondary_hostile_slice) else None,
            "quality_risks": _find_row(branch_priority.get("hostile_priority_rows") or [], secondary_hostile_slice).get("quality_risks") if _find_row(branch_priority.get("hostile_priority_rows") or [], secondary_hostile_slice) else [],
            "symbols": secondary_hostile_row.get("symbols") or [],
            "gate": {
                "failure_count_min": HOSTILE_EMERGENT_FAILURE_COUNT_MIN,
                "failure_rate_min": HOSTILE_EMERGENT_FAILURE_RATE_MIN,
            },
            "watch_for": [
                "whether this slice expands into more symbols or stays concentrated",
                "whether failure rate stays near 1.0 or softens materially",
                "whether it begins to show a cleaner separable sub-texture on future refreshes",
            ],
        },
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__priority_slice_focus_pack_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__priority_slice_focus_pack_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__priority_slice_focus_pack_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__priority_slice_focus_pack_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_focus_pack()
    print(json.dumps({
        "primary_buy_focus": payload["primary_buy_focus"]["slice"],
        "secondary_hostile_focus": payload["secondary_hostile_focus"]["slice"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
