"""
Build replay-specific critique records from saved replay artifacts.

Usage:
    python replay_case_critique.py 2025-12-21_to_2025-12-31__EBL__JBBL__daily_truth_replay_v1
"""
import json
import os
import sys
from datetime import datetime
from glob import glob

from config import REPLAYS_DIR
from replay_confidence_remap import lookup_replay_calibrated_confidence
from replay_validated_sector_guidance import resolve_validated_sector_guidance


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _replace_dir(path, old_part, new_part):
    parts = path.split(os.sep)
    parts = [new_part if part == old_part else part for part in parts]
    return os.sep.join(parts)


def _build_case_status(verdict):
    if verdict == "good_call":
        return "resolved_success"
    if verdict in {"bad_call", "missed_opportunity"}:
        return "resolved_failure"
    if verdict in {"good_avoid", "neutral_avoid"}:
        return "resolved_non_actionable"
    return "mixed_or_unclear"


def _load_family_guidance(replay_id):
    if not replay_id:
        return {}
    path = os.path.join(REPLAYS_DIR, replay_id, "summaries", "latest__family_guidance_v1.json")
    if not os.path.exists(path):
        return {}
    try:
        return load_json(path)
    except FileNotFoundError:
        return {}


def _resolve_case_family_guidance(frozen_case, comparison):
    replay_id = comparison.get("replay_id")
    guidance_bundle = _load_family_guidance(replay_id)
    if not guidance_bundle:
        return {}

    regime = frozen_case.get("regime_context") or {}
    if regime.get("alignment_label") != "both_supportive":
        return {}

    symbol = comparison.get("symbol")
    sector_name = frozen_case.get("sector_name")
    return {
        "symbol_guidance": (guidance_bundle.get("symbol_guidance") or {}).get(symbol),
        "sector_guidance": (guidance_bundle.get("sector_guidance") or {}).get(sector_name),
    }


def _resolve_validated_sector_context_guidance(frozen_case):
    regime = frozen_case.get("regime_context") or {}
    return resolve_validated_sector_guidance(
        frozen_case.get("sector_name"),
        regime.get("alignment_label"),
    )


def _build_confidence_interpretation(comparison):
    prediction = comparison.get("prediction") or {}
    action = prediction.get("action")
    raw_confidence = prediction.get("confidence")
    calibrated = lookup_replay_calibrated_confidence(action, raw_confidence)
    calibrated_pct = calibrated.get("calibrated_confidence_pct")
    raw_pct = raw_confidence
    gap = None
    if isinstance(raw_pct, (int, float)) and isinstance(calibrated_pct, (int, float)):
        gap = round(float(calibrated_pct) - float(raw_pct), 2)
    return {
        **calibrated,
        "calibration_gap_pct": gap,
    }


def _build_strengths(frozen_case, decision, comparison, family_guidance, validated_sector_guidance):
    metrics = frozen_case.get("metrics") or {}
    cross = frozen_case.get("cross_sectional_context") or {}
    regime = frozen_case.get("regime_context") or {}
    strengths = []
    if comparison.get("comparison_verdict") == "good_call":
        strengths.append("the replay action aligned well with the later price path")
    if comparison.get("comparison_verdict") == "good_avoid":
        strengths.append("the avoid decision appears to have filtered a weak or low-reward setup")
    if metrics.get("trend_label") in {"uptrend", "improving"}:
        strengths.append(f"trend context at decision time was {metrics.get('trend_label')}")
    if metrics.get("liquidity_label") in {"acceptable", "strong"}:
        strengths.append(f"liquidity was {metrics.get('liquidity_label')} at decision time")
    if (metrics.get("volume_ratio_5d") or 0) >= 1.1:
        strengths.append("recent trading activity was stronger than the 20-day average")
    if cross.get("leadership_label") in {"basket_leader", "sector_leader", "both_leader"}:
        strengths.append(f"the symbol was a relative leader inside the replay basket ({cross.get('leadership_label')})")
    if regime.get("alignment_label") in {"both_supportive", "partly_supportive"}:
        strengths.append(f"market and sector backdrop was {regime.get('alignment_label').replace('_', ' ')}")
    symbol_guidance = family_guidance.get("symbol_guidance") or {}
    sector_guidance = family_guidance.get("sector_guidance") or {}
    if symbol_guidance.get("guidance_label") == "supportive_followthrough_support":
        strengths.append("historical replay suggests this symbol often follows through in supportive setups")
    if sector_guidance.get("guidance_label") == "supportive_followthrough_support":
        strengths.append("historical replay suggests this sector family often follows through in supportive setups")
    validated_sector = validated_sector_guidance.get("sector_guidance") or {}
    validated_alignment = validated_sector_guidance.get("alignment_guidance") or {}
    if validated_sector.get("guidance_label") == "validated_actionable_support":
        strengths.append("multi-month replay validation suggests this sector family is supportive for actionable setups")
    if validated_alignment.get("guidance_label") == "validated_constructive_zone":
        strengths.append("multi-month replay validation suggests this alignment is often constructive")
    return strengths


def _build_risks(frozen_case, decision, comparison, family_guidance, validated_sector_guidance):
    metrics = frozen_case.get("metrics") or {}
    cross = frozen_case.get("cross_sectional_context") or {}
    regime = frozen_case.get("regime_context") or {}
    verdict = comparison.get("comparison_verdict")
    risks = []
    if "insufficient_confirmation" in (comparison.get("reason_codes") or []):
        risks.append("setup confirmation was weak at decision time")
    if "rr_too_thin" in (comparison.get("reason_codes") or []):
        risks.append("risk/reward was too thin for a dependable setup")
    if "avoid_too_strict" in (comparison.get("reason_codes") or []):
        risks.append("the current avoid threshold may be too strict for similar improving setups")
    if "breakout_too_extended" in (comparison.get("reason_codes") or []):
        risks.append("the setup looked extended relative to recent range and volume context")
    if metrics.get("liquidity_label") == "weak":
        risks.append("liquidity was weak, reducing execution confidence")
    if verdict == "mixed_call":
        risks.append("the action was directionally acceptable but lacked strong follow-through")
    if cross.get("leadership_label") == "basket_laggard":
        risks.append("the symbol was a laggard inside the replay basket at decision time")
    if regime.get("alignment_label") in {"headwind", "both_headwind"}:
        risks.append(f"broader market or sector regime was a headwind ({regime.get('alignment_label').replace('_', ' ')})")
    symbol_guidance = family_guidance.get("symbol_guidance") or {}
    sector_guidance = family_guidance.get("sector_guidance") or {}
    if symbol_guidance.get("guidance_label") == "supportive_fragility_caution":
        risks.append("historical replay suggests this symbol often turns fragile even when the setup looks supportive")
    if sector_guidance.get("guidance_label") == "supportive_fragility_caution":
        risks.append("historical replay suggests this sector family often turns fragile in supportive setups")
    validated_sector = validated_sector_guidance.get("sector_guidance") or {}
    validated_alignment = validated_sector_guidance.get("alignment_guidance") or {}
    if validated_sector.get("guidance_label") in {"validated_avoid_support", "validated_fragility_caution"}:
        risks.append("multi-month replay validation suggests this sector family is fragile or better treated as an avoid context")
    if validated_alignment.get("guidance_label") == "validated_avoid_zone":
        risks.append("multi-month replay validation suggests this alignment behaves like a clean avoid zone")
    return risks


def _build_proposals(frozen_case, decision, comparison, family_guidance, validated_sector_guidance):
    metrics = frozen_case.get("metrics") or {}
    cross = frozen_case.get("cross_sectional_context") or {}
    regime = frozen_case.get("regime_context") or {}
    verdict = comparison.get("comparison_verdict")
    reason_codes = set(comparison.get("reason_codes") or [])
    proposals = []

    if verdict == "missed_opportunity" and "avoid_too_strict" in reason_codes:
        proposals.append("review avoid-to-watch thresholds for improving setups with acceptable liquidity")
    if "rr_too_thin" in reason_codes and decision.get("action") in {"buy", "watch_only"}:
        proposals.append("demote or reject actionable setups when replay risk/reward is below a stronger minimum")
    if verdict == "mixed_call":
        proposals.append("add a clearer distinction between weak watch setups and high-conviction actionable setups")
    if metrics.get("close_position_20d") is not None and metrics.get("close_position_20d") >= 0.9 and (metrics.get("volume_ratio_5d") or 0) < 1:
        proposals.append("penalize extended range position when volume confirmation is weak")
    if verdict == "missed_opportunity" and cross.get("leadership_label") in {"basket_leader", "sector_leader", "both_leader"}:
        proposals.append("consider basket or sector leadership as a supporting context for borderline setups")
    if verdict in {"bad_call", "mixed_call"} and cross.get("leadership_label") == "basket_laggard":
        proposals.append("penalize borderline setups that are lagging the replay basket")
    if verdict in {"bad_call", "mixed_call", "missed_opportunity"} and regime.get("alignment_label") == "mixed":
        proposals.append("add clearer regime context to distinguish mixed-market setups from true continuation setups")
    symbol_guidance = family_guidance.get("symbol_guidance") or {}
    sector_guidance = family_guidance.get("sector_guidance") or {}
    if (
        verdict in {"bad_call", "mixed_call"}
        and (
            symbol_guidance.get("guidance_label") == "supportive_fragility_caution"
            or sector_guidance.get("guidance_label") == "supportive_fragility_caution"
        )
    ):
        proposals.append("use family-level fragility as a context warning for supportive setups before changing thresholds")
    validated_sector = validated_sector_guidance.get("sector_guidance") or {}
    validated_alignment = validated_sector_guidance.get("alignment_guidance") or {}
    if (
        verdict in {"bad_call", "mixed_call", "missed_opportunity"}
        and validated_sector.get("guidance_label") in {"validated_avoid_support", "validated_fragility_caution"}
    ):
        proposals.append("use validated sector-level fragility as a stronger context warning before promoting borderline setups")
    if verdict in {"bad_call", "mixed_call"} and validated_alignment.get("guidance_label") == "validated_avoid_zone":
        proposals.append("treat validated avoid-zone alignment as a stronger caution layer before changing thresholds")
    return sorted(set(proposals))


def build_replay_case_critique_from_paths(frozen_case_path, decision_path, comparison_path):
    frozen_case = load_json(frozen_case_path)
    decision = load_json(decision_path)
    comparison = load_json(comparison_path)
    family_guidance = _resolve_case_family_guidance(frozen_case, comparison)
    validated_sector_guidance = _resolve_validated_sector_context_guidance(frozen_case)
    confidence_interpretation = _build_confidence_interpretation(comparison)

    status = _build_case_status(comparison.get("comparison_verdict"))
    strengths = _build_strengths(frozen_case, decision, comparison, family_guidance, validated_sector_guidance)
    risks = _build_risks(frozen_case, decision, comparison, family_guidance, validated_sector_guidance)
    proposals = _build_proposals(frozen_case, decision, comparison, family_guidance, validated_sector_guidance)

    narrative = {
        "schema_version": "1.0",
        "summary": {
            "status": status,
            "replay_id": comparison.get("replay_id"),
            "session_id": comparison.get("session_id"),
            "symbol": comparison.get("symbol"),
            "session_date": comparison.get("session_date"),
            "timeframe": comparison.get("timeframe"),
            "decision_action": comparison.get("prediction", {}).get("action"),
            "comparison_verdict": comparison.get("comparison_verdict"),
            "return_10d_pct": comparison.get("horizon_returns", {}).get("return_10d_pct"),
        },
        "strengths": strengths,
        "risks": risks,
        "reason_codes": comparison.get("reason_codes") or [],
        "proposals": proposals,
        "cross_sectional_context": frozen_case.get("cross_sectional_context") or {},
        "regime_context": frozen_case.get("regime_context") or {},
        "family_guidance": family_guidance,
        "validated_sector_guidance": validated_sector_guidance,
        "confidence_interpretation": confidence_interpretation,
        "source_paths": {
            "frozen_case": frozen_case_path,
            "decision": decision_path,
            "comparison": comparison_path,
        },
        "captured_at": datetime.now().isoformat(),
    }

    prompt_lines = [
        f"REPLAY CASE: {comparison.get('symbol')} {comparison.get('timeframe')} {comparison.get('session_date')}",
        f"Decision: {comparison.get('prediction', {}).get('action')} | score {comparison.get('prediction', {}).get('score')} | confidence {comparison.get('prediction', {}).get('confidence')}",
        f"Replay verdict: {comparison.get('comparison_verdict')}",
        f"10-session return: {comparison.get('horizon_returns', {}).get('return_10d_pct')}",
        "",
        "Confidence interpretation:",
        f"- raw_confidence: {comparison.get('prediction', {}).get('confidence')}",
        f"- calibrated_confidence_pct: {confidence_interpretation.get('calibrated_confidence_pct')}",
        f"- calibration_gap_pct: {confidence_interpretation.get('calibration_gap_pct')}",
        f"- reference_group: {confidence_interpretation.get('reference_group')}",
        f"- interpretation: {confidence_interpretation.get('confidence_interpretation_label')}",
        "",
        "Strengths:",
    ]
    prompt_lines.extend([f"- {item}" for item in strengths] or ["- none"])
    prompt_lines.append("")
    prompt_lines.append("Risks:")
    prompt_lines.extend([f"- {item}" for item in risks] or ["- none"])
    prompt_lines.append("")
    prompt_lines.append("Reason codes:")
    prompt_lines.extend([f"- {item}" for item in (comparison.get("reason_codes") or [])] or ["- none"])
    prompt_lines.append("")
    prompt_lines.append("Proposals:")
    prompt_lines.extend([f"- {item}" for item in proposals] or ["- none"])
    prompt_lines.append("")
    prompt_lines.append("Task for the LLM:")
    prompt_lines.append("1. Explain why this replay case worked, failed, or stayed mixed.")
    prompt_lines.append("2. Say whether the decision logic was too strict, too loose, or appropriate.")
    prompt_lines.append("3. Suggest at most one or two careful improvements.")
    prompt_lines.append("4. Do not invent facts beyond the replay files.")
    narrative["llm_prompt"] = "\n".join(prompt_lines)

    critique_json_path = _replace_dir(comparison_path, "comparisons", "critiques").replace(
        "__comparison_v1.json", "__replay_case_critique_v1.json"
    )
    critique_md_path = critique_json_path.replace(".json", ".md")
    save_json(critique_json_path, narrative)
    with open(critique_md_path, "w", encoding="utf-8") as handle:
        handle.write(narrative["llm_prompt"] + "\n")

    return critique_json_path, critique_md_path, narrative


def build_replay_case_critiques(replay_id):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    comparison_paths = glob(os.path.join(replay_root, "sessions", "*", "*", "comparisons", "*__comparison_v1.json"))
    outputs = []

    for comparison_path in sorted(comparison_paths):
        decision_path = _replace_dir(comparison_path, "comparisons", "derived").replace(
            "__comparison_v1.json", "__replay_decision_v1.json"
        )
        frozen_case_path = _replace_dir(comparison_path, "comparisons", "normalized").replace(
            "__comparison_v1.json", "__frozen_case_v1.json"
        )
        if not os.path.exists(decision_path) or not os.path.exists(frozen_case_path):
            continue
        try:
            critique_json_path, critique_md_path, narrative = build_replay_case_critique_from_paths(
                frozen_case_path,
                decision_path,
                comparison_path,
            )
        except FileNotFoundError:
            continue
        outputs.append({
            "json_path": critique_json_path,
            "md_path": critique_md_path,
            "summary": narrative["summary"],
            "proposals": narrative["proposals"],
            "risks": narrative["risks"],
        })

    return outputs


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_case_critique.py REPLAY_ID")
        sys.exit(1)

    replay_id = sys.argv[1]
    outputs = build_replay_case_critiques(replay_id)
    print(json.dumps({
        "replay_id": replay_id,
        "critique_count": len(outputs),
        "sample_path": outputs[0]["json_path"] if outputs else None,
    }, indent=2))


if __name__ == "__main__":
    main()
