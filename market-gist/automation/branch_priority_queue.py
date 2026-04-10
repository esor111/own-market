"""
Build one unified branch-priority queue for the next replay refresh.

This does not open research by itself. It answers:
- what buy-side slice should we watch first
- what hostile-side slice should we watch first
- why those are the current priorities

Usage:
    python branch_priority_queue.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
READINESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__system_reliability_readiness_scorecard_v1.json")
HOSTILE_WATCHLIST_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__hostile_watchlist_v1.json")
BUY_QUEUE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__buy_side_branch_readiness_queue_v1.json")


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


def _top_share(pairs, total_count):
    if not pairs or not total_count:
        return None
    return round((pairs[0][1] or 0) / total_count, 4)


def _hostile_quality_risks(row):
    risks = []
    count = row.get("count") or 0
    symbol_share = _top_share(row.get("symbols") or [], count)
    if count < 8:
        risks.append("thin_sample")
    if symbol_share is not None and symbol_share > 0.6:
        risks.append("symbol_concentration")
    return risks


def _hostile_attention_bucket(row):
    failure_count = row.get("failure_count") or 0
    failure_rate = row.get("failure_rate") or 0
    if failure_count >= 10 and failure_rate >= 0.8:
        return "critical_watch"
    if failure_count >= 5 and failure_rate >= 0.6:
        return "strong_watch"
    return "guarded_watch"


def render_markdown(payload):
    lines = [
        "# Branch Priority Queue",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- main_trust_gap: `{payload['main_trust_gap']}`",
        f"- champion_state: `{payload['champion_state']}`",
        "",
        "## Primary Focus",
        "",
        f"- buy-side first slice: `{payload['primary_buy_focus']['slice']}`",
        f"- why: `{payload['primary_buy_focus']['why']}`",
        "",
        "## Secondary Focus",
        "",
        f"- hostile-side first slice: `{payload['secondary_hostile_focus']['slice']}`",
        f"- why: `{payload['secondary_hostile_focus']['why']}`",
        "",
        "## Buy-Side Priority Queue",
        "",
    ]
    for row in payload.get("buy_priority_rows") or []:
        lines.append(
            f"- `{row['slice']}`: readiness `{row['readiness_bucket']}`, quality `{row['quality_status']}`, "
            f"additional_clean_successes_needed `{row['additional_clean_successes_needed']}`, "
            f"success_rate `{row['success_rate']}`, quality_risks `{row['quality_risks']}`"
        )

    lines.extend(["", "## Hostile-Side Priority Queue", ""])
    for row in payload.get("hostile_priority_rows") or []:
        lines.append(
            f"- `{row['slice']}`: attention `{row['attention_bucket']}`, failure_count `{row['failure_count']}`, "
            f"failure_rate `{row['failure_rate']}`, quality_risks `{row['quality_risks']}`"
        )

    lines.extend([
        "",
        "## Current Decision",
        "",
        "- champion stays frozen",
        "- no branch opens from the queue alone",
        "- on the next replay refresh, inspect the primary buy-side focus first and the secondary hostile-side focus second",
    ])
    return "\n".join(lines) + "\n"


def build_queue():
    readiness = load_json(READINESS_PATH)
    hostile_watchlist = load_json(HOSTILE_WATCHLIST_PATH)
    buy_queue = load_json(BUY_QUEUE_PATH)

    buy_priority_rows = list(buy_queue.get("queue_rows") or [])
    hostile_priority_rows = []
    for row in hostile_watchlist.get("warning_slices") or []:
        enriched = dict(row)
        enriched["quality_risks"] = _hostile_quality_risks(row)
        enriched["attention_bucket"] = _hostile_attention_bucket(row)
        hostile_priority_rows.append(enriched)

    hostile_priority_rows.sort(
        key=lambda item: (
            item["attention_bucket"] != "critical_watch",
            -(item.get("failure_count") or 0),
            -(item.get("failure_rate") or 0),
        )
    )

    main_trust_gap = "buy_side" if readiness.get("buy_side_readiness") != "high_trust_ready" else "monitoring_only"
    primary_buy = buy_priority_rows[0] if buy_priority_rows else {"slice": "none", "readiness_bucket": "none", "quality_status": "none"}
    secondary_hostile = hostile_priority_rows[0] if hostile_priority_rows else {"slice": "none", "attention_bucket": "none"}

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "main_trust_gap": main_trust_gap,
        "champion_state": "frozen",
        "primary_buy_focus": {
            "slice": primary_buy.get("slice"),
            "why": "buy side is still the main trust gap, and this is the closest positive slice to the current research gate without being promoted yet",
        },
        "secondary_hostile_focus": {
            "slice": secondary_hostile.get("slice"),
            "why": "this is the strongest repeated hostile warning slice to watch for future drift even while buy-side trust remains the main open problem",
        },
        "buy_priority_rows": buy_priority_rows,
        "hostile_priority_rows": hostile_priority_rows[:5],
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__branch_priority_queue_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__branch_priority_queue_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__branch_priority_queue_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__branch_priority_queue_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_queue()
    print(json.dumps({
        "main_trust_gap": payload["main_trust_gap"],
        "primary_buy_focus": payload["primary_buy_focus"]["slice"],
        "secondary_hostile_focus": payload["secondary_hostile_focus"]["slice"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
