"""
Aggregate hostile-window monitoring across one or more promoted replay runs.

Usage:
    python aggregate_hostile_window_monitor.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

from config import REPLAYS_DIR, VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
HOSTILE_PHASES = {
    "fiscal_year_end_window",
    "post_fiscal_results_window",
}


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


def _load_summary(replay_id):
    path = os.path.join(REPLAYS_DIR, replay_id, "summaries", "latest__replay_summary_v1.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Replay summary not found: {path}")
    return load_json(path)


def _is_hostile_record(record):
    return (record.get("calendar_phase") or "") in HOSTILE_PHASES


def _triggered(record):
    return bool(
        record.get("calendar_confidence_guidance_action_change")
        or record.get("bank_exhaustion_guidance_action_change")
        or record.get("commercial_bank_watch_caution_guidance_action_change")
        or record.get("commercial_bank_overconfident_watch_caution_guidance_action_change")
        or record.get("hydropower_buy_caution_guidance_action_change")
    )


def _trigger_source(record):
    return (
        record.get("commercial_bank_overconfident_watch_caution_guidance_action_change") and "commercial_bank_overconfident_watch_caution"
    ) or (
        record.get("commercial_bank_watch_caution_guidance_action_change") and "commercial_bank_watch_caution"
    ) or (
        record.get("hydropower_buy_caution_guidance_action_change") and "hydropower_buy_caution"
    ) or (
        record.get("bank_exhaustion_guidance_action_change") and "bank_exhaustion"
    ) or (
        record.get("calendar_confidence_guidance_action_change") and "calendar_confidence"
    ) or "none"


def _bucket_key(record):
    return " | ".join([
        f"sector={record.get('sector_name') or 'UNKNOWN'}",
        f"event={record.get('event_state') or 'unknown'}",
        f"confidence={record.get('confidence_interpretation_label') or 'unknown'}",
        f"action={record.get('action') or 'unknown'}",
    ])


def _month_row(replay_id, records):
    action_counter = Counter(item.get("action") or "unknown" for item in records)
    verdict_counter = Counter(item.get("comparison_verdict") or "unknown" for item in records)
    triggered_rows = [item for item in records if _triggered(item)]
    actionable_rows = [item for item in records if item.get("action") in {"buy", "watch_only"}]
    actionable_failures = [
        item for item in actionable_rows
        if item.get("comparison_verdict") in {"bad_call", "mixed_call"}
    ]

    return {
        "replay_id": replay_id,
        "hostile_case_count": len(records),
        "action_counts": dict(action_counter),
        "verdict_counts": dict(verdict_counter),
        "triggered_case_count": len(triggered_rows),
        "triggered_good_avoid_count": sum(1 for item in triggered_rows if item.get("comparison_verdict") == "good_avoid"),
        "triggered_bad_call_count": sum(1 for item in triggered_rows if item.get("comparison_verdict") == "bad_call"),
        "actionable_count": len(actionable_rows),
        "actionable_failure_count": len(actionable_failures),
        "actionable_failure_rate": _rate(len(actionable_failures), len(actionable_rows)),
    }


def build_hostile_window_monitor(replay_ids):
    all_records = []
    month_rows = []
    sector_verdict_counter = Counter()
    symbol_verdict_counter = Counter()
    guidance_change_counter = Counter()
    confidence_verdict_counter = Counter()
    slice_groups = defaultdict(list)

    for replay_id in replay_ids:
        summary = _load_summary(replay_id)
        hostile_records = [item for item in (summary.get("records") or []) if _is_hostile_record(item)]
        month_rows.append(_month_row(replay_id, hostile_records))

        for item in hostile_records:
            all_records.append({"replay_id": replay_id, **item})
            verdict = item.get("comparison_verdict") or "unknown"
            sector_verdict_counter[f"{item.get('sector_name') or 'UNKNOWN'}:{verdict}"] += 1
            symbol_verdict_counter[f"{item.get('symbol') or 'UNKNOWN'}:{verdict}"] += 1
            confidence_verdict_counter[f"{item.get('confidence_interpretation_label') or 'unknown'}:{verdict}"] += 1
            guidance_change_counter[_trigger_source(item)] += 1
            slice_groups[_bucket_key(item)].append(item)

    actionable_rows = [item for item in all_records if item.get("action") in {"buy", "watch_only"}]
    actionable_failures = [
        item for item in actionable_rows
        if item.get("comparison_verdict") in {"bad_call", "mixed_call"}
    ]
    triggered_rows = [item for item in all_records if _triggered(item)]
    triggered_good_avoid = [item for item in triggered_rows if item.get("comparison_verdict") == "good_avoid"]

    top_failure_slices = []
    for slice_name, rows in slice_groups.items():
        if len(rows) < 2:
            continue
        actionable = [item for item in rows if item.get("action") in {"buy", "watch_only"}]
        if not actionable:
            continue
        failures = [item for item in actionable if item.get("comparison_verdict") in {"bad_call", "mixed_call"}]
        if not failures:
            continue
        top_failure_slices.append({
            "slice": slice_name,
            "count": len(rows),
            "actionable_count": len(actionable),
            "failure_count": len(failures),
            "failure_rate": _rate(len(failures), len(actionable)),
            "symbols": Counter(item.get("symbol") or "UNKNOWN" for item in rows).most_common(5),
        })
    top_failure_slices.sort(
        key=lambda item: (item["failure_count"], item["failure_rate"] or 0, item["actionable_count"]),
        reverse=True,
    )

    top_trigger_symbols = Counter(item.get("symbol") or "UNKNOWN" for item in triggered_rows).most_common(10)

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_ids": replay_ids,
        "hostile_phases": sorted(HOSTILE_PHASES),
        "hostile_case_count": len(all_records),
        "triggered_case_count": len(triggered_rows),
        "triggered_good_avoid_count": len(triggered_good_avoid),
        "actionable_count": len(actionable_rows),
        "actionable_failure_count": len(actionable_failures),
        "actionable_failure_rate": _rate(len(actionable_failures), len(actionable_rows)),
        "sector_verdict_counts": dict(sector_verdict_counter),
        "symbol_verdict_counts": dict(symbol_verdict_counter),
        "confidence_verdict_counts": dict(confidence_verdict_counter),
        "guidance_change_counts": dict(guidance_change_counter),
        "top_trigger_symbols": top_trigger_symbols,
        "top_actionable_failure_slices": top_failure_slices[:10],
        "month_rows": month_rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_hostile_window_monitor_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_hostile_window_monitor_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_hostile_window_monitor_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_hostile_window_monitor_v1.md")
    markdown = render_markdown(summary)

    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def render_markdown(summary):
    lines = [
        "# Aggregate Hostile-Window Monitor",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- replay_count: `{len(summary['replay_ids'])}`",
        f"- hostile_case_count: `{summary['hostile_case_count']}`",
        f"- triggered_case_count: `{summary['triggered_case_count']}`",
        f"- triggered_good_avoid_count: `{summary['triggered_good_avoid_count']}`",
        f"- actionable_count: `{summary['actionable_count']}`",
        f"- actionable_failure_count: `{summary['actionable_failure_count']}`",
        f"- actionable_failure_rate: `{summary['actionable_failure_rate']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in summary.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")

    lines.extend(["", "## Month Rows", ""])
    for item in summary.get("month_rows", []):
        lines.append(
            f"- `{item['replay_id']}`: hostile_cases `{item['hostile_case_count']}`, "
            f"triggered `{item['triggered_case_count']}`, actionable `{item['actionable_count']}`, "
            f"actionable_failure_rate `{item['actionable_failure_rate']}`, verdicts `{item['verdict_counts']}`"
        )

    lines.extend(["", "## Guidance Changes", ""])
    for key, value in sorted((summary.get("guidance_change_counts") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Top Trigger Symbols", ""])
    for symbol, count in summary.get("top_trigger_symbols", []):
        lines.append(f"- `{symbol}`: `{count}`")

    lines.extend(["", "## Sector Verdict Counts", ""])
    for key, value in list((summary.get("sector_verdict_counts") or {}).items())[:15]:
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Confidence Verdict Counts", ""])
    for key, value in list((summary.get("confidence_verdict_counts") or {}).items())[:15]:
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Top Actionable Failure Slices", ""])
    if not summary.get("top_actionable_failure_slices"):
        lines.append("- none")
    else:
        for item in summary.get("top_actionable_failure_slices", []):
            lines.append(
                f"- `{item['slice']}`: count `{item['count']}`, actionable `{item['actionable_count']}`, "
                f"failure_count `{item['failure_count']}`, failure_rate `{item['failure_rate']}`, symbols `{item['symbols']}`"
            )

    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) < 2:
        print("Usage: python aggregate_hostile_window_monitor.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    summary, latest_json_path, latest_md_path = build_hostile_window_monitor(sys.argv[1:])
    print(json.dumps({
        "replay_count": len(summary["replay_ids"]),
        "hostile_case_count": summary["hostile_case_count"],
        "triggered_case_count": summary["triggered_case_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
