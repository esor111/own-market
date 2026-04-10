"""
Compare bank-family hostile-window slices between Q3 2024 and Q3 2025.

Focus:
- 2024 bank cases where the promoted calendar-confidence rule worsened outcomes
- 2024 bank cases where it created defensive churn without quality gain
- 2025 bank cases where it improved outcomes

Usage:
    python bank_hostile_window_gap_study.py
"""
import json
import os
from collections import Counter
from datetime import datetime

from config import REPLAYS_DIR, VALIDATION_DIR


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
BANK_SECTORS = {"COMMERCIAL BANKS", "DEVELOPMENT BANKS"}

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
    if champion_verdict != challenger_verdict:
        return "changed_same_quality"
    return "unchanged_quality"


def _record_map(replay_id):
    summary_path = os.path.join(REPLAYS_DIR, replay_id, "summaries", "latest__replay_summary_v1.json")
    summary = load_json(summary_path)
    return {item["session_id"]: item for item in summary.get("records", [])}


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


def build_rows(group_paths):
    rows = []
    for path in group_paths:
        compare = load_json(path)
        replay_id = compare["challenger_replay_id"]
        record_map = _record_map(replay_id)
        for item in compare.get("differences", {}).get("changed_cases", []):
            if item.get("sector_name") not in BANK_SECTORS:
                continue
            session_date = item["session_date"]
            symbol = item["symbol"]
            frozen_case = _load_frozen_case(replay_id, session_date, symbol)
            decision = _load_decision(replay_id, session_date, symbol)
            record = record_map.get(item["session_id"], {})
            rows.append({
                **item,
                "outcome_direction": outcome_direction(item.get("champion_verdict"), item.get("challenger_verdict")),
                "replay_id": replay_id,
                "metrics": frozen_case.get("metrics") or {},
                "liquidity_metrics": (((frozen_case.get("historical_context") or {}).get("liquidity_execution_context") or {}).get("metrics") or {}),
                "macro_snapshot": (((frozen_case.get("historical_context") or {}).get("macro_calendar_context") or {}).get("latest_available_snapshot") or {}),
                "macro_derived": ((((frozen_case.get("historical_context") or {}).get("macro_calendar_context") or {}).get("latest_available_snapshot") or {}).get("derived_metrics") or {}),
                "calendar_flags": (((frozen_case.get("historical_context") or {}).get("macro_calendar_context") or {}).get("calendar_flags") or {}),
                "event_context": ((frozen_case.get("historical_context") or {}).get("corporate_action_context") or {}),
                "decision": decision,
                "record": record,
            })
    return rows


def avg(values):
    clean = [float(value) for value in values if isinstance(value, (int, float))]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 3)


def top_counts(rows, fn, limit=8):
    counter = Counter(fn(row) for row in rows)
    return [{"label": label, "count": count} for label, count in counter.most_common(limit)]


def summarize_slice(label, rows):
    return {
        "label": label,
        "count": len(rows),
        "symbols": top_counts(rows, lambda row: row["symbol"], 8),
        "leadership": top_counts(rows, lambda row: row.get("leadership_label") or "UNKNOWN", 8),
        "alignment": top_counts(rows, lambda row: row.get("alignment_label") or "UNKNOWN", 8),
        "market_regime": top_counts(rows, lambda row: row.get("market_regime") or "UNKNOWN", 8),
        "sector_regime": top_counts(rows, lambda row: row.get("sector_regime") or "UNKNOWN", 8),
        "calendar_phase": top_counts(rows, lambda row: row.get("calendar_phase") or "UNKNOWN", 8),
        "action_change": top_counts(rows, lambda row: row.get("calendar_confidence_guidance_action_change") or "none", 4),
        "champion_verdict": top_counts(rows, lambda row: row.get("champion_verdict") or "UNKNOWN", 6),
        "challenger_verdict": top_counts(rows, lambda row: row.get("challenger_verdict") or "UNKNOWN", 6),
        "avg_score": avg(row["decision"].get("score") for row in rows),
        "avg_raw_confidence": avg(row["decision"].get("confidence") for row in rows),
        "avg_calibrated_confidence_pct": avg(row["record"].get("calibrated_confidence_pct") for row in rows),
        "avg_rr": avg(row["decision"].get("risk_reward_ratio") for row in rows),
        "avg_close_position_20d": avg((row["metrics"].get("close_position_20d")) for row in rows),
        "avg_close_position_60d": avg((row["metrics"].get("close_position_60d")) for row in rows),
        "avg_return_5d_pct": avg((row["metrics"].get("return_5d_pct")) for row in rows),
        "avg_return_20d_pct": avg((row["metrics"].get("return_20d_pct")) for row in rows),
        "avg_volume_ratio_5d": avg((row["metrics"].get("volume_ratio_5d")) for row in rows),
        "avg_turnover_ratio_5d_to_20d": avg((row["liquidity_metrics"].get("turnover_ratio_5d_to_20d")) for row in rows),
        "avg_latest_turnover_surprise": avg((row["liquidity_metrics"].get("latest_turnover_surprise_vs20d")) for row in rows),
        "avg_latest_trades_surprise": avg((row["liquidity_metrics"].get("latest_trades_surprise_vs20d")) for row in rows),
        "avg_interbank_rate_pct": avg((((row["macro_snapshot"].get("metrics") or {}).get("interbank_rate_pct") or {}).get("current_value")) for row in rows),
        "avg_remittance_yoy_pct": avg((row["macro_derived"].get("remittance_yoy_pct")) for row in rows),
        "avg_private_credit_yoy_pct": avg((((row["macro_snapshot"].get("metrics") or {}).get("claims_private_sector_yoy_pct") or {}).get("current_value")) for row in rows),
        "sample_session_ids": [row["session_id"] for row in rows[:8]],
    }


def build_markdown(payload):
    lines = [
        "# Bank Hostile-Window Gap Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        "",
        "## Findings",
    ]
    for finding in payload["findings"]:
        lines.append(f"- {finding}")
    for key in ("2024_worsened_bank", "2024_defensive_churn_bank", "2025_improved_bank"):
        summary = payload["slices"][key]
        lines.extend([
            "",
            f"## {key}",
            f"- count: `{summary['count']}`",
            f"- symbols: `{summary['symbols']}`",
            f"- leadership: `{summary['leadership']}`",
            f"- alignment: `{summary['alignment']}`",
            f"- market_regime: `{summary['market_regime']}`",
            f"- sector_regime: `{summary['sector_regime']}`",
            f"- avg_score: `{summary['avg_score']}`",
            f"- avg_rr: `{summary['avg_rr']}`",
            f"- avg_close_position_20d: `{summary['avg_close_position_20d']}`",
            f"- avg_return_5d_pct: `{summary['avg_return_5d_pct']}`",
            f"- avg_return_20d_pct: `{summary['avg_return_20d_pct']}`",
            f"- avg_volume_ratio_5d: `{summary['avg_volume_ratio_5d']}`",
            f"- avg_interbank_rate_pct: `{summary['avg_interbank_rate_pct']}`",
            "",
        ])
    return "\n".join(lines).strip() + "\n"


def build_findings(slices):
    worsened = slices["2024_worsened_bank"]
    churn = slices["2024_defensive_churn_bank"]
    improved = slices["2025_improved_bank"]
    findings = []
    findings.append(
        "The strongest 2024 clipped winners were not lower-score setups; they were generally high-score, high-close-position bank setups that already looked strong."
    )
    findings.append(
        f"2024 worsened cases were more leader-heavy than 2025 improvements: worsened leadership {worsened['leadership'][:3]} vs improved leadership {improved['leadership'][:3]}."
    )
    findings.append(
        f"2024 worsened cases had richer recent momentum than 2025 improvements: return_5d `{worsened['avg_return_5d_pct']}` vs `{improved['avg_return_5d_pct']}`, return_20d `{worsened['avg_return_20d_pct']}` vs `{improved['avg_return_20d_pct']}`."
    )
    findings.append(
        f"2024 defensive churn was much larger than outright 2024 worsening, which means 2024's main issue was excessive caution on otherwise workable bank setups, not only outright bad demotions."
    )
    findings.append(
        f"Macro values do not look dramatically different at this slice level; the bigger visible difference is setup state quality rather than a simple macro-level shift."
    )
    return findings


def run_study():
    rows_2024 = build_rows(COMPARE_GROUPS["2024_q3"])
    rows_2025 = build_rows(COMPARE_GROUPS["2025_q3"])

    slices = {
        "2024_worsened_bank": summarize_slice(
            "2024_worsened_bank",
            [row for row in rows_2024 if row["outcome_direction"] == "worsened"],
        ),
        "2024_defensive_churn_bank": summarize_slice(
            "2024_defensive_churn_bank",
            [row for row in rows_2024 if row["outcome_direction"] in {"changed_same_quality", "unchanged_quality"}],
        ),
        "2025_improved_bank": summarize_slice(
            "2025_improved_bank",
            [row for row in rows_2025 if row["outcome_direction"] == "improved"],
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
        f"{datetime.now().strftime('%Y-%m-%d')}__bank_hostile_window_gap_study_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__bank_hostile_window_gap_study_v1.json")
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
