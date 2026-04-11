"""
Check consistency across the unified program-status artifact and its source handoff files.

Usage:
    python system_program_status_consistency_check.py
"""
import json
import os
import time
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
SYSTEM_STATUS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__system_program_status_v1.json")
SYSTEM_OPERATING_STATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_operating_state_v1.json"
)
SYSTEM_DECISION_GATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_decision_gate_v1.json"
)
SYSTEM_PACKET_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_cycle_packet_v1.json"
)
SYSTEM_REFRESH_FRESHNESS_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__system_program_refresh_freshness_gate_v1.json"
)
MONITORING_OPERATING_STATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__monitoring_operating_state_v1.json"
)
ENTRY_OPERATING_STATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__entry_next_open_operating_state_v1.json"
)
MONITORING_PACKET_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_packet_v1.json"
)
ENTRY_PACKET_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__entry_next_open_cycle_packet_v1.json"
)


def load_json(path):
    last_error = None
    for _ in range(3):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            last_error = exc
            time.sleep(0.1)
    raise last_error


def render_markdown(payload):
    lines = [
        "# System Program Status Consistency Check",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- overall_status: `{payload['overall_status']}`",
        "",
        "## Checks",
        "",
    ]
    for row in payload.get("checks") or []:
        lines.append(
            f"- `{row['name']}`: status `{row['status']}`, expected `{row['expected']}`, actual `{row['actual']}`"
        )

    lines.extend(["", "## Current Action", ""])
    for item in payload.get("current_action") or []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _expected_program_state(monitoring_state, entry_state):
    if (
        monitoring_state.get("current_decision") == "keep_frozen"
        and entry_state.get("decision") == "keep_guarded"
    ):
        return "stable_but_not_ready_for_live_prediction"
    return "needs_attention"


def build_system_program_status_consistency_check():
    system_status = load_json(SYSTEM_STATUS_PATH)
    system_operating_state = load_json(SYSTEM_OPERATING_STATE_PATH)
    system_decision_gate = load_json(SYSTEM_DECISION_GATE_PATH)
    system_packet = load_json(SYSTEM_PACKET_PATH)
    system_refresh_freshness = load_json(SYSTEM_REFRESH_FRESHNESS_PATH)
    monitoring_state = load_json(MONITORING_OPERATING_STATE_PATH)
    entry_state = load_json(ENTRY_OPERATING_STATE_PATH)
    monitoring_packet = load_json(MONITORING_PACKET_PATH)
    entry_packet = load_json(ENTRY_PACKET_PATH)

    checks = []

    def add_check(name, expected, actual):
        checks.append(
            {
                "name": name,
                "expected": expected,
                "actual": actual,
                "status": "pass" if expected == actual else "fail",
            }
        )

    add_check(
        "risk_engine_decision_alignment",
        monitoring_state.get("current_decision"),
        system_status.get("risk_engine_decision"),
    )
    add_check(
        "entry_lane_decision_alignment",
        entry_state.get("decision"),
        system_status.get("entry_lane_decision"),
    )
    add_check(
        "risk_packet_alignment",
        monitoring_packet.get("current_decision"),
        system_status.get("risk_engine_decision"),
    )
    add_check(
        "entry_packet_alignment",
        entry_packet.get("decision"),
        system_status.get("entry_lane_decision"),
    )
    add_check(
        "entry_candidate_alignment",
        entry_state.get("current_best_candidate"),
        system_status.get("entry_current_best_candidate"),
    )
    add_check(
        "overall_program_state_alignment",
        _expected_program_state(monitoring_state, entry_state),
        system_status.get("overall_program_state"),
    )
    add_check(
        "operating_state_program_state_alignment",
        system_status.get("overall_program_state"),
        system_operating_state.get("overall_program_state"),
    )
    add_check(
        "freshness_refresh_needed_alignment",
        bool(system_refresh_freshness.get("refresh_needed")),
        bool(system_operating_state.get("refresh_needed")),
    )
    add_check(
        "freshness_monitoring_alignment",
        bool(system_refresh_freshness.get("monitoring_refresh_needed")),
        bool(system_operating_state.get("monitoring_refresh_needed")),
    )
    add_check(
        "freshness_entry_alignment",
        bool(system_refresh_freshness.get("entry_refresh_needed")),
        bool(system_operating_state.get("entry_refresh_needed")),
    )
    add_check(
        "decision_gate_risk_alignment",
        system_status.get("risk_engine_decision"),
        (system_decision_gate.get("signals") or {}).get("risk_engine_decision"),
    )
    add_check(
        "decision_gate_entry_alignment",
        system_status.get("entry_lane_decision"),
        (system_decision_gate.get("signals") or {}).get("entry_lane_decision"),
    )
    add_check(
        "packet_program_state_alignment",
        system_status.get("overall_program_state"),
        system_packet.get("overall_program_state"),
    )
    add_check(
        "packet_decision_alignment",
        system_decision_gate.get("decision"),
        system_packet.get("current_decision"),
    )
    add_check(
        "decision_gate_refresh_alignment",
        bool(system_operating_state.get("refresh_needed")),
        bool((system_decision_gate.get("signals") or {}).get("refresh_needed")),
    )
    add_check(
        "packet_refresh_alignment",
        bool(system_operating_state.get("refresh_needed")),
        bool(system_packet.get("refresh_needed")),
    )

    overall_status = "pass" if all(row["status"] == "pass" for row in checks) else "fail"
    current_action = (
        [
            "the unified program-status artifact is aligned with the risk, entry, and whole-project freshness bundles",
            "use the program-status file as the top-level current-state summary",
        ]
        if overall_status == "pass"
        else [
            "rebuild the system program status after rebuilding the operating states",
            "do not trust the unified handoff until consistency passes",
        ]
    )

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "overall_status": overall_status,
        "checks": checks,
        "current_action": current_action,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__system_program_status_consistency_check_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR, "latest__system_program_status_consistency_check_v1.json"
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
    payload, latest_json_path, latest_md_path = build_system_program_status_consistency_check()
    print(
        json.dumps(
            {
                "overall_status": payload["overall_status"],
                "latest_json_path": latest_json_path,
                "latest_md_path": latest_md_path,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
