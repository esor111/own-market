"""
Build one plain executive-status sheet for the frozen-monitoring phase.

This is the shortest high-signal answer to:
- where we are now
- what is working
- what is still blocked
- what the next refresh must prove

Usage:
    python monitoring_executive_status.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
PACKET_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_packet_v1.json")
READINESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__system_reliability_readiness_scorecard_v1.json")
DRILLDOWN_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__priority_slice_drilldown_v1.json")
TRIGGER_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__next_refresh_trigger_sheet_v1.json")


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


def _format_months(rows):
    months = []
    for row in rows or []:
        month_key = row.get("month_key")
        if month_key:
            months.append(month_key)
    return months


def _format_symbols(rows):
    symbols = []
    for row in rows or []:
        symbol = row.get("symbol")
        if symbol:
            symbols.append(symbol)
    return symbols


def render_markdown(payload):
    lines = [
        "# Monitoring Executive Status",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- champion_state: `{payload['champion_state']}`",
        f"- refresh_needed: `{payload['refresh_needed']}`",
        f"- current_decision: `{payload['current_decision']}`",
        f"- overall_prediction_readiness: `{payload['overall_prediction_readiness']}`",
        f"- buy_side_readiness: `{payload['buy_side_readiness']}`",
        "",
        "## Rough Picture",
        "",
    ]
    for item in payload.get("rough_picture") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Current Best Truths",
        "",
    ])
    for item in payload.get("current_best_truths") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Main Blockers",
        "",
    ])
    for item in payload.get("main_blockers") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Priority Slices",
        "",
        f"- buy_side_focus: `{payload['buy_side_focus']}`",
        f"- buy_side_current_evidence: {payload['buy_side_current_evidence']}",
        f"- hostile_side_focus: `{payload['hostile_side_focus']}`",
        f"- hostile_side_current_evidence: {payload['hostile_side_current_evidence']}",
        "",
        "## Next Refresh Must Prove",
        "",
    ])
    for item in payload.get("next_refresh_must_prove") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## What To Do Now",
        "",
    ])
    for item in payload.get("what_to_do_now") or []:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def build_executive_status():
    packet = load_json(PACKET_PATH)
    readiness = load_json(READINESS_PATH)
    drilldown = load_json(DRILLDOWN_PATH)
    trigger = load_json(TRIGGER_PATH)

    sections = readiness.get("sections") or {}
    buy_focus = drilldown.get("primary_buy_focus") or {}
    hostile_focus = drilldown.get("secondary_hostile_focus") or {}

    buy_symbols = _format_symbols(buy_focus.get("symbol_rows"))
    hostile_symbols = _format_symbols(hostile_focus.get("symbol_rows"))
    hostile_months = _format_months(hostile_focus.get("month_rows"))

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "champion_state": "frozen",
        "refresh_needed": packet.get("refresh_needed"),
        "current_decision": packet.get("current_decision"),
        "overall_prediction_readiness": packet.get("overall_prediction_readiness"),
        "buy_side_readiness": packet.get("buy_side_readiness"),
        "rough_picture": [
            "the process is stable and the champion is frozen",
            "the caution side is the strongest part of the system right now",
            "the main remaining trust gap is still the buy side",
            "the current state says keep_frozen until genuinely newer replay data appears",
        ],
        "current_best_truths": [
            f"monitoring discipline: {sections.get('monitoring_discipline', {}).get('status', 'unknown')}",
            f"caution engine: {sections.get('caution_engine', {}).get('status', 'unknown')}",
            f"actionable side: {sections.get('actionable_side', {}).get('status', 'unknown')}",
            f"strict buy side: {sections.get('strict_buy_side', {}).get('status', 'unknown')}",
        ],
        "main_blockers": readiness.get("main_blockers") or [],
        "buy_side_focus": buy_focus.get("slice"),
        "buy_side_current_evidence": (
            f"{buy_focus.get('realistic_success_count')} realistic successes vs "
            f"{buy_focus.get('realistic_failure_count')} realistic failures; "
            f"current success rate {buy_focus.get('realistic_success_rate')}; "
            f"symbol split still concentrated in {buy_symbols}"
        ),
        "hostile_side_focus": hostile_focus.get("slice"),
        "hostile_side_current_evidence": (
            f"{hostile_focus.get('failure_count')} failures from {hostile_focus.get('case_count')} cases; "
            f"current failure rate {hostile_focus.get('failure_rate')}; "
            f"spread is currently across {hostile_symbols} in months {hostile_months}"
        ),
        "next_refresh_must_prove": [],
        "what_to_do_now": packet.get("current_action") or [],
    }

    for item in (trigger.get("primary_buy_focus") or {}).get("next_refresh_must_prove") or []:
        payload["next_refresh_must_prove"].append(f"buy side: {item}")

    for item in (trigger.get("secondary_hostile_focus") or {}).get("next_refresh_must_prove") or []:
        payload["next_refresh_must_prove"].append(f"hostile side: {item}")

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_executive_status_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_executive_status_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_executive_status_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_executive_status_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_executive_status()
    print(json.dumps({
        "refresh_needed": payload["refresh_needed"],
        "current_decision": payload["current_decision"],
        "overall_prediction_readiness": payload["overall_prediction_readiness"],
        "buy_side_readiness": payload["buy_side_readiness"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
