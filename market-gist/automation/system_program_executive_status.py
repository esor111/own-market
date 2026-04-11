"""
Build one short executive summary for the whole project.

Usage:
    python system_program_executive_status.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
SYSTEM_STATUS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__system_program_status_v1.json")
SYSTEM_OPERATING_STATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_operating_state_v1.json"
)
SYSTEM_REFRESH_FRESHNESS_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_refresh_freshness_gate_v1.json"
)
SYSTEM_DECISION_GATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_decision_gate_v1.json"
)
SYSTEM_FINAL_GATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_final_gate_v1.json"
)
MONITORING_EXEC_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__monitoring_executive_status_v1.json"
)
ENTRY_EXEC_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__entry_next_open_executive_status_v1.json"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def render_markdown(payload):
    lines = [
        "# System Program Executive Status",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- overall_program_state: `{payload['overall_program_state']}`",
        f"- current_decision: `{payload['current_decision']}`",
        f"- raw_decision: `{payload['raw_decision']}`",
        "",
        "## Rough Picture",
        "",
    ]
    for item in payload.get("rough_picture") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## What Is Working", ""])
    for item in payload.get("what_is_working") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Main Blockers", ""])
    for item in payload.get("main_blockers") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## What To Do Now", ""])
    for item in payload.get("what_to_do_now") or []:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def build_system_program_executive_status():
    system_status = load_json(SYSTEM_STATUS_PATH)
    operating_state = load_json(SYSTEM_OPERATING_STATE_PATH)
    system_refresh_freshness = load_json(SYSTEM_REFRESH_FRESHNESS_PATH)
    decision_gate = load_json(SYSTEM_DECISION_GATE_PATH)
    final_gate = load_json(SYSTEM_FINAL_GATE_PATH)
    monitoring_exec = load_json(MONITORING_EXEC_PATH)
    entry_exec = load_json(ENTRY_EXEC_PATH)

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "overall_program_state": system_status.get("overall_program_state"),
        "current_decision": final_gate.get("effective_decision"),
        "raw_decision": decision_gate.get("decision"),
        "rough_picture": [
            "the project is stable and internally aligned",
            "the risk engine is real enough to stay frozen",
            "the entry lane is alive, but still guarded and not promotable",
            f"broadening beyond the best entry texture is {system_status.get('entry_candidate_broadening_state')}",
            "current progress is still more about trust and clarity than new predictive power",
        ],
        "what_is_working": [
            f"risk side: {system_status.get('risk_engine_decision')}",
            f"entry side: {system_status.get('entry_lane_decision')}",
            "whole-project operating stack is now in place",
            "whole-project consistency is passing",
            f"whole-project final gate: {final_gate.get('effective_decision')}",
        ],
        "main_blockers": [],
        "what_to_do_now": final_gate.get("current_action") or decision_gate.get("current_action") or operating_state.get("next_commands") or [],
    }

    if system_refresh_freshness.get("refresh_needed"):
        payload["rough_picture"].append("at least one lane has genuinely newer input than the current build")
    else:
        payload["rough_picture"].append("the top-level freshness gate still says no new lane input is worth rerunning")

    payload["main_blockers"].extend(monitoring_exec.get("main_blockers") or [])
    payload["main_blockers"].extend(entry_exec.get("main_blockers") or [])

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__system_program_executive_status_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR, "latest__system_program_executive_status_v1.json"
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
    payload, latest_json_path, latest_md_path = build_system_program_executive_status()
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
