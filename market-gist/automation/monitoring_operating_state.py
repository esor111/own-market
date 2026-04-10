"""
Build one top-level operating-state sheet for the frozen-monitoring phase.

This combines:
- freshness gate
- current decision
- readiness
- priority focuses

Usage:
    python monitoring_operating_state.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
FRESHNESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_refresh_freshness_gate_v1.json")
CYCLE_SUMMARY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_summary_v1.json")
BRANCH_PRIORITY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__branch_priority_queue_v1.json")
READINESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__system_reliability_readiness_scorecard_v1.json")
TRIGGER_SHEET_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__next_refresh_trigger_sheet_v1.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _next_commands(refresh_needed):
    if refresh_needed:
        return [
            "python monitoring_refresh_freshness_gate.py",
            "python refresh_monitoring_stack.py --stage core",
            "python refresh_monitoring_stack.py --stage tail",
        ]
    return [
        "wait for a genuinely newer replay window",
        "then run python monitoring_refresh_freshness_gate.py",
        "then run python refresh_monitoring_stack.py --stage core",
        "then run python refresh_monitoring_stack.py --stage tail",
    ]


def render_markdown(payload):
    lines = [
        "# Monitoring Operating State",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- champion_state: `{payload['champion_state']}`",
        f"- refresh_needed: `{payload['refresh_needed']}`",
        f"- current_decision: `{payload['current_decision']}`",
        f"- overall_prediction_readiness: `{payload['overall_prediction_readiness']}`",
        f"- buy_side_readiness: `{payload['buy_side_readiness']}`",
        "",
        "## Current Focus",
        "",
        f"- primary_buy_focus: `{payload['primary_buy_focus']}`",
        f"- secondary_hostile_focus: `{payload['secondary_hostile_focus']}`",
        "",
        "## Why",
        "",
    ]
    for reason in payload.get("why") or []:
        lines.append(f"- {reason}")

    lines.extend(["", "## Next Commands", ""])
    for command in payload.get("next_commands") or []:
        lines.append(f"- `{command}`")

    lines.extend(["", "## Reading Order", ""])
    for item in payload.get("reading_order") or []:
        lines.append(f"- `{item}`")

    lines.extend(["", "## Trigger Reminder", ""])
    for item in payload.get("trigger_reminder") or []:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def build_operating_state():
    freshness = load_json(FRESHNESS_PATH)
    cycle_summary = load_json(CYCLE_SUMMARY_PATH)
    branch_priority = load_json(BRANCH_PRIORITY_PATH)
    readiness = load_json(READINESS_PATH)
    trigger_sheet = load_json(TRIGGER_SHEET_PATH)

    refresh_needed = bool(freshness.get("refresh_needed"))
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "champion_state": "frozen",
        "refresh_needed": refresh_needed,
        "current_decision": cycle_summary.get("decision"),
        "overall_prediction_readiness": readiness.get("overall_prediction_readiness"),
        "buy_side_readiness": readiness.get("buy_side_readiness"),
        "primary_buy_focus": ((branch_priority.get("primary_buy_focus") or {}).get("slice")),
        "secondary_hostile_focus": ((branch_priority.get("secondary_hostile_focus") or {}).get("slice")),
        "why": [],
        "next_commands": _next_commands(refresh_needed),
        "reading_order": [
            "latest__monitoring_cycle_summary_v1.md",
            "latest__priority_slice_focus_pack_v1.md",
            "latest__priority_slice_drilldown_v1.md",
            "latest__next_refresh_trigger_sheet_v1.md",
            "latest__system_reliability_readiness_scorecard_v1.md",
        ],
        "trigger_reminder": [],
    }

    if refresh_needed:
        payload["why"].append("newer replay input exists, so a fresh core monitoring run is justified")
    else:
        payload["why"].append("no monitored replay input is newer than the latest core build")
        payload["why"].append("running the heavy core now would only churn unchanged data")

    if cycle_summary.get("decision") == "keep_frozen":
        payload["why"].append("the current decision gate still says keep_frozen")

    if readiness.get("overall_prediction_readiness") != "ready":
        payload["why"].append("overall prediction trust is still not ready, and the main open gap remains the buy side")

    primary_buy = trigger_sheet.get("primary_buy_focus") or {}
    secondary_hostile = trigger_sheet.get("secondary_hostile_focus") or {}
    payload["trigger_reminder"].append(
        f"buy side: {primary_buy.get('slice')} must improve in quality, not just count"
    )
    payload["trigger_reminder"].append(
        f"hostile side: {secondary_hostile.get('slice')} should only reopen research if it spreads or reveals a cleaner sub-texture"
    )

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_operating_state_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_operating_state_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_operating_state_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_operating_state_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_operating_state()
    print(json.dumps({
        "refresh_needed": payload["refresh_needed"],
        "current_decision": payload["current_decision"],
        "primary_buy_focus": payload["primary_buy_focus"],
        "secondary_hostile_focus": payload["secondary_hostile_focus"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
