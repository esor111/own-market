"""
Check consistency across the latest next-open entry artifacts.

Usage:
    python entry_next_open_artifact_consistency_check.py
"""
import json
import os
import time
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
FRESHNESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_refresh_freshness_gate_v1.json")
OPERATING_STATE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_operating_state_v1.json")
EXECUTIVE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_executive_status_v1.json")
PACKET_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_cycle_packet_v1.json")
QUEUE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_branch_readiness_queue_v1.json")
TRIGGER_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_trigger_sheet_v1.json")


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
        "# Entry Next-Open Artifact Consistency Check",
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


def build_entry_next_open_consistency_check():
    freshness = load_json(FRESHNESS_PATH)
    operating_state = load_json(OPERATING_STATE_PATH)
    executive = load_json(EXECUTIVE_PATH)
    packet = load_json(PACKET_PATH)
    queue = load_json(QUEUE_PATH)
    trigger = load_json(TRIGGER_PATH)

    top_row = (queue.get("queue_rows") or [{}])[0]
    checks = []

    def add_check(name, expected, actual):
        checks.append({
            "name": name,
            "expected": expected,
            "actual": actual,
            "status": "pass" if expected == actual else "fail",
        })

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
    add_check(
        "lane_state_alignment",
        executive.get("current_entry_lane_status"),
        operating_state.get("lane_state"),
    )
    add_check(
        "packet_lane_state_alignment",
        executive.get("current_entry_lane_status"),
        packet.get("current_entry_lane_status"),
    )
    add_check(
        "best_candidate_alignment",
        executive.get("current_best_candidate"),
        operating_state.get("current_best_candidate"),
    )
    add_check(
        "packet_best_candidate_alignment",
        executive.get("current_best_candidate"),
        packet.get("current_best_candidate"),
    )
    add_check(
        "queue_top_candidate_alignment",
        top_row.get("slice"),
        executive.get("current_best_candidate"),
    )
    add_check(
        "trigger_top_candidate_alignment",
        top_row.get("slice"),
        trigger.get("current_top_candidate"),
    )
    overall_status = "pass" if all(row["status"] == "pass" for row in checks) else "fail"
    current_action = (
        [
            "entry next-open artifacts are aligned",
            "use the cycle packet or operating state as the current entry-lane handoff",
        ]
        if overall_status == "pass"
        else [
            "rebuild the entry next-open packet after refreshing the stack",
            "do not trust the entry handoff bundle until consistency passes",
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
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_artifact_consistency_check_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_artifact_consistency_check_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_next_open_consistency_check()
    print(json.dumps({
        "overall_status": payload["overall_status"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
