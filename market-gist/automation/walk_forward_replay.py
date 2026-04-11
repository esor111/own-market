"""
Run a truth-only walk-forward replay on historical daily data.

Usage:
    python walk_forward_replay.py 2025-12-21 2025-12-31 EBL JBBL
    python walk_forward_replay.py 2025-12-21 2025-12-31 @controlled_expansion_v1
"""
import json
import os
import sys
import shutil
from collections import Counter
from datetime import datetime, timedelta

from config import REPLAYS_DIR, build_run_label, resolve_symbols
from data_sources import get_truth_source
from outcome_tracker import OutcomeTracker
from replay_bank_leadership_context import enrich_session_cases_with_bank_leadership_context
from replay_calendar import is_nepal_trading_weekday, load_replay_sessions
from replay_case_builder import DEFAULT_REPLAY_RULES, build_replay_case
from replay_confidence_remap import lookup_replay_calibrated_confidence
from replay_cross_section import enrich_session_cases_with_cross_section
from replay_regime_context import enrich_session_cases_with_regime_context
from replay_validated_sector_guidance import resolve_validated_sector_guidance


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _parse_date(value):
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _load_future_bars(symbol, session_date, truth_source_name="sharesansar_local", horizon_sessions=10):
    source = get_truth_source(truth_source_name)
    if not hasattr(source, "_iter_available_dates"):
        raise RuntimeError(f"Truth source does not expose replay sessions: {truth_source_name}")

    session_dt = _parse_date(session_date)
    future_sessions = [
        item for item in source._iter_available_dates(session_dt + timedelta(days=1), None)
        if is_nepal_trading_weekday(item)
    ][:horizon_sessions]
    if not future_sessions:
        return []

    payload = source.get_ticker_history(
        symbol,
        future_sessions[0].isoformat(),
        future_sessions[-1].isoformat(),
    )
    rows = (((payload or {}).get("history") or {}).get("content") or [])
    rows = sorted(rows, key=lambda row: row.get("businessDate") or "")
    future_bars = []
    for row in rows:
        business_date = row.get("businessDate")
        future_bars.append({
            "time": business_date,
            "open": row.get("openPrice"),
            "high": row.get("highPrice"),
            "low": row.get("lowPrice"),
            "close": row.get("closePrice"),
            "volume": row.get("totalTradedQuantity"),
            "close_time_ms": int(datetime.combine(_parse_date(business_date), datetime.max.time()).timestamp() * 1000),
        })
    return future_bars


def _horizon_return(current_close, future_bars, index):
    if current_close in (None, 0) or len(future_bars) <= index:
        return None
    future_close = future_bars[index].get("close")
    if future_close in (None, 0):
        return None
    return round(((float(future_close) / float(current_close)) - 1.0) * 100, 2)


def _comparison_reason_codes(frozen_case, decision, comparison_verdict, outcome_data, horizon_returns):
    metrics = frozen_case.get("metrics") or {}
    codes = set(decision.get("reason_codes") or [])

    if comparison_verdict in {"bad_call", "missed_opportunity"}:
        if metrics.get("liquidity_label") == "weak":
            codes.add("liquidity_weak")
        if decision.get("risk_reward_ratio") is not None and decision["risk_reward_ratio"] < 1.2:
            codes.add("rr_too_thin")
        if (metrics.get("close_position_20d") or 0) >= 0.92 and (metrics.get("volume_ratio_5d") or 0) < 1:
            codes.add("breakout_too_extended")
        if metrics.get("trend_label") in {"mixed", "unknown"}:
            codes.add("insufficient_confirmation")
    if comparison_verdict == "missed_opportunity":
        codes.add("avoid_too_strict")
    if comparison_verdict == "good_call" and outcome_data.get("outcome_label") == "target_1_hit":
        codes.add("valid_setup_followthrough")
    if comparison_verdict == "good_avoid" and (horizon_returns.get("return_10d_pct") or 0) < 0:
        codes.add("avoid_preserved_capital")

    return sorted(codes)


def _event_state_label(context):
    if context.get("has_active_event"):
        return "active_event"
    if int(context.get("recent_event_count_90d") or 0) > 0:
        return "recent_event_no_active"
    if int(context.get("matched_event_count") or 0) > 0:
        return "matched_but_stale"
    return "no_symbol_event_match"


def _calendar_phase_label(context):
    phase_labels = ((context.get("calendar_flags") or {}).get("phase_labels")) or []
    if not phase_labels:
        return "no_named_phase"
    return "+".join(sorted(str(item) for item in phase_labels))


def _comparison_verdict(frozen_case, action, outcome_data, horizon_returns):
    outcome_label = outcome_data.get("outcome_label")
    return_10d = horizon_returns.get("return_10d_pct")
    metrics = (frozen_case or {}).get("metrics") or {}

    if action in {"buy", "watch_only"}:
        if outcome_label in {"target_1_hit", "target_2_hit", "target_3_hit"} or (return_10d is not None and return_10d >= 5):
            return "good_call"
        if outcome_label == "stopped_out" or (return_10d is not None and return_10d <= -4):
            return "bad_call"
        return "mixed_call"

    if action == "avoid":
        had_positive_setup_bias = (
            metrics.get("trend_label") in {"uptrend", "improving"}
            or (metrics.get("return_20d_pct") or 0) > 0
            or (metrics.get("close_position_20d") or 0) >= 0.55
        )
        if outcome_label in {"target_1_hit", "target_2_hit", "target_3_hit"} or (
            return_10d is not None and return_10d >= 5 and had_positive_setup_bias
        ):
            return "missed_opportunity"
        if return_10d is not None and return_10d <= 3:
            return "good_avoid"
        return "neutral_avoid"

    return "unscored"


def _build_comparison_record(replay_id, frozen_case, decision, outcome_data, future_bars):
    current_close = frozen_case.get("latest_row", {}).get("closePrice")
    horizon_returns = {
        "return_1d_pct": _horizon_return(current_close, future_bars, 0),
        "return_5d_pct": _horizon_return(current_close, future_bars, 4),
        "return_10d_pct": _horizon_return(current_close, future_bars, 9),
    }
    verdict = _comparison_verdict(frozen_case, decision.get("action"), outcome_data, horizon_returns)
    reason_codes = _comparison_reason_codes(frozen_case, decision, verdict, outcome_data, horizon_returns)

    return {
        "schema_version": "1.0",
        "replay_id": replay_id,
        "session_id": decision.get("session_id"),
        "symbol": decision.get("symbol"),
        "session_date": decision.get("run_date"),
        "timeframe": decision.get("timeframe"),
        "prediction": {
            "action": decision.get("action"),
            "score": decision.get("score"),
            "confidence": decision.get("confidence"),
            "setup_type": decision.get("setup_type"),
            "risk_reward_ratio": decision.get("risk_reward_ratio"),
        },
        "outcome": outcome_data,
        "horizon_returns": horizon_returns,
        "comparison_verdict": verdict,
        "reason_codes": reason_codes,
        "captured_at": datetime.now().isoformat(),
    }


def _build_replay_summary(replay_id, start_date, end_date, truth_source_name, symbols, sessions, records):
    action_counts = Counter(record["decision"]["action"] for record in records)
    verdict_counts = Counter(record["comparison"]["comparison_verdict"] for record in records)
    reason_counts = Counter()
    for record in records:
        reason_counts.update(record["comparison"].get("reason_codes") or [])

    return_1d_values = [record["comparison"]["horizon_returns"]["return_1d_pct"] for record in records if record["comparison"]["horizon_returns"]["return_1d_pct"] is not None]
    return_5d_values = [record["comparison"]["horizon_returns"]["return_5d_pct"] for record in records if record["comparison"]["horizon_returns"]["return_5d_pct"] is not None]
    return_10d_values = [record["comparison"]["horizon_returns"]["return_10d_pct"] for record in records if record["comparison"]["horizon_returns"]["return_10d_pct"] is not None]

    def avg(values):
        return round(sum(values) / len(values), 2) if values else None

    def confidence_view(record):
        prediction = record["comparison"].get("prediction") or {}
        calibrated = lookup_replay_calibrated_confidence(
            prediction.get("action"),
            prediction.get("confidence"),
        )
        return {
            "raw_confidence": prediction.get("confidence"),
            "calibrated_confidence_pct": calibrated.get("calibrated_confidence_pct"),
            "confidence_interpretation_label": calibrated.get("confidence_interpretation_label"),
            "confidence_reference_group": calibrated.get("reference_group"),
        }

    return {
        "schema_version": "1.0",
        "replay_id": replay_id,
        "built_at": datetime.now().isoformat(),
        "truth_source": truth_source_name,
        "start_date": start_date,
        "end_date": end_date,
        "symbols": symbols,
        "session_count": len(sessions),
        "case_count": len(records),
        "action_counts": dict(action_counts),
        "comparison_verdict_counts": dict(verdict_counts),
        "average_return_1d_pct": avg(return_1d_values),
        "average_return_5d_pct": avg(return_5d_values),
        "average_return_10d_pct": avg(return_10d_values),
        "top_reason_codes": reason_counts.most_common(10),
        "records": [
            {
                **confidence_view(record),
                "session_id": record["decision"]["session_id"],
                "symbol": record["decision"]["symbol"],
                "session_date": record["decision"]["run_date"],
                "sector_name": record["frozen_case"].get("sector_name"),
                "action": record["decision"]["action"],
                "comparison_verdict": record["comparison"]["comparison_verdict"],
                "return_10d_pct": record["comparison"]["horizon_returns"]["return_10d_pct"],
                "reason_codes": record["comparison"]["reason_codes"],
                "leadership_label": ((record["frozen_case"].get("cross_sectional_context") or {}).get("leadership_label")),
                "basket_rank": ((record["frozen_case"].get("cross_sectional_context") or {}).get("basket_return_20d_rank")),
                "market_regime": ((record["frozen_case"].get("regime_context") or {}).get("market_proxy") or {}).get("regime_label"),
                "sector_regime": ((record["frozen_case"].get("regime_context") or {}).get("sector_proxy") or {}).get("regime_label"),
                "alignment_label": ((record["frozen_case"].get("regime_context") or {}).get("alignment_label")),
                "guidance_adjustment_total": ((record["decision"].get("validated_sector_guidance_adjustment") or {}).get("net_adjustment")),
                "guidance_action_change": (
                    ((record["decision"].get("validated_hydropower_buy_caution_guidance_adjustment") or {}).get("action_change"))
                    or ((record["decision"].get("validated_commercial_bank_overconfident_watch_caution_guidance_adjustment") or {}).get("action_change"))
                    or ((record["decision"].get("validated_commercial_bank_watch_caution_guidance_adjustment") or {}).get("action_change"))
                    or ((record["decision"].get("validated_bank_exhaustion_guidance_adjustment") or {}).get("action_change"))
                    or ((record["decision"].get("validated_calendar_confidence_guidance_adjustment") or {}).get("action_change"))
                    or ((record["decision"].get("validated_liquidity_guidance_adjustment") or {}).get("action_change"))
                    or ((record["decision"].get("validated_sector_guidance_adjustment") or {}).get("action_change"))
                ),
                "calendar_confidence_guidance_action_change": ((record["decision"].get("validated_calendar_confidence_guidance_adjustment") or {}).get("action_change")),
                "calendar_phase": _calendar_phase_label(((record["frozen_case"].get("historical_context") or {}).get("macro_calendar_context") or {})),
                "event_state": _event_state_label(((record["frozen_case"].get("historical_context") or {}).get("corporate_action_context") or {})),
                "liquidity_guidance_action_change": ((record["decision"].get("validated_liquidity_guidance_adjustment") or {}).get("action_change")),
                "liquidity_trigger_count": ((record["decision"].get("validated_liquidity_guidance_adjustment") or {}).get("trigger_count")),
                "bank_exhaustion_guidance_action_change": ((record["decision"].get("validated_bank_exhaustion_guidance_adjustment") or {}).get("action_change")),
                "commercial_bank_watch_caution_guidance_action_change": ((record["decision"].get("validated_commercial_bank_watch_caution_guidance_adjustment") or {}).get("action_change")),
                "commercial_bank_overconfident_watch_caution_guidance_action_change": ((record["decision"].get("validated_commercial_bank_overconfident_watch_caution_guidance_adjustment") or {}).get("action_change")),
                "hydropower_buy_caution_guidance_action_change": ((record["decision"].get("validated_hydropower_buy_caution_guidance_adjustment") or {}).get("action_change")),
                "bank_leadership_top2_count": ((record["frozen_case"].get("bank_leadership_context") or {}).get("leadership_top2_count")),
                "bank_return_5d_rank": ((record["frozen_case"].get("bank_leadership_context") or {}).get("return_5d_rank")),
                "bank_volume_ratio_rank": ((record["frozen_case"].get("bank_leadership_context") or {}).get("volume_ratio_rank")),
                "bank_close_position_rank": ((record["frozen_case"].get("bank_leadership_context") or {}).get("close_position_rank")),
            }
            for record in records
        ],
    }


def _apply_validated_sector_guidance(frozen_case, decision, rules):
    if not rules.get("use_validated_sector_guidance"):
        return decision

    allow_support_promotions = bool(rules.get("validated_sector_guidance_allow_support_promotions", True))
    allow_fragility_demotions = bool(rules.get("validated_sector_guidance_allow_fragility_demotions", True))
    sector_name = frozen_case.get("sector_name")
    alignment_name = ((frozen_case.get("regime_context") or {}).get("alignment_label"))
    guidance = resolve_validated_sector_guidance(sector_name, alignment_name)
    sector_guidance = guidance.get("sector_guidance") or {}
    alignment_guidance = guidance.get("alignment_guidance") or {}

    sector_label = sector_guidance.get("guidance_label")
    alignment_label = alignment_guidance.get("guidance_label")
    raw_sector_points = {
        "validated_actionable_support": 4,
        "validated_fragility_caution": -4,
        "validated_avoid_support": -4,
    }.get(sector_label, 0)
    raw_alignment_points = {
        "validated_constructive_zone": 3,
        "validated_avoid_zone": -5,
    }.get(alignment_label, 0)
    sector_points = raw_sector_points if (raw_sector_points <= 0 or allow_support_promotions) and (raw_sector_points >= 0 or allow_fragility_demotions) else 0
    alignment_points = raw_alignment_points if (raw_alignment_points <= 0 or allow_support_promotions) and (raw_alignment_points >= 0 or allow_fragility_demotions) else 0
    net_adjustment = sector_points + alignment_points

    metrics = frozen_case.get("metrics") or {}
    close_position = metrics.get("close_position_20d") or 0
    trend_label = metrics.get("trend_label")
    liquidity_label = metrics.get("liquidity_label")
    rr = decision.get("risk_reward_ratio")
    original_action = decision.get("action")
    updated_action = original_action
    action_change = None

    buy_rr_min = float(rules.get("buy_rr_min", 1.2))
    buy_close_position_min = float(rules.get("buy_close_position_min", 0.75))
    watch_close_position_min = float(rules.get("watch_close_position_min", 0.55))

    if (
        allow_support_promotions
        and original_action == "watch_only"
        and net_adjustment >= 7
        and trend_label == "uptrend"
        and liquidity_label in {"acceptable", "strong"}
        and close_position >= max(0.0, buy_close_position_min - 0.03)
        and rr not in (None, 0)
        and rr >= max(1.0, buy_rr_min - 0.2)
    ):
        updated_action = "buy"
        action_change = "watch_only_to_buy"
    elif (
        allow_fragility_demotions
        and original_action == "buy"
        and net_adjustment <= -4
        and (
            rr in (None, 0)
            or rr < (buy_rr_min + 0.15)
            or close_position < (buy_close_position_min + 0.03)
            or trend_label != "uptrend"
        )
    ):
        updated_action = "watch_only"
        action_change = "buy_to_watch_only"
    elif (
        allow_fragility_demotions
        and
        original_action == "watch_only"
        and net_adjustment <= -4
        and (
            rr in (None, 0)
            or rr < 1.0
            or close_position < (watch_close_position_min + 0.05)
            or trend_label not in {"uptrend", "improving"}
        )
    ):
        updated_action = "avoid"
        action_change = "watch_only_to_avoid"

    adjusted_decision = dict(decision)
    adjusted_decision["score"] = min(100, max(0, int((decision.get("score") or 0) + net_adjustment)))
    adjusted_decision["confidence"] = min(95, max(20, int((decision.get("confidence") or 0) + net_adjustment)))
    adjusted_decision["action"] = updated_action
    adjusted_decision["validated_sector_guidance_adjustment"] = {
        "enabled": True,
        "allow_support_promotions": allow_support_promotions,
        "allow_fragility_demotions": allow_fragility_demotions,
        "sector_name": sector_name,
        "alignment_name": alignment_name,
        "sector_guidance_label": sector_label,
        "alignment_guidance_label": alignment_label,
        "sector_points": sector_points,
        "alignment_points": alignment_points,
        "net_adjustment": net_adjustment,
        "action_change": action_change,
        "use_as": guidance.get("use_as"),
        "do_not_use_as_hard_rule": guidance.get("do_not_use_as_hard_rule", True),
    }

    if net_adjustment > 0 and allow_support_promotions:
        reason_list = list(adjusted_decision.get("reason_list") or [])
        if "validated sector context is supportive" not in reason_list:
            reason_list.append("validated sector context is supportive")
        adjusted_decision["reason_list"] = reason_list
    elif net_adjustment < 0 and allow_fragility_demotions:
        warnings = list(adjusted_decision.get("warnings") or [])
        if "validated sector context suggests added fragility" not in warnings:
            warnings.append("validated sector context suggests added fragility")
        adjusted_decision["warnings"] = warnings

    reason_codes = set(adjusted_decision.get("reason_codes") or [])
    if sector_label == "validated_actionable_support" and allow_support_promotions:
        reason_codes.add("validated_sector_support")
    if sector_label in {"validated_fragility_caution", "validated_avoid_support"} and allow_fragility_demotions:
        reason_codes.add("validated_sector_caution")
    if alignment_label == "validated_constructive_zone" and allow_support_promotions:
        reason_codes.add("validated_alignment_support")
    if alignment_label == "validated_avoid_zone" and allow_fragility_demotions:
        reason_codes.add("validated_alignment_caution")
    adjusted_decision["reason_codes"] = sorted(reason_codes)
    return adjusted_decision


def _apply_validated_liquidity_guidance(frozen_case, decision, rules):
    if not rules.get("use_validated_liquidity_guidance"):
        return decision

    sector_name = frozen_case.get("sector_name")
    alignment_name = ((frozen_case.get("regime_context") or {}).get("alignment_label"))
    liquidity_context = ((frozen_case.get("historical_context") or {}).get("liquidity_execution_context") or {})
    metrics = liquidity_context.get("metrics") or {}

    target_sector = str(rules.get("validated_liquidity_sector_name") or "").upper()
    target_alignment = str(rules.get("validated_liquidity_alignment_label") or "")
    threshold_map = {
        "turnover_ratio_5d_to_20d": float(rules.get("validated_liquidity_turnover_ratio_threshold", 1.64)),
        "latest_turnover_surprise_vs20d": float(rules.get("validated_liquidity_turnover_surprise_threshold", 2.03)),
        "latest_trades_surprise_vs20d": float(rules.get("validated_liquidity_trades_surprise_threshold", 1.77)),
    }
    min_trigger_count = int(rules.get("validated_liquidity_min_trigger_count", 2))

    original_action = decision.get("action")
    updated_action = original_action
    action_change = None
    triggered_metrics = []
    slice_match = (
        original_action == "watch_only"
        and str(sector_name or "").upper() == target_sector
        and str(alignment_name or "") == target_alignment
    )

    if slice_match:
        for metric_name, threshold_value in threshold_map.items():
            metric_value = metrics.get(metric_name)
            if metric_value is not None and float(metric_value) >= threshold_value:
                triggered_metrics.append({
                    "metric_name": metric_name,
                    "metric_value": round(float(metric_value), 4),
                    "threshold": threshold_value,
                })
        if len(triggered_metrics) >= min_trigger_count:
            updated_action = "avoid"
            action_change = "watch_only_to_avoid"

    adjusted_decision = dict(decision)
    adjusted_decision["action"] = updated_action
    adjusted_decision["validated_liquidity_guidance_adjustment"] = {
        "enabled": True,
        "sector_name": sector_name,
        "alignment_name": alignment_name,
        "slice_match": slice_match,
        "guidance_label": "validated_supportive_hydropower_overheat_caution" if slice_match else None,
        "trigger_count": len(triggered_metrics),
        "triggered_metrics": triggered_metrics,
        "thresholds": threshold_map,
        "min_trigger_count": min_trigger_count,
        "action_change": action_change,
        "use_as": "challenger_only",
        "do_not_use_as_hard_rule": True,
    }

    if action_change:
        warnings = list(adjusted_decision.get("warnings") or [])
        warning_text = "validated liquidity context suggests overheat risk for supportive hydropower setups"
        if warning_text not in warnings:
            warnings.append(warning_text)
        adjusted_decision["warnings"] = warnings

        reason_codes = set(adjusted_decision.get("reason_codes") or [])
        reason_codes.add("validated_liquidity_overheat_caution")
        adjusted_decision["reason_codes"] = sorted(reason_codes)

    return adjusted_decision


def _apply_validated_calendar_confidence_guidance(frozen_case, decision, rules):
    if not rules.get("use_validated_calendar_confidence_guidance"):
        return decision

    historical_context = frozen_case.get("historical_context") or {}
    macro_context = historical_context.get("macro_calendar_context") or {}
    event_context = historical_context.get("corporate_action_context") or {}
    calendar_phase = _calendar_phase_label(macro_context)
    event_state = _event_state_label(event_context)
    calibrated = lookup_replay_calibrated_confidence(
        decision.get("action"),
        decision.get("confidence"),
    )
    confidence_label = calibrated.get("confidence_interpretation_label")
    sector_name = str(frozen_case.get("sector_name") or "")
    normalized_sector_name = sector_name.upper()
    hostile_phases = {str(item) for item in (rules.get("validated_calendar_confidence_hostile_phases") or [])}
    required_event_states = {str(item) for item in (rules.get("validated_calendar_confidence_required_event_states") or [])}
    required_labels = {str(item) for item in (rules.get("validated_calendar_confidence_required_labels") or [])}
    allowed_sectors = {
        str(item).upper() for item in (rules.get("validated_calendar_confidence_allowed_sectors") or [])
        if str(item).strip()
    }
    blocked_sectors = {
        str(item).upper() for item in (rules.get("validated_calendar_confidence_blocked_sectors") or [])
        if str(item).strip()
    }
    sector_allowed = (
        normalized_sector_name not in blocked_sectors
        and (not allowed_sectors or normalized_sector_name in allowed_sectors)
    )

    original_action = decision.get("action")
    updated_action = original_action
    action_change = None
    trigger_match = (
        original_action in {"buy", "watch_only"}
        and calendar_phase in hostile_phases
        and event_state in required_event_states
        and confidence_label in required_labels
        and sector_allowed
    )

    if trigger_match:
        if original_action == "buy":
            updated_action = "watch_only"
            action_change = "buy_to_watch_only"
        elif original_action == "watch_only":
            updated_action = "avoid"
            action_change = "watch_only_to_avoid"

    adjusted_decision = dict(decision)
    adjusted_decision["action"] = updated_action
    adjusted_decision["validated_calendar_confidence_guidance_adjustment"] = {
        "enabled": True,
        "calendar_phase": calendar_phase,
        "event_state": event_state,
        "sector_name": sector_name,
        "sector_allowed": sector_allowed,
        "confidence_interpretation_label": confidence_label,
        "calibrated_confidence_pct": calibrated.get("calibrated_confidence_pct"),
        "reference_group": calibrated.get("reference_group"),
        "trigger_match": trigger_match,
        "hostile_phases": sorted(hostile_phases),
        "required_event_states": sorted(required_event_states),
        "required_labels": sorted(required_labels),
        "allowed_sectors": sorted(allowed_sectors),
        "blocked_sectors": sorted(blocked_sectors),
        "action_change": action_change,
        "use_as": "guarded_champion_rule",
        "do_not_use_as_hard_rule": False,
    }

    if action_change:
        warnings = list(adjusted_decision.get("warnings") or [])
        warning_text = "validated calendar-confidence context suggests actionable overreach in a hostile window"
        if warning_text not in warnings:
            warnings.append(warning_text)
        adjusted_decision["warnings"] = warnings

        reason_codes = set(adjusted_decision.get("reason_codes") or [])
        reason_codes.add("validated_calendar_confidence_caution")
        adjusted_decision["reason_codes"] = sorted(reason_codes)

    return adjusted_decision


def _apply_validated_bank_exhaustion_guidance(frozen_case, decision, rules):
    if not rules.get("use_validated_bank_exhaustion_guidance"):
        return decision

    historical_context = frozen_case.get("historical_context") or {}
    macro_context = historical_context.get("macro_calendar_context") or {}
    calendar_phase = _calendar_phase_label(macro_context)
    bank_context = frozen_case.get("bank_leadership_context") or {}
    metrics = frozen_case.get("metrics") or {}
    sector_name = str(frozen_case.get("sector_name") or "")
    normalized_sector_name = sector_name.upper()

    hostile_phases = {str(item) for item in (rules.get("validated_bank_exhaustion_hostile_phases") or [])}
    allowed_sectors = {
        str(item).upper() for item in (rules.get("validated_bank_exhaustion_allowed_sectors") or [])
        if str(item).strip()
    }
    sector_allowed = (not allowed_sectors) or normalized_sector_name in allowed_sectors
    return_20d_min = float(rules.get("validated_bank_exhaustion_return_20d_min", 6.45))
    leadership_top2_min = int(rules.get("validated_bank_exhaustion_leadership_top2_min", 1))
    return_20d_pct = metrics.get("return_20d_pct")
    leadership_top2_count = int(bank_context.get("leadership_top2_count") or 0)

    original_action = decision.get("action")
    updated_action = original_action
    action_change = None
    trigger_match = (
        original_action in {"buy", "watch_only"}
        and calendar_phase in hostile_phases
        and sector_allowed
        and return_20d_pct is not None
        and float(return_20d_pct) >= return_20d_min
        and leadership_top2_count >= leadership_top2_min
    )

    if trigger_match:
        if original_action == "buy":
            updated_action = "watch_only"
            action_change = "buy_to_watch_only"
        elif original_action == "watch_only":
            updated_action = "avoid"
            action_change = "watch_only_to_avoid"

    adjusted_decision = dict(decision)
    adjusted_decision["action"] = updated_action
    adjusted_decision["validated_bank_exhaustion_guidance_adjustment"] = {
        "enabled": True,
        "calendar_phase": calendar_phase,
        "sector_name": sector_name,
        "sector_allowed": sector_allowed,
        "return_20d_pct": return_20d_pct,
        "return_20d_min": return_20d_min,
        "leadership_top2_count": leadership_top2_count,
        "leadership_top2_min": leadership_top2_min,
        "leader_like": bool(bank_context.get("leader_like")),
        "leadership_composite_rank": bank_context.get("leadership_composite_rank"),
        "trigger_match": trigger_match,
        "hostile_phases": sorted(hostile_phases),
        "allowed_sectors": sorted(allowed_sectors),
        "action_change": action_change,
        "use_as": "challenger_only",
        "do_not_use_as_hard_rule": True,
    }

    if action_change:
        warnings = list(adjusted_decision.get("warnings") or [])
        warning_text = "validated bank exhaustion context suggests leader-like hostile-window extension risk"
        if warning_text not in warnings:
            warnings.append(warning_text)
        adjusted_decision["warnings"] = warnings

        reason_codes = set(adjusted_decision.get("reason_codes") or [])
        reason_codes.add("validated_bank_exhaustion_caution")
        adjusted_decision["reason_codes"] = sorted(reason_codes)

    return adjusted_decision


def _apply_validated_hydropower_buy_caution_guidance(frozen_case, decision, rules):
    if not rules.get("use_validated_hydropower_buy_caution_guidance"):
        return decision

    historical_context = frozen_case.get("historical_context") or {}
    macro_context = historical_context.get("macro_calendar_context") or {}
    event_context = historical_context.get("corporate_action_context") or {}
    metrics = frozen_case.get("metrics") or {}
    calendar_phase = _calendar_phase_label(macro_context)
    event_state = _event_state_label(event_context)
    calibrated = lookup_replay_calibrated_confidence(
        decision.get("action"),
        decision.get("confidence"),
    )
    confidence_label = calibrated.get("confidence_interpretation_label")
    sector_name = str(frozen_case.get("sector_name") or "")
    normalized_sector_name = sector_name.upper()

    hostile_phases = {str(item) for item in (rules.get("validated_hydropower_buy_caution_hostile_phases") or [])}
    allowed_sectors = {
        str(item).upper() for item in (rules.get("validated_hydropower_buy_caution_allowed_sectors") or [])
        if str(item).strip()
    }
    required_event_states = {
        str(item) for item in (rules.get("validated_hydropower_buy_caution_required_event_states") or [])
    }
    required_labels = {
        str(item) for item in (rules.get("validated_hydropower_buy_caution_required_labels") or [])
    }
    return_20d_min = float(rules.get("validated_hydropower_buy_caution_return_20d_min", 30.0))
    close_position_20d_min = float(rules.get("validated_hydropower_buy_caution_close_position_20d_min", 0.98))
    return_20d_pct = metrics.get("return_20d_pct")
    close_position_20d = metrics.get("close_position_20d")

    original_action = decision.get("action")
    updated_action = original_action
    action_change = None
    trigger_match = (
        original_action == "buy"
        and calendar_phase in hostile_phases
        and ((not allowed_sectors) or normalized_sector_name in allowed_sectors)
        and event_state in required_event_states
        and confidence_label in required_labels
        and return_20d_pct is not None
        and float(return_20d_pct) >= return_20d_min
        and close_position_20d is not None
        and float(close_position_20d) >= close_position_20d_min
    )

    if trigger_match:
        updated_action = "watch_only"
        action_change = "buy_to_watch_only"

    adjusted_decision = dict(decision)
    adjusted_decision["action"] = updated_action
    adjusted_decision["validated_hydropower_buy_caution_guidance_adjustment"] = {
        "enabled": True,
        "calendar_phase": calendar_phase,
        "event_state": event_state,
        "sector_name": sector_name,
        "confidence_interpretation_label": confidence_label,
        "calibrated_confidence_pct": calibrated.get("calibrated_confidence_pct"),
        "return_20d_pct": return_20d_pct,
        "return_20d_min": return_20d_min,
        "close_position_20d": close_position_20d,
        "close_position_20d_min": close_position_20d_min,
        "trigger_match": trigger_match,
        "hostile_phases": sorted(hostile_phases),
        "allowed_sectors": sorted(allowed_sectors),
        "required_event_states": sorted(required_event_states),
        "required_labels": sorted(required_labels),
        "action_change": action_change,
        "use_as": "challenger_only",
        "do_not_use_as_hard_rule": True,
    }

    if action_change:
        warnings = list(adjusted_decision.get("warnings") or [])
        warning_text = "validated hydropower hostile-window buy context suggests overextended buy risk"
        if warning_text not in warnings:
            warnings.append(warning_text)
        adjusted_decision["warnings"] = warnings

        reason_codes = set(adjusted_decision.get("reason_codes") or [])
        reason_codes.add("validated_hydropower_buy_caution")
        adjusted_decision["reason_codes"] = sorted(reason_codes)

    return adjusted_decision


def _apply_validated_commercial_bank_watch_caution_guidance(frozen_case, decision, rules):
    if not rules.get("use_validated_commercial_bank_watch_caution_guidance"):
        return decision

    historical_context = frozen_case.get("historical_context") or {}
    macro_context = historical_context.get("macro_calendar_context") or {}
    event_context = historical_context.get("corporate_action_context") or {}
    metrics = frozen_case.get("metrics") or {}
    calendar_phase = _calendar_phase_label(macro_context)
    event_state = _event_state_label(event_context)
    calibrated = lookup_replay_calibrated_confidence(
        decision.get("action"),
        decision.get("confidence"),
    )
    confidence_label = calibrated.get("confidence_interpretation_label")
    sector_name = str(frozen_case.get("sector_name") or "")
    normalized_sector_name = sector_name.upper()

    hostile_phases = {str(item) for item in (rules.get("validated_commercial_bank_watch_caution_hostile_phases") or [])}
    allowed_sectors = {
        str(item).upper() for item in (rules.get("validated_commercial_bank_watch_caution_allowed_sectors") or [])
        if str(item).strip()
    }
    required_event_states = {
        str(item) for item in (rules.get("validated_commercial_bank_watch_caution_required_event_states") or [])
    }
    required_labels = {
        str(item) for item in (rules.get("validated_commercial_bank_watch_caution_required_labels") or [])
    }
    return_20d_min = float(rules.get("validated_commercial_bank_watch_caution_return_20d_min", 10.32))
    close_position_20d_min = float(rules.get("validated_commercial_bank_watch_caution_close_position_20d_min", 0.941))
    rr_min = float(rules.get("validated_commercial_bank_watch_caution_rr_min", 1.5))
    return_20d_pct = metrics.get("return_20d_pct")
    close_position_20d = metrics.get("close_position_20d")
    risk_reward_ratio = decision.get("risk_reward_ratio")

    original_action = decision.get("action")
    updated_action = original_action
    action_change = None
    trigger_match = (
        original_action == "watch_only"
        and calendar_phase in hostile_phases
        and ((not allowed_sectors) or normalized_sector_name in allowed_sectors)
        and event_state in required_event_states
        and confidence_label in required_labels
        and return_20d_pct is not None and float(return_20d_pct) >= return_20d_min
        and close_position_20d is not None and float(close_position_20d) >= close_position_20d_min
        and risk_reward_ratio is not None and float(risk_reward_ratio) >= rr_min
    )
    if trigger_match:
        updated_action = "avoid"
        action_change = "watch_only_to_avoid"

    adjusted_decision = dict(decision)
    adjusted_decision["action"] = updated_action
    adjusted_decision["validated_commercial_bank_watch_caution_guidance_adjustment"] = {
        "enabled": True,
        "calendar_phase": calendar_phase,
        "event_state": event_state,
        "sector_name": sector_name,
        "confidence_interpretation_label": confidence_label,
        "calibrated_confidence_pct": calibrated.get("calibrated_confidence_pct"),
        "return_20d_pct": return_20d_pct,
        "return_20d_min": return_20d_min,
        "close_position_20d": close_position_20d,
        "close_position_20d_min": close_position_20d_min,
        "risk_reward_ratio": risk_reward_ratio,
        "risk_reward_ratio_min": rr_min,
        "trigger_match": trigger_match,
        "hostile_phases": sorted(hostile_phases),
        "required_event_states": sorted(required_event_states),
        "required_labels": sorted(required_labels),
        "allowed_sectors": sorted(allowed_sectors),
        "action_change": action_change,
        "use_as": "research_only_challenger",
        "do_not_use_as_hard_rule": True,
    }

    if action_change:
        warnings = list(adjusted_decision.get("warnings") or [])
        warnings.append("validated hostile-window commercial-bank watch context suggests stretched watch-only failure risk")
        adjusted_decision["warnings"] = warnings

        reason_codes = set(adjusted_decision.get("reason_codes") or [])
        reason_codes.add("validated_commercial_bank_watch_caution")
        adjusted_decision["reason_codes"] = sorted(reason_codes)

    return adjusted_decision


def _apply_validated_commercial_bank_overconfident_watch_caution_guidance(frozen_case, decision, rules):
    if not rules.get("use_validated_commercial_bank_overconfident_watch_caution_guidance"):
        return decision

    historical_context = frozen_case.get("historical_context") or {}
    macro_context = historical_context.get("macro_calendar_context") or {}
    event_context = historical_context.get("corporate_action_context") or {}
    metrics = frozen_case.get("metrics") or {}
    calendar_phase = _calendar_phase_label(macro_context)
    event_state = _event_state_label(event_context)
    calibrated = lookup_replay_calibrated_confidence(
        decision.get("action"),
        decision.get("confidence"),
    )
    confidence_label = calibrated.get("confidence_interpretation_label")
    sector_name = str(frozen_case.get("sector_name") or "")
    normalized_sector_name = sector_name.upper()

    hostile_phases = {
        str(item)
        for item in (rules.get("validated_commercial_bank_overconfident_watch_caution_hostile_phases") or [])
    }
    allowed_sectors = {
        str(item).upper()
        for item in (rules.get("validated_commercial_bank_overconfident_watch_caution_allowed_sectors") or [])
        if str(item).strip()
    }
    required_event_states = {
        str(item)
        for item in (rules.get("validated_commercial_bank_overconfident_watch_caution_required_event_states") or [])
    }
    required_labels = {
        str(item)
        for item in (rules.get("validated_commercial_bank_overconfident_watch_caution_required_labels") or [])
    }
    return_5d_max = float(
        rules.get("validated_commercial_bank_overconfident_watch_caution_return_5d_max", 2.38)
    )
    volume_ratio_5d_max = float(
        rules.get("validated_commercial_bank_overconfident_watch_caution_volume_ratio_5d_max", 1.07)
    )
    return_5d_pct = metrics.get("return_5d_pct")
    volume_ratio_5d = metrics.get("volume_ratio_5d")

    original_action = decision.get("action")
    updated_action = original_action
    action_change = None
    weak_short_push = return_5d_pct is not None and float(return_5d_pct) <= return_5d_max
    weak_participation = volume_ratio_5d is not None and float(volume_ratio_5d) <= volume_ratio_5d_max
    trigger_match = (
        original_action == "watch_only"
        and calendar_phase in hostile_phases
        and ((not allowed_sectors) or normalized_sector_name in allowed_sectors)
        and event_state in required_event_states
        and confidence_label in required_labels
        and (weak_short_push or weak_participation)
    )

    if trigger_match:
        updated_action = "avoid"
        action_change = "watch_only_to_avoid"

    adjusted_decision = dict(decision)
    adjusted_decision["action"] = updated_action
    adjusted_decision["validated_commercial_bank_overconfident_watch_caution_guidance_adjustment"] = {
        "enabled": True,
        "calendar_phase": calendar_phase,
        "event_state": event_state,
        "sector_name": sector_name,
        "confidence_interpretation_label": confidence_label,
        "calibrated_confidence_pct": calibrated.get("calibrated_confidence_pct"),
        "return_5d_pct": return_5d_pct,
        "return_5d_max": return_5d_max,
        "volume_ratio_5d": volume_ratio_5d,
        "volume_ratio_5d_max": volume_ratio_5d_max,
        "weak_short_push": weak_short_push,
        "weak_participation": weak_participation,
        "trigger_match": trigger_match,
        "hostile_phases": sorted(hostile_phases),
        "required_event_states": sorted(required_event_states),
        "required_labels": sorted(required_labels),
        "allowed_sectors": sorted(allowed_sectors),
        "action_change": action_change,
        "use_as": "guarded_champion_rule",
        "do_not_use_as_hard_rule": False,
    }

    if action_change:
        warnings = list(adjusted_decision.get("warnings") or [])
        warning_text = "validated hostile-window bank watch context suggests stale overconfident continuation risk"
        if warning_text not in warnings:
            warnings.append(warning_text)
        adjusted_decision["warnings"] = warnings

        reason_codes = set(adjusted_decision.get("reason_codes") or [])
        reason_codes.add("validated_commercial_bank_overconfident_watch_caution")
        adjusted_decision["reason_codes"] = sorted(reason_codes)

    return adjusted_decision


def run_walk_forward_replay(start_date, end_date, symbols, truth_source_name="sharesansar_local", rule_overrides=None, replay_suffix=None):
    sessions_payload = load_replay_sessions(start_date, end_date, truth_source_name)
    sessions = sessions_payload["sessions"]
    run_label = build_run_label(symbols, [symbol for symbol in resolve_symbols(symbols)])
    replay_context_list_name = symbols[0] if len(symbols) == 1 and str(symbols[0]).startswith("@") else None
    rules = {**DEFAULT_REPLAY_RULES, **(rule_overrides or {})}
    suffix = replay_suffix or "daily_truth_replay_v1"
    replay_id = f"{start_date}_to_{end_date}__{run_label}__{suffix}"
    replay_root = os.path.join(REPLAYS_DIR, replay_id)

    if os.path.isdir(replay_root):
        shutil.rmtree(replay_root)

    tracker = OutcomeTracker()
    records = []

    resolved_symbols = resolve_symbols(symbols)
    for session_date in sessions:
        session_cases = []
        for symbol in resolved_symbols:
            try:
                frozen_case, decision = build_replay_case(
                    symbol,
                    session_date,
                    truth_source_name,
                    rules=rules,
                    replay_context_list_name=replay_context_list_name,
                )
            except FileNotFoundError:
                continue
            session_cases.append({
                "symbol": symbol,
                "frozen_case": frozen_case,
                "decision": decision,
            })

        session_cases = enrich_session_cases_with_cross_section(session_cases)
        session_cases = enrich_session_cases_with_bank_leadership_context(session_cases)
        session_cases = enrich_session_cases_with_regime_context(session_cases)

        for session_case in session_cases:
            symbol = session_case["symbol"]
            frozen_case = session_case["frozen_case"]
            decision = _apply_validated_sector_guidance(frozen_case, session_case["decision"], rules)
            decision = _apply_validated_calendar_confidence_guidance(frozen_case, decision, rules)
            decision = _apply_validated_liquidity_guidance(frozen_case, decision, rules)
            decision = _apply_validated_bank_exhaustion_guidance(frozen_case, decision, rules)
            decision = _apply_validated_commercial_bank_watch_caution_guidance(frozen_case, decision, rules)
            decision = _apply_validated_commercial_bank_overconfident_watch_caution_guidance(frozen_case, decision, rules)
            decision = _apply_validated_hydropower_buy_caution_guidance(frozen_case, decision, rules)

            future_bars = _load_future_bars(symbol, session_date, truth_source_name, horizon_sessions=10)
            outcome_data = tracker.evaluate(decision, future_bars, session_date, "1D")
            comparison = _build_comparison_record(replay_id, frozen_case, decision, outcome_data, future_bars)

            symbol_dir = os.path.join(replay_root, "sessions", session_date, symbol)
            raw_path = os.path.join(symbol_dir, "raw", f"{session_date}__{symbol}__future_bars.json")
            frozen_path = os.path.join(symbol_dir, "normalized", f"{session_date}__{symbol}__frozen_case_v1.json")
            decision_path = os.path.join(symbol_dir, "derived", f"{session_date}__{symbol}__replay_decision_v1.json")
            outcome_path = os.path.join(symbol_dir, "derived", f"{session_date}__{symbol}__replay_outcome_v1.json")
            comparison_path = os.path.join(symbol_dir, "comparisons", f"{session_date}__{symbol}__comparison_v1.json")

            save_json(raw_path, {"session_date": session_date, "symbol": symbol, "future_bars": future_bars})
            save_json(frozen_path, frozen_case)
            save_json(decision_path, decision)
            save_json(outcome_path, outcome_data)
            save_json(comparison_path, comparison)

            records.append({
                "frozen_case": frozen_case,
                "decision": decision,
                "outcome": outcome_data,
                "comparison": comparison,
                "paths": {
                    "raw_future_bars": raw_path,
                    "frozen_case": frozen_path,
                    "decision": decision_path,
                    "outcome": outcome_path,
                    "comparison": comparison_path,
                },
            })

    summary = _build_replay_summary(
        replay_id,
        start_date,
        end_date,
        truth_source_name,
        resolved_symbols,
        sessions,
        records,
    )
    summary_dir = os.path.join(replay_root, "summaries")
    dated_summary_path = os.path.join(summary_dir, f"{datetime.now().strftime('%Y-%m-%d')}__replay_summary_v1.json")
    latest_summary_path = os.path.join(summary_dir, "latest__replay_summary_v1.json")
    save_json(dated_summary_path, summary)
    save_json(latest_summary_path, summary)

    return {
        "replay_id": replay_id,
        "replay_root": replay_root,
        "dated_summary_path": dated_summary_path,
        "latest_summary_path": latest_summary_path,
        "summary": summary,
        "rules": rules,
    }


def main():
    if len(sys.argv) < 4:
        print("Usage: python walk_forward_replay.py START_DATE END_DATE SYMBOL_OR_LIST ...")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]
    symbols = sys.argv[3:]
    result = run_walk_forward_replay(start_date, end_date, symbols)
    print(json.dumps({
        "replay_id": result["replay_id"],
        "replay_root": result["replay_root"],
        "dated_summary_path": result["dated_summary_path"],
        "latest_summary_path": result["latest_summary_path"],
        "case_count": result["summary"]["case_count"],
        "action_counts": result["summary"]["action_counts"],
        "comparison_verdict_counts": result["summary"]["comparison_verdict_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
