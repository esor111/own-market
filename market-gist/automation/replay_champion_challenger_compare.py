"""
Compare two replay runs and save a reusable champion-vs-challenger summary.

Usage:
    python replay_champion_challenger_compare.py CHAMPION_REPLAY_ID CHALLENGER_REPLAY_ID
"""
import json
import os
import sys
from datetime import datetime

from config import VALIDATION_DIR, REPLAYS_DIR


COMPARE_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")


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


def _load_replay_bundle(replay_id):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    summary = load_json(os.path.join(replay_root, "summaries", "latest__replay_summary_v1.json"))
    review = load_json(os.path.join(replay_root, "summaries", "latest__replay_review_summary_v1.json"))
    return summary, review


def _count_action_changes(records):
    counts = {}
    for item in records:
        key = (
            item.get("calendar_confidence_guidance_action_change")
            or item.get("liquidity_guidance_action_change")
            or item.get("bank_exhaustion_guidance_action_change")
            or item.get("commercial_bank_watch_caution_guidance_action_change")
            or item.get("hydropower_buy_caution_guidance_action_change")
            or item.get("guidance_action_change")
            or "none"
        )
        counts[key] = counts.get(key, 0) + 1
    return counts


def _changed_cases(champion_summary, challenger_summary):
    champion_map = {item["session_id"]: item for item in champion_summary.get("records", [])}
    rows = []
    for item in challenger_summary.get("records", []):
        base_item = champion_map.get(item["session_id"])
        if not base_item:
            continue
        champion_action = base_item.get("action")
        challenger_action = item.get("action")
        champion_guidance_change = base_item.get("guidance_action_change")
        challenger_guidance_change = item.get("guidance_action_change")
        champion_calendar_change = base_item.get("calendar_confidence_guidance_action_change")
        challenger_calendar_change = item.get("calendar_confidence_guidance_action_change")
        champion_liquidity_change = base_item.get("liquidity_guidance_action_change")
        challenger_liquidity_change = item.get("liquidity_guidance_action_change")
        champion_bank_exhaustion_change = base_item.get("bank_exhaustion_guidance_action_change")
        challenger_bank_exhaustion_change = item.get("bank_exhaustion_guidance_action_change")
        champion_commercial_bank_watch_change = base_item.get("commercial_bank_watch_caution_guidance_action_change")
        challenger_commercial_bank_watch_change = item.get("commercial_bank_watch_caution_guidance_action_change")
        champion_hydropower_buy_change = base_item.get("hydropower_buy_caution_guidance_action_change")
        challenger_hydropower_buy_change = item.get("hydropower_buy_caution_guidance_action_change")

        if (
            challenger_action != champion_action
            or challenger_guidance_change != champion_guidance_change
            or challenger_calendar_change != champion_calendar_change
            or challenger_liquidity_change != champion_liquidity_change
            or challenger_bank_exhaustion_change != champion_bank_exhaustion_change
            or challenger_commercial_bank_watch_change != champion_commercial_bank_watch_change
            or challenger_hydropower_buy_change != champion_hydropower_buy_change
        ):
            rows.append({
                "session_id": item["session_id"],
                "symbol": item.get("symbol"),
                "session_date": item.get("session_date"),
                "sector_name": item.get("sector_name"),
                "champion_action": champion_action,
                "challenger_action": challenger_action,
                "champion_verdict": base_item.get("comparison_verdict"),
                "challenger_verdict": item.get("comparison_verdict"),
                "return_10d_pct": item.get("return_10d_pct"),
                "leadership_label": item.get("leadership_label"),
                "alignment_label": item.get("alignment_label"),
                "calendar_phase": item.get("calendar_phase"),
                "event_state": item.get("event_state"),
                "guidance_adjustment_total": item.get("guidance_adjustment_total"),
                "guidance_action_change": item.get("guidance_action_change") or item.get("liquidity_guidance_action_change") or item.get("bank_exhaustion_guidance_action_change") or item.get("commercial_bank_watch_caution_guidance_action_change"),
                "calendar_confidence_guidance_action_change": item.get("calendar_confidence_guidance_action_change"),
                "liquidity_guidance_action_change": item.get("liquidity_guidance_action_change"),
                "bank_exhaustion_guidance_action_change": item.get("bank_exhaustion_guidance_action_change"),
                "commercial_bank_watch_caution_guidance_action_change": item.get("commercial_bank_watch_caution_guidance_action_change"),
                "hydropower_buy_caution_guidance_action_change": item.get("hydropower_buy_caution_guidance_action_change"),
                "liquidity_trigger_count": item.get("liquidity_trigger_count"),
            })
    return rows


def _build_markdown(payload):
    lines = [
        "# Replay Champion vs Challenger Comparison",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- champion_replay_id: `{payload['champion_replay_id']}`",
        f"- challenger_replay_id: `{payload['challenger_replay_id']}`",
        "",
        "## Champion",
        f"- action_counts: `{payload['champion']['action_counts']}`",
        f"- verdict_counts: `{payload['champion']['verdict_counts']}`",
        f"- average_return_10d_pct: `{payload['champion']['average_return_10d_pct']}`",
        "",
        "## Challenger",
        f"- action_counts: `{payload['challenger']['action_counts']}`",
        f"- verdict_counts: `{payload['challenger']['verdict_counts']}`",
        f"- average_return_10d_pct: `{payload['challenger']['average_return_10d_pct']}`",
        f"- action_changes: `{payload['challenger']['action_changes']}`",
        "",
        "## Net Differences",
        f"- changed_case_count: `{payload['differences']['changed_case_count']}`",
        f"- verdict_delta: `{payload['differences']['verdict_delta']}`",
        f"- action_delta: `{payload['differences']['action_delta']}`",
        "",
        "## Changed Cases",
    ]
    if not payload["differences"]["changed_cases"]:
        lines.append("- none")
    else:
        for item in payload["differences"]["changed_cases"]:
            lines.extend([
                f"### {item['session_id']}",
                f"- sector_name: `{item['sector_name']}`",
                f"- champion_action: `{item['champion_action']}`",
                f"- challenger_action: `{item['challenger_action']}`",
                f"- champion_verdict: `{item['champion_verdict']}`",
                f"- challenger_verdict: `{item['challenger_verdict']}`",
                f"- return_10d_pct: `{item['return_10d_pct']}`",
                f"- leadership_label: `{item['leadership_label']}`",
                f"- alignment_label: `{item['alignment_label']}`",
                f"- calendar_phase: `{item.get('calendar_phase')}`",
                f"- event_state: `{item.get('event_state')}`",
                f"- guidance_adjustment_total: `{item['guidance_adjustment_total']}`",
                f"- guidance_action_change: `{item['guidance_action_change']}`",
                f"- calendar_confidence_guidance_action_change: `{item.get('calendar_confidence_guidance_action_change')}`",
                f"- liquidity_guidance_action_change: `{item.get('liquidity_guidance_action_change')}`",
                f"- bank_exhaustion_guidance_action_change: `{item.get('bank_exhaustion_guidance_action_change')}`",
                f"- commercial_bank_watch_caution_guidance_action_change: `{item.get('commercial_bank_watch_caution_guidance_action_change')}`",
                f"- hydropower_buy_caution_guidance_action_change: `{item.get('hydropower_buy_caution_guidance_action_change')}`",
                f"- liquidity_trigger_count: `{item.get('liquidity_trigger_count')}`",
                "",
            ])
    return "\n".join(lines).strip() + "\n"


def _delta_counts(champion_counts, challenger_counts):
    keys = sorted(set(champion_counts) | set(challenger_counts))
    return {
        key: int((challenger_counts.get(key) or 0) - (champion_counts.get(key) or 0))
        for key in keys
        if int((challenger_counts.get(key) or 0) - (champion_counts.get(key) or 0)) != 0
    }


def _comparison_label(champion_replay_id, challenger_replay_id):
    champion_bits = champion_replay_id.split("__")
    challenger_bits = challenger_replay_id.split("__")
    if len(champion_bits) >= 3 and len(challenger_bits) >= 3:
        return f"{champion_bits[0]}__{champion_bits[2]}__vs__{challenger_bits[2]}"
    return "replay_compare"


def compare_replays(champion_replay_id, challenger_replay_id):
    champion_summary, champion_review = _load_replay_bundle(champion_replay_id)
    challenger_summary, challenger_review = _load_replay_bundle(challenger_replay_id)
    changed_cases = _changed_cases(champion_summary, challenger_summary)

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "champion_replay_id": champion_replay_id,
        "challenger_replay_id": challenger_replay_id,
        "champion": {
            "action_counts": champion_summary.get("action_counts") or {},
            "verdict_counts": champion_summary.get("comparison_verdict_counts") or {},
            "average_return_10d_pct": champion_summary.get("average_return_10d_pct"),
            "top_proposals": (champion_review.get("top_proposals") or [])[:5],
        },
        "challenger": {
            "action_counts": challenger_summary.get("action_counts") or {},
            "verdict_counts": challenger_summary.get("comparison_verdict_counts") or {},
            "average_return_10d_pct": challenger_summary.get("average_return_10d_pct"),
            "top_proposals": (challenger_review.get("top_proposals") or [])[:5],
            "action_changes": _count_action_changes(changed_cases),
        },
        "differences": {
            "changed_case_count": len(changed_cases),
            "action_delta": _delta_counts(
                champion_summary.get("action_counts") or {},
                challenger_summary.get("action_counts") or {},
            ),
            "verdict_delta": _delta_counts(
                champion_summary.get("comparison_verdict_counts") or {},
                challenger_summary.get("comparison_verdict_counts") or {},
            ),
            "changed_cases": changed_cases,
        },
    }

    label = _comparison_label(champion_replay_id, challenger_replay_id)
    dated_json = os.path.join(
        COMPARE_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__{label}__replay_champion_challenger_compare_v1.json",
    )
    latest_json = os.path.join(COMPARE_DIR, f"latest__{label}__replay_champion_challenger_compare_v1.json")
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")
    save_json(dated_json, payload)
    save_json(latest_json, payload)
    markdown = _build_markdown(payload)
    save_text(dated_md, markdown)
    save_text(latest_md, markdown)
    return dated_json, latest_json, dated_md, latest_md, payload


def main():
    if len(sys.argv) != 3:
        print("Usage: python replay_champion_challenger_compare.py CHAMPION_REPLAY_ID CHALLENGER_REPLAY_ID")
        sys.exit(1)

    dated_json, latest_json, dated_md, latest_md, payload = compare_replays(sys.argv[1], sys.argv[2])
    print(json.dumps({
        "dated_json": dated_json,
        "latest_json": latest_json,
        "dated_md": dated_md,
        "latest_md": latest_md,
        "changed_case_count": payload["differences"]["changed_case_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
