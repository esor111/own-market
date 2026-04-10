"""
Triage uncovered monitoring candidate gaps into actionable versus rerun backlog.

Usage:
    python monitoring_gap_triage.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
GAP_REPORT_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_candidate_replay_gap_report_v1.json")

INCLUDE_NOW_TOKENS = (
    "currentchampion",
    "postbankwatchpromotion",
    "promotedchampion",
)


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


def _triage_row(row):
    replay_id = (row.get("replay_id") or "").lower()
    if any(token in replay_id for token in INCLUDE_NOW_TOKENS):
        return "include_now"
    return "needs_current_champion_rerun"


def render_markdown(payload):
    lines = [
        "# Monitoring Gap Triage",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- total_gap_rows: `{payload['total_gap_rows']}`",
        f"- include_now_count: `{payload['include_now_count']}`",
        f"- rerun_backlog_count: `{payload['rerun_backlog_count']}`",
        "",
        "## Include Now",
        "",
    ]

    if not payload.get("include_now_rows"):
        lines.append("- none")
    else:
        for row in payload["include_now_rows"]:
            lines.append(f"- `{row['month_key']}`: `{row['replay_id']}`")

    lines.extend(["", "## Rerun Backlog", ""])
    if not payload.get("rerun_backlog_rows"):
        lines.append("- none")
    else:
        for row in payload["rerun_backlog_rows"]:
            lines.append(f"- `{row['month_key']}`: `{row['replay_id']}`")

    return "\n".join(lines) + "\n"


def build_gap_triage():
    gap_report = load_json(GAP_REPORT_PATH)

    include_now_rows = []
    rerun_backlog_rows = []

    for row in gap_report.get("gap_rows") or []:
        triage = _triage_row(row)
        triaged = {**row, "triage": triage}
        if triage == "include_now":
            include_now_rows.append(triaged)
        else:
            rerun_backlog_rows.append(triaged)

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "total_gap_rows": len((gap_report.get("gap_rows") or [])),
        "include_now_count": len(include_now_rows),
        "rerun_backlog_count": len(rerun_backlog_rows),
        "include_now_rows": include_now_rows,
        "rerun_backlog_rows": rerun_backlog_rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_gap_triage_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_gap_triage_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_gap_triage_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_gap_triage_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_gap_triage()
    print(json.dumps({
        "total_gap_rows": payload["total_gap_rows"],
        "include_now_count": payload["include_now_count"],
        "rerun_backlog_count": payload["rerun_backlog_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
