"""
Study market/sector regime context as a genuinely different entry family.

This family is intentionally different from:
- close-based ranking
- liquidity/gap stability
- Thursday drag
- the guarded commercial-bank candidate refinement lane

It asks whether broad market participation, weak breadth, or official
sector/benchmark context creates a reusable execution-aware entry lane.

Usage:
    python entry_market_regime_context_study.py
    python entry_market_regime_context_study.py DATASET_JSON_PATH
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

from artifact_io import save_json_atomic as save_json, save_text_atomic as save_text
from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DEFAULT_DATASET_PATH = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__entry_research_dataset_v1.json",
)

DERIVED_COVERED_FIELDS = [
    "market_advance_decline_ratio",
    "market_median_diff_pct",
    "market_top_5_turnover_share",
]

OFFICIAL_COVERED_FIELDS = [
    "official_benchmark_pct_change",
    "official_sector_pct_change",
]

REGIME_SPECS = [
    {
        "name": "baseline_derived_context",
        "coverage": "derived",
        "matcher": lambda row: True,
    },
    {
        "name": "broad_support",
        "coverage": "derived",
        "matcher": lambda row: row["market_advance_decline_ratio"] >= 1.0 and row["market_median_diff_pct"] >= 0.0,
    },
    {
        "name": "weak_breadth",
        "coverage": "derived",
        "matcher": lambda row: row["market_advance_decline_ratio"] < 1.0,
    },
    {
        "name": "very_weak_breadth",
        "coverage": "derived",
        "matcher": lambda row: row["market_advance_decline_ratio"] < 0.60,
    },
    {
        "name": "official_sector_up_benchmark_up",
        "coverage": "official",
        "matcher": lambda row: row["official_sector_pct_change"] >= 0.0 and row["official_benchmark_pct_change"] >= 0.0,
    },
    {
        "name": "official_sector_gt1_benchmark_nonneg",
        "coverage": "official",
        "matcher": lambda row: row["official_sector_pct_change"] >= 1.0 and row["official_benchmark_pct_change"] >= 0.0,
    },
    {
        "name": "official_sector_down",
        "coverage": "official",
        "matcher": lambda row: row["official_sector_pct_change"] < 0.0,
    },
]

RANKER_SPECS = [
    {
        "name": "weak_breadth_rr_low_top1_global",
        "coverage": "derived",
        "matcher": lambda row: row["market_advance_decline_ratio"] < 1.0,
        "group_keys": ["session_date"],
        "sort_keys": [("risk_reward_ratio", False), ("return_5d_pct", True)],
    },
    {
        "name": "weak_breadth_rr_low_top1_by_sector",
        "coverage": "derived",
        "matcher": lambda row: row["market_advance_decline_ratio"] < 1.0,
        "group_keys": ["session_date", "sector_name"],
        "sort_keys": [("risk_reward_ratio", False), ("return_5d_pct", True)],
    },
    {
        "name": "broad_support_rr_low_top1_global",
        "coverage": "derived",
        "matcher": lambda row: row["market_advance_decline_ratio"] >= 1.0 and row["market_median_diff_pct"] >= 0.0,
        "group_keys": ["session_date"],
        "sort_keys": [("risk_reward_ratio", False), ("return_5d_pct", True)],
    },
    {
        "name": "broad_support_ret5_top1_global",
        "coverage": "derived",
        "matcher": lambda row: row["market_advance_decline_ratio"] >= 1.0 and row["market_median_diff_pct"] >= 0.0,
        "group_keys": ["session_date"],
        "sort_keys": [("return_5d_pct", True), ("risk_reward_ratio", False)],
    },
    {
        "name": "official_sector_tailwind_rel_sector_top1_global",
        "coverage": "official",
        "matcher": lambda row: row["official_sector_pct_change"] >= 0.0 and row["official_benchmark_pct_change"] >= 0.0,
        "group_keys": ["session_date"],
        "sort_keys": [("relative_return_vs_sector", True), ("risk_reward_ratio", False)],
    },
    {
        "name": "official_sector_tailwind_rr_low_top1_by_sector",
        "coverage": "official",
        "matcher": lambda row: row["official_sector_pct_change"] >= 0.0 and row["official_benchmark_pct_change"] >= 0.0,
        "group_keys": ["session_date", "sector_name"],
        "sort_keys": [("risk_reward_ratio", False), ("return_5d_pct", True)],
    },
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


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


def _top_symbol_share(rows):
    if not rows:
        return None
    counts = Counter(str(row.get("symbol") or "UNKNOWN") for row in rows)
    return _rate(max(counts.values()), len(rows))


def _subset_summary(name, rows):
    positive_count = sum(1 for row in rows if row["executable_entry_label"] == "tradable_positive_after_costs")
    negative_count = sum(1 for row in rows if row["executable_entry_label"] == "tradable_negative_after_costs")
    return {
        "name": name,
        "candidate_count": len(rows),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "positive_rate": _rate(positive_count, len(rows)),
        "negative_rate": _rate(negative_count, len(rows)),
        "symbol_concentration": _counts(rows, "symbol"),
        "month_concentration": _counts(rows, "month_key"),
        "sector_concentration": _counts(rows, "sector_name"),
        "top_symbol_share": _top_symbol_share(rows),
        "avg_market_advance_decline_ratio": _avg(rows, "market_advance_decline_ratio"),
        "avg_market_median_diff_pct": _avg(rows, "market_median_diff_pct"),
        "avg_official_sector_pct_change": _avg(rows, "official_sector_pct_change"),
        "avg_official_benchmark_pct_change": _avg(rows, "official_benchmark_pct_change"),
    }


def _covered_rows(rows, coverage_name):
    if coverage_name == "derived":
        return [
            row for row in rows
            if all(isinstance(row.get(field), (int, float)) for field in DERIVED_COVERED_FIELDS)
        ]
    return [
        row for row in rows
        if all(isinstance(row.get(field), (int, float)) for field in OFFICIAL_COVERED_FIELDS)
    ]


def _safe_sort_value(value, descending):
    if value is None:
        return float("-inf") if descending else float("inf")
    return -value if descending else value


def _sort_key(row, sort_keys):
    values = []
    for key, descending in sort_keys:
        values.append(_safe_sort_value(row.get(key), descending))
    values.append(str(row.get("symbol") or ""))
    return tuple(values)


def _group_key(row, keys):
    return tuple(row.get(key) for key in keys)


def _ranker_summary(rows, spec):
    covered = _covered_rows(rows, spec["coverage"])
    matched = [row for row in covered if spec["matcher"](row)]
    grouped = defaultdict(list)
    for row in matched:
        grouped[_group_key(row, spec["group_keys"])].append(row)
    selected = []
    for _, items in grouped.items():
        ranked = sorted(items, key=lambda item: _sort_key(item, spec["sort_keys"]))
        selected.append(ranked[0])
    summary = _subset_summary(spec["name"], selected)
    summary["coverage_type"] = spec["coverage"]
    summary["selected_group_count"] = len(grouped)
    return summary


def _sector_regime_rows(rows):
    derived = _covered_rows(rows, "derived")
    output = []
    for sector_name in sorted(set(row.get("sector_name") for row in derived)):
        sector_rows = [row for row in derived if row.get("sector_name") == sector_name]
        weak_rows = [row for row in sector_rows if row["market_advance_decline_ratio"] < 1.0]
        strong_rows = [
            row for row in sector_rows
            if row["market_advance_decline_ratio"] >= 1.0 and row["market_median_diff_pct"] >= 0.0
        ]
        output.append({
            "sector_name": sector_name,
            "all_rows": _subset_summary(f"{sector_name}_all", sector_rows),
            "weak_breadth_rows": _subset_summary(f"{sector_name}_weak_breadth", weak_rows),
            "broad_support_rows": _subset_summary(f"{sector_name}_broad_support", strong_rows),
        })
    return output


def _render_markdown(payload):
    lines = [
        "# Entry Market Regime Context Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- dataset_path: `{payload['dataset_path']}`",
        f"- enterable_row_count: `{payload['enterable_row_count']}`",
        f"- derived_context_coverage: `{payload['derived_context_coverage']}`",
        f"- official_context_coverage: `{payload['official_context_coverage']}`",
        "",
        "## Regime Rows",
        "",
    ]

    for row in payload["regime_rows"]:
        lines.extend([
            f"### `{row['name']}`",
            f"- coverage_type: `{row['coverage_type']}`",
            f"- candidate_count: `{row['candidate_count']}`",
            f"- positive_rate: `{row['positive_rate']}`",
            f"- negative_rate: `{row['negative_rate']}`",
            f"- top_symbol_share: `{row['top_symbol_share']}`",
            f"- sectors: `{row['sector_concentration']}`",
            "",
        ])

    lines.extend(["## Ranker Rows", ""])
    for row in payload["ranker_rows"]:
        lines.extend([
            f"### `{row['name']}`",
            f"- coverage_type: `{row['coverage_type']}`",
            f"- candidate_count: `{row['candidate_count']}`",
            f"- selected_group_count: `{row['selected_group_count']}`",
            f"- positive_rate: `{row['positive_rate']}`",
            f"- negative_rate: `{row['negative_rate']}`",
            f"- top_symbol_share: `{row['top_symbol_share']}`",
            f"- sectors: `{row['sector_concentration']}`",
            "",
        ])

    lines.extend(["## Sector Split", ""])
    for row in payload["sector_regime_rows"]:
        lines.extend([
            f"### `{row['sector_name']}`",
            f"- all_rows: `{row['all_rows']['positive_rate']}` from `{row['all_rows']['candidate_count']}`",
            f"- weak_breadth_rows: `{row['weak_breadth_rows']['positive_rate']}` from `{row['weak_breadth_rows']['candidate_count']}`",
            f"- broad_support_rows: `{row['broad_support_rows']['positive_rate']}` from `{row['broad_support_rows']['candidate_count']}`",
            "",
        ])

    lines.extend([
        "## Interpretation",
        "",
        f"- verdict: `{payload['interpretation']['verdict']}`",
        f"- reason: `{payload['interpretation']['reason']}`",
        "",
        "## Decision",
        "",
        "- do not open a broad market-regime entry branch from this study alone",
        "- treat any weak-breadth lift as descriptive unless it survives cleaner cross-symbol validation",
        "- if a future market-context branch opens, it should be narrow and sector-aware, not global",
    ])
    return "\n".join(lines) + "\n"


def build_entry_market_regime_context_study(dataset_path):
    dataset = load_json(dataset_path)
    rows = [row for row in (dataset.get("rows") or []) if row.get("entry_executed")]
    derived_rows = _covered_rows(rows, "derived")
    official_rows = _covered_rows(rows, "official")

    regime_rows = []
    for spec in REGIME_SPECS:
        covered = _covered_rows(rows, spec["coverage"])
        matched = [row for row in covered if spec["matcher"](row)]
        summary = _subset_summary(spec["name"], matched)
        summary["coverage_type"] = spec["coverage"]
        regime_rows.append(summary)

    ranker_rows = [_ranker_summary(rows, spec) for spec in RANKER_SPECS]
    sector_rows = _sector_regime_rows(rows)

    baseline_derived = next(row for row in regime_rows if row["name"] == "baseline_derived_context")
    weak_breadth = next(row for row in regime_rows if row["name"] == "weak_breadth")
    broad_support = next(row for row in regime_rows if row["name"] == "broad_support")
    best_ranker = max(ranker_rows, key=lambda row: (row.get("positive_rate") or -1, row.get("candidate_count") or 0))
    bank_row = next((row for row in sector_rows if row["sector_name"] == "COMMERCIAL BANKS"), None)

    if (
        (best_ranker.get("positive_rate") or 0) < 0.40
        and (weak_breadth.get("positive_rate") or 0) < 0.42
        and (broad_support.get("positive_rate") or 0) <= (baseline_derived.get("positive_rate") or 0)
    ):
        verdict = "market_context_not_a_broad_entry_family"
        reason = (
            "broad support did not improve executable quality, official sector/benchmark context was weak, "
            "and the only lift came from weak-breadth pockets that stayed too small or too heterogeneous to trust globally"
        )
    elif bank_row and (bank_row["weak_breadth_rows"].get("positive_rate") or 0) > (bank_row["broad_support_rows"].get("positive_rate") or 0):
        verdict = "descriptive_sector_regime_effect_only"
        reason = (
            "commercial banks were clearly weaker in broad-support sessions than in weak-breadth sessions, "
            "but the effect is still sector-specific and not strong enough to justify a reusable global entry branch"
        )
    else:
        verdict = "unclear_market_context_signal"
        reason = "market context moved quality a little, but not enough to justify a new broad branch yet"

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "enterable_row_count": len(rows),
        "derived_context_coverage": _rate(len(derived_rows), len(rows)),
        "official_context_coverage": _rate(len(official_rows), len(rows)),
        "regime_rows": regime_rows,
        "ranker_rows": ranker_rows,
        "sector_regime_rows": sector_rows,
        "interpretation": {
            "verdict": verdict,
            "reason": reason,
            "best_ranker_name": best_ranker.get("name"),
            "best_ranker_positive_rate": best_ranker.get("positive_rate"),
        },
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_market_regime_context_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_market_regime_context_study_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_market_regime_context_study(dataset_path)
    print(json.dumps({
        "verdict": (payload.get("interpretation") or {}).get("verdict"),
        "best_ranker_name": (payload.get("interpretation") or {}).get("best_ranker_name"),
        "best_ranker_positive_rate": (payload.get("interpretation") or {}).get("best_ranker_positive_rate"),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
