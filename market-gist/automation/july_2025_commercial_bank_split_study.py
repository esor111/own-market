"""
Research-only study of the July 2025 commercial-bank survivor vs failure split.

Usage:
    python july_2025_commercial_bank_split_study.py
    python july_2025_commercial_bank_split_study.py '@replay_basket_v1'
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime
from statistics import mean

from config import REPLAYS_DIR, VALIDATION_DIR
from replay_after_close_label_drift_study import LATEST_TRADABILITY_STUDY_PATH, load_json, save_json, save_text
from replay_confidence_remap import lookup_replay_calibrated_confidence
from replay_macro_calendar_context import load_replay_macro_calendar_context


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
_FROZEN_CASE_CACHE = {}

COHORT_DEFINITIONS = [
    {
        "cohort_name": "early_sanima_positive",
        "description": "SANIMA early-July cases that stayed positive after next-open realism",
        "predicate": lambda record: (
            record.get("symbol") == "SANIMA"
            and "2025-07-01" <= str(record.get("session_date") or "") <= "2025-07-10"
            and record.get("next_open_label") == "tradable_positive_gross"
        ),
    },
    {
        "cohort_name": "early_ebl_nabil_damage",
        "description": "EBL and NABIL early-July cases that failed through downside damage",
        "predicate": lambda record: (
            record.get("symbol") in {"EBL", "NABIL"}
            and "2025-07-01" <= str(record.get("session_date") or "") <= "2025-07-10"
            and record.get("next_open_label") in {"tradable_negative_gross", "gap_below_stop"}
        ),
    },
    {
        "cohort_name": "late_sanima_damage",
        "description": "SANIMA later-July cases that flipped into downside damage",
        "predicate": lambda record: (
            record.get("symbol") == "SANIMA"
            and "2025-07-13" <= str(record.get("session_date") or "") <= "2025-07-31"
            and record.get("next_open_label") in {"tradable_negative_gross", "gap_below_stop"}
        ),
    },
    {
        "cohort_name": "late_ebl_nabil_damage",
        "description": "EBL and NABIL later-July downside-damage cases",
        "predicate": lambda record: (
            record.get("symbol") in {"EBL", "NABIL"}
            and "2025-07-13" <= str(record.get("session_date") or "") <= "2025-07-31"
            and record.get("next_open_label") in {"tradable_negative_gross", "gap_below_stop"}
        ),
    },
]

NUMERIC_FIELDS = [
    "raw_confidence",
    "calibrated_confidence_pct",
    "confidence_gap_pct",
    "target_distance_close_pct",
    "risk_reward_ratio",
    "return_1d_pct",
    "return_5d_pct",
    "return_20d_pct",
    "close_position_20d",
    "volume_ratio_5d",
    "next_open_gap_pct",
    "recomputed_rr_at_entry",
    "market_advance_decline_ratio",
    "market_median_diff_pct",
    "market_top_5_turnover_share",
    "benchmark_pct_change",
    "sector_index_pct_change",
    "sector_average_diff_pct",
    "turnover_ratio_5d_to_20d",
    "trades_ratio_5d_to_20d",
    "latest_turnover_surprise_vs20d",
    "latest_trades_surprise_vs20d",
]


def _mean(records, field_name):
    values = [record.get(field_name) for record in records if record.get(field_name) is not None]
    return round(mean(values), 4) if values else None


def _count_map(records, field_name, limit=10):
    counter = Counter(record.get(field_name) or "unknown" for record in records)
    return dict(counter.most_common(limit))


def _frozen_case_path(replay_id, session_date, symbol):
    return os.path.join(
        REPLAYS_DIR,
        replay_id,
        "sessions",
        session_date,
        str(symbol).upper(),
        "normalized",
        f"{session_date}__{str(symbol).upper()}__frozen_case_v1.json",
    )


def _load_frozen_case(replay_id, session_date, symbol):
    cache_key = (replay_id, session_date, str(symbol).upper())
    if cache_key not in _FROZEN_CASE_CACHE:
        path = _frozen_case_path(replay_id, session_date, symbol)
        _FROZEN_CASE_CACHE[cache_key] = load_json(path) if os.path.exists(path) else {}
    return _FROZEN_CASE_CACHE[cache_key]


def _calendar_phase_label(calendar_flags):
    labels = (calendar_flags or {}).get("phase_labels") or []
    if not labels:
        return "no_named_phase"
    return "+".join(sorted(str(item) for item in labels))


def _event_state_label(context):
    if context.get("has_active_event"):
        return "active_event"
    if int(context.get("recent_event_count_90d") or 0) > 0:
        return "recent_event_no_active"
    if int(context.get("matched_event_count") or 0) > 0:
        return "matched_but_stale"
    return "no_symbol_event_match"


def _liquidity_profile(liquidity_context):
    metrics = liquidity_context.get("metrics") or {}
    flags = set(liquidity_context.get("context_flags") or [])
    if "has_zero_trade_days" in flags or "high_zero_return_share" in flags:
        return "illiquid_or_inactive"
    if (metrics.get("turnover_ratio_5d_to_20d") or 0) < 0.8 or (metrics.get("trades_ratio_5d_to_20d") or 0) < 0.8:
        return "weak_short_term_participation"
    if (
        (metrics.get("latest_turnover_surprise_vs20d") or 0) >= 2.0
        and (metrics.get("latest_trades_surprise_vs20d") or 0) >= 2.0
    ):
        return "participation_spike"
    if "frequent_large_gaps" in flags or "weekend_gap_carry" in flags:
        return "gap_risk_or_weekend_carry"
    return "stable_or_normal"


def _top_feature_drift(left_records, right_records):
    rows = []
    for field_name in NUMERIC_FIELDS:
        left_mean = _mean(left_records, field_name)
        right_mean = _mean(right_records, field_name)
        if left_mean is None or right_mean is None:
            continue
        rows.append({
            "field_name": field_name,
            "left_mean": left_mean,
            "right_mean": right_mean,
            "delta": round(right_mean - left_mean, 4),
        })
    rows.sort(key=lambda item: abs(item["delta"]), reverse=True)
    return rows[:12]


def _enrich_record(base_record):
    replay_id = base_record.get("replay_id")
    session_date = base_record.get("session_date")
    symbol = base_record.get("symbol")
    frozen_case = _load_frozen_case(replay_id, session_date, symbol)
    historical = frozen_case.get("historical_context") or {}
    derived_context = historical.get("derived_context") or {}
    official_context = historical.get("official_context") or {}
    event_context = historical.get("corporate_action_context") or {}
    liquidity_context = historical.get("liquidity_execution_context") or {}
    macro_context = load_replay_macro_calendar_context(session_date)
    calibrated = lookup_replay_calibrated_confidence(base_record.get("action"), base_record.get("confidence"))
    calibrated_confidence_pct = calibrated.get("calibrated_confidence_pct")

    market = derived_context.get("market") or {}
    sector = derived_context.get("sector") or {}
    benchmark = official_context.get("benchmark_nepse_index") or {}
    sector_index = official_context.get("sector_index") or {}

    return {
        **base_record,
        "calendar_phase": _calendar_phase_label((macro_context or {}).get("calendar_flags") or {}),
        "event_state": _event_state_label(event_context),
        "dominant_event_type": event_context.get("dominant_event_type") or "none",
        "matched_event_count": event_context.get("matched_event_count"),
        "recent_event_count_90d": event_context.get("recent_event_count_90d"),
        "liquidity_profile": _liquidity_profile(liquidity_context),
        "liquidity_flags": liquidity_context.get("context_flags") or [],
        "raw_confidence": base_record.get("confidence"),
        "calibrated_confidence_pct": calibrated_confidence_pct,
        "confidence_gap_pct": (
            round(float(calibrated_confidence_pct) - float(base_record.get("confidence")), 4)
            if calibrated_confidence_pct is not None and base_record.get("confidence") is not None else None
        ),
        "confidence_interpretation_label": calibrated.get("confidence_interpretation_label") or "unknown",
        "market_advance_decline_ratio": market.get("advance_decline_ratio"),
        "market_median_diff_pct": market.get("median_diff_pct"),
        "market_top_5_turnover_share": market.get("top_5_turnover_share"),
        "benchmark_pct_change": benchmark.get("percentageChange"),
        "sector_index_pct_change": sector_index.get("percentageChange"),
        "sector_average_diff_pct": sector.get("average_diff_pct"),
        "turnover_ratio_5d_to_20d": ((liquidity_context.get("metrics") or {}).get("turnover_ratio_5d_to_20d")),
        "trades_ratio_5d_to_20d": ((liquidity_context.get("metrics") or {}).get("trades_ratio_5d_to_20d")),
        "latest_turnover_surprise_vs20d": ((liquidity_context.get("metrics") or {}).get("latest_turnover_surprise_vs20d")),
        "latest_trades_surprise_vs20d": ((liquidity_context.get("metrics") or {}).get("latest_trades_surprise_vs20d")),
    }


def _cohort_summary(records, cohort_name, description):
    return {
        "cohort_name": cohort_name,
        "description": description,
        "count": len(records),
        "date_counts": _count_map(records, "session_date", limit=100),
        "symbol_counts": _count_map(records, "symbol"),
        "label_counts": _count_map(records, "next_open_label"),
        "verdict_counts": _count_map(records, "comparison_verdict"),
        "calendar_phase_counts": _count_map(records, "calendar_phase"),
        "event_state_counts": _count_map(records, "event_state"),
        "confidence_interpretation_counts": _count_map(records, "confidence_interpretation_label"),
        "liquidity_profile_counts": _count_map(records, "liquidity_profile"),
        "feature_means": {field_name: _mean(records, field_name) for field_name in NUMERIC_FIELDS},
        "example_cases": [
            {
                "session_date": record.get("session_date"),
                "symbol": record.get("symbol"),
                "action": record.get("action"),
                "next_open_label": record.get("next_open_label"),
                "comparison_verdict": record.get("comparison_verdict"),
                "target_distance_close_pct": record.get("target_distance_close_pct"),
                "risk_reward_ratio": record.get("risk_reward_ratio"),
                "return_5d_pct": record.get("return_5d_pct"),
                "return_20d_pct": record.get("return_20d_pct"),
                "volume_ratio_5d": record.get("volume_ratio_5d"),
                "next_open_gap_pct": record.get("next_open_gap_pct"),
                "benchmark_pct_change": record.get("benchmark_pct_change"),
                "sector_index_pct_change": record.get("sector_index_pct_change"),
            }
            for record in records[:10]
        ],
    }


def _render_markdown(summary):
    lines = [
        "# July 2025 Commercial-Bank Split Study",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- source_path: `{summary['source_path']}`",
        "",
        "## Short Answer",
        "",
        "This study asks whether the July 2025 commercial-bank split was mostly symbol-specific, timing-specific, or both.",
        "",
    ]

    for cohort in summary.get("cohorts", []):
        lines.extend([
            f"## Cohort `{cohort['cohort_name']}`",
            "",
            f"- description: {cohort['description']}",
            f"- count: `{cohort['count']}`",
            f"- date_counts: `{cohort['date_counts']}`",
            f"- symbol_counts: `{cohort['symbol_counts']}`",
            f"- label_counts: `{cohort['label_counts']}`",
            f"- verdict_counts: `{cohort['verdict_counts']}`",
            f"- confidence_interpretation_counts: `{cohort['confidence_interpretation_counts']}`",
            f"- liquidity_profile_counts: `{cohort['liquidity_profile_counts']}`",
            "",
            "### Feature Means",
            "",
        ])
        for field_name, value in cohort.get("feature_means", {}).items():
            lines.append(f"- `{field_name}`: `{value}`")
        lines.extend(["", "### Example Cases", ""])
        for row in cohort.get("example_cases", []):
            lines.append(f"- `{row}`")
        lines.append("")

    for comparison in summary.get("comparisons", []):
        lines.extend([
            f"## Comparison `{comparison['comparison_name']}`",
            "",
            f"- left_cohort: `{comparison['left_cohort']}`",
            f"- right_cohort: `{comparison['right_cohort']}`",
            "",
            "### Strongest Feature Drift",
            "",
        ])
        for row in comparison.get("feature_drift", []):
            lines.append(
                f"- `{row['field_name']}`: left `{row['left_mean']}`, right `{row['right_mean']}`, delta `{row['delta']}`"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def build_july_2025_commercial_bank_split_study():
    payload = load_json(LATEST_TRADABILITY_STUDY_PATH)
    base_records = [
        record for record in (payload.get("records") or [])
        if record.get("sector_name") == "COMMERCIAL BANKS" and str(record.get("session_date") or "").startswith("2025-07")
    ]
    enriched_records = [_enrich_record(record) for record in base_records]

    cohort_rows = []
    cohort_map = {}
    for definition in COHORT_DEFINITIONS:
        cohort_records = [record for record in enriched_records if definition["predicate"](record)]
        cohort_map[definition["cohort_name"]] = cohort_records
        cohort_rows.append(_cohort_summary(
            cohort_records,
            definition["cohort_name"],
            definition["description"],
        ))

    comparison_pairs = [
        ("early_sanima_positive", "early_ebl_nabil_damage"),
        ("early_sanima_positive", "late_sanima_damage"),
        ("late_sanima_damage", "late_ebl_nabil_damage"),
    ]
    comparisons = []
    for left_name, right_name in comparison_pairs:
        comparisons.append({
            "comparison_name": f"{left_name}__vs__{right_name}",
            "left_cohort": left_name,
            "right_cohort": right_name,
            "feature_drift": _top_feature_drift(cohort_map.get(left_name) or [], cohort_map.get(right_name) or []),
        })

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_path": LATEST_TRADABILITY_STUDY_PATH,
        "cohorts": cohort_rows,
        "comparisons": comparisons,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__july_2025_commercial_bank_split_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__july_2025_commercial_bank_split_study_v1.json",
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")
    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) > 1:
        print("This study takes no positional arguments.")
        sys.exit(1)

    summary, latest_json_path, latest_md_path = build_july_2025_commercial_bank_split_study()
    print(json.dumps({
        "cohort_count": len(summary.get("cohorts") or []),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
