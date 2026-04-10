"""
Turn the latest monitoring diff into an explicit next-step decision.

This keeps the frozen-monitoring phase operational:
- keep champion frozen when nothing meaningful changed
- open a narrow research branch only when a monitored slice crosses a clear gate

Usage:
    python monitoring_decision_gate.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DIFF_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_watchlist_diff_v1.json")

HOSTILE_EMERGENT_FAILURE_COUNT_MIN = 5
HOSTILE_EMERGENT_FAILURE_RATE_MIN = 0.6
BUY_POSITIVE_EMERGENT_SUCCESS_COUNT_MIN = 5
BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN = 0.5
BUY_WARNING_EMERGENT_FAILURE_COUNT_MIN = 8
BUY_WARNING_EMERGENT_FAILURE_RATE_MIN = 0.8


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


def _hostile_emergent_candidates(rows):
    candidates = []
    for row in rows:
        if (row.get("failure_count") or 0) < HOSTILE_EMERGENT_FAILURE_COUNT_MIN:
            continue
        if (row.get("failure_rate") or 0) < HOSTILE_EMERGENT_FAILURE_RATE_MIN:
            continue
        candidates.append(row)
    return candidates


def _buy_positive_emergent_candidates(rows):
    candidates = []
    for row in rows:
        if (row.get("success_count") or 0) < BUY_POSITIVE_EMERGENT_SUCCESS_COUNT_MIN:
            continue
        if (row.get("success_rate") or 0) < BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN:
            continue
        candidates.append(row)
    return candidates


def _buy_warning_emergent_candidates(rows):
    candidates = []
    for row in rows:
        success_rate = row.get("success_rate")
        failure_rate = row.get("failure_rate")
        if failure_rate is None and success_rate is not None:
            failure_rate = round(1 - success_rate, 4)
        if (row.get("failure_count") or 0) < BUY_WARNING_EMERGENT_FAILURE_COUNT_MIN:
            continue
        if (failure_rate or 0) < BUY_WARNING_EMERGENT_FAILURE_RATE_MIN:
            continue
        candidates.append({**row, "failure_rate": failure_rate})
    return candidates


def render_markdown(payload):
    lines = [
        "# Monitoring Decision Gate",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- decision: `{payload['decision']}`",
        "",
        "## Why",
        "",
    ]
    for reason in payload.get("reasons") or []:
        lines.append(f"- {reason}")

    lines.extend(["", "## Trigger Summary", ""])
    lines.append(f"- hostile_warning_worsened: `{payload['trigger_summary']['hostile_warning_worsened']}`")
    lines.append(f"- hostile_secondary_worsened: `{payload['trigger_summary']['hostile_secondary_worsened']}`")
    lines.append(f"- hostile_emergent_candidates: `{payload['trigger_summary']['hostile_emergent_candidates']}`")
    lines.append(f"- buy_positive_worsened: `{payload['trigger_summary']['buy_positive_worsened']}`")
    lines.append(f"- buy_positive_improved: `{payload['trigger_summary']['buy_positive_improved']}`")
    lines.append(f"- buy_positive_emergent_candidates: `{payload['trigger_summary']['buy_positive_emergent_candidates']}`")
    lines.append(f"- buy_warning_worsened: `{payload['trigger_summary']['buy_warning_worsened']}`")
    lines.append(f"- buy_warning_emergent_candidates: `{payload['trigger_summary']['buy_warning_emergent_candidates']}`")

    if payload.get("candidate_slices"):
        lines.extend(["", "## Candidate Slices", ""])
        for row in payload["candidate_slices"]:
            lines.append(
                f"- `{row['category']}` -> `{row['slice']}`: count `{row.get('count')}`, "
                f"success_count `{row.get('success_count')}`, failure_count `{row.get('failure_count')}`, "
                f"success_rate `{row.get('success_rate')}`, failure_rate `{row.get('failure_rate')}`"
            )

    lines.extend([
        "",
        "## Current Action",
        "",
    ])
    for action in payload.get("current_action") or []:
        lines.append(f"- {action}")
    return "\n".join(lines) + "\n"


def build_decision():
    diff = load_json(DIFF_PATH)

    hostile_warning_worsened = diff["hostile"]["warning_summary"]["worsened"]
    hostile_secondary_worsened = diff["hostile"]["secondary_summary"]["worsened"]
    hostile_emergent_candidates = _hostile_emergent_candidates(diff["hostile"]["emergent_warning_slices"])

    buy_positive_worsened = diff["buy_side"]["positive_summary"]["worsened"]
    buy_positive_improved = diff["buy_side"]["positive_summary"]["improved"]
    buy_positive_emergent_candidates = _buy_positive_emergent_candidates(diff["buy_side"]["emergent_positive_slices"])

    buy_warning_worsened = diff["buy_side"]["warning_summary"]["worsened"]
    buy_warning_emergent_candidates = _buy_warning_emergent_candidates(diff["buy_side"]["emergent_warning_slices"])

    decision = "keep_frozen"
    reasons = [
        "no monitored hostile warning slice worsened",
        "no monitored buy-side positive slice worsened",
        "no emergent slice crossed the branch-opening thresholds",
    ]
    current_action = [
        "champion stays frozen",
        "run refresh_monitoring_stack.py on the next replay refresh",
        "only open research if this gate stops returning keep_frozen",
    ]
    candidate_slices = []

    if hostile_warning_worsened or hostile_secondary_worsened or hostile_emergent_candidates:
        decision = "open_hostile_research"
        reasons = []
        current_action = [
            "keep the champion frozen",
            "open one hostile-side research branch only for the flagged slice set",
        ]
        if hostile_warning_worsened:
            reasons.append("one or more hostile warning slices worsened against the frozen baseline")
        if hostile_secondary_worsened:
            reasons.append("one or more hostile secondary-watch slices worsened against the frozen baseline")
        if hostile_emergent_candidates:
            reasons.append("a new hostile emergent slice crossed the failure-count and failure-rate gate")
            for row in hostile_emergent_candidates:
                candidate_slices.append({"category": "hostile_emergent", **row})

    elif buy_positive_worsened or buy_positive_improved or buy_positive_emergent_candidates or buy_warning_worsened or buy_warning_emergent_candidates:
        decision = "open_buy_side_research"
        reasons = []
        current_action = [
            "keep the champion frozen",
            "open one buy-side research branch only for the flagged slice set",
        ]
        if buy_positive_worsened:
            reasons.append("a monitored buy-side positive slice worsened materially")
        if buy_positive_improved:
            reasons.append("a monitored buy-side positive slice improved materially")
        if buy_positive_emergent_candidates:
            reasons.append("a new buy-side positive slice crossed the success-count and success-rate gate")
            for row in buy_positive_emergent_candidates:
                candidate_slices.append({"category": "buy_positive_emergent", **row})
        if buy_warning_worsened:
            reasons.append("a monitored buy-side warning slice worsened materially")
        if buy_warning_emergent_candidates:
            reasons.append("a new buy-side warning slice crossed the failure-count and failure-rate gate")
            for row in buy_warning_emergent_candidates:
                candidate_slices.append({"category": "buy_warning_emergent", **row})

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "diff_path": DIFF_PATH,
        "decision": decision,
        "reasons": reasons,
        "trigger_summary": {
            "hostile_warning_worsened": hostile_warning_worsened,
            "hostile_secondary_worsened": hostile_secondary_worsened,
            "hostile_emergent_candidates": len(hostile_emergent_candidates),
            "buy_positive_worsened": buy_positive_worsened,
            "buy_positive_improved": buy_positive_improved,
            "buy_positive_emergent_candidates": len(buy_positive_emergent_candidates),
            "buy_warning_worsened": buy_warning_worsened,
            "buy_warning_emergent_candidates": len(buy_warning_emergent_candidates),
        },
        "candidate_slices": candidate_slices,
        "current_action": current_action,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_decision_gate_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_decision_gate_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__monitoring_decision_gate_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_decision_gate_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_decision()
    print(json.dumps({
        "decision": payload["decision"],
        "reasons": payload["reasons"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
