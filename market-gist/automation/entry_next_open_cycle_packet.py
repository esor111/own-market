"""
Build one readable packet for the current next-open entry lane.

Usage:
    python entry_next_open_cycle_packet.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
EXECUTIVE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_executive_status_v1.json")
TRIGGER_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_trigger_sheet_v1.json")
TEXTURE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_commercial_bank_texture_validation_v1.json")
QUEUE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_branch_readiness_queue_v1.json")
OPERATING_STATE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_operating_state_v1.json")
FRESHNESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_refresh_freshness_gate_v1.json")
CONSISTENCY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_artifact_consistency_check_v1.json")
EXACT_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_exact_texture_monitor_v1.json")
FUTURE_COVERAGE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_future_coverage_report_v1.json")
NEAR_MISS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_future_near_miss_report_v1.json")
DECISION_GATE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_decision_gate_v1.json")
ATTRIBUTION_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_commercial_bank_attribution_study_v1.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_json_optional(path, default):
    if not os.path.exists(path):
        return default
    return load_json(path)


def render_markdown(payload):
    lines = [
        "# Entry Next-Open Cycle Packet",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- refresh_needed: `{payload['refresh_needed']}`",
        f"- current_entry_lane_status: `{payload['current_entry_lane_status']}`",
        f"- current_best_candidate: `{payload['current_best_candidate']}`",
        f"- current_texture_verdict: `{payload['current_texture_verdict']}`",
        f"- candidate_broadening_state: `{payload['candidate_broadening_state']}`",
        f"- future_signal_state: `{payload['future_signal_state']}`",
        f"- future_coverage_state: `{payload['future_coverage_state']}`",
        f"- future_near_miss_state: `{payload['future_near_miss_state']}`",
        f"- decision: `{payload['decision']}`",
        f"- consistency_status: `{payload['consistency_status']}`",
        "",
        "## Rough Picture",
        "",
    ]
    for item in payload.get("rough_picture") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## What To Do Now",
        "",
    ])
    for item in payload.get("what_to_do_now") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## What Future Data Must Prove",
        "",
    ])
    for item in payload.get("future_must_prove") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Source Files",
        "",
    ])
    for item in payload.get("source_files") or []:
        lines.append(f"- `{item}`")

    return "\n".join(lines) + "\n"


def build_entry_next_open_cycle_packet():
    executive = load_json(EXECUTIVE_PATH)
    trigger = load_json(TRIGGER_PATH)
    texture = load_json(TEXTURE_PATH)
    queue = load_json(QUEUE_PATH)
    operating_state = load_json(OPERATING_STATE_PATH)
    freshness = load_json(FRESHNESS_PATH)
    consistency = load_json_optional(CONSISTENCY_PATH, {"overall_status": "unknown"})
    exact_monitor = load_json_optional(EXACT_MONITOR_PATH, {"future_signal_state": "unknown"})
    future_coverage = load_json_optional(FUTURE_COVERAGE_PATH, {"coverage_state": "unknown"})
    near_miss = load_json_optional(NEAR_MISS_PATH, {"near_miss_state": "unknown"})
    decision_gate = load_json_optional(DECISION_GATE_PATH, {"decision": "unknown"})
    attribution = load_json_optional(ATTRIBUTION_PATH, {"interpretation": {"broadening_verdict": "unknown"}})

    top_row = (queue.get("queue_rows") or [{}])[0]
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "refresh_needed": bool(freshness.get("refresh_needed")),
        "current_entry_lane_status": executive.get("current_entry_lane_status"),
        "current_best_candidate": executive.get("current_best_candidate"),
        "current_texture_verdict": (texture.get("interpretation") or {}).get("verdict"),
        "future_signal_state": exact_monitor.get("future_signal_state"),
        "future_coverage_state": future_coverage.get("coverage_state"),
        "future_near_miss_state": near_miss.get("near_miss_state"),
        "candidate_broadening_state": (attribution.get("interpretation") or {}).get("broadening_verdict"),
        "decision": decision_gate.get("decision"),
        "consistency_status": consistency.get("overall_status"),
        "rough_picture": executive.get("rough_picture") or [],
        "what_to_do_now": (
            [
                "run python entry_next_open_refresh_freshness_gate.py",
                "run python refresh_entry_next_open_stack.py",
                "rebuild the entry packet and consistency check",
                "then reread the refreshed entry handoff bundle",
            ]
            if freshness.get("refresh_needed")
            else [
                "keep Risk Engine v1 frozen",
                "keep the current next-open commercial-bank texture on watch",
                "treat broadening outside the exact texture as guarded and symbol-dependent",
                "wait for a genuinely newer replay window before refreshing the entry stack",
                "do not promote an entry rule until future exact-texture evidence arrives",
            ]
        ),
        "future_must_prove": trigger.get("future_must_prove") or [],
        "current_context": {
            "top_slice_readiness": top_row.get("readiness_bucket"),
            "top_slice_quality": top_row.get("quality_status"),
            "lane_state": operating_state.get("lane_state"),
        },
        "source_files": [
            "latest__entry_next_open_refresh_freshness_gate_v1.md",
            "latest__entry_next_open_operating_state_v1.md",
            "latest__entry_next_open_decision_study_v1.md",
            "latest__entry_next_open_slice_monitor_v1.md",
            "latest__entry_next_open_branch_readiness_queue_v1.md",
            "latest__entry_next_open_commercial_bank_candidate_study_v1.md",
            "latest__entry_next_open_commercial_bank_texture_validation_v1.md",
            "latest__entry_next_open_trigger_sheet_v1.md",
            "latest__entry_next_open_executive_status_v1.md",
            "latest__entry_next_open_exact_texture_monitor_v1.md",
            "latest__entry_next_open_future_coverage_report_v1.md",
            "latest__entry_next_open_future_near_miss_report_v1.md",
            "latest__entry_next_open_commercial_bank_attribution_study_v1.md",
            "latest__entry_next_open_artifact_consistency_check_v1.md",
            "latest__entry_next_open_decision_gate_v1.md",
        ],
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_cycle_packet_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_cycle_packet_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_next_open_cycle_packet()
    print(json.dumps({
        "current_entry_lane_status": payload["current_entry_lane_status"],
        "current_best_candidate": payload["current_best_candidate"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
