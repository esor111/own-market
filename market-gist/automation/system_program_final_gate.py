"""
Build the final whole-project trust gate after all top-level artifacts exist.

Usage:
    python system_program_final_gate.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
SYSTEM_DECISION_GATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_decision_gate_v1.json"
)
SYSTEM_CONSISTENCY_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_status_consistency_check_v1.json"
)
SYSTEM_RECENCY_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_artifact_recency_check_v1.json"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def render_markdown(payload):
    lines = [
        "# System Program Final Gate",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- effective_decision: `{payload['effective_decision']}`",
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


def build_system_program_final_gate():
    decision_gate = load_json(SYSTEM_DECISION_GATE_PATH)
    consistency = load_json(SYSTEM_CONSISTENCY_PATH)
    recency = load_json(SYSTEM_RECENCY_PATH)

    effective_decision = decision_gate.get("decision")
    reasons = list(decision_gate.get("reasons") or [])
    current_action = list(decision_gate.get("current_action") or [])

    if consistency.get("overall_status") != "pass":
        effective_decision = "repair_program_handoff"
        reasons = ["the top-level consistency check is failing"]
        current_action = [
            "rerun python run_system_program_cycle.py",
            "do not trust the whole-project handoff until consistency passes",
        ]
    elif recency.get("overall_status") != "pass":
        effective_decision = "repair_program_handoff"
        reasons = ["the top-level artifact recency check is failing"]
        current_action = [
            "rerun python run_system_program_cycle.py",
            "do not trust the whole-project handoff until recency passes",
        ]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "effective_decision": effective_decision,
        "reasons": reasons,
        "signals": {
            "decision_gate_decision": decision_gate.get("decision"),
            "system_consistency_status": consistency.get("overall_status"),
            "system_recency_status": recency.get("overall_status"),
        },
        "current_action": current_action,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__system_program_final_gate_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR, "latest__system_program_final_gate_v1.json"
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
    payload, latest_json_path, latest_md_path = build_system_program_final_gate()
    print(
        json.dumps(
            {
                "effective_decision": payload["effective_decision"],
                "latest_json_path": latest_json_path,
                "latest_md_path": latest_md_path,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
