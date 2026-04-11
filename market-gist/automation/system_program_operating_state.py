"""
Build one top-level operating-state sheet for the whole project.

Usage:
    python system_program_operating_state.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
SYSTEM_FRESHNESS_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_refresh_freshness_gate_v1.json"
)
SYSTEM_STATUS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__system_program_status_v1.json")
SYSTEM_CONSISTENCY_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_status_consistency_check_v1.json"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _next_commands(monitoring_refresh_needed, entry_refresh_needed):
    if monitoring_refresh_needed or entry_refresh_needed:
        return ["python run_system_program_cycle.py"]
    return [
        "wait for a genuinely newer replay window",
        "then run python run_system_program_cycle.py",
    ]


def render_markdown(payload):
    lines = [
        "# System Program Operating State",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- overall_program_state: `{payload['overall_program_state']}`",
        f"- refresh_needed: `{payload['refresh_needed']}`",
        f"- monitoring_refresh_needed: `{payload['monitoring_refresh_needed']}`",
        f"- entry_refresh_needed: `{payload['entry_refresh_needed']}`",
        f"- risk_engine_decision: `{payload['risk_engine_decision']}`",
        f"- entry_lane_decision: `{payload['entry_lane_decision']}`",
        f"- system_consistency_status: `{payload['system_consistency_status']}`",
        "",
        "## Why",
        "",
    ]
    for item in payload.get("why") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Next Commands", ""])
    for item in payload.get("next_commands") or []:
        lines.append(f"- `{item}`")

    lines.extend(["", "## Reading Order", ""])
    for item in payload.get("reading_order") or []:
        lines.append(f"- `{item}`")

    lines.extend(["", "## Trigger Reminder", ""])
    for item in payload.get("trigger_reminder") or []:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def build_system_program_operating_state():
    system_freshness = load_json(SYSTEM_FRESHNESS_PATH)
    system_status = load_json(SYSTEM_STATUS_PATH)
    system_consistency = load_json(SYSTEM_CONSISTENCY_PATH)

    monitoring_refresh_needed = bool(system_freshness.get("monitoring_refresh_needed"))
    entry_refresh_needed = bool(system_freshness.get("entry_refresh_needed"))
    refresh_needed = bool(system_freshness.get("refresh_needed"))

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "overall_program_state": system_status.get("overall_program_state"),
        "refresh_needed": refresh_needed,
        "monitoring_refresh_needed": monitoring_refresh_needed,
        "entry_refresh_needed": entry_refresh_needed,
        "risk_engine_decision": system_status.get("risk_engine_decision"),
        "entry_lane_decision": system_status.get("entry_lane_decision"),
        "system_consistency_status": system_consistency.get("overall_status"),
        "why": [],
        "next_commands": _next_commands(monitoring_refresh_needed, entry_refresh_needed),
        "reading_order": [
            "latest__system_program_cycle_packet_v1.md",
            "latest__system_program_decision_gate_v1.md",
            "latest__system_program_status_v1.md",
            "latest__system_program_status_consistency_check_v1.md",
        ],
        "trigger_reminder": [
            "risk side: do not open a new caution branch unless the frozen monitoring gate changes",
            "entry side: do not increase trust unless future exact-texture evidence actually repeats",
        ],
    }

    if system_consistency.get("overall_status") != "pass":
        payload["why"].append("the unified program handoff is not aligned yet, so repair beats interpretation")
    if refresh_needed:
        payload["why"].append("the whole-project freshness gate says at least one lane has genuinely newer input")
    else:
        payload["why"].append("the whole-project freshness gate says neither lane has genuinely newer input")
    if system_status.get("overall_program_state") == "stable_but_not_ready_for_live_prediction":
        payload["why"].append("the project is stable, but still not ready for live standalone prediction")
    if system_status.get("risk_engine_decision") == "keep_frozen":
        payload["why"].append("the frozen risk engine still says keep_frozen")
    if system_status.get("entry_lane_decision") == "keep_guarded":
        payload["why"].append("the entry lane still says keep_guarded")

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__system_program_operating_state_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR, "latest__system_program_operating_state_v1.json"
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
    payload, latest_json_path, latest_md_path = build_system_program_operating_state()
    print(
        json.dumps(
            {
                "overall_program_state": payload["overall_program_state"],
                "refresh_needed": payload["refresh_needed"],
                "monitoring_refresh_needed": payload["monitoring_refresh_needed"],
                "entry_refresh_needed": payload["entry_refresh_needed"],
                "risk_engine_decision": payload["risk_engine_decision"],
                "entry_lane_decision": payload["entry_lane_decision"],
                "latest_json_path": latest_json_path,
                "latest_md_path": latest_md_path,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
