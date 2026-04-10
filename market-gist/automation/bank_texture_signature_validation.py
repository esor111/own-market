"""
Validate the hostile-window bank texture signature outside the original Q3 study.

Signature under test:
- return_5d_pct >= 3.04
- return_20d_pct <= 5.66

This is research-only. It does not change any rule.

Usage:
    python bank_texture_signature_validation.py
"""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

from bank_hostile_window_gap_study import build_rows
from config import VALIDATION_DIR


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
SIGNATURE = {
    "return_5d_min": 3.04,
    "return_20d_max": 5.66,
}

COMPARE_GROUPS = {
    "reference_q3_2024": [
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
    "validation_active_windows": [
        os.path.join(
            OUTPUT_DIR,
            "latest__2023-07-01_to_2023-07-31__daily_truth_replay_jul2023_eventcovered_champion_v1__vs__daily_truth_replay_jul2023_eventcovered_calendarconfidence_sectoraware_v1__replay_champion_challenger_compare_v1.json",
        ),
        os.path.join(
            OUTPUT_DIR,
            "latest__2023-08-01_to_2023-08-31__daily_truth_replay_aug2023_eventcovered_champion_v1__vs__daily_truth_replay_aug2023_eventcovered_calendarconfidence_sectoraware_v1__replay_champion_challenger_compare_v1.json",
        ),
        os.path.join(
            OUTPUT_DIR,
            "latest__2024-08-01_to_2024-08-31__daily_truth_replay_aug2024_eventcovered_champion_v1__vs__daily_truth_replay_aug2024_eventcovered_calendarconfidence_sectoraware_v1__replay_champion_challenger_compare_v1.json",
        ),
        os.path.join(
            OUTPUT_DIR,
            "latest__2025-08-01_to_2025-08-31__daily_truth_replay_august_champion_v1__vs__daily_truth_replay_aug2025_calendarconfidence_sectoraware_v1__replay_champion_challenger_compare_v1.json",
        ),
    ],
}


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _signature_match(row):
    metrics = row.get("metrics") or {}
    return_5d = metrics.get("return_5d_pct")
    return_20d = metrics.get("return_20d_pct")
    if not isinstance(return_5d, (int, float)) or not isinstance(return_20d, (int, float)):
        return False
    return return_5d >= SIGNATURE["return_5d_min"] and return_20d <= SIGNATURE["return_20d_max"]


def _summarize_rows(rows):
    by_direction = defaultdict(list)
    for row in rows:
        by_direction[row["outcome_direction"]].append(row)

    summary = {
        "total_bank_changed_cases": len(rows),
        "signature_matches": 0,
        "signature_rate": None,
        "by_direction": {},
        "symbol_counts_for_signature": [],
        "leadership_counts_for_signature": [],
    }

    matched_rows = [row for row in rows if _signature_match(row)]
    summary["signature_matches"] = len(matched_rows)
    summary["signature_rate"] = round(len(matched_rows) / len(rows), 3) if rows else None

    for direction, direction_rows in by_direction.items():
        matched = [row for row in direction_rows if _signature_match(row)]
        summary["by_direction"][direction] = {
            "count": len(direction_rows),
            "signature_matches": len(matched),
            "signature_rate": round(len(matched) / len(direction_rows), 3) if direction_rows else None,
        }

    symbol_counter = Counter(row["symbol"] for row in matched_rows)
    leadership_counter = Counter(row.get("leadership_label") or "UNKNOWN" for row in matched_rows)
    summary["symbol_counts_for_signature"] = [
        {"label": label, "count": count} for label, count in symbol_counter.most_common(10)
    ]
    summary["leadership_counts_for_signature"] = [
        {"label": label, "count": count} for label, count in leadership_counter.most_common(10)
    ]
    return summary


def _build_markdown(payload):
    lines = [
        "# Bank Texture Signature Validation",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- signature: `return_5d_pct >= {SIGNATURE['return_5d_min']} and return_20d_pct <= {SIGNATURE['return_20d_max']}`",
        "",
        "## Findings",
    ]
    for finding in payload["findings"]:
        lines.append(f"- {finding}")

    for label, summary in payload["summaries"].items():
        lines.extend([
            "",
            f"## {label}",
            f"- total_bank_changed_cases: `{summary['total_bank_changed_cases']}`",
            f"- signature_matches: `{summary['signature_matches']}`",
            f"- signature_rate: `{summary['signature_rate']}`",
            f"- by_direction: `{summary['by_direction']}`",
            f"- signature_symbols: `{summary['symbol_counts_for_signature']}`",
            f"- signature_leadership: `{summary['leadership_counts_for_signature']}`",
        ])
    return "\n".join(lines).strip() + "\n"


def run_validation():
    reference_rows = build_rows(COMPARE_GROUPS["reference_q3_2024"])
    validation_rows = build_rows(COMPARE_GROUPS["validation_active_windows"])

    reference_worsened = [row for row in reference_rows if row["outcome_direction"] == "worsened"]
    reference_not_worsened = [row for row in reference_rows if row["outcome_direction"] != "worsened"]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "signature": SIGNATURE,
        "compare_groups": COMPARE_GROUPS,
        "summaries": {
            "reference_q3_2024_worsened": _summarize_rows(reference_worsened),
            "reference_q3_2024_not_worsened": _summarize_rows(reference_not_worsened),
            "validation_active_windows_all": _summarize_rows(validation_rows),
            "validation_active_windows_improved": _summarize_rows([row for row in validation_rows if row["outcome_direction"] == "improved"]),
            "validation_active_windows_non_improved": _summarize_rows([row for row in validation_rows if row["outcome_direction"] != "improved"]),
        },
    }

    ref_worse = payload["summaries"]["reference_q3_2024_worsened"]
    val_improved = payload["summaries"]["validation_active_windows_improved"]
    val_all = payload["summaries"]["validation_active_windows_all"]

    payload["findings"] = [
        f"In the original 2024 worsened reference slice, the texture signature matched `{ref_worse['signature_matches']}` of `{ref_worse['total_bank_changed_cases']}` cases.",
        f"Across later active hostile windows outside the original Q3 study, the same signature matched `{val_all['signature_matches']}` of `{val_all['total_bank_changed_cases']}` changed bank cases.",
        f"Inside later improved bank cases specifically, the signature matched `{val_improved['signature_matches']}` of `{val_improved['total_bank_changed_cases']}` cases.",
        "If the signature stays concentrated in worsened or non-improved cases and stays rare in improved cases, it is useful as research evidence for a future protective exception. If it leaks heavily into improved cases, it is not stable enough.",
    ]

    dated_json = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__bank_texture_signature_validation_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__bank_texture_signature_validation_v1.json")
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
        "findings": payload["findings"],
    }, indent=2))


if __name__ == "__main__":
    main()
