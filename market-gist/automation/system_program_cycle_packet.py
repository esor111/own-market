"""
Build one readable packet for the whole project cycle.

Usage:
    python system_program_cycle_packet.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
SYSTEM_STATUS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__system_program_status_v1.json")
SYSTEM_CONSISTENCY_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_status_consistency_check_v1.json"
)
SYSTEM_REFRESH_FRESHNESS_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_refresh_freshness_gate_v1.json"
)
SYSTEM_OPERATING_STATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_operating_state_v1.json"
)
SYSTEM_DECISION_GATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_decision_gate_v1.json"
)
SYSTEM_FINAL_GATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_final_gate_v1.json"
)
SYSTEM_RECENCY_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_artifact_recency_check_v1.json"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def render_markdown(payload):
    lines = [
        "# System Program Cycle Packet",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- overall_program_state: `{payload['overall_program_state']}`",
        f"- current_decision: `{payload['current_decision']}`",
        f"- raw_decision: `{payload['raw_decision']}`",
        f"- risk_engine_decision: `{payload['risk_engine_decision']}`",
        f"- entry_lane_decision: `{payload['entry_lane_decision']}`",
        f"- refresh_needed: `{payload['refresh_needed']}`",
        f"- system_consistency_status: `{payload['system_consistency_status']}`",
        f"- system_recency_status: `{payload['system_recency_status']}`",
        "",
        "## What To Do Now",
        "",
    ]
    for item in payload.get("current_action") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Why", ""])
    for item in payload.get("why") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Source Files", ""])
    for item in payload.get("source_files") or []:
        lines.append(f"- `{item}`")

    return "\n".join(lines) + "\n"


def build_system_program_cycle_packet():
    system_status = load_json(SYSTEM_STATUS_PATH)
    system_consistency = load_json(SYSTEM_CONSISTENCY_PATH)
    system_refresh_freshness = load_json(SYSTEM_REFRESH_FRESHNESS_PATH)
    operating_state = load_json(SYSTEM_OPERATING_STATE_PATH)
    decision_gate = load_json(SYSTEM_DECISION_GATE_PATH)
    final_gate = load_json(SYSTEM_FINAL_GATE_PATH)
    recency = load_json(SYSTEM_RECENCY_PATH)
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "overall_program_state": system_status.get("overall_program_state"),
        "current_decision": final_gate.get("effective_decision"),
        "raw_decision": decision_gate.get("decision"),
        "risk_engine_decision": system_status.get("risk_engine_decision"),
        "entry_lane_decision": system_status.get("entry_lane_decision"),
        "refresh_needed": operating_state.get("refresh_needed"),
        "system_consistency_status": system_consistency.get("overall_status"),
        "system_recency_status": recency.get("overall_status"),
        "current_action": final_gate.get("current_action") or decision_gate.get("current_action") or [],
        "why": operating_state.get("why") or [],
        "source_files": [
            "latest__system_program_refresh_freshness_gate_v1.md",
            "latest__system_program_status_v1.md",
            "latest__system_program_status_consistency_check_v1.md",
            "latest__system_program_artifact_recency_check_v1.md",
            "latest__system_program_final_gate_v1.md",
            "latest__system_program_operating_state_v1.md",
            "latest__system_program_decision_gate_v1.md",
        ],
    }

    if system_refresh_freshness.get("refresh_needed") != payload["refresh_needed"]:
        payload["why"] = [
            "warning: top-level freshness gate and operating-state refresh flags are out of sync"
        ] + payload["why"]

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__system_program_cycle_packet_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR, "latest__system_program_cycle_packet_v1.json"
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_system_program_cycle_packet()
    print(
        json.dumps(
            {
                "overall_program_state": payload["overall_program_state"],
                "current_decision": payload["current_decision"],
                "latest_json_path": latest_json_path,
                "latest_md_path": latest_md_path,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
