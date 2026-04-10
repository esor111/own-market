"""
Build a point-in-time replay case from historical truth data only.

Usage:
    python replay_case_builder.py EBL 2025-12-31
"""
import json
import sys
from datetime import datetime, timedelta

from data_sources import get_truth_source
from replay_backfill_context import load_replay_context_bundle
from replay_calendar import is_nepal_trading_weekday
from replay_corporate_action_context import load_replay_corporate_action_context
from replay_liquidity_upgrade import build_replay_liquidity_execution_context
from replay_macro_calendar_context import load_replay_macro_calendar_context


DEFAULT_REPLAY_RULES = {
    "buy_rr_min": 1.2,
    "watch_rr_min": 0.0,
    "buy_close_position_min": 0.75,
    "watch_close_position_min": 0.55,
    "buy_volume_ratio_min": 0.0,
    "buy_score_min": 0,
    "watch_score_min": 0,
    "improving_watch_close_position_min": 0.55,
    "use_validated_sector_guidance": True,
    "validated_sector_guidance_allow_support_promotions": False,
    "validated_sector_guidance_allow_fragility_demotions": True,
    "use_validated_liquidity_guidance": False,
    "validated_liquidity_sector_name": "HYDROPOWER",
    "validated_liquidity_alignment_label": "both_supportive",
    "validated_liquidity_turnover_ratio_threshold": 1.64,
    "validated_liquidity_turnover_surprise_threshold": 2.03,
    "validated_liquidity_trades_surprise_threshold": 1.77,
    "validated_liquidity_min_trigger_count": 2,
    "use_validated_calendar_confidence_guidance": True,
    "validated_calendar_confidence_hostile_phases": [
        "fiscal_year_end_window",
        "post_fiscal_results_window",
    ],
    "validated_calendar_confidence_required_event_states": [
        "matched_but_stale",
    ],
    "validated_calendar_confidence_required_labels": [
        "strongly_overconfident",
    ],
    "validated_calendar_confidence_allowed_sectors": [
        "COMMERCIAL BANKS",
        "DEVELOPMENT BANKS",
    ],
    "validated_calendar_confidence_blocked_sectors": [
        "HYDROPOWER",
    ],
    "use_validated_bank_exhaustion_guidance": False,
    "validated_bank_exhaustion_hostile_phases": [
        "fiscal_year_end_window",
        "post_fiscal_results_window",
    ],
    "validated_bank_exhaustion_allowed_sectors": [
        "COMMERCIAL BANKS",
    ],
    "validated_bank_exhaustion_return_20d_min": 6.45,
    "validated_bank_exhaustion_leadership_top2_min": 1,
    "use_validated_hydropower_buy_caution_guidance": False,
    "validated_hydropower_buy_caution_hostile_phases": [
        "fiscal_year_end_window",
        "post_fiscal_results_window",
    ],
    "validated_hydropower_buy_caution_allowed_sectors": [
        "HYDROPOWER",
    ],
    "validated_hydropower_buy_caution_required_event_states": [
        "matched_but_stale",
    ],
    "validated_hydropower_buy_caution_required_labels": [
        "strongly_overconfident",
    ],
    "validated_hydropower_buy_caution_return_20d_min": 30.0,
    "validated_hydropower_buy_caution_close_position_20d_min": 0.98,
    "use_validated_commercial_bank_watch_caution_guidance": True,
    "validated_commercial_bank_watch_caution_hostile_phases": [
        "fiscal_year_end_window",
        "post_fiscal_results_window",
    ],
    "validated_commercial_bank_watch_caution_allowed_sectors": [
        "COMMERCIAL BANKS",
    ],
    "validated_commercial_bank_watch_caution_required_event_states": [
        "matched_but_stale",
    ],
    "validated_commercial_bank_watch_caution_required_labels": [
        "strongly_overconfident",
    ],
    "validated_commercial_bank_watch_caution_return_20d_min": 10.32,
    "validated_commercial_bank_watch_caution_close_position_20d_min": 0.941,
    "validated_commercial_bank_watch_caution_rr_min": 1.5,
    "use_validated_commercial_bank_overconfident_watch_caution_guidance": True,
    "validated_commercial_bank_overconfident_watch_caution_hostile_phases": [
        "fiscal_year_end_window",
        "post_fiscal_results_window",
    ],
    "validated_commercial_bank_overconfident_watch_caution_allowed_sectors": [
        "COMMERCIAL BANKS",
    ],
    "validated_commercial_bank_overconfident_watch_caution_required_event_states": [
        "matched_but_stale",
    ],
    "validated_commercial_bank_overconfident_watch_caution_required_labels": [
        "overconfident",
    ],
    "validated_commercial_bank_overconfident_watch_caution_return_5d_max": 2.38,
    "validated_commercial_bank_overconfident_watch_caution_volume_ratio_5d_max": 1.07,
}


def _parse_date(value):
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _load_history_rows(symbol, session_date, truth_source_name="sharesansar_local", history_days=180):
    source = get_truth_source(truth_source_name)
    end_dt = _parse_date(session_date)
    start_dt = end_dt - timedelta(days=history_days)
    payload = source.get_ticker_history(symbol, start_dt.isoformat(), end_dt.isoformat())
    rows = (((payload or {}).get("history") or {}).get("content") or [])
    rows = [
        row for row in rows
        if row.get("businessDate") and is_nepal_trading_weekday(_parse_date(row["businessDate"]))
    ]
    rows = sorted(rows, key=lambda row: row.get("businessDate") or "")
    return rows


def _avg(values):
    values = [float(value) for value in values if value is not None]
    return round(sum(values) / len(values), 2) if values else None


def _pct_change(current, previous):
    if current in (None, 0) or previous in (None, 0):
        return None
    return round(((float(current) / float(previous)) - 1.0) * 100, 2)


def _safe_ratio(a_value, b_value):
    if a_value in (None, 0) or b_value in (None, 0):
        return None
    return round(float(a_value) / float(b_value), 2)


def _rolling_average(rows, field, length):
    return _avg([row.get(field) for row in rows[-length:]])


def _rolling_high(rows, field, length):
    values = [row.get(field) for row in rows[-length:] if row.get(field) is not None]
    return round(max(values), 2) if values else None


def _rolling_low(rows, field, length):
    values = [row.get(field) for row in rows[-length:] if row.get(field) is not None]
    return round(min(values), 2) if values else None


def _close_position(close_price, high_value, low_value):
    if close_price is None or high_value is None or low_value is None or high_value == low_value:
        return None
    return round((float(close_price) - float(low_value)) / (float(high_value) - float(low_value)), 3)


def _trend_label(close_price, sma20, sma50, return_20d):
    if close_price is None or sma20 is None or sma50 is None or return_20d is None:
        return "unknown"
    if close_price > sma20 > sma50 and return_20d >= 3:
        return "uptrend"
    if close_price > sma20 and return_20d > 0:
        return "improving"
    if close_price < sma20 < sma50 and return_20d <= -3:
        return "downtrend"
    return "mixed"


def _liquidity_label(avg_value_20d, avg_trades_20d):
    if avg_value_20d is None or avg_trades_20d is None:
        return "unknown"
    if avg_value_20d >= 25_000_000 and avg_trades_20d >= 150:
        return "strong"
    if avg_value_20d >= 10_000_000 and avg_trades_20d >= 60:
        return "acceptable"
    return "weak"


def _build_trade_plan(latest_row, metrics):
    close_price = latest_row.get("closePrice")
    support_10 = metrics.get("support_10d")
    resistance_20 = metrics.get("resistance_20d")
    resistance_60 = metrics.get("resistance_60d")
    fifty_two_week_high = latest_row.get("fiftyTwoWeekHigh")

    if close_price is None or support_10 is None:
        return {
            "entry_zone": [],
            "stop_loss": None,
            "invalidation_level": None,
            "targets": [],
            "risk_reward_ratio": None,
        }

    entry = round(float(close_price), 2)
    stop_loss = round(float(support_10) * 0.99, 2)
    risk = round(entry - stop_loss, 2)
    if risk <= 0:
        return {
            "entry_zone": [],
            "stop_loss": stop_loss,
            "invalidation_level": stop_loss,
            "targets": [],
            "risk_reward_ratio": None,
        }

    candidate_targets = []
    for value in (resistance_20, resistance_60, fifty_two_week_high):
        if value is not None and value > entry * 1.01:
            candidate_targets.append(round(float(value), 2))

    if not candidate_targets:
        candidate_targets = [
            round(entry + (risk * 1.5), 2),
            round(entry + (risk * 2.5), 2),
            round(entry + (risk * 4.0), 2),
        ]

    targets = sorted(set(candidate_targets))[:3]
    first_target = targets[0] if targets else None
    rr = round((first_target - entry) / risk, 2) if first_target and risk > 0 else None

    return {
        "entry_zone": [round(entry * 0.995, 2), round(entry, 2)],
        "stop_loss": stop_loss,
        "invalidation_level": stop_loss,
        "targets": targets,
        "risk_reward_ratio": rr,
    }


def _decision_reasons(metrics, action, trade_plan, rules):
    reasons = []
    warnings = []
    reason_codes = []

    if metrics["trend_label"] in {"uptrend", "improving"}:
        reasons.append(f"trend is {metrics['trend_label']}")
    if metrics["close_position_20d"] is not None and metrics["close_position_20d"] >= 0.75:
        reasons.append("price is near the upper part of the 20-day range")
    if metrics["volume_ratio_5d"] is not None and metrics["volume_ratio_5d"] >= 1.1:
        reasons.append("recent activity is stronger than the 20-day average")
    if metrics["liquidity_label"] in {"acceptable", "strong"}:
        reasons.append(f"liquidity is {metrics['liquidity_label']}")

    if metrics["liquidity_label"] == "weak":
        warnings.append("liquidity is weak")
        reason_codes.append("liquidity_weak")
    if metrics["close_position_20d"] is not None and metrics["close_position_20d"] >= 0.92 and (metrics["volume_ratio_5d"] or 0) < 1:
        warnings.append("move looks extended without strong volume confirmation")
        reason_codes.append("breakout_too_extended")
    if metrics["trend_label"] in {"mixed", "unknown"}:
        warnings.append("trend confirmation is incomplete")
        reason_codes.append("insufficient_confirmation")
    if metrics["trend_label"] == "downtrend":
        warnings.append("trend is negative")
        reason_codes.append("market_headwind")
    rr_warning_min = max(float(rules.get("buy_rr_min", 1.2)), float(rules.get("watch_rr_min", 0.0) or 0.0))
    if trade_plan.get("risk_reward_ratio") is not None and trade_plan["risk_reward_ratio"] < rr_warning_min:
        warnings.append("risk/reward is thin")
        reason_codes.append("rr_too_thin")

    if action == "avoid" and not warnings:
        warnings.append("setup quality is not strong enough yet")
        reason_codes.append("insufficient_confirmation")

    return reasons, warnings, sorted(set(reason_codes))


def build_replay_case(symbol, session_date, truth_source_name="sharesansar_local", rules=None, replay_context_list_name=None):
    symbol = str(symbol).upper()
    rules = {**DEFAULT_REPLAY_RULES, **(rules or {})}
    history_rows = _load_history_rows(symbol, session_date, truth_source_name=truth_source_name)
    if not history_rows:
        raise FileNotFoundError(f"No historical rows found for {symbol} on or before {session_date}")

    latest_row = history_rows[-1]
    if latest_row.get("businessDate") != session_date:
        raise FileNotFoundError(f"No row found for {symbol} on session date {session_date}")

    bars = history_rows
    close_price = latest_row.get("closePrice")
    sma10 = _rolling_average(bars, "closePrice", 10)
    sma20 = _rolling_average(bars, "closePrice", 20)
    sma50 = _rolling_average(bars, "closePrice", 50)
    avg_value_5d = _rolling_average(bars, "totalTradedValue", 5)
    avg_value_20d = _rolling_average(bars, "totalTradedValue", 20)
    avg_trades_5d = _rolling_average(bars, "totalTrades", 5)
    avg_trades_20d = _rolling_average(bars, "totalTrades", 20)
    avg_volume_5d = _rolling_average(bars, "totalTradedQuantity", 5)
    avg_volume_20d = _rolling_average(bars, "totalTradedQuantity", 20)
    resistance_20d = _rolling_high(bars, "highPrice", 20)
    support_10d = _rolling_low(bars, "lowPrice", 10)
    resistance_60d = _rolling_high(bars, "highPrice", 60)
    support_60d = _rolling_low(bars, "lowPrice", 60)
    close_position_20d = _close_position(close_price, resistance_20d, _rolling_low(bars, "lowPrice", 20))
    close_position_60d = _close_position(close_price, resistance_60d, support_60d)
    return_1d = _pct_change(close_price, bars[-2].get("closePrice") if len(bars) >= 2 else None)
    return_5d = _pct_change(close_price, bars[-6].get("closePrice") if len(bars) >= 6 else None)
    return_20d = _pct_change(close_price, bars[-21].get("closePrice") if len(bars) >= 21 else None)
    volume_ratio_5d = _safe_ratio(avg_volume_5d, avg_volume_20d)
    liquidity_label = _liquidity_label(avg_value_20d, avg_trades_20d)
    trend_label = _trend_label(close_price, sma20, sma50, return_20d)

    metrics = {
        "bar_count": len(bars),
        "close_price": close_price,
        "return_1d_pct": return_1d,
        "return_5d_pct": return_5d,
        "return_20d_pct": return_20d,
        "sma10": sma10,
        "sma20": sma20,
        "sma50": sma50,
        "avg_value_5d": avg_value_5d,
        "avg_value_20d": avg_value_20d,
        "avg_trades_5d": avg_trades_5d,
        "avg_trades_20d": avg_trades_20d,
        "volume_ratio_5d": volume_ratio_5d,
        "resistance_20d": resistance_20d,
        "support_10d": support_10d,
        "resistance_60d": resistance_60d,
        "support_60d": support_60d,
        "close_position_20d": close_position_20d,
        "close_position_60d": close_position_60d,
        "trend_label": trend_label,
        "liquidity_label": liquidity_label,
    }

    if len(bars) < 60 or close_price is None:
        action = "incomplete_data"
        setup_type = "insufficient_history"
        score = 0
        confidence = 20
        trade_plan = {
            "entry_zone": [],
            "stop_loss": None,
            "invalidation_level": None,
            "targets": [],
            "risk_reward_ratio": None,
        }
    else:
        trade_plan = _build_trade_plan(latest_row, metrics)
        momentum_points = 25 if trend_label == "uptrend" else 15 if trend_label == "improving" else 5 if trend_label == "mixed" else 0
        range_points = 20 if (close_position_20d or 0) >= 0.75 else 10 if (close_position_20d or 0) >= 0.55 else 0
        liquidity_points = 20 if liquidity_label == "strong" else 12 if liquidity_label == "acceptable" else 0
        volume_points = 15 if (volume_ratio_5d or 0) >= 1.1 else 8 if (volume_ratio_5d or 0) >= 0.9 else 0
        return_points = 20 if (return_20d or -999) >= 8 else 12 if (return_20d or -999) >= 3 else 6 if (return_20d or -999) > 0 else 0
        score = int(momentum_points + range_points + liquidity_points + volume_points + return_points)
        confidence = min(90, max(25, score + 10))
        risk_reward_ratio = trade_plan.get("risk_reward_ratio")
        close_position_value = close_position_20d or 0
        volume_ratio_value = volume_ratio_5d or 0
        buy_rr_min = float(rules.get("buy_rr_min", 1.2))
        watch_rr_min = float(rules.get("watch_rr_min", 0.0) or 0.0)
        buy_close_position_min = float(rules.get("buy_close_position_min", 0.75))
        watch_close_position_min = float(rules.get("watch_close_position_min", 0.55))
        improving_watch_close_position_min = float(rules.get("improving_watch_close_position_min", watch_close_position_min))
        buy_volume_ratio_min = float(rules.get("buy_volume_ratio_min", 0.0))
        buy_score_min = float(rules.get("buy_score_min", 0))
        watch_score_min = float(rules.get("watch_score_min", 0))

        if (
            trend_label == "uptrend"
            and liquidity_label in {"acceptable", "strong"}
            and close_position_value >= buy_close_position_min
            and risk_reward_ratio not in (None, 0)
            and risk_reward_ratio >= buy_rr_min
            and volume_ratio_value >= buy_volume_ratio_min
            and score >= buy_score_min
        ):
            action = "buy"
            setup_type = "daily_breakout_continuation"
        elif (
            (
                (trend_label == "uptrend" and close_position_value >= watch_close_position_min)
                or (trend_label == "improving" and close_position_value >= improving_watch_close_position_min)
            )
            and liquidity_label in {"acceptable", "strong"}
            and score >= watch_score_min
            and (risk_reward_ratio is None or risk_reward_ratio >= watch_rr_min)
        ):
            action = "watch_only"
            setup_type = "trend_watch"
        else:
            action = "avoid"
            setup_type = "weak_or_unconfirmed"

        if action in {"buy", "watch_only"} and not trade_plan.get("targets"):
            action = "avoid"
            setup_type = "target_missing"

    reasons, warnings, reason_codes = _decision_reasons(metrics, action, trade_plan, rules)
    session_id = f"replay__{session_date}__{symbol}__1D"

    frozen_case = {
        "schema_version": "1.0",
        "session_id": session_id,
        "symbol": symbol,
        "session_date": session_date,
        "timeframe": "1D",
        "truth_source": truth_source_name,
        "captured_at": datetime.now().isoformat(),
        "latest_row": latest_row,
        "metrics": metrics,
        "data_quality": {
            "history_bar_count": len(bars),
            "has_full_20d_context": len(bars) >= 21,
            "has_full_60d_context": len(bars) >= 61,
        },
        "replay_rules": rules,
    }
    context_bundle = load_replay_context_bundle(symbol, session_date, replay_context_list_name)
    context_bundle["corporate_action_context"] = load_replay_corporate_action_context(
        symbol,
        session_date,
        replay_context_list_name,
    )
    context_bundle["macro_calendar_context"] = load_replay_macro_calendar_context(session_date)
    context_bundle["liquidity_execution_context"] = build_replay_liquidity_execution_context(
        bars,
        session_date,
    )
    frozen_case["sector_name"] = context_bundle.get("sector_name")
    frozen_case["historical_context"] = context_bundle

    replay_decision = {
        "schema_version": "1.0",
        "session_id": session_id,
        "symbol": symbol,
        "run_date": session_date,
        "timeframe": "1D",
        "action": action,
        "setup_type": setup_type,
        "score": score,
        "confidence": confidence,
        "entry_zone": trade_plan.get("entry_zone") or [],
        "stop_loss": trade_plan.get("stop_loss"),
        "invalidation_level": trade_plan.get("invalidation_level"),
        "targets": trade_plan.get("targets") or [],
        "risk_reward_ratio": trade_plan.get("risk_reward_ratio"),
        "reason_list": reasons,
        "warnings": warnings,
        "reason_codes": reason_codes,
        "replay_rules": rules,
        "captured_at": datetime.now().isoformat(),
    }

    return frozen_case, replay_decision


def main():
    if len(sys.argv) < 3:
        print("Usage: python replay_case_builder.py SYMBOL SESSION_DATE [TRUTH_SOURCE]")
        sys.exit(1)

    symbol = sys.argv[1].upper()
    session_date = sys.argv[2]
    truth_source_name = sys.argv[3] if len(sys.argv) > 3 else "sharesansar_local"
    frozen_case, replay_decision = build_replay_case(symbol, session_date, truth_source_name)
    print(json.dumps({
        "session_id": frozen_case["session_id"],
        "action": replay_decision["action"],
        "score": replay_decision["score"],
        "confidence": replay_decision["confidence"],
        "reason_codes": replay_decision["reason_codes"],
    }, indent=2))


if __name__ == "__main__":
    main()
