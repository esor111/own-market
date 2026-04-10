"""
Check consistency across the latest monitoring artifacts.

Usage:
    python monitoring_artifact_consistency_check.py
"""
import json
import os
import time
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DECISION_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_decision_gate_v1.json")
OPERATING_STATE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_operating_state_v1.json")
PACKET_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_packet_v1.json")
BRANCH_PRIORITY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__branch_priority_queue_v1.json")
FRESHNESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_refresh_freshness_gate_v1.json")


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
        "# Monitoring Artifact Consistency Check",
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


def build_check():
    decision = load_json(DECISION_PATH)
    operating_state = load_json(OPERATING_STATE_PATH)
    packet = load_json(PACKET_PATH)
    branch_priority = load_json(BRANCH_PRIORITY_PATH)
    freshness = load_json(FRESHNESS_PATH)

    checks = []

    def add_check(name, expected, actual):
        checks.append({
            "name": name,
            "expected": expected,
            "actual": actual,
            "status": "pass" if expected == actual else "fail",
        })

    add_check(
        "decision_alignment",
        decision.get("decision"),
        operating_state.get("current_decision"),
    )
    add_check(
        "packet_decision_alignment",
        decision.get("decision"),
        packet.get("current_decision"),
    )
    add_check(
        "buy_focus_alignment",
        ((branch_priority.get("primary_buy_focus") or {}).get("slice")),
        operating_state.get("primary_buy_focus"),
    )
    add_check(
        "packet_buy_focus_alignment",
        ((branch_priority.get("primary_buy_focus") or {}).get("slice")),
        packet.get("primary_buy_focus"),
    )
    add_check(
        "hostile_focus_alignment",
        ((branch_priority.get("secondary_hostile_focus") or {}).get("slice")),
        operating_state.get("secondary_hostile_focus"),
    )
    add_check(
        "packet_hostile_focus_alignment",
        ((branch_priority.get("secondary_hostile_focus") or {}).get("slice")),
        packet.get("secondary_hostile_focus"),
    )
    add_check(
        "refresh_needed_alignment",
        freshness.get("refresh_needed"),
        operating_state.get("refresh_needed"),
    )
    add_check(
        "packet_refresh_needed_alignment",
        freshness.get("refresh_needed"),
        packet.get("refresh_needed"),
    )

    overall_status = "pass" if all(row["status"] == "pass" for row in checks) else "fail"
    current_action = (
        ["monitoring artifacts are aligned", "use the packet or operating state as the current handoff"]
        if overall_status == "pass"
        else ["rebuild the monitoring tail artifacts", "do not trust the handoff bundle until consistency passes"]
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
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_artifact_consistency_check_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_artifact_consistency_check_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_artifact_consistency_check_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_artifact_consistency_check_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_check()
    print(json.dumps({
        "overall_status": payload["overall_status"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
