"""
Run the next-open entry cycle safely.

This is the operational entrypoint for the current Entry Research v1 lane:
- check freshness first
- run the entry next-open stack only when needed
- always rebuild the operating state and packet

Usage:
    python run_entry_next_open_cycle.py
    python run_entry_next_open_cycle.py --force-refresh
"""
import argparse
import json

from build_entry_research_dataset import (
    _load_default_replay_ids as load_default_entry_replay_ids,
    build_entry_research_dataset,
)
from entry_next_open_artifact_consistency_check import build_entry_next_open_consistency_check
from entry_next_open_commercial_bank_attribution_study import build_entry_next_open_commercial_bank_attribution_study
from entry_next_open_cycle_packet import build_entry_next_open_cycle_packet
from entry_next_open_decision_gate import build_entry_next_open_decision_gate
from entry_next_open_executive_status import build_entry_next_open_executive_status
from entry_next_open_exact_texture_monitor import build_entry_next_open_exact_texture_monitor
from entry_next_open_future_coverage_report import build_entry_next_open_future_coverage_report
from entry_next_open_future_near_miss_report import build_entry_next_open_future_near_miss_report
from entry_next_open_operating_state import build_entry_next_open_operating_state
from entry_next_open_refresh_freshness_gate import build_entry_next_open_freshness_gate
from refresh_entry_next_open_stack import refresh_entry_next_open_stack
from system_program_status import build_system_program_status
from system_program_status_consistency_check import build_system_program_status_consistency_check


def _maybe_build_system_consistency():
    try:
        return build_system_program_status_consistency_check()
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None, None


def parse_args():
    parser = argparse.ArgumentParser(description="Run the next-open entry cycle safely with freshness awareness.")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Run the full next-open entry stack even if the freshness gate says it is not needed.",
    )
    return parser.parse_args()


def _rebuild_entry_dataset():
    replay_ids = load_default_entry_replay_ids()
    summary, latest_json_path, latest_md_path = build_entry_research_dataset(replay_ids)
    return {
        "replay_id_count": len(summary.get("replay_ids") or []),
        "row_count": summary.get("row_count"),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }


def run_entry_next_open_cycle(force_refresh=False):
    freshness, freshness_json_path, freshness_md_path = build_entry_next_open_freshness_gate()
    refresh_needed = bool(freshness.get("refresh_needed")) or force_refresh

    stack_result = None
    dataset_refresh = None
    if refresh_needed:
        dataset_refresh = _rebuild_entry_dataset()
        stack_result = refresh_entry_next_open_stack(
            dataset_path=r"C:\Users\ishwor\Music\own-organize\own-market\market-gist\data\validation\learning_reviews\latest__entry_research_dataset_v1.json"
        )
        freshness, freshness_json_path, freshness_md_path = build_entry_next_open_freshness_gate()

    operating_state, operating_state_json_path, operating_state_md_path = build_entry_next_open_operating_state()
    attribution_study, attribution_json_path, attribution_md_path = build_entry_next_open_commercial_bank_attribution_study(
        dataset_path=r"C:\Users\ishwor\Music\own-organize\own-market\market-gist\data\validation\learning_reviews\latest__entry_research_dataset_v1.json"
    )
    executive_status, executive_status_json_path, executive_status_md_path = build_entry_next_open_executive_status()
    exact_monitor, exact_monitor_json_path, exact_monitor_md_path = build_entry_next_open_exact_texture_monitor(
        dataset_path=r"C:\Users\ishwor\Music\own-organize\own-market\market-gist\data\validation\learning_reviews\latest__entry_research_dataset_v1.json"
    )
    coverage_report, coverage_json_path, coverage_md_path = build_entry_next_open_future_coverage_report(
        dataset_path=r"C:\Users\ishwor\Music\own-organize\own-market\market-gist\data\validation\learning_reviews\latest__entry_research_dataset_v1.json"
    )
    near_miss_report, near_miss_json_path, near_miss_md_path = build_entry_next_open_future_near_miss_report(
        dataset_path=r"C:\Users\ishwor\Music\own-organize\own-market\market-gist\data\validation\learning_reviews\latest__entry_research_dataset_v1.json"
    )
    build_entry_next_open_cycle_packet()
    consistency, consistency_json_path, consistency_md_path = build_entry_next_open_consistency_check()
    decision_gate, decision_gate_json_path, decision_gate_md_path = build_entry_next_open_decision_gate()
    packet, packet_json_path, packet_md_path = build_entry_next_open_cycle_packet()
    system_status, system_status_json_path, system_status_md_path = build_system_program_status()
    system_consistency, system_consistency_json_path, system_consistency_md_path = _maybe_build_system_consistency()

    return {
        "refresh_needed": freshness.get("refresh_needed"),
        "force_refresh": force_refresh,
        "stack_executed": refresh_needed,
        "dataset_rebuilt": bool(dataset_refresh),
        "dataset_refresh": dataset_refresh,
        "lane_state": operating_state.get("lane_state"),
        "current_best_candidate": operating_state.get("current_best_candidate"),
        "texture_verdict": operating_state.get("current_texture_verdict"),
        "candidate_broadening_state": (attribution_study.get("interpretation") or {}).get("broadening_verdict"),
        "future_signal_state": exact_monitor.get("future_signal_state"),
        "future_coverage_state": coverage_report.get("coverage_state"),
        "future_near_miss_state": near_miss_report.get("near_miss_state"),
        "consistency_status": consistency.get("overall_status"),
        "decision": decision_gate.get("decision"),
        "freshness_json": freshness_json_path,
        "freshness_md": freshness_md_path,
        "stack_result": stack_result,
        "operating_state_json": operating_state_json_path,
        "operating_state_md": operating_state_md_path,
        "executive_status_json": executive_status_json_path,
        "executive_status_md": executive_status_md_path,
        "attribution_json": attribution_json_path,
        "attribution_md": attribution_md_path,
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
        "system_status_json": system_status_json_path,
        "system_status_md": system_status_md_path,
        "overall_program_state": system_status.get("overall_program_state"),
        "system_consistency_json": system_consistency_json_path,
        "system_consistency_md": system_consistency_md_path,
        "system_consistency_status": (system_consistency or {}).get("overall_status", "unknown"),
    }


def main():
    args = parse_args()
    result = run_entry_next_open_cycle(force_refresh=args.force_refresh)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
