"""
Build a critique bundle for one case by comparing decision, package context, similar setups,
and realized outcome status.

Usage:
    python llm_case_critique.py EBL 2026-03-19 1W
"""
import json
import os
import sys
from datetime import datetime

from config import (
    get_decision_filename,
    get_model_input_filename,
    get_run_directories,
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def maybe_load(path):
    if not os.path.exists(path):
        return None
    return load_json(path)


def _truth_liquidity_label(manual_package):
    today_row = (((manual_package or {}).get("truth_bundle") or {}).get("ticker") or {}).get("today_price_row") or {}
    traded_value = today_row.get("totalTradedValue") or 0
    trades = today_row.get("totalTrades") or 0
    if traded_value >= 100_000_000 and trades >= 500:
        return "strong"
    if traded_value >= 25_000_000 and trades >= 150:
        return "acceptable"
    return "weak"


def _critique_status(decision, outcome):
    action = (decision or {}).get("action")
    outcome_label = (outcome or {}).get("outcome_label")
    if outcome_label in {"target_1_hit", "target_2_hit", "target_3_hit"}:
        return "resolved_success"
    if outcome_label == "stopped_out":
        return "resolved_failure"
    if outcome_label == "not_applicable" or action == "avoid":
        return "non_actionable"
    if outcome_label in {"pending", "open"}:
        return "unresolved_actionable"
    if not outcome:
        return "outcome_missing"
    return "unknown"


def build_case_critique(symbol, run_date, timeframe="1W"):
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
    manual_package_path = os.path.join(
        run_dirs["raw_tables"],
        f"{run_date}__{symbol}__{timeframe}__manual_package.json",
    )
    similar_path = os.path.join(
        run_dirs["raw_tables"],
        f"{run_date}__{symbol}__{timeframe}__similar_setups.json",
    )

    decision = load_json(decision_path)
    model_input = maybe_load(model_input_path) or {}
    outcome = maybe_load(outcome_path) or {}
    manual_package = maybe_load(manual_package_path) or {}
    similar_setups = maybe_load(similar_path) or {}

    alignment = model_input.get("derived_alignment") or {}
    quality_flags = model_input.get("quality_flags") or {}
    event_context = model_input.get("event_context") or {}
    decision_inputs = model_input.get("decision_inputs") or {}
    tf_weekly = ((model_input.get("timeframes") or {}).get("1W")) or {}
    broker_edge_summary = manual_package.get("broker_edge_summary") or {}
    similar_summary = (similar_setups.get("human_summary") or {})
    similar_stats = (similar_setups.get("summary") or {})

    critique_status = _critique_status(decision, outcome)
    strengths = []
    risks = []
    proposals = []
    monitor_points = []

    if quality_flags.get("truth_alignment_quality") == "aligned":
        strengths.append("truth-layer data aligned with browser capture")
    if decision.get("risk_reward_ratio") is not None and decision.get("risk_reward_ratio") >= 2:
        strengths.append("risk/reward is attractive on the current plan")
    if tf_weekly.get("structure_confidence") == "high":
        strengths.append("weekly structure confidence is high")
    if not event_context.get("has_active_event"):
        strengths.append("no active official event is currently distorting the setup")
    if broker_edge_summary.get("closing_flow") == "firm":
        strengths.append("closing-session order flow looked firm")
    if broker_edge_summary.get("weekly_holdings_signal") == "weekly_accumulation_bias":
        strengths.append("weekly broker holdings showed accumulation bias")

    if quality_flags.get("stock_structure_quality") == "low" or tf_weekly.get("structure_confidence") == "low":
        risks.append("weekly structure confidence is low")
    if decision.get("risk_reward_ratio") is not None and decision.get("risk_reward_ratio") < 1.5:
        risks.append("risk/reward is thin for a reliable actionable setup")
    if event_context.get("has_active_event"):
        risks.append("active official event may distort the setup")
    if alignment.get("alignment_gate_status") in {"conflicted", "mixed_but_acceptable"}:
        risks.append("multi-timeframe alignment is not fully supportive")
    if broker_edge_summary.get("holding_change_signal") == "distribution":
        risks.append("broker holding changes lean toward distribution")
    if broker_edge_summary.get("concentration_signal") in {"selling_concentrated", "both_sides_concentrated"}:
        risks.append("participation concentration may make the move less trustworthy")
    if _truth_liquidity_label(manual_package) == "weak":
        risks.append("liquidity is weak in truth-layer data")

    if critique_status == "resolved_failure":
        if decision.get("risk_reward_ratio") is not None and decision.get("risk_reward_ratio") < 1.5:
            proposals.append("raise the minimum risk/reward threshold for similar setups")
        if alignment.get("alignment_gate_status") in {"conflicted", "mixed_but_acceptable"}:
            proposals.append("treat mixed/conflicted timeframe alignment more strictly for similar cases")
        if broker_edge_summary.get("holding_change_signal") == "distribution":
            proposals.append("add stronger negative weight when broker holding changes show distribution")
    elif critique_status == "resolved_success":
        if broker_edge_summary.get("closing_flow") == "firm":
            proposals.append("consider rewarding firm closing flow in future broker-edge scoring")
        if broker_edge_summary.get("weekly_holdings_signal") == "weekly_accumulation_bias":
            proposals.append("consider rewarding weekly accumulation bias in future broker-edge scoring")
    elif critique_status == "unresolved_actionable":
        monitor_points.append("wait for more bars before drawing outcome-level conclusions")
        if broker_edge_summary.get("holding_change_signal") == "distribution":
            monitor_points.append("watch for failure if broker distribution continues on the next sessions")
        if decision.get("risk_reward_ratio") is not None and decision.get("risk_reward_ratio") < 1.5:
            monitor_points.append("watch closely because the plan still has only moderate margin of safety")
    elif critique_status == "non_actionable":
        monitor_points.append("no trade-quality judgment should be forced from this case because it was not actionable")

    if similar_stats.get("resolved_match_count", 0) == 0:
        risks.append("similar-case memory exists, but no resolved similar outcomes are available yet")
    elif similar_stats.get("resolved_success_rate_pct") is not None and similar_stats["resolved_success_rate_pct"] < 50:
        risks.append("similar historical setups have weak observed success so far")
    elif similar_stats.get("resolved_success_rate_pct") is not None:
        strengths.append("similar historical setups have a favorable observed success rate")

    narrative = {
        "summary": {
            "status": critique_status,
            "symbol": symbol,
            "run_date": run_date,
            "timeframe": timeframe,
            "decision_action": decision.get("action"),
            "decision_score": decision.get("score"),
            "decision_confidence": decision.get("confidence"),
            "outcome_label": outcome.get("outcome_label", "missing"),
        },
        "strengths": strengths,
        "risks": risks,
        "monitor_points": monitor_points,
        "proposals": proposals,
        "similar_setup_summary": similar_summary,
        "broker_edge_summary": broker_edge_summary,
        "source_paths": {
            "decision": decision_path,
            "model_input": model_input_path if os.path.exists(model_input_path) else None,
            "outcome": outcome_path if os.path.exists(outcome_path) else None,
            "manual_package": manual_package_path if os.path.exists(manual_package_path) else None,
            "similar_setups": similar_path if os.path.exists(similar_path) else None,
        },
        "captured_at": datetime.now().isoformat(),
    }

    prompt_lines = [
        f"CASE: {symbol} {timeframe} {run_date}",
        f"Decision: {decision.get('action')} | score {decision.get('score')} | confidence {decision.get('confidence')}",
        f"Outcome: {outcome.get('outcome_label', 'missing')}",
        "",
        "Strengths:",
    ]
    prompt_lines.extend([f"- {item}" for item in strengths] or ["- none"])
    prompt_lines.append("")
    prompt_lines.append("Risks:")
    prompt_lines.extend([f"- {item}" for item in risks] or ["- none"])
    prompt_lines.append("")
    prompt_lines.append("Monitor points:")
    prompt_lines.extend([f"- {item}" for item in monitor_points] or ["- none"])
    prompt_lines.append("")
    prompt_lines.append("Proposals:")
    prompt_lines.extend([f"- {item}" for item in proposals] or ["- none"])
    prompt_lines.append("")
    prompt_lines.append("Task for the LLM:")
    prompt_lines.append("1. Explain in plain language why this case is strong, weak, or unresolved.")
    prompt_lines.append("2. Say whether the current system decision seems appropriate.")
    prompt_lines.append("3. If a future filter should change, propose only one or two changes.")
    prompt_lines.append("4. Do not invent missing facts.")
    narrative["llm_prompt"] = "\n".join(prompt_lines)

    json_path = os.path.join(
        run_dirs["features_case_critiques"],
        f"{run_date}__{symbol}__{timeframe}__case_critique_v1.json",
    )
    md_path = os.path.join(
        run_dirs["features_case_critiques"],
        f"{run_date}__{symbol}__{timeframe}__case_critique_v1.md",
    )
    save_json(json_path, narrative)
    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write(narrative["llm_prompt"] + "\n")

    return json_path, md_path, narrative


def main():
    if len(sys.argv) < 3:
        print("Usage: python llm_case_critique.py SYMBOL RUN_DATE [TIMEFRAME]")
        sys.exit(1)

    symbol = sys.argv[1].upper()
    run_date = sys.argv[2]
    timeframe = sys.argv[3].upper() if len(sys.argv) > 3 else "1W"
    json_path, md_path, narrative = build_case_critique(symbol, run_date, timeframe)
    print(json.dumps({
        "json_path": json_path,
        "md_path": md_path,
        "status": narrative["summary"]["status"],
        "outcome_label": narrative["summary"]["outcome_label"],
        "proposal_count": len(narrative["proposals"]),
    }, indent=2))


if __name__ == "__main__":
    main()
