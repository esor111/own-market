"""
Build a coverage ledger for replay windows currently used by monitoring.

This answers:
- which replay windows are already inside the hostile monitor
- which replay windows are already inside the buy-side monitor
- which months are covered by both versus only one side

Usage:
    python monitoring_replay_coverage_ledger.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
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


def _month_key_from_replay_id(replay_id):
    if not replay_id or len(replay_id) < 7:
        return None
    return replay_id[:7]


def _build_month_map(replay_ids):
    month_map = {}
    for replay_id in replay_ids or []:
        month_key = _month_key_from_replay_id(replay_id)
        if not month_key:
            continue
        month_map.setdefault(month_key, []).append(replay_id)
    return month_map


def render_markdown(payload):
    lines = [
        "# Monitoring Replay Coverage Ledger",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- hostile_replay_count: `{payload['hostile_replay_count']}`",
        f"- buy_replay_count: `{payload['buy_replay_count']}`",
        f"- combined_month_count: `{payload['combined_month_count']}`",
        "",
        "## Coverage Summary",
        "",
        f"- months_covered_by_both: `{payload['months_covered_by_both']}`",
        f"- months_hostile_only: `{payload['months_hostile_only']}`",
        f"- months_buy_only: `{payload['months_buy_only']}`",
        "",
        "## Coverage Rows",
        "",
    ]

    for row in payload.get("coverage_rows") or []:
        lines.append(
            f"- `{row['month_key']}`: hostile `{row['hostile_covered']}` ({row['hostile_count']}), "
            f"buy `{row['buy_covered']}` ({row['buy_count']})"
        )

    lines.extend(["", "## Month Details", ""])
    for row in payload.get("coverage_rows") or []:
        lines.append(f"- `{row['month_key']}`")
        lines.append(f"  hostile_replay_ids: `{row['hostile_replay_ids']}`")
        lines.append(f"  buy_replay_ids: `{row['buy_replay_ids']}`")

    return "\n".join(lines) + "\n"


def build_coverage_ledger():
    hostile_monitor = load_json(HOSTILE_MONITOR_PATH)
    buy_monitor = load_json(BUY_MONITOR_PATH)

    hostile_replay_ids = hostile_monitor.get("replay_ids") or []
    buy_replay_ids = buy_monitor.get("replay_ids") or []

    hostile_month_map = _build_month_map(hostile_replay_ids)
    buy_month_map = _build_month_map(buy_replay_ids)

    all_months = sorted(set(hostile_month_map) | set(buy_month_map))
    coverage_rows = []
    months_covered_by_both = 0
    months_hostile_only = 0
    months_buy_only = 0

    for month_key in all_months:
        hostile_ids = hostile_month_map.get(month_key, [])
        buy_ids = buy_month_map.get(month_key, [])
        hostile_covered = bool(hostile_ids)
        buy_covered = bool(buy_ids)

        if hostile_covered and buy_covered:
            months_covered_by_both += 1
        elif hostile_covered:
            months_hostile_only += 1
        elif buy_covered:
            months_buy_only += 1

        coverage_rows.append({
            "month_key": month_key,
            "hostile_covered": hostile_covered,
            "hostile_count": len(hostile_ids),
            "hostile_replay_ids": hostile_ids,
            "buy_covered": bool(buy_ids),
            "buy_count": len(buy_ids),
            "buy_replay_ids": buy_ids,
        })

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "hostile_replay_count": len(hostile_replay_ids),
        "buy_replay_count": len(buy_replay_ids),
        "combined_month_count": len(all_months),
        "months_covered_by_both": months_covered_by_both,
        "months_hostile_only": months_hostile_only,
        "months_buy_only": months_buy_only,
        "coverage_rows": coverage_rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_replay_coverage_ledger_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_replay_coverage_ledger_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_replay_coverage_ledger_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_replay_coverage_ledger_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_coverage_ledger()
    print(json.dumps({
        "hostile_replay_count": payload["hostile_replay_count"],
        "buy_replay_count": payload["buy_replay_count"],
        "combined_month_count": payload["combined_month_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
