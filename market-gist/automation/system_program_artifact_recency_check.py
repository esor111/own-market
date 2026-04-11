"""
Check whether the top-level whole-project artifacts were rebuilt in the same run window.

Usage:
    python system_program_artifact_recency_check.py
"""
import json
import os
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
TOP_LEVEL_ARTIFACTS = {
    "system_refresh_freshness": "latest__system_program_refresh_freshness_gate_v1.json",
    "system_status": "latest__system_program_status_v1.json",
    "system_operating_state": "latest__system_program_operating_state_v1.json",
    "system_decision_gate": "latest__system_program_decision_gate_v1.json",
    "system_consistency": "latest__system_program_status_consistency_check_v1.json",
}
MAX_ALLOWED_SPREAD_SECONDS = 120.0


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def render_markdown(payload):
    lines = [
        "# System Program Artifact Recency Check",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- overall_status: `{payload['overall_status']}`",
        f"- max_built_at_spread_seconds: `{payload['max_built_at_spread_seconds']}`",
        "",
        "## Artifact Built Times",
        "",
    ]
    for row in payload.get("artifact_times") or []:
        lines.append(f"- `{row['name']}`: `{row['built_at']}`")

    lines.extend(["", "## Current Action", ""])
    for item in payload.get("current_action") or []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_system_program_artifact_recency_check():
    artifact_times = []
    timestamps = []

    for name, filename in TOP_LEVEL_ARTIFACTS.items():
        path = os.path.join(LEARNING_REVIEWS_DIR, filename)
        payload = load_json(path)
        built_at = payload.get("built_at")
        built_dt = datetime.fromisoformat(built_at)
        timestamps.append(built_dt)
        artifact_times.append({"name": name, "built_at": built_at})

    spread_seconds = 0.0
    if timestamps:
        spread_seconds = (max(timestamps) - min(timestamps)).total_seconds()

    overall_status = "pass" if spread_seconds <= MAX_ALLOWED_SPREAD_SECONDS else "fail"
    current_action = (
        [
            "the core top-level whole-project trust artifacts were rebuilt close enough together to trust the current handoff bundle",
            "use the final gate first, then the executive status as the shortest human-readable read",
        ]
        if overall_status == "pass"
        else [
            "rerun python run_system_program_cycle.py",
            "do not trust the top-level packet until the recency spread comes back inside the allowed window",
        ]
    )

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "overall_status": overall_status,
        "max_built_at_spread_seconds": round(spread_seconds, 3),
        "max_allowed_spread_seconds": MAX_ALLOWED_SPREAD_SECONDS,
        "artifact_times": artifact_times,
        "current_action": current_action,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__system_program_artifact_recency_check_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR, "latest__system_program_artifact_recency_check_v1.json"
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_system_program_artifact_recency_check()
    print(
        json.dumps(
            {
                "overall_status": payload["overall_status"],
                "max_built_at_spread_seconds": payload["max_built_at_spread_seconds"],
                "latest_json_path": latest_json_path,
                "latest_md_path": latest_md_path,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
