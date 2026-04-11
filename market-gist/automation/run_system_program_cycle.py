"""
Run the full project program cycle safely.

This is the top-level entrypoint across both lanes:
- frozen risk engine monitoring
- guarded entry next-open lane
- unified program status and consistency

Usage:
    python run_system_program_cycle.py
    python run_system_program_cycle.py --force-monitoring
    python run_system_program_cycle.py --force-entry
    python run_system_program_cycle.py --force-all
"""
import argparse
import json

from run_monitoring_cycle import run_cycle
from run_entry_next_open_cycle import run_entry_next_open_cycle
from system_program_artifact_recency_check import build_system_program_artifact_recency_check
from system_program_cycle_packet import build_system_program_cycle_packet
from system_program_decision_gate import build_system_program_decision_gate
from system_program_executive_status import build_system_program_executive_status
from system_program_final_gate import build_system_program_final_gate
from system_program_operating_state import build_system_program_operating_state
from system_program_refresh_freshness_gate import build_system_program_refresh_freshness_gate
from system_program_status import build_system_program_status
from system_program_status_consistency_check import build_system_program_status_consistency_check


def parse_args():
    parser = argparse.ArgumentParser(description="Run the whole project program cycle safely.")
    parser.add_argument(
        "--force-monitoring",
        action="store_true",
        help="Force the frozen risk-engine monitoring cycle even if freshness says not needed.",
    )
    parser.add_argument(
        "--force-entry",
        action="store_true",
        help="Force the guarded entry-lane cycle even if freshness says not needed.",
    )
    parser.add_argument(
        "--force-all",
        action="store_true",
        help="Force both monitoring and entry cycles.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the concise top-level summary instead of the full nested result.",
    )
    return parser.parse_args()


def run_system_program_cycle(force_monitoring=False, force_entry=False):
    monitoring_result = run_cycle(force_core=force_monitoring)
    entry_result = run_entry_next_open_cycle(force_refresh=force_entry)
    system_status, system_status_json_path, system_status_md_path = build_system_program_status()
    system_freshness, system_freshness_json_path, system_freshness_md_path = (
        build_system_program_refresh_freshness_gate()
    )
    system_operating_state, system_operating_state_json_path, system_operating_state_md_path = (
        build_system_program_operating_state()
    )
    system_consistency, system_consistency_json_path, system_consistency_md_path = (
        build_system_program_status_consistency_check()
    )
    system_decision_gate, system_decision_gate_json_path, system_decision_gate_md_path = (
        build_system_program_decision_gate()
    )
    system_recency, system_recency_json_path, system_recency_md_path = (
        build_system_program_artifact_recency_check()
    )
    system_final_gate, system_final_gate_json_path, system_final_gate_md_path = (
        build_system_program_final_gate()
    )
    system_packet, system_packet_json_path, system_packet_md_path = build_system_program_cycle_packet()
    system_exec, system_exec_json_path, system_exec_md_path = build_system_program_executive_status()

    return {
        "monitoring_executed": monitoring_result.get("core_executed"),
        "entry_executed": entry_result.get("stack_executed"),
        "risk_engine_decision": monitoring_result.get("current_decision"),
        "entry_lane_decision": entry_result.get("decision"),
        "overall_program_state": system_status.get("overall_program_state"),
        "system_consistency_status": system_consistency.get("overall_status"),
        "system_operating_state_json": system_operating_state_json_path,
        "system_operating_state_md": system_operating_state_md_path,
        "system_freshness_json": system_freshness_json_path,
        "system_freshness_md": system_freshness_md_path,
        "system_decision_gate_json": system_decision_gate_json_path,
        "system_decision_gate_md": system_decision_gate_md_path,
        "system_packet_json": system_packet_json_path,
        "system_packet_md": system_packet_md_path,
        "system_status_json": system_status_json_path,
        "system_status_md": system_status_md_path,
        "system_consistency_json": system_consistency_json_path,
        "system_consistency_md": system_consistency_md_path,
        "system_exec_json": system_exec_json_path,
        "system_exec_md": system_exec_md_path,
        "system_recency_json": system_recency_json_path,
        "system_recency_md": system_recency_md_path,
        "system_final_gate_json": system_final_gate_json_path,
        "system_final_gate_md": system_final_gate_md_path,
        "system_program_decision": system_decision_gate.get("decision"),
        "system_program_effective_decision": system_final_gate.get("effective_decision"),
        "system_recency_status": system_recency.get("overall_status"),
        "monitoring_result": monitoring_result,
        "entry_result": entry_result,
    }


def main():
    args = parse_args()
    force_monitoring = args.force_monitoring or args.force_all
    force_entry = args.force_entry or args.force_all
    result = run_system_program_cycle(
        force_monitoring=force_monitoring,
        force_entry=force_entry,
    )
    if args.summary_only:
        summary = {
            "overall_program_state": result["overall_program_state"],
            "system_program_decision": result["system_program_decision"],
            "system_program_effective_decision": result["system_program_effective_decision"],
            "risk_engine_decision": result["risk_engine_decision"],
            "entry_lane_decision": result["entry_lane_decision"],
            "system_consistency_status": result["system_consistency_status"],
            "system_recency_status": result["system_recency_status"],
            "system_exec_md": result["system_exec_md"],
            "system_packet_md": result["system_packet_md"],
            "system_final_gate_md": result["system_final_gate_md"],
        }
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
