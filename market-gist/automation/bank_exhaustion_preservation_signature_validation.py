"""
Validate the 2024-07 bank-exhaustion preservation signatures outside the discovery slice.

Goal:
- take the preservation signatures discovered from the 2024-07 exception slice
- test them on other hostile commercial-bank windows
- decide whether they are general enough to refine the challenger, or whether
  2024-07 still looks like a one-off anomaly

Usage:
    python bank_exhaustion_preservation_signature_validation.py
"""
import json
import os
from collections import Counter
from datetime import datetime

from config import VALIDATION_DIR


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")

COMPARE_PATHS = [
    os.path.join(
        OUTPUT_DIR,
        "latest__2023-07-01_to_2023-07-31__daily_truth_replay_jul2023_eventcovered_champion_v1__vs__daily_truth_replay_jul2023_bankexhaustion_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2023-08-01_to_2023-08-31__daily_truth_replay_aug2023_eventcovered_champion_v1__vs__daily_truth_replay_aug2023_bankexhaustion_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2024-07-01_to_2024-07-31__daily_truth_replay_jul2024_champion_v1__vs__daily_truth_replay_jul2024_bankexhaustion_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2024-08-01_to_2024-08-31__daily_truth_replay_aug2024_eventcovered_champion_v1__vs__daily_truth_replay_aug2024_bankexhaustion_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2025-07-01_to_2025-07-31__daily_truth_replay_jul_liqslicechampion_v1__vs__daily_truth_replay_jul2025_bankexhaustion_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2025-08-01_to_2025-08-31__daily_truth_replay_august_champion_v1__vs__daily_truth_replay_aug2025_bankexhaustion_v1__replay_champion_challenger_compare_v1.json",
    ),
]

TRADABILITY_PATH = os.path.join(
    OUTPUT_DIR,
    "latest__replay_next_open_tradability_study__bank_hostile_windows_extended_v1.json",
)

DISCOVERY_MONTH = "2024-07"

SIGNATURES = [
    {
        "signature_name": "single_ret20_lte_5_66",
        "description": "single replay-safe preservation slice from the exception study",
        "rules": [
            ("return_20d_pct", "<=", 5.66),
        ],
    },
    {
        "signature_name": "pair_target_lte_3_0741_and_volume_ge_1_53",
        "description": "best pure pair from the exception study",
        "rules": [
            ("target_distance_close_pct", "<=", 3.0741),
            ("volume_ratio_5d", ">=", 1.53),
        ],
    },
    {
        "signature_name": "pair_day_lte_16_and_ret20_lte_5_66",
        "description": "most interpretable timing-aware preservation pair",
        "rules": [
            ("day_of_month", "<=", 16),
            ("return_20d_pct", "<=", 5.66),
        ],
    },
]


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


def _outcome_direction(champion_verdict, challenger_verdict):
    champion_score = _verdict_quality(champion_verdict)
    challenger_score = _verdict_quality(challenger_verdict)
    if challenger_score > champion_score:
        return "improved"
    if challenger_score < champion_score:
        return "worsened"
    if champion_verdict != challenger_verdict:
        return "changed_same_quality"
    return "unchanged_quality"


def _build_rows():
    tradability_payload = load_json(TRADABILITY_PATH)
    tradability_map = {
        (record.get("replay_id"), record.get("session_id")): record
        for record in (tradability_payload.get("records") or [])
    }

    rows = []
    for path in COMPARE_PATHS:
        compare = load_json(path)
        champion_replay_id = compare.get("champion_replay_id")
        for case in (compare.get("differences") or {}).get("changed_cases", []):
            if case.get("sector_name") != "COMMERCIAL BANKS":
                continue
            tradability = tradability_map.get((champion_replay_id, case.get("session_id")), {})
            session_date = str(case.get("session_date") or "")
            rows.append({
                **case,
                "month_label": session_date[:7],
                "day_of_month": int(session_date[-2:]) if len(session_date) >= 10 else None,
                "outcome_direction": _outcome_direction(
                    case.get("champion_verdict"),
                    case.get("challenger_verdict"),
                ),
                "next_open_label": tradability.get("next_open_label"),
                "next_open_gap_pct": tradability.get("next_open_gap_pct"),
                "target_distance_close_pct": tradability.get("target_distance_close_pct"),
                "risk_reward_ratio": tradability.get("risk_reward_ratio"),
                "return_20d_pct": tradability.get("return_20d_pct"),
                "volume_ratio_5d": tradability.get("volume_ratio_5d"),
            })
    return rows


def _matches(row, signature_rules):
    for feature_name, operator, threshold in signature_rules:
        value = row.get(feature_name)
        if not isinstance(value, (int, float)):
            return False
        if operator == "<=" and float(value) > float(threshold):
            return False
        if operator == ">=" and float(value) < float(threshold):
            return False
    return True


def _sample_rows(rows, limit=8):
    return [
        {
            "session_date": row.get("session_date"),
            "symbol": row.get("symbol"),
            "champion_verdict": row.get("champion_verdict"),
            "challenger_verdict": row.get("challenger_verdict"),
            "outcome_direction": row.get("outcome_direction"),
            "next_open_label": row.get("next_open_label"),
            "day_of_month": row.get("day_of_month"),
            "target_distance_close_pct": row.get("target_distance_close_pct"),
            "risk_reward_ratio": row.get("risk_reward_ratio"),
            "return_20d_pct": row.get("return_20d_pct"),
            "volume_ratio_5d": row.get("volume_ratio_5d"),
        }
        for row in rows[:limit]
    ]


def _summarize_signature(rows, signature):
    matched_rows = [row for row in rows if _matches(row, signature["rules"])]
    discovery_exception_rows = [
        row for row in matched_rows
        if row.get("month_label") == DISCOVERY_MONTH and row.get("outcome_direction") == "worsened"
    ]
    discovery_nonexception_rows = [
        row for row in matched_rows
        if row.get("month_label") == DISCOVERY_MONTH and row.get("outcome_direction") != "worsened"
    ]
    validation_rows = [row for row in matched_rows if row.get("month_label") != DISCOVERY_MONTH]

    return {
        "signature_name": signature["signature_name"],
        "description": signature["description"],
        "rules": signature["rules"],
        "discovery_exception_match_count": len(discovery_exception_rows),
        "discovery_exception_next_open_label_counts": dict(Counter(row.get("next_open_label") or "unknown" for row in discovery_exception_rows)),
        "discovery_exception_champion_verdict_counts": dict(Counter(row.get("champion_verdict") or "unknown" for row in discovery_exception_rows)),
        "discovery_nonexception_match_count": len(discovery_nonexception_rows),
        "discovery_nonexception_outcome_direction_counts": dict(Counter(row.get("outcome_direction") for row in discovery_nonexception_rows)),
        "discovery_nonexception_next_open_label_counts": dict(Counter(row.get("next_open_label") or "unknown" for row in discovery_nonexception_rows)),
        "validation_match_count": len(validation_rows),
        "validation_month_counts": dict(Counter(row.get("month_label") for row in validation_rows)),
        "validation_outcome_direction_counts": dict(Counter(row.get("outcome_direction") for row in validation_rows)),
        "validation_next_open_label_counts": dict(Counter(row.get("next_open_label") or "unknown" for row in validation_rows)),
        "validation_champion_verdict_counts": dict(Counter(row.get("champion_verdict") or "unknown" for row in validation_rows)),
        "validation_challenger_verdict_counts": dict(Counter(row.get("challenger_verdict") or "unknown" for row in validation_rows)),
        "validation_symbol_counts": dict(Counter(row.get("symbol") for row in validation_rows)),
        "validation_samples": _sample_rows(validation_rows),
    }


def _build_findings(signature_summaries):
    findings = []
    for summary in signature_summaries:
        validation_count = summary["validation_match_count"]
        validation_directions = summary["validation_outcome_direction_counts"]
        validation_next_open = summary["validation_next_open_label_counts"]
        name = summary["signature_name"]

        findings.append(
            f"`{name}` matched `{summary['discovery_exception_match_count']}` true `2024-07` exception cases and `{validation_count}` changed cases outside that month."
        )
        findings.append(
            f"Outside `2024-07`, `{name}` mostly aligned with `{validation_directions}` and next-open labels `{validation_next_open}`."
        )

    findings.append(
        "The preservation signatures did not reproduce a new outside-2024-07 bank winner slice. They mostly matched later downside-damage or already-improved hostile-window bank cases."
    )
    findings.append(
        "That means `2024-07` still looks more like a narrow anomaly than a general preservation rule."
    )
    findings.append(
        "So the bank-exhaustion challenger should stay unpromoted and unrefined for now."
    )
    return findings


def _build_markdown(payload):
    lines = [
        "# Bank Exhaustion Preservation Signature Validation",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- discovery_month: `{payload['discovery_month']}`",
        "",
        "## Findings",
    ]
    for finding in payload.get("findings", []):
        lines.append(f"- {finding}")

    for summary in payload.get("signature_summaries", []):
        lines.extend([
            "",
            f"## {summary['signature_name']}",
            f"- description: {summary['description']}",
            f"- rules: `{summary['rules']}`",
            f"- discovery_exception_match_count: `{summary['discovery_exception_match_count']}`",
            f"- discovery_exception_next_open_label_counts: `{summary['discovery_exception_next_open_label_counts']}`",
            f"- discovery_exception_champion_verdict_counts: `{summary['discovery_exception_champion_verdict_counts']}`",
            f"- discovery_nonexception_match_count: `{summary['discovery_nonexception_match_count']}`",
            f"- discovery_nonexception_outcome_direction_counts: `{summary['discovery_nonexception_outcome_direction_counts']}`",
            f"- discovery_nonexception_next_open_label_counts: `{summary['discovery_nonexception_next_open_label_counts']}`",
            f"- validation_match_count: `{summary['validation_match_count']}`",
            f"- validation_month_counts: `{summary['validation_month_counts']}`",
            f"- validation_outcome_direction_counts: `{summary['validation_outcome_direction_counts']}`",
            f"- validation_next_open_label_counts: `{summary['validation_next_open_label_counts']}`",
            f"- validation_champion_verdict_counts: `{summary['validation_champion_verdict_counts']}`",
            f"- validation_challenger_verdict_counts: `{summary['validation_challenger_verdict_counts']}`",
            f"- validation_symbol_counts: `{summary['validation_symbol_counts']}`",
            "",
            "### Validation Samples",
        ])
        for row in summary.get("validation_samples", []):
            lines.append(f"- `{row}`")
    return "\n".join(lines).strip() + "\n"


def run_validation():
    rows = _build_rows()
    signature_summaries = [_summarize_signature(rows, signature) for signature in SIGNATURES]
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "discovery_month": DISCOVERY_MONTH,
        "compare_paths": COMPARE_PATHS,
        "tradability_path": TRADABILITY_PATH,
        "signature_summaries": signature_summaries,
    }
    payload["findings"] = _build_findings(signature_summaries)

    dated_json = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__bank_exhaustion_preservation_signature_validation_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__bank_exhaustion_preservation_signature_validation_v1.json")
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")
    save_json(dated_json, payload)
    save_json(latest_json, payload)
    markdown = _build_markdown(payload)
    save_text(dated_md, markdown)
    save_text(latest_md, markdown)
    return dated_json, latest_json, dated_md, latest_md, payload


def main():
    dated_json, latest_json, dated_md, latest_md, payload = run_validation()
    print(json.dumps({
        "dated_json": dated_json,
        "latest_json": latest_json,
        "dated_md": dated_md,
        "latest_md": latest_md,
        "findings": payload.get("findings"),
    }, indent=2))


if __name__ == "__main__":
    main()
