"""
Build a candidate replay gap report for the monitoring stack.

This scans replay directories and flags monthly replay windows that look like
final-champion candidates but are not currently covered by the monitoring stack.

Usage:
    python monitoring_candidate_replay_gap_report.py
"""
import json
import os
import re
from calendar import monthrange
from datetime import datetime

from config import REPLAYS_DIR, VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
BUY_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_buy_side_pattern_monitor_v1.json")
HOSTILE_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_hostile_window_monitor_v1.json")

MONTHLY_RANGE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})_to_(\d{4})-(\d{2})-(\d{2})__")

EXCLUDE_TOKENS = (
    "legacy",
    "challenger",
    "study",
    "context",
    "liquidity",
    "liqslice",
    "fragilityonly",
    "sectorsoft",
    "regime",
    "smoketest",
    "confidenceview",
    "eventcovered",
    "bankexhaustion",
    "calendarconfidence",
    "hydrobuy",
    "strictbuy",
    "improvingwatch",
    "rrwatch",
    "xsection",
    "control",
)

PREFERRED_TOKENS = (
    "currentchampion",
    "postbankwatchpromotion",
    "promotedchampion",
    "promoted_calendar",
    "champion_v1",
    "daily_truth_replay_v1",
)

PREFERRED_TOKEN_PRIORITY = {
    "currentchampion": 100,
    "postbankwatchpromotion": 90,
    "promotedchampion": 80,
    "promoted_calendar": 70,
    "champion_v1": 60,
    "daily_truth_replay_v1": 50,
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


def _is_monthly_window(name):
    match = MONTHLY_RANGE_RE.match(name)
    if not match:
        return False
    start_year, start_month, start_day, end_year, end_month, end_day = map(int, match.groups())
    if start_year != end_year or start_month != end_month:
        return False
    if start_day != 1:
        return False
    return end_day == monthrange(start_year, start_month)[1]


def _month_key(name):
    match = MONTHLY_RANGE_RE.match(name)
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}"


def _looks_like_candidate(name):
    lowered = name.lower()
    if not _is_monthly_window(name):
        return False
    if "__replay_basket_v1__" not in lowered and "__ebl__nabil__sanima__jbbl__mnbbl__api__akpl__upper__" not in lowered:
        return False
    if any(token in lowered for token in EXCLUDE_TOKENS):
        return False
    return any(token in lowered for token in PREFERRED_TOKENS)


def _has_replay_summary(name):
    summary_path = os.path.join(REPLAYS_DIR, name, "summaries", "latest__replay_summary_v1.json")
    return os.path.exists(summary_path)


def _hostile_candidate(month_key):
    return month_key in {"2023-07", "2023-08", "2024-07", "2024-08", "2025-07", "2025-08"}


def _candidate_priority(name):
    lowered = name.lower()
    best = 0
    for token, score in PREFERRED_TOKEN_PRIORITY.items():
        if token in lowered:
            best = max(best, score)
    return best


def render_markdown(payload):
    lines = [
        "# Monitoring Candidate Replay Gap Report",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- candidate_month_count: `{payload['candidate_month_count']}`",
        f"- candidate_replay_count: `{payload['candidate_replay_count']}`",
        f"- uncovered_buy_months: `{payload['uncovered_buy_months']}`",
        f"- uncovered_hostile_months: `{payload['uncovered_hostile_months']}`",
        "",
        "## Candidate Rows",
        "",
    ]

    if not payload.get("candidate_rows"):
        lines.append("- none")
    else:
        for row in payload["candidate_rows"]:
            lines.append(
                f"- `{row['month_key']}`: replay `{row['replay_id']}`, priority `{row['priority_score']}`, "
                f"buy_covered `{row['buy_covered']}`, hostile_covered `{row['hostile_covered']}`, "
                f"hostile_candidate `{row['hostile_candidate']}`"
            )

    lines.extend(["", "## Gaps", ""])
    if not payload.get("gap_rows"):
        lines.append("- none")
    else:
        for row in payload["gap_rows"]:
            lines.append(
                f"- `{row['month_key']}`: replay `{row['replay_id']}`, "
                f"missing_buy `{row['missing_buy']}`, missing_hostile `{row['missing_hostile']}`"
            )

    return "\n".join(lines) + "\n"


def build_gap_report():
    buy_monitor = load_json(BUY_MONITOR_PATH)
    hostile_monitor = load_json(HOSTILE_MONITOR_PATH)

    buy_ids = set(buy_monitor.get("replay_ids") or [])
    hostile_ids = set(hostile_monitor.get("replay_ids") or [])

    candidate_map = {}
    for name in sorted(os.listdir(REPLAYS_DIR)):
        path = os.path.join(REPLAYS_DIR, name)
        if not os.path.isdir(path):
            continue
        if not _looks_like_candidate(name):
            continue
        if not _has_replay_summary(name):
            continue
        month_key = _month_key(name)
        hostile_candidate = _hostile_candidate(month_key)
        row = {
            "month_key": month_key,
            "replay_id": name,
            "buy_covered": name in buy_ids,
            "hostile_covered": name in hostile_ids,
            "hostile_candidate": hostile_candidate,
            "priority_score": _candidate_priority(name),
        }
        current = candidate_map.get(month_key)
        if current is None or row["priority_score"] > current["priority_score"] or (
            row["priority_score"] == current["priority_score"] and row["replay_id"] > current["replay_id"]
        ):
            candidate_map[month_key] = row

    candidate_rows = [candidate_map[key] for key in sorted(candidate_map)]

    gap_rows = []
    for row in candidate_rows:
        missing_buy = not row["buy_covered"]
        missing_hostile = row["hostile_candidate"] and not row["hostile_covered"]
        if missing_buy or missing_hostile:
            gap_rows.append({
                **row,
                "missing_buy": missing_buy,
                "missing_hostile": missing_hostile,
            })

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "candidate_month_count": len({row["month_key"] for row in candidate_rows}),
        "candidate_replay_count": len(candidate_rows),
        "uncovered_buy_months": len({row["month_key"] for row in gap_rows if row["missing_buy"]}),
        "uncovered_hostile_months": len({row["month_key"] for row in gap_rows if row["missing_hostile"]}),
        "candidate_rows": candidate_rows,
        "gap_rows": gap_rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_candidate_replay_gap_report_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_candidate_replay_gap_report_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_candidate_replay_gap_report_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_candidate_replay_gap_report_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_gap_report()
    print(json.dumps({
        "candidate_replay_count": payload["candidate_replay_count"],
        "uncovered_buy_months": payload["uncovered_buy_months"],
        "uncovered_hostile_months": payload["uncovered_hostile_months"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
