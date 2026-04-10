"""
Explain why the guarded commercial-bank next-open candidate stays guarded.

Target slice:
    COMMERCIAL BANKS
    no_named_phase
    no_symbol_event_match
    strongly_overconfident
    watch_only

Goal:
    Separate three questions cleanly:
    1. Is the exact cross-symbol texture still real?
    2. Does the broader slice widen cleanly beyond that texture?
    3. If not, are the residual positives still symbol-dependent?

Usage:
    python entry_next_open_commercial_bank_attribution_study.py
    python entry_next_open_commercial_bank_attribution_study.py DATASET_JSON_PATH
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR
from entry_next_open_branch_readiness_queue import DEFAULT_DATASET_PATH, load_json


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
TARGET_SLICE = "COMMERCIAL BANKS | no_named_phase | no_symbol_event_match | strongly_overconfident | watch_only"

POSITIVE_REFINEMENT_CONDITIONS = [
    ("risk_reward_ratio <= 0.78", lambda row: _numeric_le(row, "risk_reward_ratio", 0.78)),
    ("risk_reward_ratio <= 0.66", lambda row: _numeric_le(row, "risk_reward_ratio", 0.66)),
    ("leadership != both_leader", lambda row: (row.get("leadership_label") or "UNKNOWN") != "both_leader"),
    ("return_5d_pct >= 0", lambda row: _numeric_ge(row, "return_5d_pct", 0.0)),
    ("liq_turnover_cv_20d <= 0.75", lambda row: _numeric_le(row, "liq_turnover_cv_20d", 0.75)),
    ("market_advance_decline_ratio >= 1.0", lambda row: _numeric_ge(row, "market_advance_decline_ratio", 1.0)),
]

NEGATIVE_ATTRIBUTION_CONDITIONS = [
    ("risk_reward_ratio > 0.78", lambda row: _numeric_gt(row, "risk_reward_ratio", 0.78)),
    ("leadership == both_leader", lambda row: (row.get("leadership_label") or "UNKNOWN") == "both_leader"),
    ("return_5d_pct < 0", lambda row: _numeric_lt(row, "return_5d_pct", 0.0)),
    ("liq_turnover_cv_20d > 0.75", lambda row: _numeric_gt(row, "liq_turnover_cv_20d", 0.75)),
    ("market_advance_decline_ratio < 0.60", lambda row: _numeric_lt(row, "market_advance_decline_ratio", 0.60)),
]


def _numeric_le(row, key, threshold):
    value = row.get(key)
    return isinstance(value, (int, float)) and value <= threshold


def _numeric_lt(row, key, threshold):
    value = row.get(key)
    return isinstance(value, (int, float)) and value < threshold


def _numeric_ge(row, key, threshold):
    value = row.get(key)
    return isinstance(value, (int, float)) and value >= threshold


def _numeric_gt(row, key, threshold):
    value = row.get(key)
    return isinstance(value, (int, float)) and value > threshold


def _bucket_key(row):
    return " | ".join([
        row.get("sector_name") or "UNKNOWN",
        row.get("calendar_phase") or "UNKNOWN",
        row.get("event_state") or "UNKNOWN",
        row.get("confidence_label") or "UNKNOWN",
        row.get("action") or "UNKNOWN",
    ])


def _target_slice_match(row):
    return _bucket_key(row) == TARGET_SLICE


def _exact_texture_match(row):
    return _numeric_le(row, "risk_reward_ratio", 0.78) and (row.get("leadership_label") != "both_leader")


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _counts(rows, key):
    return dict(Counter(str(row.get(key) or "UNKNOWN") for row in rows).most_common(10))


def _avg(rows, key):
    values = [row.get(key) for row in rows if isinstance(row.get(key), (int, float))]
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _subset_summary(name, rows):
    positive_count = sum(1 for row in rows if row["entry_outcome_family"] == "strict_positive")
    negative_count = sum(1 for row in rows if row["entry_outcome_family"] == "strict_negative")
    return {
        "name": name,
        "count": len(rows),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "positive_rate": _rate(positive_count, len(rows)),
        "symbols": _counts(rows, "symbol"),
        "months": _counts(rows, "month_key"),
        "leadership": _counts(rows, "leadership_label"),
        "avg_risk_reward_ratio": _avg(rows, "risk_reward_ratio"),
        "avg_recomputed_rr_at_entry": _avg(rows, "recomputed_rr_at_entry"),
        "avg_return_5d_pct": _avg(rows, "return_5d_pct"),
        "avg_return_20d_pct": _avg(rows, "return_20d_pct"),
        "avg_liq_turnover_cv_20d": _avg(rows, "liq_turnover_cv_20d"),
        "avg_market_advance_decline_ratio": _avg(rows, "market_advance_decline_ratio"),
    }


def _symbol_summary(rows, symbol):
    symbol_rows = [row for row in rows if row.get("symbol") == symbol]
    return _subset_summary(symbol, symbol_rows)


def _top_symbol_share(rows):
    if not rows:
        return None
    counts = Counter(str(row.get("symbol") or "UNKNOWN") for row in rows)
    return _rate(max(counts.values()), len(rows))


def _evaluate_condition(rows, name, matcher):
    matched = [row for row in rows if matcher(row)]
    positive_count = sum(1 for row in matched if row["entry_outcome_family"] == "strict_positive")
    negative_count = sum(1 for row in matched if row["entry_outcome_family"] == "strict_negative")
    return {
        "description": name,
        "matched_count": len(matched),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "positive_rate": _rate(positive_count, len(matched)),
        "negative_capture_rate": None,
        "positive_leak_rate": None,
        "unique_symbols": len(Counter(row.get("symbol") for row in matched)),
        "top_symbol_share": _top_symbol_share(matched),
        "symbols": _counts(matched, "symbol"),
        "months": _counts(matched, "month_key"),
        "leadership": _counts(matched, "leadership_label"),
    }


def _positive_refinement_sort_key(item):
    return (
        item.get("positive_rate") or -1,
        item.get("positive_count") or 0,
        -(item.get("negative_count") or 0),
        -(item.get("top_symbol_share") or 1.0),
        item.get("matched_count") or 0,
    )


def _negative_attribution_sort_key(item):
    return (
        item.get("negative_capture_rate") or -1,
        -(item.get("positive_leak_rate") or 1.0),
        item.get("negative_count") or 0,
        -(item.get("matched_count") or 0),
    )


def _discover_positive_refinements(rows):
    candidates = []
    for name, matcher in POSITIVE_REFINEMENT_CONDITIONS:
        evaluated = _evaluate_condition(rows, name, matcher)
        if evaluated["matched_count"] >= 5 and evaluated["positive_count"] >= 5 and (evaluated["positive_rate"] or 0) >= 0.75:
            candidates.append(evaluated)

    for i, (left_name, left_matcher) in enumerate(POSITIVE_REFINEMENT_CONDITIONS):
        for right_name, right_matcher in POSITIVE_REFINEMENT_CONDITIONS[i + 1:]:
            evaluated = _evaluate_condition(
                rows,
                f"{left_name} AND {right_name}",
                lambda row, l=left_matcher, r=right_matcher: l(row) and r(row),
            )
            if evaluated["matched_count"] >= 4 and evaluated["positive_count"] >= 4 and (evaluated["positive_rate"] or 0) >= 0.75:
                candidates.append(evaluated)

    unique = {}
    for candidate in candidates:
        unique[candidate["description"]] = candidate
    output = list(unique.values())
    output.sort(key=_positive_refinement_sort_key, reverse=True)
    return output


def _discover_negative_attributions(rows, total_negatives, total_positives):
    candidates = []
    for name, matcher in NEGATIVE_ATTRIBUTION_CONDITIONS:
        evaluated = _evaluate_condition(rows, name, matcher)
        if evaluated["negative_count"] < 2:
            continue
        evaluated["negative_capture_rate"] = _rate(evaluated["negative_count"], total_negatives)
        evaluated["positive_leak_rate"] = _rate(evaluated["positive_count"], total_positives)
        candidates.append(evaluated)

    for i, (left_name, left_matcher) in enumerate(NEGATIVE_ATTRIBUTION_CONDITIONS):
        for right_name, right_matcher in NEGATIVE_ATTRIBUTION_CONDITIONS[i + 1:]:
            evaluated = _evaluate_condition(
                rows,
                f"{left_name} AND {right_name}",
                lambda row, l=left_matcher, r=right_matcher: l(row) and r(row),
            )
            if evaluated["negative_count"] < 2:
                continue
            evaluated["negative_capture_rate"] = _rate(evaluated["negative_count"], total_negatives)
            evaluated["positive_leak_rate"] = _rate(evaluated["positive_count"], total_positives)
            candidates.append(evaluated)

    unique = {}
    for candidate in candidates:
        unique[candidate["description"]] = candidate
    output = list(unique.values())
    output.sort(key=_negative_attribution_sort_key, reverse=True)
    return output


def _render_refinement(lines, title, rows):
    lines.extend([title, ""])
    if not rows:
        lines.extend(["- none", ""])
        return
    for item in rows:
        lines.append(
            f"- `{item['description']}`: `{item['positive_count']}/{item['matched_count']}` positive, "
            f"`{item['negative_count']}` negative, top symbol share `{item['top_symbol_share']}`"
        )
        lines.append(f"  - symbols: `{item['symbols']}`")
        lines.append(f"  - months: `{item['months']}`")
    lines.append("")


def _render_negative_flags(lines, rows):
    lines.extend(["## Negative Attribution Flags", ""])
    for item in rows:
        lines.append(
            f"- `{item['description']}`: captures `{item['negative_count']}/{item['matched_count']}` rows, "
            f"negative capture `{item['negative_capture_rate']}`, positive leak `{item['positive_leak_rate']}`"
        )
        lines.append(f"  - symbols: `{item['symbols']}`")
        lines.append(f"  - months: `{item['months']}`")
    lines.append("")


def _render_markdown(payload):
    lines = [
        "# Entry Next-Open Commercial Bank Attribution Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- dataset_path: `{payload['dataset_path']}`",
        f"- target_slice: `{payload['target_slice']}`",
        "",
        "## Slice Decomposition",
        "",
        f"- target_slice: `{payload['summaries']['target_slice']['positive_count']}/{payload['summaries']['target_slice']['count']}` positive",
        f"- exact_texture: `{payload['summaries']['exact_texture']['positive_count']}/{payload['summaries']['exact_texture']['count']}` positive",
        f"- residual_broadening: `{payload['summaries']['residual_broadening']['positive_count']}/{payload['summaries']['residual_broadening']['count']}` positive",
        f"- exact_texture_positive_share: `{payload['coverage']['exact_texture_positive_share']}`",
        f"- residual_positive_symbol_concentration: `{payload['coverage']['residual_positive_symbol_concentration']}`",
        "",
        "## Symbol Attribution",
        "",
        f"- EBL: `{payload['symbol_summaries']['EBL']['positive_count']}/{payload['symbol_summaries']['EBL']['count']}` positive",
        f"- SANIMA: `{payload['symbol_summaries']['SANIMA']['positive_count']}/{payload['symbol_summaries']['SANIMA']['count']}` positive",
        f"- residual positives by symbol: `{payload['residual_positive_symbols']}`",
        f"- residual negatives by symbol: `{payload['residual_negative_symbols']}`",
        "",
    ]

    _render_refinement(lines, "## Cross-Symbol Positive Refinements", payload["cross_symbol_positive_refinements"][:6])
    _render_refinement(lines, "## Residual Cross-Symbol Refinements", payload["residual_cross_symbol_refinements"][:6])
    _render_refinement(lines, "## Residual Symbol-Heavy Refinements", payload["residual_symbol_heavy_refinements"][:6])
    _render_negative_flags(lines, payload["negative_attribution_flags"][:8])

    lines.extend([
        "## Interpretation",
        "",
        f"- broadening_verdict: `{payload['interpretation']['broadening_verdict']}`",
        f"- reason: `{payload['interpretation']['reason']}`",
        "",
        "## Decision",
        "",
        "- keep the guarded commercial-bank next-open candidate unchanged",
        "- do not broaden it beyond the exact texture from this attribution study",
        "- treat residual broadening outside the exact texture as descriptive until it stops being symbol-dependent",
    ])
    return "\n".join(lines) + "\n"


def build_entry_next_open_commercial_bank_attribution_study(dataset_path):
    dataset = load_json(dataset_path)
    rows = [row for row in (dataset.get("rows") or []) if row.get("entry_executed")]
    target_rows = [row for row in rows if _target_slice_match(row)]
    exact_rows = [row for row in target_rows if _exact_texture_match(row)]
    residual_rows = [row for row in target_rows if not _exact_texture_match(row)]

    target_summary = _subset_summary("target_slice", target_rows)
    exact_summary = _subset_summary("exact_texture", exact_rows)
    residual_summary = _subset_summary("residual_broadening", residual_rows)

    total_positives = target_summary["positive_count"]
    total_negatives = target_summary["negative_count"]
    residual_positive_rows = [row for row in residual_rows if row["entry_outcome_family"] == "strict_positive"]
    residual_negative_rows = [row for row in residual_rows if row["entry_outcome_family"] == "strict_negative"]

    positive_refinements = _discover_positive_refinements(target_rows)
    cross_symbol_positive_refinements = [
        row for row in positive_refinements
        if (row.get("unique_symbols") or 0) >= 2 and (row.get("top_symbol_share") or 1.0) <= 0.75
    ]

    residual_refinements = _discover_positive_refinements(residual_rows)
    residual_cross_symbol_refinements = [
        row for row in residual_refinements
        if (row.get("unique_symbols") or 0) >= 2 and (row.get("top_symbol_share") or 1.0) <= 0.75
    ]
    residual_symbol_heavy_refinements = [
        row for row in residual_refinements
        if (row.get("top_symbol_share") or 0) > 0.75
    ]

    negative_attribution_flags = _discover_negative_attributions(target_rows, total_negatives, total_positives)

    exact_positive_share = _rate(exact_summary["positive_count"], total_positives)
    residual_positive_symbols = _counts(residual_positive_rows, "symbol")
    residual_negative_symbols = _counts(residual_negative_rows, "symbol")
    residual_positive_single_symbol = len(residual_positive_symbols) == 1 and bool(residual_positive_rows)

    if (
        exact_summary["negative_count"] == 0
        and exact_summary["count"] >= 5
        and residual_positive_single_symbol
        and not residual_cross_symbol_refinements
    ):
        broadening_verdict = "exact_texture_real_broadening_symbol_dependent"
        reason = (
            "the exact cross-symbol texture is still clean, but every residual broadening pocket stays symbol-dependent "
            "and the remaining leakage is still concentrated in EBL-heavy rows"
        )
    elif exact_summary["negative_count"] == 0 and exact_summary["count"] >= 5:
        broadening_verdict = "exact_texture_real_broadening_unclear"
        reason = "the exact texture is still clean, but the broader slice is not yet honest enough to trust beyond it"
    else:
        broadening_verdict = "candidate_not_clean_enough"
        reason = "the candidate no longer stays clean once the exact texture is separated from the broader slice"

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "target_slice": TARGET_SLICE,
        "summaries": {
            "target_slice": target_summary,
            "exact_texture": exact_summary,
            "residual_broadening": residual_summary,
        },
        "symbol_summaries": {
            "EBL": _symbol_summary(target_rows, "EBL"),
            "SANIMA": _symbol_summary(target_rows, "SANIMA"),
        },
        "coverage": {
            "exact_texture_positive_share": exact_positive_share,
            "residual_positive_symbol_concentration": _top_symbol_share(residual_positive_rows),
        },
        "residual_positive_symbols": residual_positive_symbols,
        "residual_negative_symbols": residual_negative_symbols,
        "cross_symbol_positive_refinements": cross_symbol_positive_refinements,
        "residual_cross_symbol_refinements": residual_cross_symbol_refinements,
        "residual_symbol_heavy_refinements": residual_symbol_heavy_refinements,
        "negative_attribution_flags": negative_attribution_flags,
        "interpretation": {
            "broadening_verdict": broadening_verdict,
            "reason": reason,
        },
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_commercial_bank_attribution_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_commercial_bank_attribution_study_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_next_open_commercial_bank_attribution_study(dataset_path)
    print(json.dumps({
        "broadening_verdict": (payload.get("interpretation") or {}).get("broadening_verdict"),
        "exact_texture_positive_share": (payload.get("coverage") or {}).get("exact_texture_positive_share"),
        "residual_positive_symbols": payload.get("residual_positive_symbols"),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
