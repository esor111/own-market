"""
Run the monitoring cycle safely.

This is the operational entrypoint for the frozen-monitoring phase:
- check freshness first
- run heavy core only when needed
- run tail only when appropriate
- always rebuild the top-level operating state

Usage:
    python run_monitoring_cycle.py
    python run_monitoring_cycle.py --force-core
"""
import argparse
import json

from monitoring_artifact_consistency_check import build_check
from monitoring_candidate_replay_gap_report import build_gap_report
from monitoring_cycle_packet import build_packet
from monitoring_executive_status import build_executive_status
from monitoring_gap_triage import build_gap_triage
from monitoring_operating_state import build_operating_state
from monitoring_replay_coverage_ledger import build_coverage_ledger
from monitoring_refresh_freshness_gate import build_freshness_gate
from refresh_monitoring_stack import _default_hostile_replay_ids, refresh_monitoring_stack
from aggregate_buy_side_pattern_monitor import DEFAULT_REPLAY_IDS as DEFAULT_BUY_REPLAY_IDS
from system_program_status import build_system_program_status
from system_program_status_consistency_check import build_system_program_status_consistency_check


def _maybe_build_system_consistency():
    try:
        return build_system_program_status_consistency_check()
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None, None


def parse_args():
    parser = argparse.ArgumentParser(description="Run the monitoring cycle safely with freshness awareness.")
    parser.add_argument(
        "--force-core",
        action="store_true",
        help="Run the heavy core refresh even if the freshness gate says it is not needed.",
    )
    return parser.parse_args()


def run_cycle(force_core=False):
    freshness, freshness_json_path, freshness_md_path = build_freshness_gate()
    refresh_needed = bool(freshness.get("refresh_needed")) or force_core

    core_result = None
    tail_result = None

    if refresh_needed:
        hostile_replay_ids = _default_hostile_replay_ids()
        if not hostile_replay_ids:
            raise SystemExit(
                "No hostile replay ids available. Build the hostile monitor once or pass ids through refresh_monitoring_stack.py."
            )
        core_result = refresh_monitoring_stack(
            hostile_replay_ids,
            list(DEFAULT_BUY_REPLAY_IDS),
            stage="core",
        )
        tail_result = refresh_monitoring_stack(
            hostile_replay_ids,
            list(DEFAULT_BUY_REPLAY_IDS),
            stage="tail",
        )

    operating_state, operating_state_json_path, operating_state_md_path = build_operating_state()
    coverage_ledger, coverage_json_path, coverage_md_path = build_coverage_ledger()
    gap_report, gap_report_json_path, gap_report_md_path = build_gap_report()
    gap_triage, gap_triage_json_path, gap_triage_md_path = build_gap_triage()
    consistency, consistency_json_path, consistency_md_path = build_check()
    packet, packet_json_path, packet_md_path = build_packet()
    executive_status, executive_status_json_path, executive_status_md_path = build_executive_status()
    system_status, system_status_json_path, system_status_md_path = build_system_program_status()
    system_consistency, system_consistency_json_path, system_consistency_md_path = _maybe_build_system_consistency()

    return {
        "refresh_needed": freshness.get("refresh_needed"),
        "force_core": force_core,
        "core_executed": refresh_needed,
        "tail_executed": refresh_needed,
        "current_decision": operating_state.get("current_decision"),
        "overall_prediction_readiness": operating_state.get("overall_prediction_readiness"),
        "buy_side_readiness": operating_state.get("buy_side_readiness"),
        "freshness_json": freshness_json_path,
        "freshness_md": freshness_md_path,
        "core_result": core_result,
        "tail_result": tail_result,
        "operating_state_json": operating_state_json_path,
        "operating_state_md": operating_state_md_path,
        "coverage_ledger_json": coverage_json_path,
        "coverage_ledger_md": coverage_md_path,
        "combined_monitored_month_count": coverage_ledger.get("combined_month_count"),
        "gap_report_json": gap_report_json_path,
        "gap_report_md": gap_report_md_path,
        "candidate_replay_gap_count": len(gap_report.get("gap_rows") or []),
        "gap_triage_json": gap_triage_json_path,
        "gap_triage_md": gap_triage_md_path,
        "candidate_replay_include_now_count": gap_triage.get("include_now_count"),
        "candidate_replay_rerun_backlog_count": gap_triage.get("rerun_backlog_count"),
        "packet_json": packet_json_path,
        "packet_md": packet_md_path,
        "packet_decision": packet.get("current_decision"),
        "consistency_status": consistency.get("overall_status"),
        "consistency_json": consistency_json_path,
        "consistency_md": consistency_md_path,
        "executive_status_json": executive_status_json_path,
        "executive_status_md": executive_status_md_path,
        "executive_status_decision": executive_status.get("current_decision"),
        "system_status_json": system_status_json_path,
        "system_status_md": system_status_md_path,
        "overall_program_state": system_status.get("overall_program_state"),
        "system_consistency_json": system_consistency_json_path,
        "system_consistency_md": system_consistency_md_path,
        "system_consistency_status": (system_consistency or {}).get("overall_status", "unknown"),
    }


def main():
    args = parse_args()
    result = run_cycle(force_core=args.force_core)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
