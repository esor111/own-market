"""
Derive a buy-side watchlist baseline from the aggregate buy-side pattern monitor.

This keeps the next candidate-positive slices and strongest warning slices in one
stable artifact so future replay refreshes can be checked against the same
watchlist instead of relying on memory.
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
SOURCE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_buy_side_pattern_monitor_v1.json")


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _classify_positive_candidates(rows):
    candidates = []
    for row in rows:
        if row.get("success_count", 0) < 3:
            continue
        if row.get("count", 0) < 5:
            continue
        success_rate = row.get("success_rate")
        if success_rate is None:
            continue
        if success_rate < 0.3 or success_rate > 0.6:
            continue
        candidates.append(dict(row))
    candidates.sort(
        key=lambda item: (item["success_count"], item["success_rate"], -item["failure_count"]),
        reverse=True,
    )
    return candidates


def _classify_warning_slices(rows):
    warnings = []
    for row in rows:
        if row.get("failure_count", 0) < 8:
            continue
        success_rate = row.get("success_rate")
        if success_rate is None:
            continue
        if success_rate > 0.2:
            continue
        warnings.append(dict(row))
    warnings.sort(
        key=lambda item: (item["failure_count"], -item["success_rate"], item["count"]),
        reverse=True,
    )
    return warnings


def render_markdown(payload):
    lines = [
        "# Buy-Side Watchlist Baseline",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- source_path: `{payload['source_path']}`",
        f"- replay_count: `{payload['replay_count']}`",
        f"- actionable_count: `{payload['actionable_count']}`",
        "",
        "## Positive Candidate Watchlist",
        "",
    ]
    if not payload.get("positive_watch_slices"):
        lines.append("- none")
    else:
        for row in payload["positive_watch_slices"]:
            lines.append(
                f"- `{row['slice']}`: count `{row['count']}`, success_count `{row['success_count']}`, "
                f"failure_count `{row['failure_count']}`, success_rate `{row['success_rate']}`, "
                f"symbols `{row['symbols']}`, months `{row['months']}`"
            )

    lines.extend(["", "## Warning Watchlist", ""])
    if not payload.get("warning_watch_slices"):
        lines.append("- none")
    else:
        for row in payload["warning_watch_slices"]:
            lines.append(
                f"- `{row['slice']}`: count `{row['count']}`, success_count `{row['success_count']}`, "
                f"failure_count `{row['failure_count']}`, success_rate `{row['success_rate']}`, "
                f"symbols `{row['symbols']}`, months `{row['months']}`"
            )

    lines.extend([
        "",
        "## Current Decision",
        "",
        "- champion stays frozen",
        "- no buy-side challenger opens from this baseline alone",
        "- future replay refreshes should compare against these watch slices first",
    ])
    return "\n".join(lines) + "\n"


def build_watchlist():
    with open(SOURCE_PATH, "r", encoding="utf-8") as handle:
        source = json.load(handle)

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_path": SOURCE_PATH,
        "replay_count": len(source.get("replay_ids") or []),
        "actionable_count": source.get("actionable_count"),
        "positive_watch_slices": _classify_positive_candidates(source.get("top_success_slices") or [])[:10],
        "warning_watch_slices": _classify_warning_slices(source.get("top_failure_slices") or [])[:10],
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__buy_side_watchlist_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__buy_side_watchlist_v1.json",
    )
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__buy_side_watchlist_v1.md",
    )
    latest_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__buy_side_watchlist_v1.md",
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
        "positive_watch_count": len(payload["positive_watch_slices"]),
        "warning_watch_count": len(payload["warning_watch_slices"]),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
