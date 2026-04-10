"""
Check whether the monitoring stack actually needs a new core refresh.

This prevents unnecessary heavy reruns when no replay inputs changed.

Usage:
    python monitoring_refresh_freshness_gate.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import REPLAYS_DIR, VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
HOSTILE_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_hostile_window_monitor_v1.json")
BUY_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_buy_side_pattern_monitor_v1.json")
CYCLE_SUMMARY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_summary_v1.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _iso_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).isoformat()


def _replay_dir_timestamp(replay_id):
    replay_dir = os.path.join(REPLAYS_DIR, replay_id)
    if not os.path.isdir(replay_dir):
        return None
    return os.path.getmtime(replay_dir)


def _latest_replay_dirs(limit=10):
    rows = []
    if not os.path.isdir(REPLAYS_DIR):
        return rows
    for name in os.listdir(REPLAYS_DIR):
        path = os.path.join(REPLAYS_DIR, name)
        if not os.path.isdir(path):
            continue
        rows.append({
            "replay_id": name,
            "last_modified_at": _iso_from_timestamp(os.path.getmtime(path)),
            "last_modified_ts": os.path.getmtime(path),
        })
    rows.sort(key=lambda item: item["last_modified_ts"], reverse=True)
    return rows[:limit]


def render_markdown(payload):
    lines = [
        "# Monitoring Refresh Freshness Gate",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- refresh_needed: `{payload['refresh_needed']}`",
        f"- latest_core_built_at: `{payload['latest_core_built_at']}`",
        "",
        "## Why",
        "",
    ]
    for reason in payload.get("reasons") or []:
        lines.append(f"- {reason}")

    lines.extend(["", "## Used Replay Inputs", ""])
    for row in payload.get("used_replay_inputs") or []:
        lines.append(
            f"- `{row['replay_id']}`: replay_last_modified_at `{row['replay_last_modified_at']}`, "
            f"newer_than_core `{row['newer_than_core']}`"
        )

    lines.extend(["", "## Newer Replay Directories", ""])
    if not payload.get("newer_replay_dirs"):
        lines.append("- none")
    else:
        for row in payload["newer_replay_dirs"]:
            lines.append(f"- `{row['replay_id']}`: `{row['last_modified_at']}`")

    lines.extend(["", "## Current Action", ""])
    for action in payload.get("current_action") or []:
        lines.append(f"- {action}")
    return "\n".join(lines) + "\n"


def build_freshness_gate():
    hostile_monitor = load_json(HOSTILE_MONITOR_PATH)
    buy_monitor = load_json(BUY_MONITOR_PATH)
    cycle_summary = load_json(CYCLE_SUMMARY_PATH)

    core_timestamp = max(
        os.path.getmtime(HOSTILE_MONITOR_PATH),
        os.path.getmtime(BUY_MONITOR_PATH),
        os.path.getmtime(CYCLE_SUMMARY_PATH),
    )

    used_ids = []
    seen = set()
    for replay_id in (hostile_monitor.get("replay_ids") or []) + (buy_monitor.get("replay_ids") or []):
        if replay_id in seen:
            continue
        seen.add(replay_id)
        replay_ts = _replay_dir_timestamp(replay_id)
        used_ids.append({
            "replay_id": replay_id,
            "replay_last_modified_at": _iso_from_timestamp(replay_ts) if replay_ts is not None else None,
            "newer_than_core": bool(replay_ts and replay_ts > core_timestamp),
        })

    latest_dirs = _latest_replay_dirs(limit=20)
    newer_replay_dirs = [
        {"replay_id": row["replay_id"], "last_modified_at": row["last_modified_at"]}
        for row in latest_dirs
        if row["last_modified_ts"] > core_timestamp and row["replay_id"] not in seen
    ]

    used_inputs_newer = [row for row in used_ids if row["newer_than_core"]]
    refresh_needed = bool(used_inputs_newer or newer_replay_dirs)

    reasons = []
    current_action = []
    if used_inputs_newer:
        reasons.append("one or more replay inputs already used by the monitors were modified after the current core build")
    if newer_replay_dirs:
        reasons.append("new replay directories exist that are newer than the current core build")
    if not reasons:
        reasons.append("no monitored replay input is newer than the current core build")
        reasons.append("no newer replay directory outside the current monitor inputs was found")

    if refresh_needed:
        current_action.extend([
            "run python refresh_monitoring_stack.py --stage core",
            "then run python refresh_monitoring_stack.py --stage tail",
        ])
    else:
        current_action.extend([
            "skip core refresh for now",
            "wait for a genuinely newer replay window before rerunning the heavy monitoring stack",
        ])

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "current_decision": cycle_summary.get("decision"),
        "latest_core_built_at": _iso_from_timestamp(core_timestamp),
        "refresh_needed": refresh_needed,
        "reasons": reasons,
        "used_replay_inputs": used_ids,
        "newer_replay_dirs": newer_replay_dirs,
        "current_action": current_action,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_refresh_freshness_gate_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_refresh_freshness_gate_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_refresh_freshness_gate_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_refresh_freshness_gate_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_freshness_gate()
    print(json.dumps({
        "refresh_needed": payload["refresh_needed"],
        "latest_core_built_at": payload["latest_core_built_at"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
