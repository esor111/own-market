"""
Aggregate multiple champion-vs-challenger comparison files into one trust summary.

Usage:
    python replay_challenger_validation_summary.py COMPARE_JSON [COMPARE_JSON ...]
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import VALIDATION_DIR


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")


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


def _verdict_quality(verdict):
    scores = {
        "good_call": 2,
        "good_avoid": 2,
        "mixed_call": 1,
        "neutral_avoid": 1,
        "missed_opportunity": 0,
        "bad_call": 0,
        "unscored": 0,
    }
    return scores.get(verdict, 0)


def _case_outcome_direction(champion_verdict, challenger_verdict):
    champion_score = _verdict_quality(champion_verdict)
    challenger_score = _verdict_quality(challenger_verdict)
    if challenger_score > champion_score:
        return "improved"
    if challenger_score < champion_score:
        return "worsened"
    if challenger_verdict != champion_verdict:
        return "changed_same_quality"
    return "unchanged_quality"


def _build_markdown(payload):
    lines = [
        "# Replay Challenger Validation Summary",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- comparison_count: `{payload['comparison_count']}`",
        f"- total_cases_seen: `{payload['total_cases_seen']}`",
        f"- changed_case_count: `{payload['changed_case_count']}`",
        f"- changed_case_rate: `{payload['changed_case_rate']}`",
        f"- outcome_directions: `{payload['outcome_directions']}`",
        "",
        "## Net Deltas",
        f"- action_delta: `{payload['net_action_delta']}`",
        f"- verdict_delta: `{payload['net_verdict_delta']}`",
        "",
        "## Changed Cases",
    ]
    if not payload["changed_cases"]:
        lines.append("- none")
    else:
        for item in payload["changed_cases"]:
            lines.extend([
                f"### {item['session_id']}",
                f"- month_label: `{item['month_label']}`",
                f"- symbol: `{item['symbol']}`",
                f"- sector_name: `{item['sector_name']}`",
                f"- champion_action: `{item['champion_action']}`",
                f"- challenger_action: `{item['challenger_action']}`",
                f"- champion_verdict: `{item['champion_verdict']}`",
                f"- challenger_verdict: `{item['challenger_verdict']}`",
                f"- outcome_direction: `{item['outcome_direction']}`",
                f"- guidance_action_change: `{item['guidance_action_change']}`",
                "",
            ])
    return "\n".join(lines).strip() + "\n"


def _summary_label(compare_paths):
    labels = []
    for path in compare_paths:
        name = os.path.basename(path)
        if "__vs__" not in name:
            continue
        right_side = name.split("__vs__", 1)[1]
        challenger_label = right_side.replace("__replay_champion_challenger_compare_v1.json", "")
        labels.append(challenger_label)
    if not labels:
        return "challenger_validation"
    tokenized = [label.split("_") for label in labels]
    first_tokens = tokenized[0]
    common_tokens = []
    for token in first_tokens:
        if all(token in items for items in tokenized[1:]):
            common_tokens.append(token)
    common = "_".join(common_tokens).strip("_-")
    return common or labels[0]


def build_validation_summary(compare_paths):
    action_delta = Counter()
    verdict_delta = Counter()
    outcome_directions = Counter()
    changed_cases = []
    total_cases_seen = 0

    for path in compare_paths:
        payload = load_json(path)
        total_cases_seen += sum((payload.get("champion") or {}).get("action_counts", {}).values())
        action_delta.update(payload.get("differences", {}).get("action_delta") or {})
        verdict_delta.update(payload.get("differences", {}).get("verdict_delta") or {})

        for item in payload.get("differences", {}).get("changed_cases", []):
            direction = _case_outcome_direction(item.get("champion_verdict"), item.get("challenger_verdict"))
            outcome_directions.update([direction])
            changed_cases.append({
                **item,
                "month_label": (payload.get("champion_replay_id") or "").split("__")[0],
                "outcome_direction": direction,
            })

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "comparison_count": len(compare_paths),
        "source_compare_paths": compare_paths,
        "total_cases_seen": total_cases_seen,
        "changed_case_count": len(changed_cases),
        "changed_case_rate": round(len(changed_cases) / total_cases_seen, 4) if total_cases_seen else None,
        "outcome_directions": dict(outcome_directions),
        "net_action_delta": dict(action_delta),
        "net_verdict_delta": dict(verdict_delta),
        "changed_cases": changed_cases,
    }

    label = _summary_label(compare_paths)
    dated_json = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__{label}__replay_challenger_validation_summary_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, f"latest__{label}__replay_challenger_validation_summary_v1.json")
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")
    save_json(dated_json, summary)
    save_json(latest_json, summary)
    markdown = _build_markdown(summary)
    save_text(dated_md, markdown)
    save_text(latest_md, markdown)
    return dated_json, latest_json, dated_md, latest_md, summary


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_challenger_validation_summary.py COMPARE_JSON [COMPARE_JSON ...]")
        sys.exit(1)

    dated_json, latest_json, dated_md, latest_md, summary = build_validation_summary(sys.argv[1:])
    print(json.dumps({
        "dated_json": dated_json,
        "latest_json": latest_json,
        "dated_md": dated_md,
        "latest_md": latest_md,
        "changed_case_count": summary["changed_case_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
