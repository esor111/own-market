"""
Derive a hostile-side watchlist baseline from the aggregate hostile-window monitor.

This turns the current hostile monitor into a stable warning/watch artifact so
future replay refreshes can compare against the same slices instead of relying
on memory.
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
SOURCE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_hostile_window_monitor_v1.json")


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _warning_slices(rows):
    warning_rows = []
    for row in rows:
        count = row.get("count", 0)
        failure_count = row.get("failure_count", 0)
        failure_rate = row.get("failure_rate")
        if count < 4:
            continue
        if failure_count < 5:
            continue
        if failure_rate is None or failure_rate < 0.5:
            continue
        warning_rows.append(dict(row))
    warning_rows.sort(
        key=lambda item: (item["failure_count"], item["failure_rate"], item["count"]),
        reverse=True,
    )
    return warning_rows


def _watch_slices(rows):
    watch_rows = []
    for row in rows:
        count = row.get("count", 0)
        failure_count = row.get("failure_count", 0)
        failure_rate = row.get("failure_rate")
        if count < 4:
            continue
        if failure_count < 2:
            continue
        if failure_rate is None:
            continue
        if 0.3 <= failure_rate < 0.5:
            watch_rows.append(dict(row))
    watch_rows.sort(
        key=lambda item: (item["count"], item["failure_rate"], item["failure_count"]),
        reverse=True,
    )
    return watch_rows


def render_markdown(payload):
    lines = [
        "# Hostile Watchlist Baseline",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- source_path: `{payload['source_path']}`",
        f"- replay_count: `{payload['replay_count']}`",
        f"- hostile_case_count: `{payload['hostile_case_count']}`",
        f"- actionable_count: `{payload['actionable_count']}`",
        "",
        "## Warning Slices",
        "",
    ]
    if not payload.get("warning_slices"):
        lines.append("- none")
    else:
        for row in payload["warning_slices"]:
            lines.append(
                f"- `{row['slice']}`: count `{row['count']}`, actionable `{row['actionable_count']}`, "
                f"failure_count `{row['failure_count']}`, failure_rate `{row['failure_rate']}`, symbols `{row['symbols']}`"
            )

    lines.extend(["", "## Secondary Watch Slices", ""])
    if not payload.get("secondary_watch_slices"):
        lines.append("- none")
    else:
        for row in payload["secondary_watch_slices"]:
            lines.append(
                f"- `{row['slice']}`: count `{row['count']}`, actionable `{row['actionable_count']}`, "
                f"failure_count `{row['failure_count']}`, failure_rate `{row['failure_rate']}`, symbols `{row['symbols']}`"
            )

    lines.extend([
        "",
        "## Trigger Sources",
        "",
    ])
    for key, value in sorted((payload.get("guidance_change_counts") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")

    lines.extend([
        "",
        "## Current Decision",
        "",
        "- champion stays frozen",
        "- hostile refreshes should compare against these warning/watch slices first",
        "- new hostile challengers should open only if one of these slices repeats more cleanly or a new slice overtakes them",
    ])
    return "\n".join(lines) + "\n"


def build_watchlist():
    with open(SOURCE_PATH, "r", encoding="utf-8") as handle:
        source = json.load(handle)
    top_failure_slices = source.get("top_actionable_failure_slices") or []
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_path": SOURCE_PATH,
        "replay_count": len(source.get("replay_ids") or []),
        "hostile_case_count": source.get("hostile_case_count"),
        "actionable_count": source.get("actionable_count"),
        "guidance_change_counts": source.get("guidance_change_counts") or {},
        "warning_slices": _warning_slices(top_failure_slices)[:10],
        "secondary_watch_slices": _watch_slices(top_failure_slices)[:10],
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__hostile_watchlist_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__hostile_watchlist_v1.json",
    )
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__hostile_watchlist_v1.md",
    )
    latest_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__hostile_watchlist_v1.md",
    )
    markdown = render_markdown(payload)
    for path in (dated_json_path, latest_json_path):
        save_json(path, payload)
    for path in (dated_md_path, latest_md_path):
        save_text(path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_watchlist()
    print(json.dumps({
        "warning_count": len(payload["warning_slices"]),
        "secondary_watch_count": len(payload["secondary_watch_slices"]),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
