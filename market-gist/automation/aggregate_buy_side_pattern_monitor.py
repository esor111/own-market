"""
Aggregate buy-side pattern monitoring across saved replay windows.

This is a research/monitoring layer for future buy-side branches. It does not
change any replay decision. It ranks repeated realistic winner slices and
repeated failure slices so new research opens only when a pattern truly repeats.

Usage:
    python aggregate_buy_side_pattern_monitor.py
    python aggregate_buy_side_pattern_monitor.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

from config import VALIDATION_DIR
from entry_label_taxonomy import executable_entry_label, next_open_label as legacy_next_open_label
from replay_confidence_remap import lookup_replay_calibrated_confidence
from replay_cost_realism_study import collect_actionable_records, _simulate_case


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DEFAULT_TICKET_NOTIONAL_NPR = 200_000.0
DEFAULT_REPLAY_IDS = [
    "2023-07-01_to_2023-07-31__replay_basket_v1__jul2023_currentchampion_v1",
    "2023-08-01_to_2023-08-31__replay_basket_v1__aug2023_currentchampion_v1",
    "2023-10-01_to_2023-10-31__replay_basket_v1__oct2023_postbankwatchpromotion_v1",
    "2023-11-01_to_2023-11-30__EBL__NABIL__SANIMA__JBBL__MNBBL__API__AKPL__UPPER__nov2023_currentchampion_v1",
    "2023-12-01_to_2023-12-31__EBL__NABIL__SANIMA__JBBL__MNBBL__API__AKPL__UPPER__dec2023_promoted_calendar_v1",
    "2024-07-01_to_2024-07-31__replay_basket_v1__jul2024_currentchampion_v1",
    "2024-08-01_to_2024-08-31__replay_basket_v1__aug2024_currentchampion_v1",
    "2024-09-01_to_2024-09-30__replay_basket_v1__daily_truth_replay_sep2024_promoted_calendar_v1",
    "2025-01-01_to_2025-01-31__replay_basket_v1__daily_truth_replay_v1",
    "2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_feb2025_champion_v1",
    "2025-03-01_to_2025-03-31__replay_basket_v1__daily_truth_replay_v1",
    "2025-04-01_to_2025-04-30__replay_basket_v1__daily_truth_replay_apr_liqslicechampion_v1",
    "2025-05-01_to_2025-05-31__replay_basket_v1__daily_truth_replay_may_champion_v1",
    "2025-06-01_to_2025-06-30__replay_basket_v1__daily_truth_replay_june_champion_v1",
    "2025-07-01_to_2025-07-31__replay_basket_v1__jul2025_currentchampion_v1",
    "2025-08-01_to_2025-08-31__replay_basket_v1__aug2025_currentchampion_v1",
    "2025-09-01_to_2025-09-30__replay_basket_v1__daily_truth_replay_september_promotedchampion_v1",
    "2025-10-01_to_2025-10-31__replay_basket_v1__oct2025_currentchampion_v1",
    "2025-11-01_to_2025-11-30__replay_basket_v1__nov2025_currentchampion_v1",
    "2025-12-01_to_2025-12-31__replay_basket_v1__dec2025_currentchampion_v1",
]


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


def _bucket_key(row):
    return " | ".join([
        row.get("sector_name") or "UNKNOWN",
        row.get("calendar_phase") or "no_named_phase",
        row.get("event_state") or "unknown",
        row.get("confidence_label") or "unknown",
        row.get("action") or "unknown",
    ])


def _collect_rows(replay_ids):
    rows = []
    for record in collect_actionable_records(replay_ids):
        decision = record["decision"]
        frozen_case_path = record["decision_path"].replace(f"{os.sep}derived{os.sep}", f"{os.sep}normalized{os.sep}").replace(
            "__replay_decision_v1.json", "__frozen_case_v1.json"
        )
        with open(frozen_case_path, "r", encoding="utf-8") as handle:
            frozen_case = json.load(handle)
        confidence_view = lookup_replay_calibrated_confidence(decision.get("action"), decision.get("confidence"))
        simulation = _simulate_case(decision, record["future_bars"], DEFAULT_TICKET_NOTIONAL_NPR)
        next_open_label = legacy_next_open_label(simulation)
        executable_label = executable_entry_label(simulation)
        realistic_success = (
            record["comparison_verdict"] == "good_call"
            and executable_label == "tradable_positive_after_costs"
        )
        rows.append({
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
            "score": record["score"],
            "risk_reward_ratio": record["risk_reward_ratio"],
            "next_open_label": next_open_label,
            "executable_entry_label": executable_label,
            "net_return_pct": simulation.get("net_return_pct"),
            "realistic_success": realistic_success,
            "realistic_failure": not realistic_success,
        })
    return rows


def _slice_rows(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[_bucket_key(row)].append(row)
    success_rows = []
    failure_rows = []
    for slice_name, items in grouped.items():
        success_count = sum(1 for item in items if item["realistic_success"])
        failure_count = len(items) - success_count
        row = {
            "slice": slice_name,
            "count": len(items),
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": _rate(success_count, len(items)),
            "symbols": Counter(item["symbol"] for item in items).most_common(5),
            "months": Counter(item["month_key"] for item in items).most_common(5),
        }
        if success_count:
            success_rows.append(row)
        if failure_count:
            failure_rows.append(row)
    success_rows.sort(key=lambda item: (item["success_count"], item["success_rate"] or 0, item["count"]), reverse=True)
    failure_rows.sort(key=lambda item: (item["failure_count"], item["success_rate"] is not None and -item["success_rate"] or 0, item["count"]), reverse=True)
    return success_rows, failure_rows


def _month_rows(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["month_key"]].append(row)
    month_rows = []
    for month_key, items in sorted(grouped.items()):
        success_count = sum(1 for item in items if item["realistic_success"])
        month_rows.append({
            "month_key": month_key,
            "count": len(items),
            "buy_count": sum(1 for item in items if item["action"] == "buy"),
            "watch_only_count": sum(1 for item in items if item["action"] == "watch_only"),
            "success_count": success_count,
            "failure_count": len(items) - success_count,
            "success_rate": _rate(success_count, len(items)),
            "sector_counts": dict(Counter(item["sector_name"] for item in items)),
        })
    return month_rows


def render_markdown(summary):
    lines = [
        "# Aggregate Buy-Side Pattern Monitor",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- replay_count: `{len(summary['replay_ids'])}`",
        f"- actionable_count: `{summary['actionable_count']}`",
        f"- realistic_success_count: `{summary['realistic_success_count']}`",
        f"- realistic_failure_count: `{summary['realistic_failure_count']}`",
        f"- realistic_success_rate: `{summary['realistic_success_rate']}`",
        f"- executable_entry_label_counts: `{summary['executable_entry_label_counts']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in summary.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")

    lines.extend(["", "## Month Rows", ""])
    for row in summary.get("month_rows", []):
        lines.append(
            f"- `{row['month_key']}`: count `{row['count']}`, buy `{row['buy_count']}`, watch_only `{row['watch_only_count']}`, "
            f"success `{row['success_count']}`, failure `{row['failure_count']}`, success_rate `{row['success_rate']}`, sectors `{row['sector_counts']}`"
        )

    lines.extend(["", "## Top Realistic Winner Slices", ""])
    for row in summary.get("top_success_slices", []):
        lines.append(
            f"- `{row['slice']}`: count `{row['count']}`, success_count `{row['success_count']}`, "
            f"failure_count `{row['failure_count']}`, success_rate `{row['success_rate']}`, "
            f"symbols `{row['symbols']}`, months `{row['months']}`"
        )

    lines.extend(["", "## Top Repeated Failure Slices", ""])
    for row in summary.get("top_failure_slices", []):
        lines.append(
            f"- `{row['slice']}`: count `{row['count']}`, success_count `{row['success_count']}`, "
            f"failure_count `{row['failure_count']}`, success_rate `{row['success_rate']}`, "
            f"symbols `{row['symbols']}`, months `{row['months']}`"
        )

    return "\n".join(lines) + "\n"


def build_buy_side_pattern_monitor(replay_ids):
    rows = _collect_rows(replay_ids)
    success_slices, failure_slices = _slice_rows(rows)
    realistic_success_count = sum(1 for row in rows if row["realistic_success"])
    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_ids": replay_ids,
        "actionable_count": len(rows),
        "realistic_success_count": realistic_success_count,
        "realistic_failure_count": len(rows) - realistic_success_count,
        "realistic_success_rate": _rate(realistic_success_count, len(rows)),
        "executable_entry_label_counts": dict(Counter(row["executable_entry_label"] for row in rows)),
        "month_rows": _month_rows(rows),
        "top_success_slices": success_slices[:12],
        "top_failure_slices": failure_slices[:12],
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_buy_side_pattern_monitor_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_buy_side_pattern_monitor_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_buy_side_pattern_monitor_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_buy_side_pattern_monitor_v1.md")
    markdown = render_markdown(summary)

    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main(argv=None):
    argv = argv or sys.argv[1:]
    replay_ids = argv or DEFAULT_REPLAY_IDS
    summary, latest_json_path, latest_md_path = build_buy_side_pattern_monitor(replay_ids)
    print(json.dumps({
        "actionable_count": summary["actionable_count"],
        "realistic_success_count": summary["realistic_success_count"],
        "realistic_failure_count": summary["realistic_failure_count"],
        "realistic_success_rate": summary["realistic_success_rate"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
