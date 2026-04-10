"""
Build one combined monitoring checkpoint from the latest hostile and buy-side watchlists.

This is a compact baseline artifact for future monitoring cycles.
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
HOSTILE_WATCHLIST_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__hostile_watchlist_v1.json")
BUY_WATCHLIST_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__buy_side_watchlist_v1.json")
HOSTILE_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_hostile_window_monitor_v1.json")
BUY_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_buy_side_pattern_monitor_v1.json")


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def render_markdown(payload):
    lines = [
        "# Monitoring Watchlist Checkpoint",
        "",
        f"- built_at: `{payload['built_at']}`",
        "",
        "## Hostile Side",
        "",
        f"- hostile_case_count: `{payload['hostile_side']['hostile_case_count']}`",
        f"- actionable_count: `{payload['hostile_side']['actionable_count']}`",
        f"- warning_watch_count: `{payload['hostile_side']['warning_watch_count']}`",
        f"- secondary_watch_count: `{payload['hostile_side']['secondary_watch_count']}`",
        f"- top_warning_slice: `{payload['hostile_side']['top_warning_slice']}`",
        "",
        "## Buy Side",
        "",
        f"- actionable_count: `{payload['buy_side']['actionable_count']}`",
        f"- realistic_success_count: `{payload['buy_side']['realistic_success_count']}`",
        f"- realistic_success_rate: `{payload['buy_side']['realistic_success_rate']}`",
        f"- positive_watch_count: `{payload['buy_side']['positive_watch_count']}`",
        f"- warning_watch_count: `{payload['buy_side']['warning_watch_count']}`",
        f"- top_positive_slice: `{payload['buy_side']['top_positive_slice']}`",
        f"- top_warning_slice: `{payload['buy_side']['top_warning_slice']}`",
        "",
        "## Current Decision",
        "",
        "- champion stays frozen",
        "- no new rule branch opens from this checkpoint alone",
        "- future replay refreshes should compare against these watchlists first",
    ]
    return "\n".join(lines) + "\n"


def build_checkpoint():
    with open(HOSTILE_WATCHLIST_PATH, "r", encoding="utf-8") as handle:
        hostile_watchlist = json.load(handle)
    with open(BUY_WATCHLIST_PATH, "r", encoding="utf-8") as handle:
        buy_watchlist = json.load(handle)
    with open(HOSTILE_MONITOR_PATH, "r", encoding="utf-8") as handle:
        hostile_monitor = json.load(handle)
    with open(BUY_MONITOR_PATH, "r", encoding="utf-8") as handle:
        buy_monitor = json.load(handle)

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "hostile_side": {
            "hostile_case_count": hostile_monitor.get("hostile_case_count"),
            "actionable_count": hostile_monitor.get("actionable_count"),
            "warning_watch_count": len(hostile_watchlist.get("warning_slices") or []),
            "secondary_watch_count": len(hostile_watchlist.get("secondary_watch_slices") or []),
            "top_warning_slice": ((hostile_watchlist.get("warning_slices") or [{}])[0]).get("slice"),
        },
        "buy_side": {
            "actionable_count": buy_monitor.get("actionable_count"),
            "realistic_success_count": buy_monitor.get("realistic_success_count"),
            "realistic_success_rate": buy_monitor.get("realistic_success_rate"),
            "positive_watch_count": len(buy_watchlist.get("positive_watch_slices") or []),
            "warning_watch_count": len(buy_watchlist.get("warning_watch_slices") or []),
            "top_positive_slice": ((buy_watchlist.get("positive_watch_slices") or [{}])[0]).get("slice"),
            "top_warning_slice": ((buy_watchlist.get("warning_watch_slices") or [{}])[0]).get("slice"),
        },
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_watchlist_checkpoint_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__monitoring_watchlist_checkpoint_v1.json",
    )
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_watchlist_checkpoint_v1.md",
    )
    latest_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__monitoring_watchlist_checkpoint_v1.md",
    )

    markdown = render_markdown(payload)
    for path in (dated_json_path, latest_json_path):
        save_json(path, payload)
    for path in (dated_md_path, latest_md_path):
        save_text(path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_checkpoint()
    print(json.dumps({
        "hostile_warning_watch_count": payload["hostile_side"]["warning_watch_count"],
        "buy_positive_watch_count": payload["buy_side"]["positive_watch_count"],
        "buy_warning_watch_count": payload["buy_side"]["warning_watch_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
