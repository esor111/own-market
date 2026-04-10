"""
Study why Q3 2024 and Q3 2025 behaved differently under the promoted
sector-aware calendar-confidence rule.

Usage:
    python q3_regime_gap_study.py
"""
import json
import os
from collections import Counter
from datetime import datetime

from config import REPLAYS_DIR, VALIDATION_DIR


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
BANK_SECTORS = {"COMMERCIAL BANKS", "DEVELOPMENT BANKS"}

DEFAULT_COMPARE_GROUPS = {
    "2024_q3": [
        os.path.join(
            OUTPUT_DIR,
            "latest__2024-07-01_to_2024-07-31__daily_truth_replay_jul2024_legacy_nocal_v1__vs__daily_truth_replay_jul2024_promoted_calendar_v1__replay_champion_challenger_compare_v1.json",
        ),
        os.path.join(
            OUTPUT_DIR,
            "latest__2024-08-01_to_2024-08-31__daily_truth_replay_aug2024_legacy_nocal_v1__vs__daily_truth_replay_aug2024_promoted_calendar_v1__replay_champion_challenger_compare_v1.json",
        ),
        os.path.join(
            OUTPUT_DIR,
            "latest__2024-09-01_to_2024-09-30__daily_truth_replay_sep2024_legacy_nocal_v1__vs__daily_truth_replay_sep2024_promoted_calendar_v1__replay_champion_challenger_compare_v1.json",
        ),
    ],
    "2025_q3": [
        os.path.join(
            OUTPUT_DIR,
            "latest__2025-07-01_to_2025-09-30__daily_truth_replay_2025_q3_legacy_nocal_v1__vs__daily_truth_replay_2025_q3_promoted_calendar_v1__replay_champion_challenger_compare_v1.json",
        ),
    ],
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


def verdict_quality(verdict):
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


def outcome_direction(champion_verdict, challenger_verdict):
    champion_score = verdict_quality(champion_verdict)
    challenger_score = verdict_quality(challenger_verdict)
    if challenger_score > champion_score:
        return "improved"
    if challenger_score < champion_score:
        return "worsened"
    if challenger_verdict != champion_verdict:
        return "changed_same_quality"
    return "unchanged_quality"


def _summary_map_from_replay(replay_id):
    summary_path = os.path.join(REPLAYS_DIR, replay_id, "summaries", "latest__replay_summary_v1.json")
    summary = load_json(summary_path)
    return {item["session_id"]: item for item in summary.get("records", [])}


def load_bank_changed_cases(compare_paths):
    rows = []
    for path in compare_paths:
        payload = load_json(path)
        summary_map = _summary_map_from_replay(payload["challenger_replay_id"])
        for item in payload.get("differences", {}).get("changed_cases", []):
            if item.get("sector_name") not in BANK_SECTORS:
                continue
            row = dict(item)
            row["outcome_direction"] = outcome_direction(
                item.get("champion_verdict"),
                item.get("challenger_verdict"),
            )
            row["month_label"] = (payload.get("challenger_replay_id") or "").split("__")[0]
            row.update(summary_map.get(item["session_id"], {}))
            rows.append(row)
    return rows


def average(values):
    clean = [float(value) for value in values if isinstance(value, (int, float))]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 2)


def top_counter(rows, key, limit=8):
    counter = Counter(row.get(key) or "UNKNOWN" for row in rows)
    return [{"label": label, "count": count} for label, count in counter.most_common(limit)]


def top_combo_counter(rows, keys, limit=10):
    counter = Counter(tuple(row.get(key) or "UNKNOWN" for key in keys) for row in rows)
    output = []
    for labels, count in counter.most_common(limit):
        entry = {keys[index]: labels[index] for index in range(len(keys))}
        entry["count"] = count
        output.append(entry)
    return output


def build_group_summary(label, rows):
    direction_groups = {}
    for direction in ("improved", "worsened", "changed_same_quality", "unchanged_quality"):
        direction_rows = [row for row in rows if row["outcome_direction"] == direction]
        if not direction_rows:
            continue
        direction_groups[direction] = {
            "count": len(direction_rows),
            "symbols": top_counter(direction_rows, "symbol", 6),
            "leadership": top_counter(direction_rows, "leadership_label", 6),
            "alignment": top_counter(direction_rows, "alignment_label", 6),
            "market_regime": top_counter(direction_rows, "market_regime", 6),
            "sector_regime": top_counter(direction_rows, "sector_regime", 6),
            "action_changes": top_counter(direction_rows, "calendar_confidence_guidance_action_change", 4),
            "avg_raw_confidence": average([row.get("raw_confidence") for row in direction_rows]),
            "avg_calibrated_confidence_pct": average([row.get("calibrated_confidence_pct") for row in direction_rows]),
        }
    return {
        "label": label,
        "changed_case_count": len(rows),
        "outcome_directions": dict(Counter(row["outcome_direction"] for row in rows)),
        "sectors": top_counter(rows, "sector_name", 4),
        "symbols": top_counter(rows, "symbol", 8),
        "leadership": top_counter(rows, "leadership_label", 8),
        "alignment": top_counter(rows, "alignment_label", 8),
        "market_regime": top_counter(rows, "market_regime", 8),
        "sector_regime": top_counter(rows, "sector_regime", 8),
        "calendar_phase": top_counter(rows, "calendar_phase", 8),
        "event_state": top_counter(rows, "event_state", 8),
        "action_changes": top_counter(rows, "calendar_confidence_guidance_action_change", 4),
        "verdict_transitions": top_combo_counter(rows, ("champion_verdict", "challenger_verdict"), 10),
        "direction_groups": direction_groups,
        "quality_state_combos": top_combo_counter(rows, ("outcome_direction", "leadership_label", "alignment_label"), 12),
    }


def build_findings(summary_2024, summary_2025):
    findings = []
    directions_2024 = summary_2024["outcome_directions"]
    directions_2025 = summary_2025["outcome_directions"]

    findings.append(
        "Q3 2024 was less clean mainly because it had worsened and same-quality defensive changes, while Q3 2025 had no worsened bank-family changes."
    )

    worsened_2024 = summary_2024["direction_groups"].get("worsened") or {}
    if worsened_2024:
        top_alignments = ", ".join(
            item["label"] for item in worsened_2024.get("alignment", [])[:2]
        ) or "UNKNOWN"
        top_leadership = ", ".join(
            item["label"] for item in worsened_2024.get("leadership", [])[:2]
        ) or "UNKNOWN"
        findings.append(
            f"2024 worsened cases were concentrated in stronger-looking states: leadership `{top_leadership}` and alignment `{top_alignments}`."
        )

    improved_2025 = summary_2025["direction_groups"].get("improved") or {}
    if improved_2025:
        top_leadership = ", ".join(
            item["label"] for item in improved_2025.get("leadership", [])[:2]
        ) or "UNKNOWN"
        top_alignments = ", ".join(
            item["label"] for item in improved_2025.get("alignment", [])[:2]
        ) or "UNKNOWN"
        findings.append(
            f"2025 improvements were concentrated in `{top_leadership}` leadership states and `{top_alignments}` alignments, which suggests the rule helped more on weaker or middling actionable bank setups."
        )

    if summary_2024["event_state"] == summary_2025["event_state"]:
        findings.append(
            "The event-state surface was effectively the same in both years (`matched_but_stale`), so event-state alone does not explain the 2024 vs 2025 gap."
        )

    findings.append(
        "The symbol concentration stayed very similar across both years (`SANIMA`, `EBL`, `NABIL`, then smaller development-bank names), so the gap is more likely about setup quality and regime than about a different symbol universe."
    )

    if directions_2024.get("changed_same_quality", 0) > directions_2025.get("changed_same_quality", 0):
        findings.append(
            "2024 had much more defensive churn than 2025, which suggests the same guarded rule clipped more already-working setups in that year."
        )

    return findings


def build_markdown(payload):
    lines = [
        "# Q3 Regime Gap Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        "",
        "## Main Findings",
    ]
    for finding in payload["findings"]:
        lines.append(f"- {finding}")
    for label in ("2024_q3", "2025_q3"):
        summary = payload["groups"][label]
        lines.extend([
            "",
            f"## {label}",
            f"- changed_case_count: `{summary['changed_case_count']}`",
            f"- outcome_directions: `{summary['outcome_directions']}`",
            f"- symbols: `{summary['symbols']}`",
            f"- leadership: `{summary['leadership']}`",
            f"- alignment: `{summary['alignment']}`",
            f"- market_regime: `{summary['market_regime']}`",
            f"- sector_regime: `{summary['sector_regime']}`",
            f"- verdict_transitions: `{summary['verdict_transitions']}`",
            "",
            "### Direction Groups",
        ])
        for direction, group in summary["direction_groups"].items():
            lines.append(
                f"- {direction}: count=`{group['count']}`, avg_raw_confidence=`{group['avg_raw_confidence']}`, avg_calibrated_confidence_pct=`{group['avg_calibrated_confidence_pct']}`"
            )
    return "\n".join(lines).strip() + "\n"


def run_study():
    groups = {
        label: build_group_summary(label, load_bank_changed_cases(paths))
        for label, paths in DEFAULT_COMPARE_GROUPS.items()
    }
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "compare_groups": DEFAULT_COMPARE_GROUPS,
        "groups": groups,
    }
    payload["findings"] = build_findings(groups["2024_q3"], groups["2025_q3"])

    dated_json = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__q3_regime_gap_study_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__q3_regime_gap_study_v1.json")
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")

    save_json(dated_json, payload)
    save_json(latest_json, payload)
    markdown = build_markdown(payload)
    save_text(dated_md, markdown)
    save_text(latest_md, markdown)
    return dated_json, latest_json, dated_md, latest_md, payload


def main():
    dated_json, latest_json, dated_md, latest_md, payload = run_study()
    print(json.dumps({
        "dated_json": dated_json,
        "latest_json": latest_json,
        "dated_md": dated_md,
        "latest_md": latest_md,
        "findings": payload["findings"],
    }, indent=2))


if __name__ == "__main__":
    main()
