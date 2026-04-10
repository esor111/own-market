"""
Build a reusable setup-memory store from saved decisions, model inputs, and outcomes.

Usage:
    python memory_store.py
"""
import json
import os
from datetime import datetime
from glob import glob

from config import SYMBOLS_DIR, VALIDATION_DIR, get_latest_validation_filename


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def outcome_to_success(outcome_record):
    label = (outcome_record or {}).get("outcome_label")
    if label in {"target_1_hit", "target_2_hit", "target_3_hit"}:
        return True
    if label == "stopped_out":
        return False
    return None


def build_index(paths, key_field):
    indexed = {}
    for path in paths:
        try:
            payload = load_json(path)
        except Exception:
            continue
        key = payload.get(key_field)
        if key:
            indexed[key] = {"path": path, "data": payload}
    return indexed


def _get_timeframe_node(model_input_data, timeframe):
    return ((model_input_data or {}).get("timeframes") or {}).get(timeframe, {})


def _round_or_none(value, digits=2):
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except Exception:
        return None


def build_memory_record(session_id, decision_data, model_input_data=None, outcome_data=None, source_paths=None):
    model_input_data = model_input_data or {}
    outcome_data = outcome_data or {}
    source_paths = source_paths or {}

    market = model_input_data.get("market") or {}
    sector = model_input_data.get("sector") or {}
    alignment = model_input_data.get("derived_alignment") or {}
    event_context = model_input_data.get("event_context") or {}
    quality_flags = model_input_data.get("quality_flags") or {}
    decision_inputs = model_input_data.get("decision_inputs") or {}
    tf_1m = _get_timeframe_node(model_input_data, "1M")
    tf_1w = _get_timeframe_node(model_input_data, "1W")
    tf_1d = _get_timeframe_node(model_input_data, "1D")

    return {
        "session_id": session_id,
        "symbol": decision_data.get("symbol"),
        "run_date": decision_data.get("run_date"),
        "timeframe": decision_data.get("timeframe"),
        "captured_at": decision_data.get("captured_at"),
        "decision": {
            "action": decision_data.get("action"),
            "setup_type": decision_data.get("setup_type"),
            "score": decision_data.get("score"),
            "confidence": decision_data.get("confidence"),
            "risk_reward_ratio": decision_data.get("risk_reward_ratio"),
            "entry_zone": decision_data.get("entry_zone") or [],
            "stop_loss": decision_data.get("stop_loss"),
            "targets": decision_data.get("targets") or [],
        },
        "market_context": {
            "trend_label": market.get("trend_label"),
            "change_pct": market.get("change_pct"),
            "structure_confidence": market.get("structure_confidence"),
        },
        "sector_context": {
            "name": sector.get("name"),
            "trend_label": sector.get("trend_label"),
            "change_pct": sector.get("change_pct"),
            "relative_strength_vs_market": sector.get("relative_strength_vs_market"),
        },
        "timeframes": {
            "1M": {
                "trend_label": tf_1m.get("trend_label"),
                "structure_label": tf_1m.get("structure_label"),
                "structure_confidence": tf_1m.get("structure_confidence"),
                "breakout_level": tf_1m.get("breakout_level"),
                "invalidation_level": tf_1m.get("invalidation_level"),
                "rsi": tf_1m.get("rsi"),
            },
            "1W": {
                "trend_label": tf_1w.get("trend_label"),
                "structure_label": tf_1w.get("structure_label"),
                "structure_confidence": tf_1w.get("structure_confidence"),
                "breakout_level": tf_1w.get("breakout_level"),
                "invalidation_level": tf_1w.get("invalidation_level"),
                "rsi": tf_1w.get("rsi"),
            },
            "1D": {
                "trend_label": tf_1d.get("trend_label"),
                "structure_label": tf_1d.get("structure_label"),
                "structure_confidence": tf_1d.get("structure_confidence"),
                "breakout_level": tf_1d.get("breakout_level"),
                "invalidation_level": tf_1d.get("invalidation_level"),
                "rsi": tf_1d.get("rsi"),
            },
        },
        "alignment": {
            "higher_timeframe_alignment": alignment.get("higher_timeframe_alignment"),
            "structure_agreement": alignment.get("structure_agreement"),
            "alignment_gate_status": alignment.get("alignment_gate_status"),
            "alignment_gate_score": alignment.get("alignment_gate_score"),
            "trigger_readiness": alignment.get("trigger_readiness"),
            "trade_quality": alignment.get("trade_quality"),
        },
        "event_context": {
            "has_active_event": event_context.get("has_active_event"),
            "event_type": event_context.get("event_type"),
            "event_status": event_context.get("event_status"),
            "event_sentiment": event_context.get("event_sentiment"),
            "impact_window_days": event_context.get("impact_window_days"),
        },
        "quality_flags": {
            "market_data_quality": quality_flags.get("market_data_quality"),
            "sector_data_quality": quality_flags.get("sector_data_quality"),
            "stock_structure_quality": quality_flags.get("stock_structure_quality"),
            "event_data_quality": quality_flags.get("event_data_quality"),
            "truth_data_quality": quality_flags.get("truth_data_quality"),
            "truth_alignment_quality": quality_flags.get("truth_alignment_quality"),
            "outcome_history_quality": quality_flags.get("outcome_history_quality"),
        },
        "qc": {
            "status": decision_inputs.get("qc_status"),
            "findings": decision_inputs.get("qc_findings") or [],
        },
        "outcome": {
            "outcome_label": outcome_data.get("outcome_label", "missing"),
            "success": outcome_to_success(outcome_data),
            "resolved": outcome_to_success(outcome_data) is not None,
            "max_favorable_excursion_pct": outcome_data.get("max_favorable_excursion_pct"),
            "max_adverse_excursion_pct": outcome_data.get("max_adverse_excursion_pct"),
        },
        "numeric_features": {
            "score": _round_or_none(decision_data.get("score")),
            "confidence": _round_or_none(decision_data.get("confidence")),
            "risk_reward_ratio": _round_or_none(decision_data.get("risk_reward_ratio")),
            "market_change_pct": _round_or_none(market.get("change_pct")),
            "sector_change_pct": _round_or_none(sector.get("change_pct")),
            "monthly_rsi": _round_or_none(tf_1m.get("rsi")),
            "weekly_rsi": _round_or_none(tf_1w.get("rsi")),
            "daily_rsi": _round_or_none(tf_1d.get("rsi")),
            "alignment_gate_score": _round_or_none(alignment.get("alignment_gate_score")),
        },
        "source_paths": source_paths,
        "captured_at_memory": datetime.now().isoformat(),
    }


def build_memory_store():
    decision_paths = glob(os.path.join(SYMBOLS_DIR, "*", "*", "normalized", "decisions", "*.json"))
    model_input_paths = glob(os.path.join(SYMBOLS_DIR, "*", "*", "features", "model_inputs", "*.json"))
    outcome_paths = glob(os.path.join(SYMBOLS_DIR, "*", "*", "outcomes", "realized_results", "*.json"))

    decisions = build_index(decision_paths, "session_id")
    model_inputs = build_index(model_input_paths, "session_id")
    outcomes = build_index(outcome_paths, "decision_session_id")

    records = []
    for session_id, decision in decisions.items():
        decision_data = decision["data"]
        model_input = model_inputs.get(session_id)
        outcome = outcomes.get(session_id)
        source_paths = {
            "decision": decision["path"],
            "model_input": model_input["path"] if model_input else None,
            "outcome": outcome["path"] if outcome else None,
        }
        records.append(
            build_memory_record(
                session_id,
                decision_data,
                model_input["data"] if model_input else None,
                outcome["data"] if outcome else None,
                source_paths=source_paths,
            )
        )

    records.sort(key=lambda item: ((item.get("run_date") or ""), (item.get("symbol") or ""), (item.get("timeframe") or "")))

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "record_count": len(records),
        "resolved_outcomes": sum(1 for record in records if record["outcome"]["resolved"]),
        "successful_resolved_outcomes": sum(1 for record in records if record["outcome"]["success"] is True),
        "symbols": sorted({record["symbol"] for record in records if record.get("symbol")}),
        "records": records,
    }

    dated_path = os.path.join(
        VALIDATION_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__setup_memory_store_v1.json",
    )
    latest_path = os.path.join(
        VALIDATION_DIR,
        get_latest_validation_filename("setup_memory_store_v1"),
    )
    save_json(dated_path, summary)
    save_json(latest_path, summary)
    return dated_path, latest_path, summary


def main():
    dated_path, latest_path, summary = build_memory_store()
    print(json.dumps({
        "dated_path": dated_path,
        "latest_path": latest_path,
        "record_count": summary["record_count"],
        "resolved_outcomes": summary["resolved_outcomes"],
    }, indent=2))


if __name__ == "__main__":
    main()
