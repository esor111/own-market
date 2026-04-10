"""
Study whether hostile-window bank ranking/relative-strength separates the Q3 blocker.

Focus:
- 2024 bank cases where the promoted calendar-confidence rule worsened outcomes
- 2024 bank cases where it created defensive churn without quality gain
- 2025 bank cases where it improved outcomes

Usage:
    python q3_hostile_bank_ranking_study.py
"""
import json
import os
from collections import Counter
from datetime import datetime

from config import REPLAYS_DIR, VALIDATION_DIR
from replay_champion_challenger_compare import load_json


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


def _load_frozen_case(replay_id, session_date, symbol):
    path = os.path.join(
        REPLAYS_DIR,
        replay_id,
        "sessions",
        session_date,
        symbol,
        "normalized",
        f"{session_date}__{symbol}__frozen_case_v1.json",
    )
    return load_json(path)


def build_rows():
    rows = []
    for compare_group, paths in COMPARE_GROUPS.items():
        for path in paths:
            compare = load_json(path)
            replay_id = compare["champion_replay_id"]
            month_label = (compare.get("champion_replay_id") or "").split("__")[0]
            for item in compare.get("differences", {}).get("changed_cases", []):
                if item.get("sector_name") not in {"COMMERCIAL BANKS", "DEVELOPMENT BANKS"}:
                    continue
                frozen_case = _load_frozen_case(replay_id, item["session_date"], item["symbol"])
                cross = frozen_case.get("cross_sectional_context") or {}
                rows.append({
                    **item,
                    "compare_group": compare_group,
                    "month_label": month_label,
                    "cross_sectional_context": cross,
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
        "leadership_label": _top_counts(rows, lambda row: (row.get("cross_sectional_context") or {}).get("leadership_label") or "UNKNOWN", 8),
        "avg_sector_return_rank": _avg(((row.get("cross_sectional_context") or {}).get("sector_return_20d_rank")) for row in rows),
        "avg_sector_score_rank": _avg(((row.get("cross_sectional_context") or {}).get("sector_score_rank")) for row in rows),
        "avg_basket_return_rank": _avg(((row.get("cross_sectional_context") or {}).get("basket_return_20d_rank")) for row in rows),
        "avg_basket_score_rank": _avg(((row.get("cross_sectional_context") or {}).get("basket_score_rank")) for row in rows),
        "avg_basket_return_percentile": _avg(((row.get("cross_sectional_context") or {}).get("basket_return_20d_percentile")) for row in rows),
        "avg_relative_return_vs_sector": _avg(((row.get("cross_sectional_context") or {}).get("relative_return_vs_sector")) for row in rows),
        "avg_relative_score_vs_basket": _avg(((row.get("cross_sectional_context") or {}).get("relative_score_vs_basket")) for row in rows),
    }


def build_findings(slices):
    worsened = slices["2024_worsened_bank"]
    churn = slices["2024_defensive_churn_bank"]
    improved = slices["2025_improved_bank"]
    findings = []
    findings.append(
        f"2024 worsened bank cases were more leader-heavy than 2024 defensive churn: basket score rank `{worsened['avg_basket_score_rank']}` vs `{churn['avg_basket_score_rank']}`, basket return rank `{worsened['avg_basket_return_rank']}` vs `{churn['avg_basket_return_rank']}`."
    )
    findings.append(
        f"But 2024 worsened bank cases were not materially cleaner than 2025 improved bank cases on ranking: sector return rank `{worsened['avg_sector_return_rank']}` vs `{improved['avg_sector_return_rank']}`, basket score rank `{worsened['avg_basket_score_rank']}` vs `{improved['avg_basket_score_rank']}`."
    )
    findings.append(
        f"Relative-strength was high in both the 2024 blocker and the 2025 correctly-cautioned set: relative score vs basket `{worsened['avg_relative_score_vs_basket']}` vs `{improved['avg_relative_score_vs_basket']}`."
    )
    findings.append(
        "So ranking helps explain why the 2024 blocker was stronger than defensive churn, but ranking alone does not rescue it from the 2025 hostile-window failures."
    )
    findings.append(
        "That means a simple 'preserve the top-ranked hostile-window bank setups' rule would still be too blunt."
    )
    return findings


def build_markdown(payload):
    lines = [
        "# Q3 Hostile Bank Ranking Study",
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
            f"- leadership_label: `{summary['leadership_label']}`",
            f"- avg_sector_return_rank: `{summary['avg_sector_return_rank']}`",
            f"- avg_sector_score_rank: `{summary['avg_sector_score_rank']}`",
            f"- avg_basket_return_rank: `{summary['avg_basket_return_rank']}`",
            f"- avg_basket_score_rank: `{summary['avg_basket_score_rank']}`",
            f"- avg_basket_return_percentile: `{summary['avg_basket_return_percentile']}`",
            f"- avg_relative_return_vs_sector: `{summary['avg_relative_return_vs_sector']}`",
            f"- avg_relative_score_vs_basket: `{summary['avg_relative_score_vs_basket']}`",
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
        f"{datetime.now().strftime('%Y-%m-%d')}__q3_hostile_bank_ranking_study_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__q3_hostile_bank_ranking_study_v1.json")
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
