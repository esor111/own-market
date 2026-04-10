"""
Build one compact summary of the latest monitoring cycle.

This turns the refresh/checkpoint/diff/gate outputs into one short artifact
that answers:
- where we are now
- what changed
- what to do next

Usage:
    python monitoring_cycle_summary.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
CHECKPOINT_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_watchlist_checkpoint_v1.json")
DIFF_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_watchlist_diff_v1.json")
DECISION_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_decision_gate_v1.json")


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


def render_markdown(payload):
    lines = [
        "# Monitoring Cycle Summary",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- decision: `{payload['decision']}`",
        "",
        "## Current State",
        "",
        f"- hostile_case_count: `{payload['hostile_case_count']}`",
        f"- hostile_actionable_count: `{payload['hostile_actionable_count']}`",
        f"- hostile_warning_watch_count: `{payload['hostile_warning_watch_count']}`",
        f"- hostile_top_warning_slice: `{payload['hostile_top_warning_slice']}`",
        f"- buy_actionable_count: `{payload['buy_actionable_count']}`",
        f"- buy_realistic_success_count: `{payload['buy_realistic_success_count']}`",
        f"- buy_realistic_success_rate: `{payload['buy_realistic_success_rate']}`",
        f"- buy_positive_watch_count: `{payload['buy_positive_watch_count']}`",
        f"- buy_top_positive_slice: `{payload['buy_top_positive_slice']}`",
        f"- buy_top_warning_slice: `{payload['buy_top_warning_slice']}`",
        "",
        "## Drift Check",
        "",
        f"- hostile_warning_worsened: `{payload['hostile_warning_worsened']}`",
        f"- hostile_emergent_candidates: `{payload['hostile_emergent_candidates']}`",
        f"- buy_positive_worsened: `{payload['buy_positive_worsened']}`",
        f"- buy_positive_emergent_candidates: `{payload['buy_positive_emergent_candidates']}`",
        f"- buy_warning_emergent_candidates: `{payload['buy_warning_emergent_candidates']}`",
        "",
        "## Why This Decision",
        "",
    ]
    for reason in payload.get("reasons") or []:
        lines.append(f"- {reason}")

    lines.extend(["", "## Next Action", ""])
    for action in payload.get("current_action") or []:
        lines.append(f"- {action}")
    return "\n".join(lines) + "\n"


def build_summary():
    checkpoint = load_json(CHECKPOINT_PATH)
    diff = load_json(DIFF_PATH)
    decision = load_json(DECISION_PATH)

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "decision": decision.get("decision"),
        "reasons": decision.get("reasons") or [],
        "current_action": decision.get("current_action") or [],
        "hostile_case_count": checkpoint["hostile_side"].get("hostile_case_count"),
        "hostile_actionable_count": checkpoint["hostile_side"].get("actionable_count"),
        "hostile_warning_watch_count": checkpoint["hostile_side"].get("warning_watch_count"),
        "hostile_top_warning_slice": checkpoint["hostile_side"].get("top_warning_slice"),
        "buy_actionable_count": checkpoint["buy_side"].get("actionable_count"),
        "buy_realistic_success_count": checkpoint["buy_side"].get("realistic_success_count"),
        "buy_realistic_success_rate": checkpoint["buy_side"].get("realistic_success_rate"),
        "buy_positive_watch_count": checkpoint["buy_side"].get("positive_watch_count"),
        "buy_top_positive_slice": checkpoint["buy_side"].get("top_positive_slice"),
        "buy_top_warning_slice": checkpoint["buy_side"].get("top_warning_slice"),
        "hostile_warning_worsened": diff["hostile"]["warning_summary"].get("worsened"),
        "hostile_emergent_candidates": len(diff["hostile"].get("emergent_warning_slices") or []),
        "buy_positive_worsened": diff["buy_side"]["positive_summary"].get("worsened"),
        "buy_positive_emergent_candidates": len(diff["buy_side"].get("emergent_positive_slices") or []),
        "buy_warning_emergent_candidates": len(diff["buy_side"].get("emergent_warning_slices") or []),
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_cycle_summary_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_summary_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_cycle_summary_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_summary_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_summary()
    print(json.dumps({
        "decision": payload["decision"],
        "hostile_top_warning_slice": payload["hostile_top_warning_slice"],
        "buy_top_positive_slice": payload["buy_top_positive_slice"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
