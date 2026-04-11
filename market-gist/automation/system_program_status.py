"""
Build one unified program-status sheet across the frozen risk engine and the guarded entry lane.

Usage:
    python system_program_status.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
MONITORING_OPERATING_STATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__monitoring_operating_state_v1.json"
)
ENTRY_OPERATING_STATE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__entry_next_open_operating_state_v1.json"
)
MONITORING_EXECUTIVE_STATUS_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__monitoring_executive_status_v1.json"
)
ENTRY_EXECUTIVE_STATUS_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__entry_next_open_executive_status_v1.json"
)
MONITORING_PACKET_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_packet_v1.json"
)
ENTRY_PACKET_PATH = os.path.join(
    LEARNING_REVIEWS_DIR, "latest__entry_next_open_cycle_packet_v1.json"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _overall_program_state(monitoring_state, entry_state):
    if (
        monitoring_state.get("current_decision") == "keep_frozen"
        and entry_state.get("decision") == "keep_guarded"
    ):
        return "stable_but_not_ready_for_live_prediction"
    return "needs_attention"


def _next_actions(monitoring_state, entry_state):
    actions = []
    if monitoring_state.get("refresh_needed"):
        actions.append("run python run_monitoring_cycle.py")
    else:
        actions.append("wait for a genuinely newer replay window before rerunning the risk engine cycle")

    if entry_state.get("refresh_needed"):
        actions.append("run python run_entry_next_open_cycle.py")
    else:
        actions.append("wait for a genuinely newer replay window before rerunning the entry lane cycle")

    actions.append("do not open a new branch unless the risk gate or the entry gate changes")
    return actions


def render_markdown(payload):
    lines = [
        "# System Program Status",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- overall_program_state: `{payload['overall_program_state']}`",
        f"- risk_engine_state: `{payload['risk_engine_state']}`",
        f"- risk_engine_decision: `{payload['risk_engine_decision']}`",
        f"- entry_lane_state: `{payload['entry_lane_state']}`",
        f"- entry_lane_decision: `{payload['entry_lane_decision']}`",
        "",
        "## Rough Picture",
        "",
    ]
    for item in payload.get("rough_picture") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Best Current Truths", ""])
    for item in payload.get("best_current_truths") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Main Blockers", ""])
    for item in payload.get("main_blockers") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## What To Do Now", ""])
    for item in payload.get("what_to_do_now") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Reading Order", ""])
    for item in payload.get("reading_order") or []:
        lines.append(f"- `{item}`")

    return "\n".join(lines) + "\n"


def build_system_program_status():
    monitoring_state = load_json(MONITORING_OPERATING_STATE_PATH)
    entry_state = load_json(ENTRY_OPERATING_STATE_PATH)
    monitoring_exec = load_json(MONITORING_EXECUTIVE_STATUS_PATH)
    entry_exec = load_json(ENTRY_EXECUTIVE_STATUS_PATH)
    monitoring_packet = load_json(MONITORING_PACKET_PATH)
    entry_packet = load_json(ENTRY_PACKET_PATH)

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "overall_program_state": _overall_program_state(monitoring_state, entry_state),
        "risk_engine_state": monitoring_state.get("champion_state"),
        "risk_engine_decision": monitoring_state.get("current_decision"),
        "risk_overall_prediction_readiness": monitoring_exec.get("overall_prediction_readiness"),
        "risk_buy_side_readiness": monitoring_exec.get("buy_side_readiness"),
        "entry_lane_state": entry_state.get("lane_state"),
        "entry_lane_decision": entry_state.get("decision"),
        "entry_current_best_candidate": entry_state.get("current_best_candidate"),
        "entry_candidate_broadening_state": entry_packet.get("candidate_broadening_state"),
        "entry_future_signal_state": entry_packet.get("future_signal_state"),
        "entry_future_coverage_state": entry_packet.get("future_coverage_state"),
        "entry_future_near_miss_state": entry_packet.get("future_near_miss_state"),
        "rough_picture": [
            "the risk engine is frozen and still behaving as expected",
            "the entry lane is alive and more honest than before, but still guarded",
            f"broadening beyond the best entry texture is currently {entry_packet.get('candidate_broadening_state')}",
            "current work is improving clarity and decision quality more than raw predictive power",
            "the project is not stuck, but it is still not ready for live standalone prediction",
        ],
        "best_current_truths": [
            f"risk side: {monitoring_exec.get('current_decision')} with overall readiness {monitoring_exec.get('overall_prediction_readiness')}",
            f"entry side: {entry_state.get('decision')} with lane state {entry_exec.get('current_entry_lane_status')}",
            f"best current entry candidate: {entry_state.get('current_best_candidate')}",
            f"entry broadening state: {entry_packet.get('candidate_broadening_state')}",
            f"entry future evidence: {entry_packet.get('future_signal_state')} / {entry_packet.get('future_coverage_state')} / {entry_packet.get('future_near_miss_state')}",
        ],
        "main_blockers": [],
        "what_to_do_now": _next_actions(monitoring_state, entry_state),
        "reading_order": [
            "latest__system_program_status_v1.md",
            "latest__monitoring_operating_state_v1.md",
            "latest__entry_next_open_operating_state_v1.md",
            "latest__monitoring_cycle_packet_v1.md",
            "latest__entry_next_open_cycle_packet_v1.md",
        ],
    }

    payload["main_blockers"].extend(monitoring_exec.get("main_blockers") or [])
    payload["main_blockers"].extend(entry_exec.get("main_blockers") or [])

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__system_program_status_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR, "latest__system_program_status_v1.json"
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
    payload, latest_json_path, latest_md_path = build_system_program_status()
    print(
        json.dumps(
            {
                "overall_program_state": payload["overall_program_state"],
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
