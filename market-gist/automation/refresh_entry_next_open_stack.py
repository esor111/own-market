"""
Refresh the next-open entry research stack in the correct order.

This is the operational wrapper for the current Entry Research v1 lane:
1. next-open decision study
2. next-open slice monitor
3. next-open readiness queue
4. commercial-bank candidate study
5. commercial-bank texture validation
6. commercial-bank attribution study
7. next-open trigger sheet
8. next-open executive status
9. next-open operating state
10. next-open exact texture monitor
11. next-open future coverage report
12. next-open future near-miss report
13. next-open cycle packet
14. next-open artifact consistency check
15. next-open decision gate

Usage:
    python refresh_entry_next_open_stack.py
    python refresh_entry_next_open_stack.py DATASET_JSON_PATH
"""
import json
import os
import sys

from config import VALIDATION_DIR
from entry_next_open_artifact_consistency_check import build_entry_next_open_consistency_check
from entry_next_open_branch_readiness_queue import build_entry_next_open_branch_readiness_queue
from entry_next_open_commercial_bank_candidate_study import build_entry_next_open_commercial_bank_candidate_study
from entry_next_open_commercial_bank_attribution_study import build_entry_next_open_commercial_bank_attribution_study
from entry_next_open_commercial_bank_texture_validation import build_entry_next_open_commercial_bank_texture_validation
from entry_next_open_cycle_packet import build_entry_next_open_cycle_packet
from entry_next_open_decision_gate import build_entry_next_open_decision_gate
from entry_next_open_decision_study import build_entry_next_open_decision_study
from entry_next_open_exact_texture_monitor import build_entry_next_open_exact_texture_monitor
from entry_next_open_executive_status import build_entry_next_open_executive_status
from entry_next_open_future_coverage_report import build_entry_next_open_future_coverage_report
from entry_next_open_future_near_miss_report import build_entry_next_open_future_near_miss_report
from entry_next_open_operating_state import build_entry_next_open_operating_state
from entry_next_open_refresh_freshness_gate import build_entry_next_open_freshness_gate
from entry_next_open_slice_monitor import build_entry_next_open_slice_monitor
from entry_next_open_trigger_sheet import build_entry_next_open_trigger_sheet

LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DEFAULT_DATASET_PATH = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__entry_research_dataset_v1.json",
)

def refresh_entry_next_open_stack(dataset_path):
    decision, decision_json_path, decision_md_path = build_entry_next_open_decision_study(dataset_path)
    slice_monitor, slice_monitor_json_path, slice_monitor_md_path = build_entry_next_open_slice_monitor(dataset_path)
    readiness_queue, readiness_json_path, readiness_md_path = build_entry_next_open_branch_readiness_queue(dataset_path)
    candidate_study, candidate_json_path, candidate_md_path = build_entry_next_open_commercial_bank_candidate_study(dataset_path)
    texture_validation, texture_json_path, texture_md_path = build_entry_next_open_commercial_bank_texture_validation(dataset_path)
    attribution_study, attribution_json_path, attribution_md_path = build_entry_next_open_commercial_bank_attribution_study(dataset_path)
    freshness, freshness_json_path, freshness_md_path = build_entry_next_open_freshness_gate()
    trigger_sheet, trigger_json_path, trigger_md_path = build_entry_next_open_trigger_sheet()
    executive_status, executive_json_path, executive_md_path = build_entry_next_open_executive_status()
    operating_state, operating_json_path, operating_md_path = build_entry_next_open_operating_state()
    exact_monitor, exact_monitor_json_path, exact_monitor_md_path = build_entry_next_open_exact_texture_monitor(dataset_path)
    coverage_report, coverage_json_path, coverage_md_path = build_entry_next_open_future_coverage_report(dataset_path)
    near_miss_report, near_miss_json_path, near_miss_md_path = build_entry_next_open_future_near_miss_report(dataset_path)
    consistency, consistency_json_path, consistency_md_path = build_entry_next_open_consistency_check()
    decision_gate, decision_gate_json_path, decision_gate_md_path = build_entry_next_open_decision_gate()
    packet, packet_json_path, packet_md_path = build_entry_next_open_cycle_packet()

    return {
        "dataset_path": dataset_path,
        "enterable_count": (decision.get("enterable_row_count")),
        "refresh_needed": freshness.get("refresh_needed"),
        "decision_best_ranker": ((decision.get("ranker_rows") or [{}])[0] or {}).get("ranker_name"),
        "top_slice": ((readiness_queue.get("queue_rows") or [{}])[0] or {}).get("slice"),
        "top_slice_readiness": ((readiness_queue.get("queue_rows") or [{}])[0] or {}).get("readiness_bucket"),
        "top_slice_quality": ((readiness_queue.get("queue_rows") or [{}])[0] or {}).get("quality_status"),
        "texture_verdict": (texture_validation.get("interpretation") or {}).get("verdict"),
        "attribution_verdict": (attribution_study.get("interpretation") or {}).get("broadening_verdict"),
        "current_entry_lane_status": executive_status.get("current_entry_lane_status"),
        "future_signal_state": exact_monitor.get("future_signal_state"),
        "future_coverage_state": coverage_report.get("coverage_state"),
        "future_near_miss_state": near_miss_report.get("near_miss_state"),
        "consistency_status": consistency.get("overall_status"),
        "decision": decision_gate.get("decision"),
        "decision_json": decision_json_path,
        "decision_md": decision_md_path,
        "freshness_json": freshness_json_path,
        "freshness_md": freshness_md_path,
        "slice_monitor_json": slice_monitor_json_path,
        "slice_monitor_md": slice_monitor_md_path,
        "readiness_queue_json": readiness_json_path,
        "readiness_queue_md": readiness_md_path,
        "candidate_json": candidate_json_path,
        "candidate_md": candidate_md_path,
        "texture_json": texture_json_path,
        "texture_md": texture_md_path,
        "attribution_json": attribution_json_path,
        "attribution_md": attribution_md_path,
        "trigger_json": trigger_json_path,
        "trigger_md": trigger_md_path,
        "executive_json": executive_json_path,
        "executive_md": executive_md_path,
        "operating_json": operating_json_path,
        "operating_md": operating_md_path,
        "exact_monitor_json": exact_monitor_json_path,
        "exact_monitor_md": exact_monitor_md_path,
        "coverage_json": coverage_json_path,
        "coverage_md": coverage_md_path,
        "near_miss_json": near_miss_json_path,
        "near_miss_md": near_miss_md_path,
        "packet_json": packet_json_path,
        "packet_md": packet_md_path,
        "consistency_json": consistency_json_path,
        "consistency_md": consistency_md_path,
        "decision_gate_json": decision_gate_json_path,
        "decision_gate_md": decision_gate_md_path,
    }


def main(argv=None):
    argv = argv or sys.argv[1:]
    dataset_path = argv[0] if argv else DEFAULT_DATASET_PATH
    result = refresh_entry_next_open_stack(dataset_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
