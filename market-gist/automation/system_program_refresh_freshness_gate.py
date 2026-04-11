"""
Build one whole-project freshness gate across the frozen risk engine and guarded entry lane.

Usage:
    python system_program_refresh_freshness_gate.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
MONITORING_FRESHNESS_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__monitoring_refresh_freshness_gate_v1.json"
)
ENTRY_FRESHNESS_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__entry_next_open_refresh_freshness_gate_v1.json"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def render_markdown(payload):
    lines = [
        "# System Program Refresh Freshness Gate",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- refresh_needed: `{payload['refresh_needed']}`",
        f"- monitoring_refresh_needed: `{payload['monitoring_refresh_needed']}`",
        f"- entry_refresh_needed: `{payload['entry_refresh_needed']}`",
        "",
        "## Why",
        "",
    ]
    for item in payload.get("reasons") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Current Action", ""])
    for item in payload.get("current_action") or []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_system_program_refresh_freshness_gate():
    monitoring_freshness = load_json(MONITORING_FRESHNESS_PATH)
    entry_freshness = load_json(ENTRY_FRESHNESS_PATH)

    monitoring_refresh_needed = bool(monitoring_freshness.get("refresh_needed"))
    entry_refresh_needed = bool(entry_freshness.get("refresh_needed"))
    refresh_needed = monitoring_refresh_needed or entry_refresh_needed

    reasons = []
    if monitoring_refresh_needed:
        reasons.append("the frozen risk-engine monitoring lane has newer input than its current build")
    if entry_refresh_needed:
        reasons.append("the guarded entry lane has newer input than its current build")
    if not reasons:
        reasons.append("neither the frozen risk-engine lane nor the guarded entry lane has newer input")

    if refresh_needed:
        current_action = ["run python run_system_program_cycle.py"]
    else:
        current_action = [
            "skip the whole-project cycle for now",
            "wait for a genuinely newer replay window before rerunning the top-level program cycle",
        ]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "refresh_needed": refresh_needed,
        "monitoring_refresh_needed": monitoring_refresh_needed,
        "entry_refresh_needed": entry_refresh_needed,
        "reasons": reasons,
        "current_action": current_action,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__system_program_refresh_freshness_gate_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR, "latest__system_program_refresh_freshness_gate_v1.json"
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
    payload, latest_json_path, latest_md_path = build_system_program_refresh_freshness_gate()
    print(
        json.dumps(
            {
                "refresh_needed": payload["refresh_needed"],
                "monitoring_refresh_needed": payload["monitoring_refresh_needed"],
                "entry_refresh_needed": payload["entry_refresh_needed"],
                "latest_json_path": latest_json_path,
                "latest_md_path": latest_md_path,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
