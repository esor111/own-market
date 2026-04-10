"""
Compare the current hostile/buy monitors against the saved watchlist baselines.

This is the missing monitoring bridge between:
- the frozen baseline watchlists
- the latest replay refresh monitor outputs

Usage:
    python monitor_watchlist_diff.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR
from derive_buy_side_watchlist import (
    _classify_positive_candidates,
    _classify_warning_slices as _classify_buy_warning_slices,
)
from derive_hostile_watchlist import _warning_slices as _classify_hostile_warning_slices
from derive_hostile_watchlist import _watch_slices as _classify_hostile_secondary_slices


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
HOSTILE_WATCHLIST_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__hostile_watchlist_v1.json")
BUY_WATCHLIST_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__buy_side_watchlist_v1.json")
HOSTILE_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_hostile_window_monitor_v1.json")
BUY_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_buy_side_pattern_monitor_v1.json")


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


def _delta(current_value, baseline_value):
    if current_value is None or baseline_value is None:
        return None
    return round(current_value - baseline_value, 4)


def _index_by_slice(rows):
    return {row.get("slice"): row for row in rows if row.get("slice")}


def _warning_metric(row):
    failure_rate = row.get("failure_rate")
    if failure_rate is not None:
        return failure_rate
    success_rate = row.get("success_rate")
    if success_rate is None:
        return None
    return round(1 - success_rate, 4)


def _presence_status(mode, current_row):
    if current_row is not None:
        return "present"
    if mode == "positive":
        return "missing_worse"
    return "missing_better"


def _compare_rows(baseline_rows, current_rows, mode):
    current_map = _index_by_slice(current_rows)
    comparisons = []
    for baseline_row in baseline_rows:
        slice_name = baseline_row.get("slice")
        current_row = current_map.get(slice_name)
        if mode == "positive":
            baseline_metric = baseline_row.get("success_rate")
            current_metric = (current_row or {}).get("success_rate")
            baseline_event_count = baseline_row.get("success_count")
            current_event_count = (current_row or {}).get("success_count")
        else:
            baseline_metric = _warning_metric(baseline_row)
            current_metric = _warning_metric(current_row or {})
            baseline_event_count = baseline_row.get("failure_count")
            current_event_count = (current_row or {}).get("failure_count")

        metric_delta = _delta(current_metric, baseline_metric)
        count_delta = _delta((current_row or {}).get("count"), baseline_row.get("count"))
        event_delta = _delta(current_event_count, baseline_event_count)
        presence_status = _presence_status(mode, current_row)

        trend = "stable"
        if presence_status == "missing_worse":
            trend = "worsened"
        elif presence_status == "missing_better":
            trend = "improved"
        elif metric_delta is not None or event_delta is not None:
            metric_delta_value = metric_delta or 0.0
            event_delta_value = event_delta or 0.0
            if mode == "positive":
                if metric_delta_value >= 0.1 or event_delta_value >= 3:
                    trend = "improved"
                elif metric_delta_value <= -0.1 or event_delta_value <= -3:
                    trend = "worsened"
            else:
                if metric_delta_value >= 0.1 or event_delta_value >= 3:
                    trend = "worsened"
                elif metric_delta_value <= -0.1 or event_delta_value <= -3:
                    trend = "improved"

        comparisons.append({
            "slice": slice_name,
            "presence_status": presence_status,
            "trend": trend,
            "baseline_count": baseline_row.get("count"),
            "current_count": (current_row or {}).get("count"),
            "count_delta": count_delta,
            "baseline_metric": baseline_metric,
            "current_metric": current_metric,
            "metric_delta": metric_delta,
            "baseline_event_count": baseline_event_count,
            "current_event_count": current_event_count,
            "event_delta": event_delta,
        })
    comparisons.sort(key=lambda item: (item["trend"] != "stable", abs(item["metric_delta"] or 0), abs(item["event_delta"] or 0)), reverse=True)
    return comparisons


def _emergent_rows(current_rows, baseline_rows):
    baseline_slices = {row.get("slice") for row in baseline_rows if row.get("slice")}
    emergent = [row for row in current_rows if row.get("slice") not in baseline_slices]
    emergent.sort(
        key=lambda item: (
            item.get("failure_count", item.get("success_count", 0)),
            item.get("failure_rate", item.get("success_rate", 0)) or 0,
            item.get("count", 0),
        ),
        reverse=True,
    )
    return emergent


def _summary_counts(rows):
    return {
        "stable": sum(1 for row in rows if row.get("trend") == "stable"),
        "improved": sum(1 for row in rows if row.get("trend") == "improved"),
        "worsened": sum(1 for row in rows if row.get("trend") == "worsened"),
        "present": sum(1 for row in rows if row.get("presence_status") == "present"),
        "missing": sum(1 for row in rows if str(row.get("presence_status", "")).startswith("missing_")),
    }


def render_markdown(payload):
    hostile = payload["hostile"]
    buy_side = payload["buy_side"]
    lines = [
        "# Monitoring Watchlist Diff",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- hostile_monitor_path: `{payload['hostile_monitor_path']}`",
        f"- hostile_watchlist_path: `{payload['hostile_watchlist_path']}`",
        f"- buy_monitor_path: `{payload['buy_monitor_path']}`",
        f"- buy_watchlist_path: `{payload['buy_watchlist_path']}`",
        "",
        "## Hostile Baseline Diff",
        "",
        f"- warning_slices_stable: `{hostile['warning_summary']['stable']}`",
        f"- warning_slices_improved: `{hostile['warning_summary']['improved']}`",
        f"- warning_slices_worsened: `{hostile['warning_summary']['worsened']}`",
        f"- warning_slices_missing: `{hostile['warning_summary']['missing']}`",
        f"- emergent_warning_slices: `{len(hostile['emergent_warning_slices'])}`",
        "",
    ]
    if hostile["warning_comparisons"]:
        lines.append("### Warning Slice Diff")
        lines.append("")
        for row in hostile["warning_comparisons"]:
            lines.append(
                f"- `{row['slice']}`: trend `{row['trend']}`, presence `{row['presence_status']}`, "
                f"baseline_count `{row['baseline_count']}`, current_count `{row['current_count']}`, "
                f"baseline_failure_rate `{row['baseline_metric']}`, current_failure_rate `{row['current_metric']}`"
            )
        lines.append("")

    if hostile["secondary_comparisons"]:
        lines.append("### Secondary Watch Diff")
        lines.append("")
        for row in hostile["secondary_comparisons"]:
            lines.append(
                f"- `{row['slice']}`: trend `{row['trend']}`, presence `{row['presence_status']}`, "
                f"baseline_count `{row['baseline_count']}`, current_count `{row['current_count']}`, "
                f"baseline_failure_rate `{row['baseline_metric']}`, current_failure_rate `{row['current_metric']}`"
            )
        lines.append("")

    lines.extend([
        "## Buy-Side Baseline Diff",
        "",
        f"- positive_slices_stable: `{buy_side['positive_summary']['stable']}`",
        f"- positive_slices_improved: `{buy_side['positive_summary']['improved']}`",
        f"- positive_slices_worsened: `{buy_side['positive_summary']['worsened']}`",
        f"- positive_slices_missing: `{buy_side['positive_summary']['missing']}`",
        f"- warning_slices_stable: `{buy_side['warning_summary']['stable']}`",
        f"- warning_slices_improved: `{buy_side['warning_summary']['improved']}`",
        f"- warning_slices_worsened: `{buy_side['warning_summary']['worsened']}`",
        f"- warning_slices_missing: `{buy_side['warning_summary']['missing']}`",
        f"- emergent_positive_slices: `{len(buy_side['emergent_positive_slices'])}`",
        f"- emergent_warning_slices: `{len(buy_side['emergent_warning_slices'])}`",
        "",
    ])

    if buy_side["positive_comparisons"]:
        lines.append("### Positive Watch Diff")
        lines.append("")
        for row in buy_side["positive_comparisons"]:
            lines.append(
                f"- `{row['slice']}`: trend `{row['trend']}`, presence `{row['presence_status']}`, "
                f"baseline_count `{row['baseline_count']}`, current_count `{row['current_count']}`, "
                f"baseline_success_rate `{row['baseline_metric']}`, current_success_rate `{row['current_metric']}`"
            )
        lines.append("")

    if buy_side["warning_comparisons"]:
        lines.append("### Buy Warning Diff")
        lines.append("")
        for row in buy_side["warning_comparisons"]:
            lines.append(
                f"- `{row['slice']}`: trend `{row['trend']}`, presence `{row['presence_status']}`, "
                f"baseline_count `{row['baseline_count']}`, current_count `{row['current_count']}`, "
                f"baseline_failure_rate `{row['baseline_metric']}`, current_failure_rate `{row['current_metric']}`"
            )
        lines.append("")

    lines.extend([
        "## Current Decision",
        "",
        "- champion stays frozen",
        "- no new branch opens from drift monitoring alone",
        "- refresh the monitors first, then compare against these same watchlists before opening research",
    ])
    return "\n".join(lines) + "\n"


def build_diff():
    hostile_watchlist = load_json(HOSTILE_WATCHLIST_PATH)
    buy_watchlist = load_json(BUY_WATCHLIST_PATH)
    hostile_monitor = load_json(HOSTILE_MONITOR_PATH)
    buy_monitor = load_json(BUY_MONITOR_PATH)

    current_hostile_warning = _classify_hostile_warning_slices(hostile_monitor.get("top_actionable_failure_slices") or [])
    current_hostile_secondary = _classify_hostile_secondary_slices(hostile_monitor.get("top_actionable_failure_slices") or [])
    current_buy_positive = _classify_positive_candidates(buy_monitor.get("top_success_slices") or [])
    current_buy_warning = _classify_buy_warning_slices(buy_monitor.get("top_failure_slices") or [])

    hostile_warning_comparisons = _compare_rows(
        hostile_watchlist.get("warning_slices") or [],
        current_hostile_warning,
        mode="warning",
    )
    hostile_secondary_comparisons = _compare_rows(
        hostile_watchlist.get("secondary_watch_slices") or [],
        current_hostile_secondary,
        mode="warning",
    )
    buy_positive_comparisons = _compare_rows(
        buy_watchlist.get("positive_watch_slices") or [],
        current_buy_positive,
        mode="positive",
    )
    buy_warning_comparisons = _compare_rows(
        buy_watchlist.get("warning_watch_slices") or [],
        current_buy_warning,
        mode="warning",
    )

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "hostile_watchlist_path": HOSTILE_WATCHLIST_PATH,
        "hostile_monitor_path": HOSTILE_MONITOR_PATH,
        "buy_watchlist_path": BUY_WATCHLIST_PATH,
        "buy_monitor_path": BUY_MONITOR_PATH,
        "hostile": {
            "warning_summary": _summary_counts(hostile_warning_comparisons),
            "secondary_summary": _summary_counts(hostile_secondary_comparisons),
            "warning_comparisons": hostile_warning_comparisons,
            "secondary_comparisons": hostile_secondary_comparisons,
            "emergent_warning_slices": _emergent_rows(current_hostile_warning, hostile_watchlist.get("warning_slices") or []),
            "emergent_secondary_slices": _emergent_rows(current_hostile_secondary, hostile_watchlist.get("secondary_watch_slices") or []),
        },
        "buy_side": {
            "positive_summary": _summary_counts(buy_positive_comparisons),
            "warning_summary": _summary_counts(buy_warning_comparisons),
            "positive_comparisons": buy_positive_comparisons,
            "warning_comparisons": buy_warning_comparisons,
            "emergent_positive_slices": _emergent_rows(current_buy_positive, buy_watchlist.get("positive_watch_slices") or []),
            "emergent_warning_slices": _emergent_rows(current_buy_warning, buy_watchlist.get("warning_watch_slices") or []),
        },
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_watchlist_diff_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_watchlist_diff_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_watchlist_diff_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_watchlist_diff_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_diff()
    print(json.dumps({
        "hostile_warning_stable": payload["hostile"]["warning_summary"]["stable"],
        "hostile_warning_worsened": payload["hostile"]["warning_summary"]["worsened"],
        "buy_positive_stable": payload["buy_side"]["positive_summary"]["stable"],
        "buy_positive_worsened": payload["buy_side"]["positive_summary"]["worsened"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
