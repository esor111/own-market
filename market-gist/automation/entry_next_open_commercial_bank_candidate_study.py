"""
Study the first repeated next-open positive entry candidate.

Target slice:
    COMMERCIAL BANKS
    no_named_phase
    no_symbol_event_match
    strongly_overconfident
    watch_only

Goal:
    Compare strict positives vs strict negatives inside the enterable next-open
    universe and test whether a simple separator survives the latest month.
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import VALIDATION_DIR
from entry_next_open_branch_readiness_queue import DEFAULT_DATASET_PATH, load_json


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
TARGET_SLICE = "COMMERCIAL BANKS | no_named_phase | no_symbol_event_match | strongly_overconfident | watch_only"
FEATURES = [
    "risk_reward_ratio",
    "recomputed_rr_at_entry",
    "return_1d_pct",
    "return_5d_pct",
    "return_20d_pct",
    "volume_ratio_5d",
    "close_position_20d",
    "next_open_gap_pct",
    "relative_return_vs_sector",
    "relative_return_vs_basket",
    "relative_score_vs_basket",
]
LEADERSHIP_CANDIDATES = [
    {"name": "not_both_leader", "allowed": {"sector_leader", "basket_leader", "middle", "basket_laggard", "sector_laggard"}},
    {"name": "sector_or_basket_leader", "allowed": {"sector_leader", "basket_leader"}},
    {"name": "sector_leader_only", "allowed": {"sector_leader"}},
    {"name": "basket_leader_only", "allowed": {"basket_leader"}},
    {"name": "both_leader_only", "allowed": {"both_leader"}},
]


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _bucket_key(row):
    return " | ".join([
        row.get("sector_name") or "UNKNOWN",
        row.get("calendar_phase") or "UNKNOWN",
        row.get("event_state") or "UNKNOWN",
        row.get("confidence_label") or "UNKNOWN",
        row.get("action") or "UNKNOWN",
    ])


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _avg(rows, key):
    values = [row.get(key) for row in rows if isinstance(row.get(key), (int, float))]
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _counts(rows, key):
    return dict(Counter(str(row.get(key) or "UNKNOWN") for row in rows).most_common(10))


def _numeric_thresholds(rows, feature_name):
    return sorted(
        set(
            round(float(row[feature_name]), 4)
            for row in rows
            if isinstance(row.get(feature_name), (int, float))
        )
    )


def _numeric_match(row, feature_name, comparator, threshold):
    value = row.get(feature_name)
    if not isinstance(value, (int, float)):
        return False
    if comparator == "<=":
        return value <= threshold
    return value >= threshold


def _categorical_match(row, allowed_labels):
    return (row.get("leadership_label") or "UNKNOWN") in allowed_labels


def _subset_summary(name, rows):
    return {
        "name": name,
        "count": len(rows),
        "positive_count": sum(1 for row in rows if row["entry_outcome_family"] == "strict_positive"),
        "negative_count": sum(1 for row in rows if row["entry_outcome_family"] == "strict_negative"),
        "positive_rate": _rate(
            sum(1 for row in rows if row["entry_outcome_family"] == "strict_positive"),
            len(rows),
        ),
        "symbols": _counts(rows, "symbol"),
        "months": _counts(rows, "month_key"),
        "leadership": _counts(rows, "leadership_label"),
        "avg_risk_reward_ratio": _avg(rows, "risk_reward_ratio"),
        "avg_recomputed_rr_at_entry": _avg(rows, "recomputed_rr_at_entry"),
        "avg_return_5d_pct": _avg(rows, "return_5d_pct"),
        "avg_next_open_gap_pct": _avg(rows, "next_open_gap_pct"),
        "avg_close_position_20d": _avg(rows, "close_position_20d"),
        "avg_volume_ratio_5d": _avg(rows, "volume_ratio_5d"),
    }


def _evaluate_numeric_candidate(rows, feature_name, comparator, threshold):
    matched = [row for row in rows if _numeric_match(row, feature_name, comparator, threshold)]
    positive_count = sum(1 for row in matched if row["entry_outcome_family"] == "strict_positive")
    return {
        "type": "numeric",
        "description": f"{feature_name} {comparator} {threshold}",
        "feature_name": feature_name,
        "comparator": comparator,
        "threshold": threshold,
        "matched_count": len(matched),
        "positive_count": positive_count,
        "negative_count": len(matched) - positive_count,
        "positive_rate": _rate(positive_count, len(matched)),
        "symbols": _counts(matched, "symbol"),
        "months": _counts(matched, "month_key"),
        "leadership": _counts(matched, "leadership_label"),
    }


def _evaluate_leadership_candidate(rows, candidate):
    matched = [row for row in rows if _categorical_match(row, candidate["allowed"])]
    positive_count = sum(1 for row in matched if row["entry_outcome_family"] == "strict_positive")
    return {
        "type": "leadership",
        "description": candidate["name"],
        "leadership_allowed": sorted(candidate["allowed"]),
        "matched_count": len(matched),
        "positive_count": positive_count,
        "negative_count": len(matched) - positive_count,
        "positive_rate": _rate(positive_count, len(matched)),
        "symbols": _counts(matched, "symbol"),
        "months": _counts(matched, "month_key"),
        "leadership": _counts(matched, "leadership_label"),
    }


def _evaluate_pair_candidate(rows, numeric_candidate, leadership_candidate):
    allowed = set(leadership_candidate["allowed"])
    matched = [
        row for row in rows
        if _numeric_match(row, numeric_candidate["feature_name"], numeric_candidate["comparator"], numeric_candidate["threshold"])
        and _categorical_match(row, allowed)
    ]
    positive_count = sum(1 for row in matched if row["entry_outcome_family"] == "strict_positive")
    return {
        "type": "pair",
        "description": f"{numeric_candidate['feature_name']} {numeric_candidate['comparator']} {numeric_candidate['threshold']} AND leadership in {sorted(allowed)}",
        "numeric_candidate": {
            "feature_name": numeric_candidate["feature_name"],
            "comparator": numeric_candidate["comparator"],
            "threshold": numeric_candidate["threshold"],
        },
        "leadership_allowed": sorted(allowed),
        "matched_count": len(matched),
        "positive_count": positive_count,
        "negative_count": len(matched) - positive_count,
        "positive_rate": _rate(positive_count, len(matched)),
        "symbols": _counts(matched, "symbol"),
        "months": _counts(matched, "month_key"),
        "leadership": _counts(matched, "leadership_label"),
    }


def _candidate_sort_key(item):
    return (
        item.get("positive_rate") or -1,
        item.get("positive_count") or 0,
        -(item.get("negative_count") or 0),
        item.get("matched_count") or 0,
    )


def _discover_numeric_candidates(discovery_rows):
    candidates = []
    for feature_name in FEATURES:
        for threshold in _numeric_thresholds(discovery_rows, feature_name):
            for comparator in ("<=", ">="):
                evaluated = _evaluate_numeric_candidate(discovery_rows, feature_name, comparator, threshold)
                if evaluated["matched_count"] < 5 or evaluated["positive_count"] < 5:
                    continue
                candidates.append(evaluated)
    candidates.sort(key=_candidate_sort_key, reverse=True)
    return candidates


def _discover_leadership_candidates(discovery_rows):
    candidates = []
    for candidate in LEADERSHIP_CANDIDATES:
        evaluated = _evaluate_leadership_candidate(discovery_rows, candidate)
        if evaluated["matched_count"] < 5 or evaluated["positive_count"] < 5:
            continue
        candidates.append(evaluated)
    candidates.sort(key=_candidate_sort_key, reverse=True)
    return candidates


def _discover_pair_candidates(discovery_rows, numeric_candidates, leadership_candidates):
    candidates = []
    for numeric_candidate in numeric_candidates[:8]:
        numeric_spec = {
            "feature_name": numeric_candidate["feature_name"],
            "comparator": numeric_candidate["comparator"],
            "threshold": numeric_candidate["threshold"],
        }
        for leadership_candidate in leadership_candidates:
            leadership_spec = {
                "allowed": set(leadership_candidate["leadership_allowed"]),
            }
            evaluated = _evaluate_pair_candidate(discovery_rows, numeric_spec, leadership_spec)
            if evaluated["matched_count"] < 4 or evaluated["positive_count"] < 4:
                continue
            candidates.append(evaluated)
    candidates.sort(key=_candidate_sort_key, reverse=True)
    return candidates


def _validation_view(candidates, validation_rows, evaluator):
    output = []
    for candidate in candidates[:10]:
        evaluated = evaluator(validation_rows, candidate)
        output.append({
            "candidate": candidate,
            "validation": evaluated,
        })
    output.sort(
        key=lambda item: (
            item["validation"].get("positive_rate") or -1,
            item["validation"].get("positive_count") or 0,
            -(item["validation"].get("negative_count") or 0),
            item["validation"].get("matched_count") or 0,
        ),
        reverse=True,
    )
    return output


def _numeric_validation_evaluator(rows, candidate):
    return _evaluate_numeric_candidate(
        rows,
        candidate["feature_name"],
        candidate["comparator"],
        candidate["threshold"],
    )


def _leadership_validation_evaluator(rows, candidate):
    return _evaluate_leadership_candidate(
        rows,
        {"allowed": set(candidate["leadership_allowed"]), "name": candidate["description"]},
    )


def _pair_validation_evaluator(rows, candidate):
    return _evaluate_pair_candidate(
        rows,
        candidate["numeric_candidate"],
        {"allowed": set(candidate["leadership_allowed"])},
    )


def _render_candidate_block(lines, title, rows):
    lines.extend([f"## {title}", ""])
    if not rows:
        lines.append("- none")
        lines.append("")
        return
    for item in rows:
        candidate = item["candidate"]
        validation = item["validation"]
        lines.extend([
            f"### `{candidate['description']}`",
            f"- discovery_match: `{candidate['matched_count']}`",
            f"- discovery_positive: `{candidate['positive_count']}`",
            f"- discovery_negative: `{candidate['negative_count']}`",
            f"- discovery_positive_rate: `{candidate['positive_rate']}`",
            f"- validation_match: `{validation['matched_count']}`",
            f"- validation_positive: `{validation['positive_count']}`",
            f"- validation_negative: `{validation['negative_count']}`",
            f"- validation_positive_rate: `{validation['positive_rate']}`",
            f"- validation_symbols: `{validation['symbols']}`",
            f"- validation_months: `{validation['months']}`",
            "",
        ])


def _render_markdown(payload):
    lines = [
        "# Entry Next-Open Commercial Bank Candidate Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- dataset_path: `{payload['dataset_path']}`",
        f"- target_slice: `{payload['target_slice']}`",
        f"- slice_count: `{payload['slice_count']}`",
        "",
        "## Split Design",
        "",
        f"- discovery_months: `{payload['split_design']['discovery_months']}`",
        f"- validation_months: `{payload['split_design']['validation_months']}`",
        "",
        "## Cohorts",
        "",
    ]
    for key in ("all_rows", "discovery_rows", "validation_rows"):
        cohort = payload["cohorts"][key]
        lines.extend([
            f"### `{key}`",
            f"- count: `{cohort['count']}`",
            f"- positive_count: `{cohort['positive_count']}`",
            f"- negative_count: `{cohort['negative_count']}`",
            f"- positive_rate: `{cohort['positive_rate']}`",
            f"- symbols: `{cohort['symbols']}`",
            f"- months: `{cohort['months']}`",
            f"- leadership: `{cohort['leadership']}`",
            f"- avg_risk_reward_ratio: `{cohort['avg_risk_reward_ratio']}`",
            f"- avg_recomputed_rr_at_entry: `{cohort['avg_recomputed_rr_at_entry']}`",
            f"- avg_return_5d_pct: `{cohort['avg_return_5d_pct']}`",
            f"- avg_next_open_gap_pct: `{cohort['avg_next_open_gap_pct']}`",
            "",
        ])

    _render_candidate_block(lines, "Top Numeric Candidates", payload["top_numeric_candidates"])
    _render_candidate_block(lines, "Top Leadership Candidates", payload["top_leadership_candidates"])
    _render_candidate_block(lines, "Top Pair Candidates", payload["top_pair_candidates"])

    broader = payload.get("broader_probe") or {}
    lines.extend([
        "## Broader Probe",
        "",
        f"- candidate: `{broader.get('candidate_description')}`",
        f"- broader_match_count: `{broader.get('matched_count')}`",
        f"- broader_positive_count: `{broader.get('positive_count')}`",
        f"- broader_negative_count: `{broader.get('negative_count')}`",
        f"- broader_positive_rate: `{broader.get('positive_rate')}`",
        f"- broader_sectors: `{broader.get('sectors')}`",
        f"- broader_symbols: `{broader.get('symbols')}`",
        "",
    ])
    return "\n".join(lines) + "\n"


def build_entry_next_open_commercial_bank_candidate_study(dataset_path):
    dataset = load_json(dataset_path)
    all_rows = [
        row for row in (dataset.get("rows") or [])
        if row.get("entry_executed") and _bucket_key(row) == TARGET_SLICE
    ]
    month_keys = sorted({row["month_key"] for row in all_rows})
    if len(month_keys) < 2:
        raise ValueError("Need at least two months in the target slice to split discovery and validation.")
    discovery_months = month_keys[:-1]
    validation_months = month_keys[-1:]

    discovery_rows = [row for row in all_rows if row["month_key"] in discovery_months]
    validation_rows = [row for row in all_rows if row["month_key"] in validation_months]

    numeric_candidates = _discover_numeric_candidates(discovery_rows)
    leadership_candidates = _discover_leadership_candidates(discovery_rows)
    pair_candidates = _discover_pair_candidates(discovery_rows, numeric_candidates, leadership_candidates)

    top_numeric_candidates = _validation_view(numeric_candidates, validation_rows, _numeric_validation_evaluator)
    top_leadership_candidates = _validation_view(leadership_candidates, validation_rows, _leadership_validation_evaluator)
    top_pair_candidates = _validation_view(pair_candidates, validation_rows, _pair_validation_evaluator)

    broader_probe = {}
    if top_pair_candidates:
        best_pair = top_pair_candidates[0]["candidate"]
        broader_eval = _pair_validation_evaluator(
            [row for row in (dataset.get("rows") or []) if row.get("entry_executed")],
            best_pair,
        )
        broader_probe = {
            "candidate_description": best_pair["description"],
            "matched_count": broader_eval["matched_count"],
            "positive_count": broader_eval["positive_count"],
            "negative_count": broader_eval["negative_count"],
            "positive_rate": broader_eval["positive_rate"],
            "sectors": _counts(
                [
                    row for row in (dataset.get("rows") or [])
                    if row.get("entry_executed")
                    and _numeric_match(
                        row,
                        best_pair["numeric_candidate"]["feature_name"],
                        best_pair["numeric_candidate"]["comparator"],
                        best_pair["numeric_candidate"]["threshold"],
                    )
                    and _categorical_match(row, set(best_pair["leadership_allowed"]))
                ],
                "sector_name",
            ),
            "symbols": broader_eval["symbols"],
        }

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "target_slice": TARGET_SLICE,
        "slice_count": len(all_rows),
        "split_design": {
            "discovery_months": discovery_months,
            "validation_months": validation_months,
        },
        "cohorts": {
            "all_rows": _subset_summary("all_rows", all_rows),
            "discovery_rows": _subset_summary("discovery_rows", discovery_rows),
            "validation_rows": _subset_summary("validation_rows", validation_rows),
        },
        "top_numeric_candidates": top_numeric_candidates[:6],
        "top_leadership_candidates": top_leadership_candidates[:5],
        "top_pair_candidates": top_pair_candidates[:6],
        "broader_probe": broader_probe,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_commercial_bank_candidate_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_commercial_bank_candidate_study_v1.json",
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")
    markdown = _render_markdown(payload)

    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main(argv=None):
    argv = argv or sys.argv[1:]
    dataset_path = argv[0] if argv else DEFAULT_DATASET_PATH
    payload, latest_json_path, latest_md_path = build_entry_next_open_commercial_bank_candidate_study(dataset_path)
    best_pair = (payload.get("top_pair_candidates") or [{}])[0]
    print(json.dumps({
        "target_slice": payload["target_slice"],
        "slice_count": payload["slice_count"],
        "best_pair_candidate": (best_pair.get("candidate") or {}).get("description"),
        "best_pair_validation_positive_rate": ((best_pair.get("validation") or {}).get("positive_rate")),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
