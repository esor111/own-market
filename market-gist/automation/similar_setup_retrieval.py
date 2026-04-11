"""
Retrieve similar historical setups from the setup memory store.

Usage:
    python similar_setup_retrieval.py EBL 2026-03-19 1W
"""
import json
import math
import os
import sys
from collections import Counter

from config import (
    VALIDATION_DIR,
    get_decision_filename,
    get_latest_validation_filename,
    get_model_input_filename,
    get_run_directories,
)
from memory_store import build_memory_record, build_memory_store, load_json


def _similarity_numeric(a_value, b_value, tolerance):
    if a_value is None or b_value is None or tolerance <= 0:
        return 0.0
    diff = abs(float(a_value) - float(b_value))
    return max(0.0, 1.0 - (diff / tolerance))


def _same(a_value, b_value):
    return 1.0 if a_value and b_value and a_value == b_value else 0.0


def _bool_same(a_value, b_value):
    if a_value is None or b_value is None:
        return 0.0
    return 1.0 if bool(a_value) == bool(b_value) else 0.0


def load_memory_summary():
    latest_path = os.path.join(
        VALIDATION_DIR,
        get_latest_validation_filename("setup_memory_store_v1"),
    )
    if not os.path.exists(latest_path):
        _, _, summary = build_memory_store()
        return summary
    return load_json(latest_path)


def load_current_case(symbol, run_date, timeframe):
    run_dirs = get_run_directories(symbol, run_date)
    decision_path = os.path.join(
        run_dirs["normalized_decisions"],
        get_decision_filename(symbol, timeframe, run_date),
    )
    model_input_path = os.path.join(
        run_dirs["features_model_inputs"],
        get_model_input_filename(symbol, timeframe, run_date),
    )
    outcome_path = os.path.join(
        run_dirs["outcomes_realized_results"],
        f"{run_date}__{symbol}__{timeframe}__outcome_v1.json",
    )

    if not os.path.exists(decision_path):
        raise FileNotFoundError(f"Decision record not found: {decision_path}")

    decision_data = load_json(decision_path)
    model_input_data = load_json(model_input_path) if os.path.exists(model_input_path) else None
    outcome_data = load_json(outcome_path) if os.path.exists(outcome_path) else None
    return build_memory_record(
        decision_data["session_id"],
        decision_data,
        model_input_data,
        outcome_data,
        source_paths={
            "decision": decision_path,
            "model_input": model_input_path if os.path.exists(model_input_path) else None,
            "outcome": outcome_path if os.path.exists(outcome_path) else None,
        },
    )


def score_similarity(current_case, candidate_case):
    score = 0.0
    max_score = 13.0

    score += 0.75 * _same(current_case.get("timeframe"), candidate_case.get("timeframe"))
    score += 1.75 * _same(
        current_case["decision"].get("setup_type"),
        candidate_case["decision"].get("setup_type"),
    )
    score += 0.75 * _same(
        current_case["sector_context"].get("name"),
        candidate_case["sector_context"].get("name"),
    )
    score += 1.5 * _same(
        current_case["timeframes"]["1W"].get("structure_label"),
        candidate_case["timeframes"]["1W"].get("structure_label"),
    )
    score += 1.0 * _same(
        current_case["timeframes"]["1W"].get("trend_label"),
        candidate_case["timeframes"]["1W"].get("trend_label"),
    )
    score += 0.75 * _same(
        current_case["timeframes"]["1M"].get("trend_label"),
        candidate_case["timeframes"]["1M"].get("trend_label"),
    )
    score += 0.75 * _same(
        current_case["timeframes"]["1D"].get("trend_label"),
        candidate_case["timeframes"]["1D"].get("trend_label"),
    )
    score += 1.0 * _same(
        current_case["alignment"].get("alignment_gate_status"),
        candidate_case["alignment"].get("alignment_gate_status"),
    )
    score += 0.5 * _bool_same(
        current_case["event_context"].get("has_active_event"),
        candidate_case["event_context"].get("has_active_event"),
    )
    score += 0.5 * _same(
        current_case["event_context"].get("event_type"),
        candidate_case["event_context"].get("event_type"),
    )
    score += 1.25 * _similarity_numeric(
        current_case["numeric_features"].get("score"),
        candidate_case["numeric_features"].get("score"),
        25,
    )
    score += 1.0 * _similarity_numeric(
        current_case["numeric_features"].get("confidence"),
        candidate_case["numeric_features"].get("confidence"),
        25,
    )
    score += 1.0 * _similarity_numeric(
        current_case["numeric_features"].get("risk_reward_ratio"),
        candidate_case["numeric_features"].get("risk_reward_ratio"),
        2,
    )
    score += 0.5 * _similarity_numeric(
        current_case["numeric_features"].get("weekly_rsi"),
        candidate_case["numeric_features"].get("weekly_rsi"),
        15,
    )

    similarity_pct = round((score / max_score) * 100, 2)
    return score, similarity_pct


def summarize_matches(current_case, candidates, top_n=5):
    ranked = []
    for candidate in candidates:
        if candidate.get("session_id") == current_case.get("session_id"):
            continue
        raw_score, similarity_pct = score_similarity(current_case, candidate)
        ranked.append({
            "session_id": candidate.get("session_id"),
            "symbol": candidate.get("symbol"),
            "run_date": candidate.get("run_date"),
            "timeframe": candidate.get("timeframe"),
            "similarity_pct": similarity_pct,
            "decision": candidate.get("decision"),
            "sector_context": candidate.get("sector_context"),
            "alignment": candidate.get("alignment"),
            "event_context": candidate.get("event_context"),
            "outcome": candidate.get("outcome"),
            "source_paths": candidate.get("source_paths"),
        })

    ranked.sort(key=lambda item: (-item["similarity_pct"], item.get("run_date") or "", item.get("symbol") or ""))
    top_matches = ranked[:top_n]

    resolved = [item for item in top_matches if item["outcome"].get("resolved")]
    successes = [item for item in resolved if item["outcome"].get("success") is True]
    action_counts = Counter(item["decision"].get("action") for item in top_matches if item["decision"].get("action"))
    outcome_counts = Counter(item["outcome"].get("outcome_label") for item in top_matches if item["outcome"].get("outcome_label"))
    setup_counts = Counter(item["decision"].get("setup_type") for item in top_matches if item["decision"].get("setup_type"))

    summary = {
        "query": {
            "session_id": current_case.get("session_id"),
            "symbol": current_case.get("symbol"),
            "run_date": current_case.get("run_date"),
            "timeframe": current_case.get("timeframe"),
            "decision": current_case.get("decision"),
        },
        "top_matches": top_matches,
        "summary": {
            "match_count": len(top_matches),
            "resolved_match_count": len(resolved),
            "resolved_success_rate_pct": round((len(successes) / len(resolved)) * 100, 2) if resolved else None,
            "average_similarity_pct": round(
                sum(item["similarity_pct"] for item in top_matches) / len(top_matches), 2
            ) if top_matches else None,
            "common_actions": dict(action_counts),
            "common_outcomes": dict(outcome_counts),
            "common_setups": dict(setup_counts),
        },
    }
    return summary


def build_human_summary(retrieval_summary):
    top_matches = retrieval_summary.get("top_matches") or []
    resolved_rate = retrieval_summary.get("summary", {}).get("resolved_success_rate_pct")
    resolved_count = retrieval_summary.get("summary", {}).get("resolved_match_count")
    if not top_matches:
        return {
            "headline": "No similar historical setups found yet.",
            "key_points": [],
        }

    best = top_matches[0]
    headline = (
        f"Found {len(top_matches)} similar setups; "
        f"{resolved_count} have resolved outcomes."
    )
    key_points = [
        f"Closest match: {best['symbol']} on {best['run_date']} at {best['similarity_pct']}% similarity.",
    ]
    if resolved_rate is not None:
        key_points.append(
            f"Resolved similar setups succeeded {resolved_rate}% of the time."
        )
    common_outcomes = retrieval_summary.get("summary", {}).get("common_outcomes") or {}
    if common_outcomes:
        top_outcome = max(common_outcomes.items(), key=lambda item: item[1])
        key_points.append(f"Most common outcome among matches: {top_outcome[0]} ({top_outcome[1]} cases).")
    return {
        "headline": headline,
        "key_points": key_points,
    }


def retrieve_similar_setups(symbol, run_date, timeframe="1W", top_n=5):
    memory_summary = load_memory_summary()
    current_case = load_current_case(symbol, run_date, timeframe)
    retrieval = summarize_matches(current_case, memory_summary.get("records") or [], top_n=top_n)
    retrieval["human_summary"] = build_human_summary(retrieval)
    return retrieval


def main():
    if len(sys.argv) < 3:
        print("Usage: python similar_setup_retrieval.py SYMBOL RUN_DATE [TIMEFRAME] [TOP_N]")
        sys.exit(1)

    symbol = sys.argv[1].upper()
    run_date = sys.argv[2]
    timeframe = sys.argv[3] if len(sys.argv) > 3 else "1W"
    top_n = int(sys.argv[4]) if len(sys.argv) > 4 else 5

    retrieval = retrieve_similar_setups(symbol, run_date, timeframe, top_n=top_n)
    output_path = os.path.join(
        get_run_directories(symbol, run_date)["raw_tables"],
        f"{run_date}__{symbol}__{timeframe}__similar_setups.json",
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(retrieval, handle, indent=2)
    print(json.dumps({
        "output_path": output_path,
        "match_count": retrieval["summary"]["match_count"],
        "resolved_match_count": retrieval["summary"]["resolved_match_count"],
        "headline": retrieval["human_summary"]["headline"],
    }, indent=2))


if __name__ == "__main__":
    main()
