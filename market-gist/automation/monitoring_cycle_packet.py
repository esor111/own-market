"""
Build one readable packet for the latest monitoring cycle.

This is the single-file handoff for the frozen-monitoring phase.

Usage:
    python monitoring_cycle_packet.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
OPERATING_STATE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_operating_state_v1.json")
FRESHNESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_refresh_freshness_gate_v1.json")
CYCLE_SUMMARY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_summary_v1.json")
FOCUS_PACK_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__priority_slice_focus_pack_v1.json")
TRIGGER_SHEET_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__next_refresh_trigger_sheet_v1.json")
READINESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__system_reliability_readiness_scorecard_v1.json")
CONSISTENCY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_artifact_consistency_check_v1.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def render_markdown(payload):
    lines = [
        "# Monitoring Cycle Packet",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- refresh_needed: `{payload['refresh_needed']}`",
        f"- current_decision: `{payload['current_decision']}`",
        f"- consistency_status: `{payload['consistency_status']}`",
        f"- overall_prediction_readiness: `{payload['overall_prediction_readiness']}`",
        f"- buy_side_readiness: `{payload['buy_side_readiness']}`",
        "",
        "## Current Focus",
        "",
        f"- primary_buy_focus: `{payload['primary_buy_focus']}`",
        f"- secondary_hostile_focus: `{payload['secondary_hostile_focus']}`",
        "",
        "## What To Do Now",
        "",
    ]
    for item in payload.get("current_action") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Why",
        "",
    ])
    for item in payload.get("why") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Trigger Reminder",
        "",
    ])
    for item in payload.get("trigger_reminder") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Source Files",
        "",
    ])
    for item in payload.get("source_files") or []:
        lines.append(f"- `{item}`")

    return "\n".join(lines) + "\n"


def build_packet():
    operating_state = load_json(OPERATING_STATE_PATH)
    freshness = load_json(FRESHNESS_PATH)
    cycle_summary = load_json(CYCLE_SUMMARY_PATH)
    focus_pack = load_json(FOCUS_PACK_PATH)
    trigger_sheet = load_json(TRIGGER_SHEET_PATH)
    readiness = load_json(READINESS_PATH)
    consistency = load_json(CONSISTENCY_PATH)

    refresh_needed = bool(freshness.get("refresh_needed"))
    if refresh_needed:
        current_action = [
            "run python monitoring_refresh_freshness_gate.py",
            "run python refresh_monitoring_stack.py --stage core",
            "run python refresh_monitoring_stack.py --stage tail",
            "then read the refreshed packet again",
        ]
    else:
        current_action = [
            "do not run the heavy monitoring core now",
            "wait for a genuinely newer replay window",
            "use the current packet as the operating baseline",
        ]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "refresh_needed": refresh_needed,
        "current_decision": cycle_summary.get("decision"),
        "consistency_status": consistency.get("overall_status"),
        "overall_prediction_readiness": readiness.get("overall_prediction_readiness"),
        "buy_side_readiness": readiness.get("buy_side_readiness"),
        "primary_buy_focus": operating_state.get("primary_buy_focus") or (focus_pack.get("primary_buy_focus") or {}).get("slice"),
        "secondary_hostile_focus": operating_state.get("secondary_hostile_focus") or (focus_pack.get("secondary_hostile_focus") or {}).get("slice"),
        "current_action": current_action,
        "why": operating_state.get("why") or [],
        "trigger_reminder": operating_state.get("trigger_reminder") or [],
        "source_files": [
            "latest__monitoring_operating_state_v1.md",
            "latest__monitoring_refresh_freshness_gate_v1.md",
            "latest__monitoring_cycle_summary_v1.md",
            "latest__priority_slice_focus_pack_v1.md",
            "latest__next_refresh_trigger_sheet_v1.md",
            "latest__system_reliability_readiness_scorecard_v1.md",
            "latest__monitoring_artifact_consistency_check_v1.md",
        ],
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_cycle_packet_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_packet_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_cycle_packet_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_packet_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_packet()
    print(json.dumps({
        "refresh_needed": payload["refresh_needed"],
        "current_decision": payload["current_decision"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
