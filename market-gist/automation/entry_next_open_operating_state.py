"""
Build one top-level operating-state sheet for the next-open entry lane.

Usage:
    python entry_next_open_operating_state.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
FRESHNESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_refresh_freshness_gate_v1.json")
QUEUE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_branch_readiness_queue_v1.json")
TEXTURE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_commercial_bank_texture_validation_v1.json")
TRIGGER_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_trigger_sheet_v1.json")
EXECUTIVE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_executive_status_v1.json")
EXACT_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_exact_texture_monitor_v1.json")
FUTURE_COVERAGE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_future_coverage_report_v1.json")
NEAR_MISS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_future_near_miss_report_v1.json")
DECISION_GATE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_decision_gate_v1.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _next_commands(refresh_needed):
    if refresh_needed:
        return [
            "python entry_next_open_refresh_freshness_gate.py",
            "python refresh_entry_next_open_stack.py",
        ]
    return [
        "wait for a genuinely newer replay window",
        "then run python entry_next_open_refresh_freshness_gate.py",
        "then run python refresh_entry_next_open_stack.py",
    ]


def render_markdown(payload):
    lines = [
        "# Entry Next-Open Operating State",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- lane_state: `{payload['lane_state']}`",
        f"- refresh_needed: `{payload['refresh_needed']}`",
        f"- current_best_candidate: `{payload['current_best_candidate']}`",
        f"- current_texture_verdict: `{payload['current_texture_verdict']}`",
        f"- decision: `{payload['decision']}`",
        f"- future_signal_state: `{payload['future_signal_state']}`",
        f"- future_coverage_state: `{payload['future_coverage_state']}`",
        f"- future_near_miss_state: `{payload['future_near_miss_state']}`",
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


def build_entry_next_open_operating_state():
    freshness = load_json(FRESHNESS_PATH)
    queue = load_json(QUEUE_PATH)
    texture = load_json(TEXTURE_PATH)
    trigger = load_json(TRIGGER_PATH)
    executive = load_json(EXECUTIVE_PATH)
    exact_monitor = load_json(EXACT_MONITOR_PATH)
    future_coverage = load_json(FUTURE_COVERAGE_PATH)
    near_miss = load_json(NEAR_MISS_PATH)
    decision_gate = load_json(DECISION_GATE_PATH)

    top_row = (queue.get("queue_rows") or [{}])[0]
    refresh_needed = bool(freshness.get("refresh_needed"))
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "lane_state": executive.get("current_entry_lane_status"),
        "refresh_needed": refresh_needed,
        "current_best_candidate": executive.get("current_best_candidate") or top_row.get("slice"),
        "current_texture_verdict": (texture.get("interpretation") or {}).get("verdict"),
        "decision": decision_gate.get("decision"),
        "future_signal_state": exact_monitor.get("future_signal_state"),
        "future_coverage_state": future_coverage.get("coverage_state"),
        "future_near_miss_state": near_miss.get("near_miss_state"),
        "why": [],
        "next_commands": _next_commands(refresh_needed),
        "reading_order": [
            "latest__entry_next_open_cycle_packet_v1.md",
            "latest__entry_next_open_decision_gate_v1.md",
            "latest__entry_next_open_future_near_miss_report_v1.md",
            "latest__entry_next_open_future_coverage_report_v1.md",
        ],
        "trigger_reminder": trigger.get("future_must_prove") or [],
    }

    if refresh_needed:
        payload["why"].append("newer replay input exists, so a fresh next-open entry refresh is justified")
    else:
        payload["why"].append("no entry-dataset replay input is newer than the latest next-open build")
        payload["why"].append("running the next-open stack now would only churn unchanged data")

    if executive.get("current_entry_lane_status") == "promising_but_not_ready":
        payload["why"].append("the next-open lane is promising, but still sample-limited and not ready for promotion")
    if top_row.get("quality_status") == "gate_ready_but_guarded":
        payload["why"].append("the top slice is good enough to watch closely, but still carries guarded-candidate risk")
    if decision_gate.get("decision") == "keep_guarded":
        payload["why"].append("the current branch decision is to keep the candidate guarded, not to promote or kill it yet")
    if future_coverage.get("coverage_state") == "future_target_slice_present_but_exact_absent":
        payload["why"].append("future months are reaching the target slice without reproducing the exact texture")
    if near_miss.get("near_miss_state") == "future_target_near_misses_without_exact_repeat":
        payload["why"].append("future target-slice near misses are currently negative, which argues for caution")

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_operating_state_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_operating_state_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_next_open_operating_state()
    print(json.dumps({
        "lane_state": payload["lane_state"],
        "refresh_needed": payload["refresh_needed"],
        "current_best_candidate": payload["current_best_candidate"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
