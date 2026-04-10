"""
Build an explicit trigger sheet for the next monitoring refresh.

This turns the current focus pack + drilldown + readiness state into:
- what exactly needs to improve
- what still blocks research
- what would count as meaningful change next cycle

Usage:
    python next_refresh_trigger_sheet.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR
from monitoring_decision_gate import (
    BUY_POSITIVE_EMERGENT_SUCCESS_COUNT_MIN,
    BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN,
    HOSTILE_EMERGENT_FAILURE_COUNT_MIN,
    HOSTILE_EMERGENT_FAILURE_RATE_MIN,
)


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
FOCUS_PACK_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__priority_slice_focus_pack_v1.json")
DRILLDOWN_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__priority_slice_drilldown_v1.json")
READINESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__system_reliability_readiness_scorecard_v1.json")
CYCLE_SUMMARY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_summary_v1.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _top_symbol(symbol_rows, key):
    if not symbol_rows:
        return None
    return max(symbol_rows, key=lambda item: (item.get(key) or 0, item.get("count") or 0, item.get("symbol") or ""))


def _buy_trigger_text(primary_focus, buy_drilldown):
    success_count = primary_focus.get("success_count") or 0
    failure_count = primary_focus.get("failure_count") or 0
    total_count = success_count + failure_count
    next_clean_rate = round((success_count + 1) / (total_count + 1), 4) if total_count >= 0 else None

    best_symbol = _top_symbol(buy_drilldown.get("symbol_rows") or [], "success_count")
    worst_symbol = _top_symbol(buy_drilldown.get("symbol_rows") or [], "failure_count")

    blockers = []
    blockers.append(
        f"needs success_rate >= {BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN} while staying at or above success_count gate {BUY_POSITIVE_EMERGENT_SUCCESS_COUNT_MIN}"
    )
    if next_clean_rate is not None:
        blockers.append(
            f"one clean success with zero new failures would move the slice to success_rate {next_clean_rate}"
        )
    if best_symbol and worst_symbol and best_symbol.get("symbol") != worst_symbol.get("symbol"):
        blockers.append(
            f"quality is still split: {best_symbol['symbol']} is carrying successes while {worst_symbol['symbol']} is carrying failures"
        )
    blockers.append("a new success is more trustworthy if it comes from the weaker symbol or a new bank, not only the current strong symbol")
    return blockers


def _hostile_trigger_text(hostile_focus, hostile_drilldown):
    symbol_rows = hostile_drilldown.get("symbol_rows") or []
    month_rows = hostile_drilldown.get("month_rows") or []
    current_symbols = [row.get("symbol") for row in symbol_rows if row.get("symbol")]
    current_months = [row.get("month_key") for row in month_rows if row.get("month_key")]

    blockers = [
        f"basic hostile gate is already exceeded (failure_count >= {HOSTILE_EMERGENT_FAILURE_COUNT_MIN} and failure_rate >= {HOSTILE_EMERGENT_FAILURE_RATE_MIN})",
        "reopen hostile research only if the next refresh adds new spread or a clearer sub-texture",
    ]
    if current_symbols:
        blockers.append(f"watch whether the slice expands beyond current symbols: {current_symbols}")
    if current_months:
        blockers.append(f"watch whether the slice repeats outside current hostile months: {current_months}")
    blockers.append("if failure rate stays near 1.0 and the slice spreads, that is stronger evidence than just repeating the same pocket")
    return blockers


def render_markdown(payload):
    lines = [
        "# Next Refresh Trigger Sheet",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- current_decision: `{payload['current_decision']}`",
        "",
        "## Primary Buy-Side Trigger",
        "",
        f"- slice: `{payload['primary_buy_focus']['slice']}`",
        f"- current_success_count: `{payload['primary_buy_focus']['success_count']}`",
        f"- current_failure_count: `{payload['primary_buy_focus']['failure_count']}`",
        f"- current_success_rate: `{payload['primary_buy_focus']['success_rate']}`",
        f"- quality_status: `{payload['primary_buy_focus']['quality_status']}`",
        "",
        "What next refresh must prove:",
        "",
    ]
    for item in payload["primary_buy_focus"]["next_refresh_must_prove"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Secondary Hostile-Side Trigger",
        "",
        f"- slice: `{payload['secondary_hostile_focus']['slice']}`",
        f"- current_failure_count: `{payload['secondary_hostile_focus']['failure_count']}`",
        f"- current_failure_rate: `{payload['secondary_hostile_focus']['failure_rate']}`",
        "",
        "What next refresh must prove:",
        "",
    ])
    for item in payload["secondary_hostile_focus"]["next_refresh_must_prove"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Readiness Context",
        "",
        f"- overall_prediction_readiness: `{payload['readiness']['overall_prediction_readiness']}`",
        f"- buy_side_readiness: `{payload['readiness']['buy_side_readiness']}`",
        "",
        "Main blockers still open:",
        "",
    ])
    for item in payload["readiness"]["main_blockers"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Current Decision",
        "",
        "- champion stays frozen",
        "- do not open research just because a slice gets larger",
        "- open research only if the next refresh improves slice quality in the way described above",
    ])
    return "\n".join(lines) + "\n"


def build_trigger_sheet():
    focus_pack = load_json(FOCUS_PACK_PATH)
    drilldown = load_json(DRILLDOWN_PATH)
    readiness = load_json(READINESS_PATH)
    cycle_summary = load_json(CYCLE_SUMMARY_PATH)

    primary_focus = focus_pack.get("primary_buy_focus") or {}
    primary_drilldown = drilldown.get("primary_buy_focus") or {}
    hostile_focus = focus_pack.get("secondary_hostile_focus") or {}
    hostile_drilldown = drilldown.get("secondary_hostile_focus") or {}

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "current_decision": cycle_summary.get("decision"),
        "primary_buy_focus": {
            "slice": primary_focus.get("slice"),
            "success_count": primary_focus.get("success_count"),
            "failure_count": primary_focus.get("failure_count"),
            "success_rate": primary_focus.get("success_rate"),
            "quality_status": primary_focus.get("quality_status"),
            "next_refresh_must_prove": _buy_trigger_text(primary_focus, primary_drilldown),
        },
        "secondary_hostile_focus": {
            "slice": hostile_focus.get("slice"),
            "failure_count": hostile_focus.get("failure_count"),
            "failure_rate": hostile_focus.get("failure_rate"),
            "next_refresh_must_prove": _hostile_trigger_text(hostile_focus, hostile_drilldown),
        },
        "readiness": {
            "overall_prediction_readiness": readiness.get("overall_prediction_readiness"),
            "buy_side_readiness": readiness.get("buy_side_readiness"),
            "main_blockers": [
                "actionable good_call_rate is still below the provisional 0.40 trust target",
                "actionable next-open survival is still below the provisional 0.50 trust target",
                "strict buy side still has too little clean sample and too little observed success",
            ],
        },
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__next_refresh_trigger_sheet_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__next_refresh_trigger_sheet_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__next_refresh_trigger_sheet_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__next_refresh_trigger_sheet_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_trigger_sheet()
    print(json.dumps({
        "current_decision": payload["current_decision"],
        "primary_buy_focus": payload["primary_buy_focus"]["slice"],
        "secondary_hostile_focus": payload["secondary_hostile_focus"]["slice"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
