"""
Turn the unified whole-project state into one explicit current decision.

Usage:
    python system_program_decision_gate.py
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
SYSTEM_OPERATING_STATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_operating_state_v1.json"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def render_markdown(payload):
    lines = [
        "# System Program Decision Gate",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- decision: `{payload['decision']}`",
        "",
        "## Why",
        "",
    ]
    for item in payload.get("reasons") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Signals", ""])
    for key, value in (payload.get("signals") or {}).items():
        lines.append(f"- {key}: `{value}`")

    lines.extend(["", "## Current Action", ""])
    for item in payload.get("current_action") or []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_system_program_decision_gate():
    system_status = load_json(SYSTEM_STATUS_PATH)
    system_consistency = load_json(SYSTEM_CONSISTENCY_PATH)
    operating_state = load_json(SYSTEM_OPERATING_STATE_PATH)

    decision = "keep_operating"
    reasons = [
        "the unified handoff bundle is aligned",
        "neither lane needs a refresh right now",
        "the risk engine still says keep_frozen and the entry lane still says keep_guarded",
    ]
    current_action = [
        "do not open a new research branch now",
        "wait for genuinely newer replay windows",
        "then run python run_system_program_cycle.py",
    ]

    if system_consistency.get("overall_status") != "pass":
        decision = "repair_program_handoff"
        reasons = ["the unified program bundle is not internally aligned"]
        current_action = [
            "rebuild the top-level program artifacts",
            "do not trust the top-level handoff until consistency passes",
        ]
    elif operating_state.get("refresh_needed"):
        if operating_state.get("monitoring_refresh_needed") and operating_state.get("entry_refresh_needed"):
            decision = "rerun_both_lanes"
            reasons = ["both the risk engine and the entry lane have newer input than the current build"]
        elif operating_state.get("monitoring_refresh_needed"):
            decision = "rerun_risk_engine"
            reasons = ["the frozen risk engine has newer input than the current build"]
        elif operating_state.get("entry_refresh_needed"):
            decision = "rerun_entry_lane"
            reasons = ["the guarded entry lane has newer input than the current build"]
        current_action = ["run python run_system_program_cycle.py"]
    elif system_status.get("overall_program_state") != "stable_but_not_ready_for_live_prediction":
        decision = "investigate_program_attention"
        reasons = ["the unified whole-project state is no longer the stable default state"]
        current_action = [
            "read the unified program status first",
            "then inspect the risk and entry lane operating states before acting",
        ]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "decision": decision,
        "reasons": reasons,
        "signals": {
            "overall_program_state": system_status.get("overall_program_state"),
            "system_consistency_status": system_consistency.get("overall_status"),
            "refresh_needed": operating_state.get("refresh_needed"),
            "monitoring_refresh_needed": operating_state.get("monitoring_refresh_needed"),
            "entry_refresh_needed": operating_state.get("entry_refresh_needed"),
            "risk_engine_decision": operating_state.get("risk_engine_decision"),
            "entry_lane_decision": operating_state.get("entry_lane_decision"),
        },
        "current_action": current_action,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__system_program_decision_gate_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR, "latest__system_program_decision_gate_v1.json"
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
    payload, latest_json_path, latest_md_path = build_system_program_decision_gate()
    print(
        json.dumps(
            {
                "decision": payload["decision"],
                "latest_json_path": latest_json_path,
                "latest_md_path": latest_md_path,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
