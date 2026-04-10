"""
Refresh the replay monitoring stack in the correct order.

This is the operational wrapper for the frozen-monitoring phase:
1. hostile monitor
2. hostile watchlist
3. buy-side monitor
4. buy-side watchlist
5. combined checkpoint
6. baseline diff

Usage:
    python refresh_monitoring_stack.py
    python refresh_monitoring_stack.py --stage core
    python refresh_monitoring_stack.py --stage tail
    python refresh_monitoring_stack.py --hostile-replay-id REPLAY_ID [--hostile-replay-id REPLAY_ID ...]
    python refresh_monitoring_stack.py --buy-replay-id REPLAY_ID [--buy-replay-id REPLAY_ID ...]
"""
import argparse
import json
import os

from aggregate_buy_side_pattern_monitor import DEFAULT_REPLAY_IDS as DEFAULT_BUY_REPLAY_IDS
from aggregate_buy_side_pattern_monitor import build_buy_side_pattern_monitor
from aggregate_hostile_window_monitor import build_hostile_window_monitor
from branch_priority_queue import build_queue as build_branch_priority_queue
from config import VALIDATION_DIR
from derive_buy_side_watchlist import build_watchlist as build_buy_watchlist
from derive_hostile_watchlist import build_watchlist as build_hostile_watchlist
from monitoring_cycle_summary import build_summary
from monitoring_decision_gate import build_decision
from monitor_watchlist_diff import build_diff
from monitoring_watchlist_checkpoint import build_checkpoint
from next_refresh_trigger_sheet import build_trigger_sheet
from priority_slice_focus_pack import build_focus_pack
from priority_slice_drilldown import build_drilldown
from system_reliability_readiness_scorecard import build_scorecard


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
HOSTILE_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_hostile_window_monitor_v1.json")


def _default_hostile_replay_ids():
    if os.path.exists(HOSTILE_MONITOR_PATH):
        with open(HOSTILE_MONITOR_PATH, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        replay_ids = payload.get("replay_ids") or []
        if replay_ids:
            return replay_ids
    return []


def parse_args():
    parser = argparse.ArgumentParser(description="Refresh the replay monitoring stack in the correct order.")
    parser.add_argument(
        "--stage",
        choices=("all", "core", "tail"),
        default="all",
        help="Refresh the full stack, only the heavy monitor core, or only the fast decision tail.",
    )
    parser.add_argument(
        "--hostile-replay-id",
        action="append",
        dest="hostile_replay_ids",
        help="Replay id to include in the hostile-window monitor refresh. Repeat for multiple ids.",
    )
    parser.add_argument(
        "--buy-replay-id",
        action="append",
        dest="buy_replay_ids",
        help="Replay id to include in the buy-side monitor refresh. Repeat for multiple ids.",
    )
    return parser.parse_args()


def _refresh_core(hostile_replay_ids, buy_replay_ids):
    hostile_summary, hostile_json_path, hostile_md_path = build_hostile_window_monitor(hostile_replay_ids)
    hostile_watchlist, hostile_watch_json_path, hostile_watch_md_path = build_hostile_watchlist()
    buy_summary, buy_json_path, buy_md_path = build_buy_side_pattern_monitor(buy_replay_ids)
    buy_watchlist, buy_watch_json_path, buy_watch_md_path = build_buy_watchlist()
    checkpoint, checkpoint_json_path, checkpoint_md_path = build_checkpoint()
    diff, diff_json_path, diff_md_path = build_diff()
    decision, decision_json_path, decision_md_path = build_decision()
    cycle_summary, cycle_summary_json_path, cycle_summary_md_path = build_summary()

    return {
        "hostile_summary": hostile_summary,
        "hostile_json_path": hostile_json_path,
        "hostile_md_path": hostile_md_path,
        "hostile_watchlist": hostile_watchlist,
        "hostile_watch_json_path": hostile_watch_json_path,
        "hostile_watch_md_path": hostile_watch_md_path,
        "buy_summary": buy_summary,
        "buy_json_path": buy_json_path,
        "buy_md_path": buy_md_path,
        "buy_watchlist": buy_watchlist,
        "buy_watch_json_path": buy_watch_json_path,
        "buy_watch_md_path": buy_watch_md_path,
        "checkpoint": checkpoint,
        "checkpoint_json_path": checkpoint_json_path,
        "checkpoint_md_path": checkpoint_md_path,
        "diff": diff,
        "diff_json_path": diff_json_path,
        "diff_md_path": diff_md_path,
        "decision": decision,
        "decision_json_path": decision_json_path,
        "decision_md_path": decision_md_path,
        "cycle_summary": cycle_summary,
        "cycle_summary_json_path": cycle_summary_json_path,
        "cycle_summary_md_path": cycle_summary_md_path,
    }


def _refresh_tail():
    branch_priority_queue, branch_priority_json_path, branch_priority_md_path = build_branch_priority_queue()
    focus_pack, focus_pack_json_path, focus_pack_md_path = build_focus_pack()
    drilldown, drilldown_json_path, drilldown_md_path = build_drilldown()
    trigger_sheet, trigger_sheet_json_path, trigger_sheet_md_path = build_trigger_sheet()
    readiness_scorecard, readiness_json_path, readiness_md_path = build_scorecard()

    return {
        "branch_priority_queue": branch_priority_queue,
        "branch_priority_json_path": branch_priority_json_path,
        "branch_priority_md_path": branch_priority_md_path,
        "focus_pack": focus_pack,
        "focus_pack_json_path": focus_pack_json_path,
        "focus_pack_md_path": focus_pack_md_path,
        "drilldown": drilldown,
        "drilldown_json_path": drilldown_json_path,
        "drilldown_md_path": drilldown_md_path,
        "trigger_sheet": trigger_sheet,
        "trigger_sheet_json_path": trigger_sheet_json_path,
        "trigger_sheet_md_path": trigger_sheet_md_path,
        "readiness_scorecard": readiness_scorecard,
        "readiness_json_path": readiness_json_path,
        "readiness_md_path": readiness_md_path,
    }


def refresh_monitoring_stack(hostile_replay_ids, buy_replay_ids, stage="all"):
    core = {}
    tail = {}
    if stage in {"all", "core"}:
        core = _refresh_core(hostile_replay_ids, buy_replay_ids)
    if stage in {"all", "tail"}:
        tail = _refresh_tail()

    return {
        "stage": stage,
        "hostile_replay_count": len((core.get("hostile_summary") or {}).get("replay_ids") or []) if core else None,
        "buy_replay_count": len((core.get("buy_summary") or {}).get("replay_ids") or []) if core else None,
        "hostile_case_count": (core.get("hostile_summary") or {}).get("hostile_case_count") if core else None,
        "buy_actionable_count": (core.get("buy_summary") or {}).get("actionable_count") if core else None,
        "hostile_warning_watch_count": len((core.get("hostile_watchlist") or {}).get("warning_slices") or []) if core else None,
        "buy_positive_watch_count": len((core.get("buy_watchlist") or {}).get("positive_watch_slices") or []) if core else None,
        "buy_warning_watch_count": len((core.get("buy_watchlist") or {}).get("warning_watch_slices") or []) if core else None,
        "hostile_warning_worsened": ((core.get("diff") or {}).get("hostile") or {}).get("warning_summary", {}).get("worsened") if core else None,
        "buy_positive_worsened": ((core.get("diff") or {}).get("buy_side") or {}).get("positive_summary", {}).get("worsened") if core else None,
        "decision": (core.get("decision") or {}).get("decision") if core else None,
        "hostile_monitor_json": core.get("hostile_json_path"),
        "hostile_monitor_md": core.get("hostile_md_path"),
        "hostile_watchlist_json": core.get("hostile_watch_json_path"),
        "hostile_watchlist_md": core.get("hostile_watch_md_path"),
        "buy_monitor_json": core.get("buy_json_path"),
        "buy_monitor_md": core.get("buy_md_path"),
        "buy_watchlist_json": core.get("buy_watch_json_path"),
        "buy_watchlist_md": core.get("buy_watch_md_path"),
        "checkpoint_json": core.get("checkpoint_json_path"),
        "checkpoint_md": core.get("checkpoint_md_path"),
        "diff_json": core.get("diff_json_path"),
        "diff_md": core.get("diff_md_path"),
        "decision_json": core.get("decision_json_path"),
        "decision_md": core.get("decision_md_path"),
        "cycle_summary_decision": (core.get("cycle_summary") or {}).get("decision") if core else None,
        "cycle_summary_json": core.get("cycle_summary_json_path"),
        "cycle_summary_md": core.get("cycle_summary_md_path"),
        "primary_buy_focus": ((tail.get("branch_priority_queue") or {}).get("primary_buy_focus") or {}).get("slice") if tail else None,
        "secondary_hostile_focus": ((tail.get("branch_priority_queue") or {}).get("secondary_hostile_focus") or {}).get("slice") if tail else None,
        "branch_priority_json": tail.get("branch_priority_json_path"),
        "branch_priority_md": tail.get("branch_priority_md_path"),
        "focus_pack_json": tail.get("focus_pack_json_path"),
        "focus_pack_md": tail.get("focus_pack_md_path"),
        "drilldown_primary_buy_case_count": ((tail.get("drilldown") or {}).get("primary_buy_focus") or {}).get("case_count") if tail else None,
        "drilldown_secondary_hostile_case_count": ((tail.get("drilldown") or {}).get("secondary_hostile_focus") or {}).get("case_count") if tail else None,
        "drilldown_json": tail.get("drilldown_json_path"),
        "drilldown_md": tail.get("drilldown_md_path"),
        "trigger_sheet_decision": (tail.get("trigger_sheet") or {}).get("current_decision") if tail else None,
        "trigger_sheet_json": tail.get("trigger_sheet_json_path"),
        "trigger_sheet_md": tail.get("trigger_sheet_md_path"),
        "overall_prediction_readiness": (tail.get("readiness_scorecard") or {}).get("overall_prediction_readiness") if tail else None,
        "buy_side_readiness": (tail.get("readiness_scorecard") or {}).get("buy_side_readiness") if tail else None,
        "readiness_json": tail.get("readiness_json_path"),
        "readiness_md": tail.get("readiness_md_path"),
    }


def main():
    args = parse_args()
    hostile_replay_ids = args.hostile_replay_ids or _default_hostile_replay_ids()
    buy_replay_ids = args.buy_replay_ids or list(DEFAULT_BUY_REPLAY_IDS)

    if args.stage in {"all", "core"} and not hostile_replay_ids:
        raise SystemExit(
            "No hostile replay ids available. Pass --hostile-replay-id or build the hostile monitor once first."
        )

    result = refresh_monitoring_stack(hostile_replay_ids, buy_replay_ids, stage=args.stage)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
