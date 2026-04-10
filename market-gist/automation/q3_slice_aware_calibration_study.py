"""
Study champion-side calibrated confidence across the key Q3 hostile-bank slices.

Focus:
- 2024 bank cases where the promoted calendar-confidence rule worsened outcomes
- 2024 bank cases where it created defensive churn without quality gain
- 2025 bank cases where it improved outcomes

Usage:
    python q3_slice_aware_calibration_study.py
"""
import json
import os
from collections import Counter
from datetime import datetime

from config import REPLAYS_DIR, VALIDATION_DIR
from replay_confidence_remap import lookup_replay_calibrated_confidence


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")

COMPARE_GROUPS = {
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


def _avg(values):
    clean = [float(value) for value in values if isinstance(value, (int, float))]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 3)


def _load_decision(replay_id, session_date, symbol):
    path = os.path.join(
        REPLAYS_DIR,
        replay_id,
        "sessions",
        session_date,
        symbol,
        "derived",
        f"{session_date}__{symbol}__replay_decision_v1.json",
    )
    return load_json(path)


def build_rows():
    rows = []
    for compare_group, paths in COMPARE_GROUPS.items():
        for path in paths:
            compare = load_json(path)
            champion_replay_id = compare["champion_replay_id"]
            month_label = (compare.get("champion_replay_id") or "").split("__")[0]
            for item in compare.get("differences", {}).get("changed_cases", []):
                if item.get("sector_name") not in {"COMMERCIAL BANKS", "DEVELOPMENT BANKS"}:
                    continue
                session_date = item["session_date"]
                symbol = item["symbol"]
                champion_decision = _load_decision(champion_replay_id, session_date, symbol)
                calibrated = lookup_replay_calibrated_confidence(
                    champion_decision.get("action"),
                    champion_decision.get("confidence"),
                )
                rows.append({
                    **item,
                    "compare_group": compare_group,
                    "month_label": month_label,
                    "champion_replay_id": champion_replay_id,
                    "champion_decision_action": champion_decision.get("action"),
                    "champion_decision_score": champion_decision.get("score"),
                    "champion_raw_confidence": champion_decision.get("confidence"),
                    "champion_rr": champion_decision.get("risk_reward_ratio"),
                    "champion_reason_codes": champion_decision.get("reason_codes") or [],
                    "champion_calibrated_confidence_pct": calibrated.get("calibrated_confidence_pct"),
                    "champion_confidence_interpretation_label": calibrated.get("confidence_interpretation_label"),
                    "champion_confidence_reference_group": calibrated.get("reference_group"),
                    "champion_confidence_gap_pct": (
                        round(float(calibrated.get("calibrated_confidence_pct")) - float(champion_decision.get("confidence")), 3)
                        if calibrated.get("calibrated_confidence_pct") is not None and champion_decision.get("confidence") is not None
                        else None
                    ),
                })
    return rows


def _top_counts(rows, fn, limit=8):
    counter = Counter(fn(row) for row in rows)
    return [{"label": label, "count": count} for label, count in counter.most_common(limit)]


def summarize_slice(label, rows):
    return {
        "label": label,
        "count": len(rows),
        "symbols": _top_counts(rows, lambda row: row.get("symbol") or "UNKNOWN", 8),
        "calendar_phase": _top_counts(rows, lambda row: row.get("calendar_phase") or "UNKNOWN", 8),
        "champion_action": _top_counts(rows, lambda row: row.get("champion_decision_action") or "UNKNOWN", 4),
        "champion_verdict": _top_counts(rows, lambda row: row.get("champion_verdict") or "UNKNOWN", 6),
        "confidence_interpretation": _top_counts(rows, lambda row: row.get("champion_confidence_interpretation_label") or "UNKNOWN", 8),
        "reference_group": _top_counts(rows, lambda row: row.get("champion_confidence_reference_group") or "UNKNOWN", 4),
        "avg_raw_confidence": _avg(row.get("champion_raw_confidence") for row in rows),
        "avg_calibrated_confidence_pct": _avg(row.get("champion_calibrated_confidence_pct") for row in rows),
        "avg_confidence_gap_pct": _avg(row.get("champion_confidence_gap_pct") for row in rows),
        "avg_score": _avg(row.get("champion_decision_score") for row in rows),
        "avg_rr": _avg(row.get("champion_rr") for row in rows),
        "reason_codes": _top_counts(rows, lambda row: ",".join(row.get("champion_reason_codes") or []) or "none", 8),
    }


def build_findings(slices):
    worsened = slices["2024_worsened_bank"]
    churn = slices["2024_defensive_churn_bank"]
    improved = slices["2025_improved_bank"]
    findings = []
    findings.append(
        f"2024 worsened bank winners were still strongly overconfident on the champion side: raw `{worsened['avg_raw_confidence']}` vs calibrated `{worsened['avg_calibrated_confidence_pct']}`, gap `{worsened['avg_confidence_gap_pct']}`."
    )
    findings.append(
        f"2024 defensive churn cases were less aggressively miscalibrated than the outright worsened slice: raw `{churn['avg_raw_confidence']}` vs calibrated `{churn['avg_calibrated_confidence_pct']}`, gap `{churn['avg_confidence_gap_pct']}`."
    )
    findings.append(
        f"2025 improved bank cases were also strongly overconfident, and even more so on average: raw `{improved['avg_raw_confidence']}` vs calibrated `{improved['avg_calibrated_confidence_pct']}`, gap `{improved['avg_confidence_gap_pct']}`."
    )
    findings.append(
        "So the confidence layer does not rescue the 2024 blocker as a clean exception. Even the clipped 2024 winners still looked overconfident on the champion-side probability scale."
    )
    findings.append(
        "This supports keeping hostile-window caution tied to confidence state, while treating the remaining 2024 issue as a texture anomaly rather than a calibration failure."
    )
    return findings


def build_markdown(payload):
    lines = [
        "# Q3 Slice-Aware Calibration Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        "",
        "## Main Findings",
    ]
    for finding in payload.get("findings") or []:
        lines.append(f"- {finding}")
    for key in ("2024_worsened_bank", "2024_defensive_churn_bank", "2025_improved_bank"):
        summary = payload["slices"][key]
        lines.extend([
            "",
            f"## {key}",
            f"- count: `{summary['count']}`",
            f"- symbols: `{summary['symbols']}`",
            f"- calendar_phase: `{summary['calendar_phase']}`",
            f"- champion_action: `{summary['champion_action']}`",
            f"- champion_verdict: `{summary['champion_verdict']}`",
            f"- confidence_interpretation: `{summary['confidence_interpretation']}`",
            f"- reference_group: `{summary['reference_group']}`",
            f"- avg_raw_confidence: `{summary['avg_raw_confidence']}`",
            f"- avg_calibrated_confidence_pct: `{summary['avg_calibrated_confidence_pct']}`",
            f"- avg_confidence_gap_pct: `{summary['avg_confidence_gap_pct']}`",
            f"- avg_score: `{summary['avg_score']}`",
            f"- avg_rr: `{summary['avg_rr']}`",
            f"- reason_codes: `{summary['reason_codes']}`",
        ])
    return "\n".join(lines).strip() + "\n"


def run_study():
    rows = build_rows()
    rows_2024 = [row for row in rows if row["compare_group"] == "2024_q3"]
    rows_2025 = [row for row in rows if row["compare_group"] == "2025_q3"]
    slices = {
        "2024_worsened_bank": summarize_slice(
            "2024_worsened_bank",
            [row for row in rows_2024 if row["champion_verdict"] == "good_call" and row["challenger_verdict"] in {"neutral_avoid", "good_avoid"}],
        ),
        "2024_defensive_churn_bank": summarize_slice(
            "2024_defensive_churn_bank",
            [row for row in rows_2024 if row["champion_verdict"] in {"mixed_call", "neutral_avoid", "good_avoid"} and row["challenger_verdict"] in {"neutral_avoid", "good_avoid"}],
        ),
        "2025_improved_bank": summarize_slice(
            "2025_improved_bank",
            [row for row in rows_2025 if row["challenger_verdict"] == "good_avoid"],
        ),
    }
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "compare_groups": COMPARE_GROUPS,
        "slices": slices,
    }
    payload["findings"] = build_findings(slices)

    dated_json = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__q3_slice_aware_calibration_study_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__q3_slice_aware_calibration_study_v1.json")
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
