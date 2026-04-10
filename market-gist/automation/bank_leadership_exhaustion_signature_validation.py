"""
Research-only validation of a commercial-bank leadership-exhaustion signature.

This study:
1. derives candidate decision-time signatures from July 2025 commercial-bank
   actionable cases, where late-July downside damage is treated as the positive
   discovery class;
2. validates the best discovery signatures on non-July commercial-bank history;
3. reports whether "leader-looking + extended" bank setups keep mapping to
   downside damage or whether the pattern is too unstable to trust.

Usage:
    python bank_leadership_exhaustion_signature_validation.py
    python bank_leadership_exhaustion_signature_validation.py --source-path PATH --output-id hostile_windows
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
SOURCE_PATH = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__replay_next_open_tradability_study_v1.json",
)
DOWNSIDE_LABELS = {"gap_below_stop", "tradable_negative_gross"}
JULY_DISCOVERY_MONTH = "2025-07"
FISCAL_YEAR_END_PHASE = "fiscal_year_end_window"


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _rank_desc(values_by_symbol):
    ranked = sorted(
        [(symbol, value) for symbol, value in values_by_symbol.items() if value is not None],
        key=lambda item: item[1],
        reverse=True,
    )
    return {symbol: index + 1 for index, (symbol, _value) in enumerate(ranked)}


def _enrich_with_leadership(records):
    grouped = defaultdict(list)
    for record in records:
        grouped[(record["replay_id"], record["session_date"])].append(record)

    enriched = []
    for (_replay_id, _session_date), items in grouped.items():
        rank_return_5d = _rank_desc({item["symbol"]: item.get("return_5d_pct") for item in items})
        rank_volume = _rank_desc({item["symbol"]: item.get("volume_ratio_5d") for item in items})
        rank_close = _rank_desc({item["symbol"]: item.get("close_position_20d") for item in items})

        for item in items:
            ranks = [
                rank_return_5d.get(item["symbol"]),
                rank_volume.get(item["symbol"]),
                rank_close.get(item["symbol"]),
            ]
            known_ranks = [rank for rank in ranks if rank is not None]
            leadership_top2_count = sum(1 for rank in known_ranks if rank <= 2)
            leadership_composite_rank = (
                round(mean(known_ranks), 4) if known_ranks else None
            )
            enriched.append({
                **item,
                "return_5d_rank": rank_return_5d.get(item["symbol"]),
                "volume_ratio_rank": rank_volume.get(item["symbol"]),
                "close_position_rank": rank_close.get(item["symbol"]),
                "leadership_top2_count": leadership_top2_count,
                "leadership_composite_rank": leadership_composite_rank,
                "is_downside_damage": item.get("next_open_label") in DOWNSIDE_LABELS,
                "is_late_july_exhaustion_damage": (
                    str(item.get("session_date") or "") > "2025-07-10"
                    and item.get("next_open_label") in DOWNSIDE_LABELS
                ),
                "is_fiscal_year_end": item.get("calendar_phase") == FISCAL_YEAR_END_PHASE,
            })
    return enriched


def _candidate_thresholds(records, feature_name):
    values = sorted(
        set(
            round(float(record[feature_name]), 4)
            for record in records
            if isinstance(record.get(feature_name), (int, float))
        )
    )
    if not values:
        return []
    if len(values) <= 15:
        return values
    percentiles = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9]
    indices = sorted(
        set(min(len(values) - 1, max(0, int((len(values) - 1) * percentile))) for percentile in percentiles)
    )
    return [values[index] for index in indices]


def _condition_match(record, condition):
    feature_name = condition["feature_name"]
    value = record.get(feature_name)
    if value is None:
        return False
    threshold = condition["threshold"]
    comparator = condition["comparator"]
    if comparator == ">=":
        return value >= threshold
    return value <= threshold


def _evaluate_signature(records, conditions, positive_field):
    matched = [record for record in records if all(_condition_match(record, condition) for condition in conditions)]
    support = len(matched)
    tp = sum(1 for record in matched if record[positive_field])
    fp = support - tp
    positive_count = sum(1 for record in records if record[positive_field])
    negative_count = len(records) - positive_count
    precision = tp / support if support else 0.0
    recall = tp / positive_count if positive_count else 0.0
    leakage = fp / negative_count if negative_count else 0.0
    f1 = 0.0 if precision + recall == 0 else (2 * precision * recall) / (precision + recall)
    return {
        "support": support,
        "true_positive": tp,
        "false_positive": fp,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "negative_leakage": round(leakage, 4),
    }


def _condition_label(condition):
    threshold = condition["threshold"]
    if isinstance(threshold, float):
        threshold_text = f"{threshold:.4f}".rstrip("0").rstrip(".")
    else:
        threshold_text = str(threshold)
    return f"{condition['feature_name']} {condition['comparator']} {threshold_text}"


def _search_discovery_signatures(records):
    feature_names = [
        "return_20d_pct",
        "return_5d_pct",
        "close_position_20d",
        "volume_ratio_5d",
        "target_distance_close_pct",
        "risk_reward_ratio",
        "return_5d_rank",
        "volume_ratio_rank",
        "close_position_rank",
        "leadership_top2_count",
        "leadership_composite_rank",
    ]
    allowed_comparators = {
        "return_20d_pct": [">="],
        "return_5d_pct": [">="],
        "close_position_20d": [">="],
        "volume_ratio_5d": [">=", "<="],
        "target_distance_close_pct": [">=", "<="],
        "risk_reward_ratio": [">=", "<="],
        "return_5d_rank": ["<="],
        "volume_ratio_rank": ["<="],
        "close_position_rank": ["<="],
        "leadership_top2_count": [">="],
        "leadership_composite_rank": ["<="],
    }
    leadership_features = {
        "return_5d_rank",
        "volume_ratio_rank",
        "close_position_rank",
        "leadership_top2_count",
        "leadership_composite_rank",
    }
    one_condition_rows = []
    for feature_name in feature_names:
        thresholds = _candidate_thresholds(records, feature_name)
        if not thresholds:
            continue
        comparators = allowed_comparators[feature_name]
        for threshold in thresholds:
            for comparator in comparators:
                conditions = [{
                    "feature_name": feature_name,
                    "comparator": comparator,
                    "threshold": threshold,
                }]
                metrics = _evaluate_signature(records, conditions, "is_late_july_exhaustion_damage")
                if metrics["support"] < 8 or metrics["support"] >= len(records) or metrics["true_positive"] < 8:
                    continue
                one_condition_rows.append({
                    "conditions": conditions,
                    "condition_text": [_condition_label(condition) for condition in conditions],
                    **metrics,
                })

    one_condition_rows.sort(
        key=lambda row: (row["f1"], row["precision"], -row["negative_leakage"], row["support"]),
        reverse=True,
    )
    seed_rows = one_condition_rows[:30]

    two_condition_rows = []
    seen_keys = set()
    for index, left_row in enumerate(seed_rows):
        for right_row in seed_rows[index + 1:]:
            left_condition = left_row["conditions"][0]
            right_condition = right_row["conditions"][0]
            if left_condition["feature_name"] == right_condition["feature_name"]:
                continue
            left_is_leadership = left_condition["feature_name"] in leadership_features
            right_is_leadership = right_condition["feature_name"] in leadership_features
            if left_is_leadership == right_is_leadership:
                continue
            conditions = [left_condition, right_condition]
            key = tuple(sorted(_condition_label(condition) for condition in conditions))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            metrics = _evaluate_signature(records, conditions, "is_late_july_exhaustion_damage")
            if metrics["support"] < 8 or metrics["true_positive"] < 8:
                continue
            two_condition_rows.append({
                "conditions": conditions,
                "condition_text": [_condition_label(condition) for condition in conditions],
                **metrics,
            })

    two_condition_rows.sort(
        key=lambda row: (row["f1"], row["precision"], -row["negative_leakage"], row["support"]),
        reverse=True,
    )
    combined = one_condition_rows[:10] + two_condition_rows[:15]
    combined.sort(
        key=lambda row: (len(row["conditions"]), row["f1"], row["precision"], -row["negative_leakage"], row["support"]),
        reverse=True,
    )
    return combined[:12], one_condition_rows[:10], two_condition_rows[:10]


def _validation_summary(records, conditions):
    matched = [record for record in records if all(_condition_match(record, condition) for condition in conditions)]
    label_counts = Counter(record.get("next_open_label") for record in matched)
    calendar_counts = Counter(record.get("calendar_phase") or "unknown" for record in matched)
    symbol_counts = Counter(record.get("symbol") or "unknown" for record in matched)
    month_counts = Counter(str(record.get("session_date") or "")[:7] for record in matched)
    downside_rate = round(label_counts.get("gap_below_stop", 0) + label_counts.get("tradable_negative_gross", 0), 4)
    downside_rate = round((label_counts.get("gap_below_stop", 0) + label_counts.get("tradable_negative_gross", 0)) / len(matched), 4) if matched else None
    return {
        "matched_count": len(matched),
        "downside_damage_count": label_counts.get("gap_below_stop", 0) + label_counts.get("tradable_negative_gross", 0),
        "downside_damage_rate": downside_rate,
        "tradable_positive_count": label_counts.get("tradable_positive_gross", 0),
        "tradable_positive_rate": round(label_counts.get("tradable_positive_gross", 0) / len(matched), 4) if matched else None,
        "gap_above_target_count": label_counts.get("gap_above_target", 0),
        "gap_above_target_rate": round(label_counts.get("gap_above_target", 0) / len(matched), 4) if matched else None,
        "label_counts": dict(label_counts),
        "calendar_phase_counts": dict(calendar_counts.most_common(10)),
        "symbol_counts": dict(symbol_counts.most_common(10)),
        "session_month_counts": dict(month_counts.most_common(20)),
        "feature_means": {
            field_name: round(mean(
                record[field_name] for record in matched
                if isinstance(record.get(field_name), (int, float))
            ), 4) if any(isinstance(record.get(field_name), (int, float)) for record in matched) else None
            for field_name in [
                "return_5d_pct",
                "return_20d_pct",
                "close_position_20d",
                "volume_ratio_5d",
                "target_distance_close_pct",
                "risk_reward_ratio",
                "leadership_top2_count",
                "leadership_composite_rank",
            ]
        },
        "example_cases": [
            {
                "session_date": record.get("session_date"),
                "symbol": record.get("symbol"),
                "calendar_phase": record.get("calendar_phase"),
                "next_open_label": record.get("next_open_label"),
                "comparison_verdict": record.get("comparison_verdict"),
                "return_5d_pct": record.get("return_5d_pct"),
                "return_20d_pct": record.get("return_20d_pct"),
                "volume_ratio_5d": record.get("volume_ratio_5d"),
                "close_position_20d": record.get("close_position_20d"),
                "return_5d_rank": record.get("return_5d_rank"),
                "volume_ratio_rank": record.get("volume_ratio_rank"),
                "close_position_rank": record.get("close_position_rank"),
                "leadership_top2_count": record.get("leadership_top2_count"),
                "leadership_composite_rank": record.get("leadership_composite_rank"),
            }
            for record in matched[:10]
        ],
    }


def _build_markdown(payload):
    lines = [
        "# Bank Leadership Exhaustion Signature Validation",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- source_path: `{payload['source_path']}`",
        "",
        "## Short Answer",
        "",
        "This study derives decision-time exhaustion signatures from July 2025 commercial-bank actionables and tests them on non-July commercial-bank history.",
        "",
        "## Discovery Setup",
        "",
        f"- july_discovery_case_count: `{payload['discovery_case_count']}`",
        f"- july_downside_damage_count: `{payload['discovery_downside_damage_count']}`",
        f"- july_non_damage_count: `{payload['discovery_non_damage_count']}`",
        "",
        "## Best Discovery Signatures",
        "",
    ]

    for row in payload.get("best_discovery_signatures", []):
        lines.extend([
            f"### `{' AND '.join(row['condition_text'])}`",
            "",
            f"- support: `{row['support']}`",
            f"- true_positive: `{row['true_positive']}`",
            f"- false_positive: `{row['false_positive']}`",
            f"- precision: `{row['precision']}`",
            f"- recall: `{row['recall']}`",
            f"- f1: `{row['f1']}`",
            f"- negative_leakage: `{row['negative_leakage']}`",
            "",
            "Validation:",
            f"- non_july_all: `{row['validation_non_july_all']}`",
            f"- non_july_fiscal_year_end: `{row['validation_non_july_fiscal_year_end']}`",
            "",
        ])

    lines.extend([
        "## Findings",
        "",
    ])
    for finding in payload.get("findings", []):
        lines.append(f"- {finding}")

    return "\n".join(lines).strip() + "\n"


def _output_file_paths(output_id=None):
    suffix = "" if not output_id else f"__{output_id}"
    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__bank_leadership_exhaustion_signature_validation{suffix}_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"latest__bank_leadership_exhaustion_signature_validation{suffix}_v1.json",
    )
    return dated_json_path, latest_json_path, dated_json_path.replace(".json", ".md"), latest_json_path.replace(".json", ".md")


def build_bank_leadership_exhaustion_signature_validation(source_path=SOURCE_PATH, output_id=None):
    payload = load_json(source_path)
    records = [
        record for record in (payload.get("records") or [])
        if record.get("sector_name") == "COMMERCIAL BANKS"
    ]
    records = _enrich_with_leadership(records)

    july_records = [
        record for record in records
        if str(record.get("session_date") or "").startswith(JULY_DISCOVERY_MONTH)
    ]
    non_july_records = [
        record for record in records
        if not str(record.get("session_date") or "").startswith(JULY_DISCOVERY_MONTH)
    ]
    non_july_fiscal_records = [
        record for record in non_july_records
        if record.get("calendar_phase") == FISCAL_YEAR_END_PHASE
    ]

    best_discovery_signatures, best_single_condition, best_two_condition = _search_discovery_signatures(july_records)

    enriched_best = []
    for row in best_discovery_signatures:
        enriched_best.append({
            **row,
            "validation_non_july_all": _validation_summary(non_july_records, row["conditions"]),
            "validation_non_july_fiscal_year_end": _validation_summary(non_july_fiscal_records, row["conditions"]),
        })

    findings = []
    if enriched_best:
        best = enriched_best[0]
        findings.append(
            f"The strongest July discovery signature was `{' AND '.join(best['condition_text'])}`, with discovery precision `{best['precision']}` and recall `{best['recall']}`."
        )
        validation_all = best["validation_non_july_all"]
        validation_fiscal = best["validation_non_july_fiscal_year_end"]
        findings.append(
            f"Outside July, that signature matched `{validation_all['matched_count']}` commercial-bank cases with downside-damage rate `{validation_all['downside_damage_rate']}` and tradable-positive leakage `{validation_all['tradable_positive_rate']}`."
        )
        findings.append(
            f"Inside non-July fiscal-year-end bank cases specifically, it matched `{validation_fiscal['matched_count']}` cases with downside-damage rate `{validation_fiscal['downside_damage_rate']}`."
        )
        findings.append(
            "If the best July signature still leaks heavily into tradable-positive cases or fails to stay concentrated in hostile fiscal-year-end windows, it is diagnostic only and not rule-ready."
        )
    else:
        findings.append("No July discovery signature met the minimum support thresholds, so there is no stable exhaustion texture to validate yet.")

    output = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_path": source_path,
        "discovery_case_count": len(july_records),
        "discovery_downside_damage_count": sum(1 for record in july_records if record["is_late_july_exhaustion_damage"]),
        "discovery_non_damage_count": sum(1 for record in july_records if not record["is_late_july_exhaustion_damage"]),
        "non_july_case_count": len(non_july_records),
        "non_july_fiscal_year_end_case_count": len(non_july_fiscal_records),
        "best_single_condition_signatures": best_single_condition,
        "best_two_condition_signatures": best_two_condition,
        "best_discovery_signatures": enriched_best,
        "findings": findings,
    }

    dated_json_path, latest_json_path, dated_md_path, latest_md_path = _output_file_paths(output_id)
    markdown = _build_markdown(output)
    save_json(dated_json_path, output)
    save_json(latest_json_path, output)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return output, latest_json_path, latest_md_path


def main():
    args = list(sys.argv[1:])
    source_path = SOURCE_PATH
    output_id = None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--source-path":
            if index + 1 >= len(args):
                print("Missing value after --source-path")
                sys.exit(1)
            source_path = args[index + 1]
            index += 2
            continue
        if arg == "--output-id":
            if index + 1 >= len(args):
                print("Missing value after --output-id")
                sys.exit(1)
            output_id = args[index + 1]
            index += 2
            continue
        print(f"Unknown argument: {arg}")
        sys.exit(1)

    output, latest_json_path, latest_md_path = build_bank_leadership_exhaustion_signature_validation(
        source_path=source_path,
        output_id=output_id,
    )
    print(json.dumps({
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
        "best_signature": (output.get("best_discovery_signatures") or [{}])[0].get("condition_text"),
    }, indent=2))


if __name__ == "__main__":
    main()
