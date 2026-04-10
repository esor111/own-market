"""
Study replay-safe liquidity/execution context as an Entry Research v2 family.

This is intentionally different from the prior close-based ranking work:
- uses enterable next-open rows only
- emphasizes gap stability, turnover stability, and liquidity pressure
- optionally mixes in replay-safe market breadth context

Usage:
    python entry_liquidity_execution_context_study.py
    python entry_liquidity_execution_context_study.py DATASET_JSON_PATH
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DEFAULT_DATASET_PATH = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__entry_research_dataset_v1.json",
)


RANKER_SPECS = [
    {
        "name": "enter_all_enterable",
        "group_keys": [],
        "filters": [],
        "sort_keys": [],
        "top_n": None,
    },
    {
        "name": "stable_liquidity_top1_global",
        "group_keys": ["session_date"],
        "filters": [],
        "sort_keys": [
            ("liq_gap_over_2pct_share_20d", False),
            ("liq_avg_abs_gap_pct_20d", False),
            ("liq_turnover_cv_20d", False),
            ("liq_turnover_ratio_5d_to_20d", True),
        ],
        "top_n": 1,
    },
    {
        "name": "stable_liquidity_top1_by_sector",
        "group_keys": ["session_date", "sector_name"],
        "filters": [],
        "sort_keys": [
            ("liq_gap_over_2pct_share_20d", False),
            ("liq_avg_abs_gap_pct_20d", False),
            ("liq_turnover_cv_20d", False),
            ("liq_turnover_ratio_5d_to_20d", True),
        ],
        "top_n": 1,
    },
    {
        "name": "turnover_surge_low_gap_top1_global",
        "group_keys": ["session_date"],
        "filters": [],
        "sort_keys": [
            ("liq_latest_turnover_surprise_vs20d", True),
            ("liq_turnover_ratio_5d_to_20d", True),
            ("liq_gap_over_2pct_share_20d", False),
            ("liq_zero_trade_share_20d", False),
        ],
        "top_n": 1,
    },
    {
        "name": "broad_support_stable_liquidity_top1_global",
        "group_keys": ["session_date"],
        "filters": [
            {"key": "market_advance_decline_ratio", "op": ">=", "value": 1.0},
            {"key": "market_median_diff_pct", "op": ">=", "value": 0.0},
        ],
        "sort_keys": [
            ("liq_gap_over_2pct_share_20d", False),
            ("liq_turnover_cv_20d", False),
            ("liq_turnover_ratio_5d_to_20d", True),
            ("market_advance_decline_ratio", True),
        ],
        "top_n": 1,
    },
    {
        "name": "non_thursday_stable_liquidity_top1_global",
        "group_keys": ["session_date"],
        "filters": [
            {"key": "liq_is_thursday_close", "op": "==", "value": False},
        ],
        "sort_keys": [
            ("liq_gap_over_2pct_share_20d", False),
            ("liq_avg_abs_gap_pct_20d", False),
            ("liq_turnover_cv_20d", False),
            ("liq_turnover_ratio_5d_to_20d", True),
        ],
        "top_n": 1,
    },
]


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


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _avg(values):
    clean = [value for value in values if isinstance(value, (int, float))]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 4)


def _concentration_summary(rows, key):
    counter = Counter(str(row.get(key) or "UNKNOWN") for row in rows)
    total = len(rows)
    if not total:
        return {
            "unique_count": 0,
            "top_1_key": None,
            "top_1_count": 0,
            "top_1_share": None,
            "top_5": [],
        }
    top_key, top_count = counter.most_common(1)[0]
    return {
        "unique_count": len(counter),
        "top_1_key": top_key,
        "top_1_count": top_count,
        "top_1_share": _rate(top_count, total),
        "top_5": counter.most_common(5),
    }


def _safe_value(value, descending):
    if value is None:
        return float("-inf") if descending else float("inf")
    if isinstance(value, bool):
        value = int(value)
    return value


def _sort_tuple(row, sort_keys):
    values = []
    for key, descending in sort_keys:
        value = _safe_value(row.get(key), descending)
        values.append(-value if descending else value)
    values.append(str(row.get("symbol") or ""))
    return tuple(values)


def _group_key(row, keys):
    return tuple(row.get(key) for key in keys)


def _apply_filters(rows, filters):
    filtered = rows
    for filter_spec in filters:
        key = filter_spec["key"]
        op = filter_spec["op"]
        value = filter_spec["value"]
        if op == "<=":
            filtered = [row for row in filtered if row.get(key) is not None and row.get(key) <= value]
        elif op == ">=":
            filtered = [row for row in filtered if row.get(key) is not None and row.get(key) >= value]
        elif op == "==":
            filtered = [row for row in filtered if row.get(key) == value]
        else:
            raise ValueError(f"Unsupported filter op: {op}")
    return filtered


def _select_rows(rows, ranker):
    filtered = _apply_filters(rows, ranker["filters"])
    if ranker["top_n"] is None:
        return sorted(filtered, key=lambda item: (item["session_date"], item["symbol"], item["sector_name"]))
    grouped = defaultdict(list)
    for row in filtered:
        grouped[_group_key(row, ranker["group_keys"])].append(row)
    selected = []
    for _, items in grouped.items():
        ranked = sorted(items, key=lambda item: _sort_tuple(item, ranker["sort_keys"]))
        selected.extend(ranked[: ranker["top_n"]])
    selected.sort(key=lambda item: (item["session_date"], item["symbol"], item["sector_name"]))
    return selected


def _summary_for_rows(rows):
    label_counts = Counter(row["executable_entry_label"] for row in rows)
    positive_count = label_counts.get("tradable_positive_after_costs", 0)
    negative_count = label_counts.get("tradable_negative_after_costs", 0)
    return {
        "candidate_count": len(rows),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "positive_rate": _rate(positive_count, len(rows)),
        "negative_rate": _rate(negative_count, len(rows)),
        "avg_gap_over_2pct_share_20d": _avg([row.get("liq_gap_over_2pct_share_20d") for row in rows]),
        "avg_avg_abs_gap_pct_20d": _avg([row.get("liq_avg_abs_gap_pct_20d") for row in rows]),
        "avg_turnover_cv_20d": _avg([row.get("liq_turnover_cv_20d") for row in rows]),
        "avg_turnover_ratio_5d_to_20d": _avg([row.get("liq_turnover_ratio_5d_to_20d") for row in rows]),
        "avg_latest_turnover_surprise_vs20d": _avg([row.get("liq_latest_turnover_surprise_vs20d") for row in rows]),
        "avg_market_advance_decline_ratio": _avg([row.get("market_advance_decline_ratio") for row in rows]),
        "symbol_concentration": _concentration_summary(rows, "symbol"),
        "month_concentration": _concentration_summary(rows, "month_key"),
        "sector_concentration": _concentration_summary(rows, "sector_name"),
        "sample_rows": [
            {
                "session_date": row["session_date"],
                "symbol": row["symbol"],
                "sector_name": row["sector_name"],
                "liq_gap_over_2pct_share_20d": row.get("liq_gap_over_2pct_share_20d"),
                "liq_turnover_cv_20d": row.get("liq_turnover_cv_20d"),
                "liq_turnover_ratio_5d_to_20d": row.get("liq_turnover_ratio_5d_to_20d"),
                "liq_latest_turnover_surprise_vs20d": row.get("liq_latest_turnover_surprise_vs20d"),
                "market_advance_decline_ratio": row.get("market_advance_decline_ratio"),
                "executable_entry_label": row.get("executable_entry_label"),
                "net_return_pct": row.get("net_return_pct"),
            }
            for row in rows[:12]
        ],
    }


def render_markdown(payload):
    lines = [
        "# Entry Liquidity Execution Context Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- dataset_path: `{payload['dataset_path']}`",
        f"- dataset_row_count: `{payload['dataset_row_count']}`",
        f"- enterable_row_count: `{payload['enterable_row_count']}`",
        "",
        "## Ranker Results",
        "",
    ]
    for row in payload["ranker_rows"]:
        lines.extend([
            f"### `{row['ranker_name']}`",
            f"- candidate_count: `{row['candidate_count']}`",
            f"- positive_rate: `{row['positive_rate']}`",
            f"- negative_rate: `{row['negative_rate']}`",
            f"- avg_gap_over_2pct_share_20d: `{row['avg_gap_over_2pct_share_20d']}`",
            f"- avg_avg_abs_gap_pct_20d: `{row['avg_avg_abs_gap_pct_20d']}`",
            f"- avg_turnover_cv_20d: `{row['avg_turnover_cv_20d']}`",
            f"- avg_turnover_ratio_5d_to_20d: `{row['avg_turnover_ratio_5d_to_20d']}`",
            f"- avg_latest_turnover_surprise_vs20d: `{row['avg_latest_turnover_surprise_vs20d']}`",
            f"- avg_market_advance_decline_ratio: `{row['avg_market_advance_decline_ratio']}`",
            f"- symbol_concentration: `{row['symbol_concentration']}`",
            f"- month_concentration: `{row['month_concentration']}`",
            f"- sector_concentration: `{row['sector_concentration']}`",
            "",
        ])
    return "\n".join(lines) + "\n"


def build_entry_liquidity_execution_context_study(dataset_path):
    dataset = load_json(dataset_path)
    rows = dataset.get("rows") or []
    enterable_rows = [row for row in rows if row.get("entry_executed")]

    ranker_rows = []
    for ranker in RANKER_SPECS:
        selected_rows = _select_rows(enterable_rows, ranker)
        summary = _summary_for_rows(selected_rows)
        ranker_rows.append({
            "ranker_name": ranker["name"],
            "group_keys": ranker["group_keys"],
            "filters": ranker["filters"],
            "sort_keys": ranker["sort_keys"],
            **summary,
        })

    ranker_rows.sort(
        key=lambda item: (
            item["positive_rate"] or -1,
            -1 * (item["negative_rate"] if item["negative_rate"] is not None else 1),
            -item["candidate_count"],
        ),
        reverse=True,
    )

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "dataset_row_count": len(rows),
        "enterable_row_count": len(enterable_rows),
        "ranker_rows": ranker_rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_liquidity_execution_context_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_liquidity_execution_context_study_v1.json",
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main(argv=None):
    argv = argv or sys.argv[1:]
    dataset_path = argv[0] if argv else DEFAULT_DATASET_PATH
    payload, latest_json_path, latest_md_path = build_entry_liquidity_execution_context_study(dataset_path)
    print(json.dumps({
        "dataset_row_count": payload["dataset_row_count"],
        "enterable_row_count": payload["enterable_row_count"],
        "best_ranker": (payload["ranker_rows"][0] or {}).get("ranker_name") if payload["ranker_rows"] else None,
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
