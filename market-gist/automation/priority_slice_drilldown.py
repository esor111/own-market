"""
Build a concrete drilldown for the current top-priority buy-side and hostile slices.

This is the next layer after the focus pack. It answers:
- which symbols are carrying the slice
- which months are improving or degrading
- what the recent case texture actually looks like

Usage:
    python priority_slice_drilldown.py
"""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

from aggregate_buy_side_pattern_monitor import DEFAULT_TICKET_NOTIONAL_NPR
from aggregate_hostile_window_monitor import HOSTILE_PHASES
from config import REPLAYS_DIR, VALIDATION_DIR
from entry_label_taxonomy import executable_entry_label, next_open_label as legacy_next_open_label
from replay_confidence_remap import lookup_replay_calibrated_confidence
from replay_cost_realism_study import _simulate_case, collect_actionable_records


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
BRANCH_PRIORITY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__branch_priority_queue_v1.json")
BUY_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_buy_side_pattern_monitor_v1.json")
HOSTILE_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_hostile_window_monitor_v1.json")


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


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _event_state(frozen_case):
    corporate_context = ((frozen_case.get("historical_context") or {}).get("corporate_action_context") or {})
    if corporate_context.get("has_active_event"):
        return "active_event"
    if int(corporate_context.get("recent_event_count_90d") or 0) > 0:
        return "recent_event_no_active"
    if int(corporate_context.get("matched_event_count") or 0) > 0:
        return "matched_but_stale"
    return "no_symbol_event_match"


def _buy_bucket_key(row):
    return " | ".join([
        row.get("sector_name") or "UNKNOWN",
        row.get("calendar_phase") or "no_named_phase",
        row.get("event_state") or "unknown",
        row.get("confidence_label") or "unknown",
        row.get("action") or "unknown",
    ])


def _hostile_bucket_key(record):
    return " | ".join([
        f"sector={record.get('sector_name') or 'UNKNOWN'}",
        f"event={record.get('event_state') or 'unknown'}",
        f"confidence={record.get('confidence_interpretation_label') or 'unknown'}",
        f"action={record.get('action') or 'unknown'}",
    ])


def _load_frozen_case(record):
    frozen_case_path = record["decision_path"].replace(
        f"{os.sep}derived{os.sep}",
        f"{os.sep}normalized{os.sep}",
    ).replace("__replay_decision_v1.json", "__frozen_case_v1.json")
    return load_json(frozen_case_path)


def _collect_buy_slice_rows(slice_name, replay_ids):
    rows = []
    for record in collect_actionable_records(replay_ids):
        frozen_case = _load_frozen_case(record)
        confidence_view = lookup_replay_calibrated_confidence(record["action"], record["confidence"])
        row = {
            "replay_id": record["replay_id"],
            "month_key": str(record["session_date"])[:7],
            "session_date": record["session_date"],
            "symbol": record["symbol"],
            "sector_name": record["sector_name"],
            "calendar_phase": record["calendar_phase"],
            "event_state": _event_state(frozen_case),
            "action": record["action"],
            "comparison_verdict": record["comparison_verdict"],
            "confidence_label": confidence_view.get("confidence_interpretation_label"),
            "raw_confidence": record["confidence"],
            "calibrated_confidence_pct": confidence_view.get("calibrated_confidence_pct"),
            "risk_reward_ratio": record["risk_reward_ratio"],
        }
        if _buy_bucket_key(row) != slice_name:
            continue

        simulation = _simulate_case(record["decision"], record["future_bars"], DEFAULT_TICKET_NOTIONAL_NPR)
        next_open_label = legacy_next_open_label(simulation)
        executable_label = executable_entry_label(simulation)
        realistic_success = (
            record["comparison_verdict"] == "good_call"
            and executable_label == "tradable_positive_after_costs"
        )
        row.update({
            "next_open_label": next_open_label,
            "executable_entry_label": executable_label,
            "net_return_pct": simulation.get("net_return_pct"),
            "realistic_success": realistic_success,
            "realistic_failure": not realistic_success,
        })
        rows.append(row)

    rows.sort(key=lambda item: (item["session_date"], item["symbol"]))
    return rows


def _load_replay_summary(replay_id):
    summary_path = os.path.join(REPLAYS_DIR, replay_id, "summaries", "latest__replay_summary_v1.json")
    return load_json(summary_path)


def _collect_hostile_slice_rows(slice_name, replay_ids):
    rows = []
    for replay_id in replay_ids:
        summary = _load_replay_summary(replay_id)
        for record in summary.get("records") or []:
            if (record.get("calendar_phase") or "") not in HOSTILE_PHASES:
                continue
            if _hostile_bucket_key(record) != slice_name:
                continue
            verdict = record.get("comparison_verdict")
            rows.append({
                "replay_id": replay_id,
                "month_key": str(record.get("session_date") or "")[:7],
                "session_date": record.get("session_date"),
                "symbol": record.get("symbol"),
                "sector_name": record.get("sector_name"),
                "action": record.get("action"),
                "comparison_verdict": verdict,
                "is_failure": verdict in {"bad_call", "mixed_call"},
                "is_good_avoid": verdict == "good_avoid",
                "triggered": bool(
                    record.get("calendar_confidence_guidance_action_change")
                    or record.get("bank_exhaustion_guidance_action_change")
                    or record.get("commercial_bank_watch_caution_guidance_action_change")
                    or record.get("commercial_bank_overconfident_watch_caution_guidance_action_change")
                    or record.get("hydropower_buy_caution_guidance_action_change")
                ),
            })
    rows.sort(key=lambda item: (item["session_date"], item["symbol"]))
    return rows


def _group_buy_symbols(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["symbol"]].append(row)
    output = []
    for symbol, items in grouped.items():
        success_count = sum(1 for item in items if item["realistic_success"])
        output.append({
            "symbol": symbol,
            "count": len(items),
            "success_count": success_count,
            "failure_count": len(items) - success_count,
            "success_rate": _rate(success_count, len(items)),
            "months": Counter(item["month_key"] for item in items).most_common(6),
            "next_open_labels": Counter(item["next_open_label"] for item in items),
            "executable_entry_labels": Counter(item["executable_entry_label"] for item in items),
        })
    output.sort(key=lambda item: (-(item["success_count"]), item["failure_count"], -item["count"], item["symbol"]))
    return output


def _group_buy_months(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["month_key"]].append(row)
    output = []
    for month_key, items in sorted(grouped.items()):
        success_count = sum(1 for item in items if item["realistic_success"])
        output.append({
            "month_key": month_key,
            "count": len(items),
            "success_count": success_count,
            "failure_count": len(items) - success_count,
            "success_rate": _rate(success_count, len(items)),
            "symbols": Counter(item["symbol"] for item in items).most_common(6),
            "next_open_labels": Counter(item["next_open_label"] for item in items),
            "executable_entry_labels": Counter(item["executable_entry_label"] for item in items),
        })
    return output


def _group_hostile_symbols(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["symbol"]].append(row)
    output = []
    for symbol, items in grouped.items():
        failure_count = sum(1 for item in items if item["is_failure"])
        good_avoid_count = sum(1 for item in items if item["is_good_avoid"])
        output.append({
            "symbol": symbol,
            "count": len(items),
            "failure_count": failure_count,
            "failure_rate": _rate(failure_count, len(items)),
            "good_avoid_count": good_avoid_count,
            "triggered_count": sum(1 for item in items if item["triggered"]),
            "months": Counter(item["month_key"] for item in items).most_common(6),
            "verdicts": Counter(item["comparison_verdict"] for item in items),
        })
    output.sort(key=lambda item: (-(item["failure_count"]), -(item["count"]), item["symbol"]))
    return output


def _group_hostile_months(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["month_key"]].append(row)
    output = []
    for month_key, items in sorted(grouped.items()):
        failure_count = sum(1 for item in items if item["is_failure"])
        output.append({
            "month_key": month_key,
            "count": len(items),
            "failure_count": failure_count,
            "failure_rate": _rate(failure_count, len(items)),
            "good_avoid_count": sum(1 for item in items if item["is_good_avoid"]),
            "triggered_count": sum(1 for item in items if item["triggered"]),
            "symbols": Counter(item["symbol"] for item in items).most_common(6),
            "verdicts": Counter(item["comparison_verdict"] for item in items),
        })
    return output


def _recent_buy_cases(rows, limit=8):
    recent = sorted(rows, key=lambda item: (item["session_date"], item["symbol"]), reverse=True)[:limit]
    return [
        {
            "session_date": row["session_date"],
            "symbol": row["symbol"],
            "comparison_verdict": row["comparison_verdict"],
            "next_open_label": row["next_open_label"],
            "executable_entry_label": row["executable_entry_label"],
            "net_return_pct": row["net_return_pct"],
            "risk_reward_ratio": row["risk_reward_ratio"],
            "raw_confidence": row["raw_confidence"],
            "calibrated_confidence_pct": row["calibrated_confidence_pct"],
        }
        for row in recent
    ]


def _recent_hostile_cases(rows, limit=8):
    recent = sorted(rows, key=lambda item: (item["session_date"], item["symbol"]), reverse=True)[:limit]
    return [
        {
            "session_date": row["session_date"],
            "symbol": row["symbol"],
            "comparison_verdict": row["comparison_verdict"],
            "triggered": row["triggered"],
        }
        for row in recent
    ]


def render_markdown(payload):
    buy = payload["primary_buy_focus"]
    hostile = payload["secondary_hostile_focus"]
    lines = [
        "# Priority Slice Drilldown",
        "",
        f"- built_at: `{payload['built_at']}`",
        "",
        "## Primary Buy Focus",
        "",
        f"- slice: `{buy['slice']}`",
        f"- case_count: `{buy['case_count']}`",
        f"- realistic_success_count: `{buy['realistic_success_count']}`",
        f"- realistic_failure_count: `{buy['realistic_failure_count']}`",
        f"- realistic_success_rate: `{buy['realistic_success_rate']}`",
        "",
        "### By Symbol",
        "",
    ]
    for row in buy["symbol_rows"]:
        lines.append(
            f"- `{row['symbol']}`: count `{row['count']}`, success `{row['success_count']}`, "
            f"failure `{row['failure_count']}`, success_rate `{row['success_rate']}`, "
            f"months `{row['months']}`, next_open_labels `{dict(row['next_open_labels'])}`, "
            f"executable_entry_labels `{dict(row['executable_entry_labels'])}`"
        )

    lines.extend(["", "### By Month", ""])
    for row in buy["month_rows"]:
        lines.append(
            f"- `{row['month_key']}`: count `{row['count']}`, success `{row['success_count']}`, "
            f"failure `{row['failure_count']}`, success_rate `{row['success_rate']}`, "
            f"symbols `{row['symbols']}`, next_open_labels `{dict(row['next_open_labels'])}`, "
            f"executable_entry_labels `{dict(row['executable_entry_labels'])}`"
        )

    lines.extend(["", "### Recent Cases", ""])
    for row in buy["recent_cases"]:
        lines.append(
            f"- `{row['session_date']} {row['symbol']}`: verdict `{row['comparison_verdict']}`, "
            f"next_open `{row['next_open_label']}`, executable `{row['executable_entry_label']}`, net_return_pct `{row['net_return_pct']}`, "
            f"rr `{row['risk_reward_ratio']}`, raw_conf `{row['raw_confidence']}`, "
            f"calibrated `{row['calibrated_confidence_pct']}`"
        )

    lines.extend([
        "",
        "## Secondary Hostile Focus",
        "",
        f"- slice: `{hostile['slice']}`",
        f"- case_count: `{hostile['case_count']}`",
        f"- failure_count: `{hostile['failure_count']}`",
        f"- failure_rate: `{hostile['failure_rate']}`",
        f"- good_avoid_count: `{hostile['good_avoid_count']}`",
        "",
        "### By Symbol",
        "",
    ])
    for row in hostile["symbol_rows"]:
        lines.append(
            f"- `{row['symbol']}`: count `{row['count']}`, failure `{row['failure_count']}`, "
            f"failure_rate `{row['failure_rate']}`, good_avoid `{row['good_avoid_count']}`, "
            f"triggered `{row['triggered_count']}`, months `{row['months']}`, verdicts `{dict(row['verdicts'])}`"
        )

    lines.extend(["", "### By Month", ""])
    for row in hostile["month_rows"]:
        lines.append(
            f"- `{row['month_key']}`: count `{row['count']}`, failure `{row['failure_count']}`, "
            f"failure_rate `{row['failure_rate']}`, good_avoid `{row['good_avoid_count']}`, "
            f"triggered `{row['triggered_count']}`, symbols `{row['symbols']}`, verdicts `{dict(row['verdicts'])}`"
        )

    lines.extend(["", "### Recent Cases", ""])
    for row in hostile["recent_cases"]:
        lines.append(
            f"- `{row['session_date']} {row['symbol']}`: verdict `{row['comparison_verdict']}`, triggered `{row['triggered']}`"
        )

    lines.extend([
        "",
        "## Current Use",
        "",
        "- use this after the cycle summary and focus pack",
        "- if the primary buy slice gets cleaner by symbol and month, it may earn research",
        "- if the hostile slice spreads or hardens further, it may earn a narrower hostile study",
    ])
    return "\n".join(lines) + "\n"


def build_drilldown():
    branch_priority = load_json(BRANCH_PRIORITY_PATH)
    buy_monitor = load_json(BUY_MONITOR_PATH)
    hostile_monitor = load_json(HOSTILE_MONITOR_PATH)

    primary_buy_slice = ((branch_priority.get("primary_buy_focus") or {}).get("slice"))
    secondary_hostile_slice = ((branch_priority.get("secondary_hostile_focus") or {}).get("slice"))

    buy_rows = _collect_buy_slice_rows(primary_buy_slice, buy_monitor.get("replay_ids") or [])
    hostile_rows = _collect_hostile_slice_rows(secondary_hostile_slice, hostile_monitor.get("replay_ids") or [])

    buy_success_count = sum(1 for row in buy_rows if row["realistic_success"])
    hostile_failure_count = sum(1 for row in hostile_rows if row["is_failure"])
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "primary_buy_focus": {
            "slice": primary_buy_slice,
            "case_count": len(buy_rows),
            "realistic_success_count": buy_success_count,
            "realistic_failure_count": len(buy_rows) - buy_success_count,
            "realistic_success_rate": _rate(buy_success_count, len(buy_rows)),
            "symbol_rows": _group_buy_symbols(buy_rows),
            "month_rows": _group_buy_months(buy_rows),
            "recent_cases": _recent_buy_cases(buy_rows),
        },
        "secondary_hostile_focus": {
            "slice": secondary_hostile_slice,
            "case_count": len(hostile_rows),
            "failure_count": hostile_failure_count,
            "failure_rate": _rate(hostile_failure_count, len(hostile_rows)),
            "good_avoid_count": sum(1 for row in hostile_rows if row["is_good_avoid"]),
            "symbol_rows": _group_hostile_symbols(hostile_rows),
            "month_rows": _group_hostile_months(hostile_rows),
            "recent_cases": _recent_hostile_cases(hostile_rows),
        },
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__priority_slice_drilldown_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__priority_slice_drilldown_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__priority_slice_drilldown_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__priority_slice_drilldown_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_drilldown()
    print(json.dumps({
        "primary_buy_focus": payload["primary_buy_focus"]["slice"],
        "primary_buy_case_count": payload["primary_buy_focus"]["case_count"],
        "secondary_hostile_focus": payload["secondary_hostile_focus"]["slice"],
        "secondary_hostile_case_count": payload["secondary_hostile_focus"]["case_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
