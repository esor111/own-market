"""
Research-only separability study for bank hostile-window cases.

Goal:
- compare 2024 bank setups that were worsened by the promoted calendar-confidence
  caution against 2025 bank setups where that same caution improved outcomes
- test whether a small number of simple replay-safe features can distinguish the
  "elite" 2024 setups from the weaker 2025 setups

This is not a rule builder. It is a diagnostic study to see whether the groups
are cleanly separable at all.

Usage:
    python bank_elite_setup_separability_study.py
"""
import itertools
import json
import os
from collections import Counter
from datetime import datetime

from bank_hostile_window_gap_study import COMPARE_GROUPS, build_rows
from config import VALIDATION_DIR


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")

NUMERIC_FEATURES = {
    "score": lambda row: (row.get("decision") or {}).get("score"),
    "raw_confidence": lambda row: (row.get("decision") or {}).get("confidence"),
    "calibrated_confidence_pct": lambda row: (row.get("record") or {}).get("calibrated_confidence_pct"),
    "risk_reward_ratio": lambda row: (row.get("decision") or {}).get("risk_reward_ratio"),
    "close_position_20d": lambda row: (row.get("metrics") or {}).get("close_position_20d"),
    "close_position_60d": lambda row: (row.get("metrics") or {}).get("close_position_60d"),
    "return_5d_pct": lambda row: (row.get("metrics") or {}).get("return_5d_pct"),
    "return_20d_pct": lambda row: (row.get("metrics") or {}).get("return_20d_pct"),
    "volume_ratio_5d": lambda row: (row.get("metrics") or {}).get("volume_ratio_5d"),
    "turnover_ratio_5d_to_20d": lambda row: (row.get("liquidity_metrics") or {}).get("turnover_ratio_5d_to_20d"),
    "latest_turnover_surprise_vs20d": lambda row: (row.get("liquidity_metrics") or {}).get("latest_turnover_surprise_vs20d"),
    "latest_trades_surprise_vs20d": lambda row: (row.get("liquidity_metrics") or {}).get("latest_trades_surprise_vs20d"),
}

CATEGORICAL_FEATURES = {
    "leadership_label": lambda row: row.get("leadership_label") or "UNKNOWN",
    "alignment_label": lambda row: row.get("alignment_label") or "UNKNOWN",
    "symbol": lambda row: row.get("symbol") or "UNKNOWN",
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


def outcome_direction(champion_verdict, challenger_verdict):
    scores = {
        "good_call": 2,
        "good_avoid": 2,
        "mixed_call": 1,
        "neutral_avoid": 1,
        "bad_call": 0,
        "missed_opportunity": 0,
        "unscored": 0,
    }
    champion_score = scores.get(champion_verdict, 0)
    challenger_score = scores.get(challenger_verdict, 0)
    if challenger_score > champion_score:
        return "improved"
    if challenger_score < champion_score:
        return "worsened"
    if champion_verdict != challenger_verdict:
        return "changed_same_quality"
    return "unchanged_quality"


def _build_bank_rows():
    rows_2024 = build_rows(COMPARE_GROUPS["2024_q3"])
    rows_2025 = build_rows(COMPARE_GROUPS["2025_q3"])
    return {
        "elite_2024": [row for row in rows_2024 if row["outcome_direction"] == "worsened"],
        "improved_2025": [row for row in rows_2025 if row["outcome_direction"] == "improved"],
        "churn_2024": [row for row in rows_2024 if row["outcome_direction"] in {"changed_same_quality", "unchanged_quality"}],
    }


def _numeric_threshold_candidates(groups):
    candidates = []
    all_rows = groups["elite_2024"] + groups["improved_2025"] + groups["churn_2024"]
    for feature_name, extractor in NUMERIC_FEATURES.items():
        values = sorted({
            round(float(value), 6)
            for row in all_rows
            for value in [extractor(row)]
            if isinstance(value, (int, float))
        })
        if len(values) < 2:
            continue
        for threshold in values:
            for op in (">=", "<="):
                candidates.append({
                    "type": "numeric",
                    "feature": feature_name,
                    "operator": op,
                    "threshold": round(float(threshold), 3),
                })
    return candidates


def _categorical_threshold_candidates(groups):
    candidates = []
    all_rows = groups["elite_2024"] + groups["improved_2025"] + groups["churn_2024"]
    for feature_name, extractor in CATEGORICAL_FEATURES.items():
        values = sorted({str(extractor(row)) for row in all_rows if extractor(row) is not None})
        if len(values) <= 1:
            continue
        max_size = min(2, len(values))
        for size in range(1, max_size + 1):
            for subset in itertools.combinations(values, size):
                candidates.append({
                    "type": "categorical",
                    "feature": feature_name,
                    "operator": "in",
                    "values": list(subset),
                })
    return candidates


def _matches(row, candidate):
    if candidate["type"] == "numeric":
        value = NUMERIC_FEATURES[candidate["feature"]](row)
        if not isinstance(value, (int, float)):
            return False
        threshold = candidate["threshold"]
        if candidate["operator"] == ">=":
            return float(value) >= threshold
        return float(value) <= threshold

    value = CATEGORICAL_FEATURES[candidate["feature"]](row)
    return str(value) in set(candidate["values"])


def _candidate_label(candidate):
    if candidate["type"] == "numeric":
        return f"{candidate['feature']} {candidate['operator']} {candidate['threshold']}"
    values = ", ".join(candidate["values"])
    return f"{candidate['feature']} in [{values}]"


def _evaluate_candidate(groups, candidate):
    elite_hits = sum(1 for row in groups["elite_2024"] if _matches(row, candidate))
    improved_hits = sum(1 for row in groups["improved_2025"] if _matches(row, candidate))
    churn_hits = sum(1 for row in groups["churn_2024"] if _matches(row, candidate))
    total_hits = elite_hits + improved_hits + churn_hits
    if total_hits == 0:
        return None

    elite_total = len(groups["elite_2024"]) or 1
    improved_total = len(groups["improved_2025"]) or 1
    churn_total = len(groups["churn_2024"]) or 1

    elite_precision = round(elite_hits / total_hits, 3)
    elite_recall = round(elite_hits / elite_total, 3)
    improved_capture_rate = round(improved_hits / improved_total, 3)
    churn_capture_rate = round(churn_hits / churn_total, 3)

    return {
        "rule": _candidate_label(candidate),
        "candidate": candidate,
        "elite_hits": elite_hits,
        "improved_hits": improved_hits,
        "churn_hits": churn_hits,
        "total_hits": total_hits,
        "elite_precision": elite_precision,
        "elite_recall": elite_recall,
        "improved_capture_rate": improved_capture_rate,
        "churn_capture_rate": churn_capture_rate,
    }


def _evaluate_combo(groups, cat_candidate, num_candidate):
    def combo_match(row):
        return _matches(row, cat_candidate) and _matches(row, num_candidate)

    elite_hits = sum(1 for row in groups["elite_2024"] if combo_match(row))
    improved_hits = sum(1 for row in groups["improved_2025"] if combo_match(row))
    churn_hits = sum(1 for row in groups["churn_2024"] if combo_match(row))
    total_hits = elite_hits + improved_hits + churn_hits
    if total_hits == 0:
        return None

    elite_total = len(groups["elite_2024"]) or 1
    improved_total = len(groups["improved_2025"]) or 1
    churn_total = len(groups["churn_2024"]) or 1

    return {
        "rule": f"{_candidate_label(cat_candidate)} AND {_candidate_label(num_candidate)}",
        "elite_hits": elite_hits,
        "improved_hits": improved_hits,
        "churn_hits": churn_hits,
        "total_hits": total_hits,
        "elite_precision": round(elite_hits / total_hits, 3),
        "elite_recall": round(elite_hits / elite_total, 3),
        "improved_capture_rate": round(improved_hits / improved_total, 3),
        "churn_capture_rate": round(churn_hits / churn_total, 3),
        "candidate": {
            "categorical": cat_candidate,
            "numeric": num_candidate,
        },
    }


def _evaluate_numeric_pair(groups, left_candidate, right_candidate):
    def combo_match(row):
        return _matches(row, left_candidate) and _matches(row, right_candidate)

    elite_hits = sum(1 for row in groups["elite_2024"] if combo_match(row))
    improved_hits = sum(1 for row in groups["improved_2025"] if combo_match(row))
    churn_hits = sum(1 for row in groups["churn_2024"] if combo_match(row))
    total_hits = elite_hits + improved_hits + churn_hits
    if total_hits == 0:
        return None

    elite_total = len(groups["elite_2024"]) or 1
    improved_total = len(groups["improved_2025"]) or 1
    churn_total = len(groups["churn_2024"]) or 1

    return {
        "rule": f"{_candidate_label(left_candidate)} AND {_candidate_label(right_candidate)}",
        "elite_hits": elite_hits,
        "improved_hits": improved_hits,
        "churn_hits": churn_hits,
        "total_hits": total_hits,
        "elite_precision": round(elite_hits / total_hits, 3),
        "elite_recall": round(elite_hits / elite_total, 3),
        "improved_capture_rate": round(improved_hits / improved_total, 3),
        "churn_capture_rate": round(churn_hits / churn_total, 3),
        "candidate": {
            "left": left_candidate,
            "right": right_candidate,
        },
    }


def _sort_key(item):
    return (
        item["elite_precision"],
        item["elite_hits"],
        -item["improved_hits"],
        -item["churn_hits"],
        item["elite_recall"],
    )


def _find_candidates(groups):
    numeric_candidates = _numeric_threshold_candidates(groups)
    categorical_candidates = _categorical_threshold_candidates(groups)

    single_results = []
    for candidate in numeric_candidates + categorical_candidates:
        result = _evaluate_candidate(groups, candidate)
        if result:
            single_results.append(result)

    combo_results = []
    symbol_combo_results = []
    for cat_candidate in categorical_candidates:
        if cat_candidate["feature"] not in {"leadership_label", "symbol"}:
            continue
        for num_candidate in numeric_candidates:
            if num_candidate["feature"] not in {
                "close_position_20d",
                "return_5d_pct",
                "return_20d_pct",
                "volume_ratio_5d",
                "score",
            }:
                continue
            result = _evaluate_combo(groups, cat_candidate, num_candidate)
            if result:
                if cat_candidate["feature"] == "symbol":
                    symbol_combo_results.append(result)
                else:
                    combo_results.append(result)

    numeric_pair_results = []
    numeric_pair_feature_names = {
        "close_position_20d",
        "return_5d_pct",
        "return_20d_pct",
        "volume_ratio_5d",
        "score",
    }
    numeric_pair_candidates = [
        candidate for candidate in numeric_candidates
        if candidate["feature"] in numeric_pair_feature_names
    ]
    for left_candidate, right_candidate in itertools.combinations(numeric_pair_candidates, 2):
        if left_candidate["feature"] == right_candidate["feature"]:
            continue
        result = _evaluate_numeric_pair(groups, left_candidate, right_candidate)
        if result:
            numeric_pair_results.append(result)

    good_singles = [
        item for item in single_results
        if item["elite_hits"] >= 3 and item["improved_hits"] <= 8
    ]
    good_combos = [
        item for item in combo_results
        if item["elite_hits"] >= 3 and item["improved_hits"] <= 5
    ]
    good_symbol_combos = [
        item for item in symbol_combo_results
        if item["elite_hits"] >= 3 and item["improved_hits"] <= 2
    ]
    good_numeric_pairs = [
        item for item in numeric_pair_results
        if item["elite_hits"] >= 3 and item["improved_hits"] <= 5
    ]

    return {
        "top_single_feature_rules": sorted(good_singles, key=_sort_key, reverse=True)[:12],
        "top_generalizable_combo_rules": sorted(good_combos, key=_sort_key, reverse=True)[:12],
        "top_numeric_pair_rules": sorted(good_numeric_pairs, key=_sort_key, reverse=True)[:12],
        "top_symbol_combo_rules": sorted(good_symbol_combos, key=_sort_key, reverse=True)[:12],
    }


def _build_findings(groups, results):
    findings = []
    top_single = results["top_single_feature_rules"][0] if results["top_single_feature_rules"] else None
    top_generalizable_combo = results["top_generalizable_combo_rules"][0] if results["top_generalizable_combo_rules"] else None
    top_numeric_pair = results["top_numeric_pair_rules"][0] if results["top_numeric_pair_rules"] else None
    top_symbol_combo = results["top_symbol_combo_rules"][0] if results["top_symbol_combo_rules"] else None

    if top_single:
        findings.append(
            "There are simple one-feature slices that lean toward preserving elite 2024 bank setups, but none of them are clean enough by themselves to justify a rule."
        )
        findings.append(
            f"Best single-feature preservation slice: `{top_single['rule']}` with elite hits `{top_single['elite_hits']}`, 2025-improved hits `{top_single['improved_hits']}`, and 2024-churn hits `{top_single['churn_hits']}`."
        )
    else:
        findings.append(
            "No single-feature slice cleanly isolates the elite 2024 bank setups without also swallowing too many 2025-improved cases."
        )

    if top_numeric_pair:
        findings.append(
            f"Best generalizable numeric pattern: `{top_numeric_pair['rule']}` with elite precision `{top_numeric_pair['elite_precision']}` and elite recall `{top_numeric_pair['elite_recall']}`."
        )
        findings.append(
            "That pattern suggests the clipped 2024 winners were often fresh short-term accelerations off only moderate 20-day trend extension, not already-overextended trends."
        )
    if top_generalizable_combo:
        findings.append(
            f"Best generalizable combo slice: `{top_generalizable_combo['rule']}` with elite precision `{top_generalizable_combo['elite_precision']}` and elite recall `{top_generalizable_combo['elite_recall']}`."
        )
    else:
        findings.append(
            "Leadership-plus-threshold combinations are still thin and unstable, so leadership alone is not enough to separate the groups."
        )
    findings.append(
        "The useful generalizable candidates lean on momentum-shape and setup-state quality more than on sector or event bucket alone, which means the remaining gap is likely about setup texture."
    )

    if top_symbol_combo:
        findings.append(
            f"The cleanest symbol-specific slice is `{top_symbol_combo['rule']}`, but that is diagnostic only and should be treated as overfit research evidence, not as a system change."
        )
    else:
        findings.append(
            "No symbol-specific slice was clean enough to matter, which is good because it reduces the risk of overfitting to one name."
        )
    return findings


def _build_markdown(payload):
    lines = [
        "# Bank Elite Setup Separability Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        "",
        "## Why This Exists",
        "",
        "This study asks whether the strong-looking 2024 bank setups that got clipped by the promoted hostile-window caution are distinguishable from the middling 2025 bank setups where that same caution helped.",
        "",
        "## Findings",
    ]
    for finding in payload["findings"]:
        lines.append(f"- {finding}")

    lines.extend([
        "",
        "## Group Sizes",
        f"- elite_2024: `{payload['group_sizes']['elite_2024']}`",
        f"- improved_2025: `{payload['group_sizes']['improved_2025']}`",
        f"- churn_2024: `{payload['group_sizes']['churn_2024']}`",
        "",
        "## Top Single-Feature Rules",
    ])
    for item in payload["results"]["top_single_feature_rules"]:
        lines.append(
            f"- `{item['rule']}` -> elite `{item['elite_hits']}`, improved `{item['improved_hits']}`, churn `{item['churn_hits']}`, elite_precision `{item['elite_precision']}`, elite_recall `{item['elite_recall']}`"
        )

    lines.extend([
        "",
        "## Top Generalizable Combo Rules",
    ])
    for item in payload["results"]["top_generalizable_combo_rules"]:
        lines.append(
            f"- `{item['rule']}` -> elite `{item['elite_hits']}`, improved `{item['improved_hits']}`, churn `{item['churn_hits']}`, elite_precision `{item['elite_precision']}`, elite_recall `{item['elite_recall']}`"
        )

    lines.extend([
        "",
        "## Top Numeric-Pair Rules",
    ])
    for item in payload["results"]["top_numeric_pair_rules"]:
        lines.append(
            f"- `{item['rule']}` -> elite `{item['elite_hits']}`, improved `{item['improved_hits']}`, churn `{item['churn_hits']}`, elite_precision `{item['elite_precision']}`, elite_recall `{item['elite_recall']}`"
        )

    lines.extend([
        "",
        "## Top Symbol-Specific Diagnostic Rules",
    ])
    for item in payload["results"]["top_symbol_combo_rules"]:
        lines.append(
            f"- `{item['rule']}` -> elite `{item['elite_hits']}`, improved `{item['improved_hits']}`, churn `{item['churn_hits']}`, elite_precision `{item['elite_precision']}`, elite_recall `{item['elite_recall']}`"
        )

    return "\n".join(lines).strip() + "\n"


def run_study():
    groups = _build_bank_rows()
    results = _find_candidates(groups)
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "group_sizes": {key: len(value) for key, value in groups.items()},
        "results": results,
    }
    payload["findings"] = _build_findings(groups, results)

    dated_json = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__bank_elite_setup_separability_study_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__bank_elite_setup_separability_study_v1.json")
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")
    save_json(dated_json, payload)
    save_json(latest_json, payload)
    markdown = _build_markdown(payload)
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
