"""
Turn the latest next-open entry artifacts into an explicit next-step decision.

Usage:
    python entry_next_open_decision_gate.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
FRESHNESS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_refresh_freshness_gate_v1.json")
EXECUTIVE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_executive_status_v1.json")
EXACT_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_exact_texture_monitor_v1.json")
FUTURE_COVERAGE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_future_coverage_report_v1.json")
NEAR_MISS_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_future_near_miss_report_v1.json")
CONSISTENCY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__entry_next_open_artifact_consistency_check_v1.json")


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


def render_markdown(payload):
    lines = [
        "# Entry Next-Open Decision Gate",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- decision: `{payload['decision']}`",
        "",
        "## Why",
        "",
    ]
    for item in payload.get("reasons") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Current Action", ""])
    for item in payload.get("current_action") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Current Signals", ""])
    lines.append(f"- refresh_needed: `{payload['signals']['refresh_needed']}`")
    lines.append(f"- consistency_status: `{payload['signals']['consistency_status']}`")
    lines.append(f"- lane_status: `{payload['signals']['lane_status']}`")
    lines.append(f"- future_signal_state: `{payload['signals']['future_signal_state']}`")
    lines.append(f"- future_coverage_state: `{payload['signals']['future_coverage_state']}`")
    lines.append(f"- future_near_miss_state: `{payload['signals']['future_near_miss_state']}`")
    return "\n".join(lines) + "\n"


def build_entry_next_open_decision_gate():
    freshness = load_json(FRESHNESS_PATH)
    executive = load_json(EXECUTIVE_PATH)
    exact_monitor = load_json(EXACT_MONITOR_PATH)
    future_coverage = load_json(FUTURE_COVERAGE_PATH)
    near_miss = load_json(NEAR_MISS_PATH)
    consistency = load_json(CONSISTENCY_PATH)

    refresh_needed = bool(freshness.get("refresh_needed"))
    consistency_status = consistency.get("overall_status")
    lane_status = executive.get("current_entry_lane_status")
    future_signal_state = exact_monitor.get("future_signal_state")
    future_coverage_state = future_coverage.get("coverage_state")
    future_near_miss_state = near_miss.get("near_miss_state")

    decision = "keep_guarded"
    reasons = [
        "the entry lane is still promising but not ready",
        "future exact-texture evidence has not repeated yet",
    ]
    current_action = [
        "keep Risk Engine v1 frozen",
        "keep the commercial-bank next-open texture guarded",
        "wait for genuinely newer replay windows before changing the branch status",
    ]

    if consistency_status != "pass":
        decision = "repair_artifacts"
        reasons = [
            "the entry handoff bundle is not internally aligned",
        ]
        current_action = [
            "rebuild the entry next-open stack",
            "do not trust the current packet until consistency passes",
        ]
    elif future_signal_state == "strengthened":
        decision = "open_future_validation_review"
        reasons = [
            "future exact-texture evidence is now strengthening the candidate",
        ]
        current_action = [
            "run a fresh untouched validation review on the new exact-texture matches",
            "do not promote directly from the gate alone",
        ]
    elif future_signal_state == "weakened":
        decision = "degrade_candidate"
        reasons = [
            "future exact-texture evidence is weakening the candidate",
        ]
        current_action = [
            "keep the branch unpromoted",
            "re-check whether the commercial-bank texture was regime-specific",
        ]
    else:
        if future_coverage_state == "future_target_slice_present_but_exact_absent":
            reasons.append("future months are producing the target slice without reproducing the exact texture")
        if future_near_miss_state == "future_target_near_misses_without_exact_repeat":
            reasons.append("future target-slice near misses are currently negative, which argues against premature promotion")
        if refresh_needed:
            current_action = [
                "run the refreshed entry next-open stack first",
                "then reread the decision gate before taking any branch action",
            ]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "decision": decision,
        "reasons": reasons,
        "current_action": current_action,
        "signals": {
            "refresh_needed": refresh_needed,
            "consistency_status": consistency_status,
            "lane_status": lane_status,
            "future_signal_state": future_signal_state,
            "future_coverage_state": future_coverage_state,
            "future_near_miss_state": future_near_miss_state,
        },
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_decision_gate_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_decision_gate_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_next_open_decision_gate()
    print(json.dumps({
        "decision": payload["decision"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
