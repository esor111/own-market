"""
Research-only study of commercial-bank after-close regime drift.

Usage:
    python commercial_bank_after_close_regime_drift_study.py
    python commercial_bank_after_close_regime_drift_study.py '@replay_basket_v1'
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
from replay_corporate_action_context import load_replay_corporate_action_context
from replay_macro_calendar_context import load_replay_macro_calendar_context


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")

COHORT_DEFINITIONS = [
    {
        "cohort_name": "discovery_upside_gap",
        "description": "commercial-bank discovery cases that became next-open upside-gap paper wins",
        "predicate": lambda record: (
            record.get("sector_name") == "COMMERCIAL BANKS"
            and str(record.get("session_date") or "")[:7] <= "2025-06"
            and record.get("next_open_label") == "gap_above_target"
        ),
    },
    {
        "cohort_name": "july_2025_downside_damage",
        "description": "commercial-bank July 2025 cases that failed through gap-down or tradable-negative behavior",
        "predicate": lambda record: (
            record.get("sector_name") == "COMMERCIAL BANKS"
            and str(record.get("session_date") or "").startswith("2025-07")
            and record.get("next_open_label") in {"gap_below_stop", "tradable_negative_gross"}
        ),
    },
    {
        "cohort_name": "july_2025_positive_survivors",
        "description": "commercial-bank July 2025 cases that still stayed positive after the next-open realism check",
        "predicate": lambda record: (
            record.get("sector_name") == "COMMERCIAL BANKS"
            and str(record.get("session_date") or "").startswith("2025-07")
            and record.get("next_open_label") == "tradable_positive_gross"
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
    "turnover_ratio_5d_to_20d",
    "trades_ratio_5d_to_20d",
    "latest_turnover_surprise_vs20d",
    "latest_trades_surprise_vs20d",
    "avg_abs_gap_pct_20d",
    "gap_over_2pct_share_20d",
    "interbank_rate_pct_current",
    "claims_private_sector_yoy_pct_current",
    "remittance_yoy_pct",
]

_FROZEN_CASE_CACHE = {}


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


def _mean(records, field_name):
    values = [record.get(field_name) for record in records if record.get(field_name) is not None]
    return round(mean(values), 4) if values else None


def _count_map(records, field_name, limit=10):
    counter = Counter(record.get(field_name) or "unknown" for record in records)
    return dict(counter.most_common(limit))


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


def _macro_value(snapshot, metric_name):
    metrics = (snapshot or {}).get("metrics") or {}
    payload = metrics.get(metric_name) or {}
    if not isinstance(payload, dict):
        return None
    current_value = payload.get("current_value")
    return round(float(current_value), 4) if current_value is not None else None


def _derived_macro_value(snapshot, metric_name):
    derived = (snapshot or {}).get("derived_metrics") or {}
    value = derived.get(metric_name)
    return round(float(value), 4) if value is not None else None


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


def _enrich_record(base_record, replay_context_list_name):
    replay_id = base_record.get("replay_id")
    symbol = base_record.get("symbol")
    session_date = base_record.get("session_date")
    action = base_record.get("action")
    confidence = base_record.get("confidence")
    frozen_case = _load_frozen_case(replay_id, session_date, symbol)
    historical_context = frozen_case.get("historical_context") or {}

    macro_context = load_replay_macro_calendar_context(session_date)
    calendar_flags = macro_context.get("calendar_flags") or {}
    macro_snapshot = macro_context.get("latest_available_snapshot") or {}
    event_context = load_replay_corporate_action_context(symbol, session_date, replay_context_list_name)
    liquidity_context = historical_context.get("liquidity_execution_context") or {}
    calibrated = lookup_replay_calibrated_confidence(action, confidence)
    calibrated_confidence_pct = calibrated.get("calibrated_confidence_pct")

    return {
        **base_record,
        "calendar_phase": _calendar_phase_label(calendar_flags),
        "macro_upload_year_month": macro_snapshot.get("upload_year_month"),
        "macro_period_end_year_month": macro_snapshot.get("period_end_year_month"),
        "interbank_rate_pct_current": _macro_value(macro_snapshot, "interbank_rate_pct"),
        "claims_private_sector_yoy_pct_current": _macro_value(macro_snapshot, "claims_private_sector_yoy_pct"),
        "private_credit_billion_current": _macro_value(macro_snapshot, "private_credit_billion"),
        "remittance_billion_current": _macro_value(macro_snapshot, "remittance_billion"),
        "remittance_yoy_pct": _derived_macro_value(macro_snapshot, "remittance_yoy_pct"),
        "event_state": _event_state_label(event_context),
        "dominant_event_type": event_context.get("dominant_event_type") or "none",
        "recent_event_count_90d": event_context.get("recent_event_count_90d"),
        "matched_event_count": event_context.get("matched_event_count"),
        "has_active_event": event_context.get("has_active_event"),
        "raw_confidence": confidence,
        "calibrated_confidence_pct": calibrated_confidence_pct,
        "confidence_interpretation_label": calibrated.get("confidence_interpretation_label") or "unknown",
        "confidence_reference_group": calibrated.get("reference_group"),
        "confidence_gap_pct": (
            round(float(calibrated_confidence_pct) - float(confidence), 4)
            if calibrated_confidence_pct is not None and confidence is not None else None
        ),
        "liquidity_profile": _liquidity_profile(liquidity_context),
        "turnover_ratio_5d_to_20d": ((liquidity_context.get("metrics") or {}).get("turnover_ratio_5d_to_20d")),
        "trades_ratio_5d_to_20d": ((liquidity_context.get("metrics") or {}).get("trades_ratio_5d_to_20d")),
        "latest_turnover_surprise_vs20d": ((liquidity_context.get("metrics") or {}).get("latest_turnover_surprise_vs20d")),
        "latest_trades_surprise_vs20d": ((liquidity_context.get("metrics") or {}).get("latest_trades_surprise_vs20d")),
        "avg_abs_gap_pct_20d": ((liquidity_context.get("metrics") or {}).get("avg_abs_gap_pct_20d")),
        "gap_over_2pct_share_20d": ((liquidity_context.get("metrics") or {}).get("gap_over_2pct_share_20d")),
        "liquidity_flags": liquidity_context.get("context_flags") or [],
    }


def _cohort_summary(records, cohort_name, description):
    return {
        "cohort_name": cohort_name,
        "description": description,
        "count": len(records),
        "month_counts": _count_map(records, "session_date", limit=200),
        "session_month_counts": dict(Counter(str(record.get("session_date") or "")[:7] for record in records)),
        "symbol_counts": _count_map(records, "symbol"),
        "action_counts": _count_map(records, "action"),
        "label_counts": _count_map(records, "next_open_label"),
        "verdict_counts": _count_map(records, "comparison_verdict"),
        "calendar_phase_counts": _count_map(records, "calendar_phase"),
        "event_state_counts": _count_map(records, "event_state"),
        "dominant_event_type_counts": _count_map(records, "dominant_event_type"),
        "confidence_interpretation_counts": _count_map(records, "confidence_interpretation_label"),
        "liquidity_profile_counts": _count_map(records, "liquidity_profile"),
        "macro_upload_month_counts": _count_map(records, "macro_upload_year_month"),
        "feature_means": {field_name: _mean(records, field_name) for field_name in NUMERIC_FIELDS},
        "example_cases": [
            {
                "session_date": record.get("session_date"),
                "symbol": record.get("symbol"),
                "action": record.get("action"),
                "next_open_label": record.get("next_open_label"),
                "comparison_verdict": record.get("comparison_verdict"),
                "calendar_phase": record.get("calendar_phase"),
                "event_state": record.get("event_state"),
                "confidence_interpretation_label": record.get("confidence_interpretation_label"),
                "target_distance_close_pct": record.get("target_distance_close_pct"),
                "risk_reward_ratio": record.get("risk_reward_ratio"),
                "return_5d_pct": record.get("return_5d_pct"),
                "return_20d_pct": record.get("return_20d_pct"),
                "next_open_gap_pct": record.get("next_open_gap_pct"),
            }
            for record in records[:10]
        ],
    }


def _render_markdown(summary):
    lines = [
        "# Commercial-Bank After-Close Regime Drift Study",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- source_path: `{summary['source_path']}`",
        f"- replay_context_list_name: `{summary['replay_context_list_name']}`",
        "",
        "## Short Answer",
        "",
        "This study compares earlier commercial-bank upside-gap paper wins against the July 2025 downside-damage bank window.",
        "It also compares July 2025 downside-damage cases against the few July 2025 bank cases that still stayed positive.",
        "",
    ]

    for cohort in summary.get("cohorts", []):
        lines.extend([
            f"## Cohort `{cohort['cohort_name']}`",
            "",
            f"- description: {cohort['description']}",
            f"- count: `{cohort['count']}`",
            f"- session_month_counts: `{cohort['session_month_counts']}`",
            f"- symbol_counts: `{cohort['symbol_counts']}`",
            f"- label_counts: `{cohort['label_counts']}`",
            f"- verdict_counts: `{cohort['verdict_counts']}`",
            f"- calendar_phase_counts: `{cohort['calendar_phase_counts']}`",
            f"- event_state_counts: `{cohort['event_state_counts']}`",
            f"- confidence_interpretation_counts: `{cohort['confidence_interpretation_counts']}`",
            f"- liquidity_profile_counts: `{cohort['liquidity_profile_counts']}`",
            f"- macro_upload_month_counts: `{cohort['macro_upload_month_counts']}`",
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


def build_commercial_bank_after_close_regime_drift_study(replay_context_list_name="@replay_basket_v1"):
    payload = load_json(LATEST_TRADABILITY_STUDY_PATH)
    base_records = payload.get("records") or []

    enriched_records = []
    for record in base_records:
        if record.get("sector_name") != "COMMERCIAL BANKS":
            continue
        enriched_records.append(_enrich_record(record, replay_context_list_name))

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

    comparisons = []
    comparison_pairs = [
        ("discovery_upside_gap", "july_2025_downside_damage"),
        ("july_2025_downside_damage", "july_2025_positive_survivors"),
    ]
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
        "replay_context_list_name": replay_context_list_name,
        "cohorts": cohort_rows,
        "comparisons": comparisons,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__commercial_bank_after_close_regime_drift_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__commercial_bank_after_close_regime_drift_study_v1.json",
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
    if len(sys.argv) > 2:
        print("Usage: python commercial_bank_after_close_regime_drift_study.py [REPLAY_CONTEXT_LIST_NAME]")
        sys.exit(1)

    replay_context_list_name = sys.argv[1] if len(sys.argv) == 2 else "@replay_basket_v1"
    summary, latest_json_path, latest_md_path = build_commercial_bank_after_close_regime_drift_study(replay_context_list_name)
    print(json.dumps({
        "cohort_count": len(summary.get("cohorts") or []),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
