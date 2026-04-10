"""
Study sector-relative and session-relative entry features on the executable-entry dataset.

This is the first baseline family that adds new information beyond absolute
feature ordering: relative ranks inside the day and inside the sector.

Usage:
    python entry_relative_feature_study.py
    python entry_relative_feature_study.py DATASET_JSON_PATH
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


RELATIVE_FEATURES = [
    "score",
    "calibrated_confidence_pct",
    "return_5d_pct",
    "return_20d_pct",
    "volume_ratio_5d",
    "close_position_20d",
]


RANKER_SPECS = [
    {
        "name": "sector_return_20d_rank_top1_global",
        "group_keys": ["session_date"],
        "sort_keys": [("sector_return_20d_pct_rank_pct", True), ("basket_return_20d_pct_rank_pct", True)],
        "top_n": 1,
    },
    {
        "name": "basket_return_20d_rank_top1_global",
        "group_keys": ["session_date"],
        "sort_keys": [("basket_return_20d_pct_rank_pct", True), ("sector_return_20d_pct_rank_pct", True)],
        "top_n": 1,
    },
    {
        "name": "sector_composite_rank_top1_global",
        "group_keys": ["session_date"],
        "sort_keys": [("sector_leadership_composite", True), ("basket_leadership_composite", True)],
        "top_n": 1,
    },
    {
        "name": "basket_composite_rank_top1_global",
        "group_keys": ["session_date"],
        "sort_keys": [("basket_leadership_composite", True), ("sector_leadership_composite", True)],
        "top_n": 1,
    },
    {
        "name": "dual_composite_rank_top1_global",
        "group_keys": ["session_date"],
        "sort_keys": [("dual_leadership_composite", True), ("sector_return_20d_pct_rank_pct", True)],
        "top_n": 1,
    },
    {
        "name": "dual_composite_rank_top1_by_sector",
        "group_keys": ["session_date", "sector_name"],
        "sort_keys": [("dual_leadership_composite", True), ("sector_return_20d_pct_rank_pct", True)],
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


def _rank_percentiles(rows, feature_name):
    valid = [row for row in rows if isinstance(row.get(feature_name), (int, float))]
    total = len(valid)
    if not total:
        return {}
    ranked = sorted(valid, key=lambda item: (-(item.get(feature_name) or 0), str(item.get("symbol") or "")))
    percentiles = {}
    for index, row in enumerate(ranked, start=1):
        if total == 1:
            percentile = 1.0
        else:
            percentile = round((total - index) / (total - 1), 4)
        percentiles[id(row)] = percentile
    return percentiles


def _enrich_relative_features(rows):
    session_groups = defaultdict(list)
    sector_groups = defaultdict(list)
    for row in rows:
        session_groups[row["session_date"]].append(row)
        sector_groups[(row["session_date"], row["sector_name"])].append(row)

    for feature_name in RELATIVE_FEATURES:
        basket_key = f"basket_{feature_name}_rank_pct"
        sector_key = f"sector_{feature_name}_rank_pct"
        for _, items in session_groups.items():
            for row_id, percentile in _rank_percentiles(items, feature_name).items():
                for row in items:
                    if id(row) == row_id:
                        row[basket_key] = percentile
        for _, items in sector_groups.items():
            for row_id, percentile in _rank_percentiles(items, feature_name).items():
                for row in items:
                    if id(row) == row_id:
                        row[sector_key] = percentile

    for row in rows:
        basket_values = [row.get(f"basket_{feature_name}_rank_pct") for feature_name in RELATIVE_FEATURES]
        basket_values = [value for value in basket_values if isinstance(value, (int, float))]
        sector_values = [row.get(f"sector_{feature_name}_rank_pct") for feature_name in RELATIVE_FEATURES]
        sector_values = [value for value in sector_values if isinstance(value, (int, float))]
        row["basket_leadership_composite"] = round(sum(basket_values) / len(basket_values), 4) if basket_values else None
        row["sector_leadership_composite"] = round(sum(sector_values) / len(sector_values), 4) if sector_values else None
        dual_values = [value for value in [row["basket_leadership_composite"], row["sector_leadership_composite"]] if isinstance(value, (int, float))]
        row["dual_leadership_composite"] = round(sum(dual_values) / len(dual_values), 4) if dual_values else None
    return rows


def _select_rows(rows, ranker):
    grouped = defaultdict(list)
    for row in rows:
        grouped[_group_key(row, ranker["group_keys"])].append(row)
    selected = []
    for _, items in grouped.items():
        ranked = sorted(items, key=lambda item: _sort_tuple(item, ranker["sort_keys"]))
        selected.extend(ranked[: ranker["top_n"]])
    selected.sort(key=lambda item: (item["session_date"], item["symbol"], item["sector_name"]))
    return selected


def _summary_for_rows(rows):
    label_counts = Counter(row["executable_entry_label"] for row in rows)
    family_counts = Counter(row["entry_outcome_family"] for row in rows)
    return {
        "candidate_count": len(rows),
        "executable_entry_label_counts": dict(label_counts),
        "entry_outcome_family_counts": dict(family_counts),
        "strict_positive_count": family_counts.get("strict_positive", 0),
        "strict_negative_count": family_counts.get("strict_negative", 0),
        "nontradable_favorable_count": family_counts.get("nontradable_favorable", 0),
        "strict_positive_rate": _rate(family_counts.get("strict_positive", 0), len(rows)),
        "strict_negative_rate": _rate(family_counts.get("strict_negative", 0), len(rows)),
        "nontradable_favorable_rate": _rate(family_counts.get("nontradable_favorable", 0), len(rows)),
        "symbol_concentration": _concentration_summary(rows, "symbol"),
        "month_concentration": _concentration_summary(rows, "month_key"),
        "sector_concentration": _concentration_summary(rows, "sector_name"),
        "sample_rows": [
            {
                "session_date": row["session_date"],
                "symbol": row["symbol"],
                "sector_name": row["sector_name"],
                "calendar_phase": row["calendar_phase"],
                "action": row["action"],
                "executable_entry_label": row["executable_entry_label"],
                "basket_return_20d_pct_rank_pct": row.get("basket_return_20d_pct_rank_pct"),
                "sector_return_20d_pct_rank_pct": row.get("sector_return_20d_pct_rank_pct"),
                "basket_leadership_composite": row.get("basket_leadership_composite"),
                "sector_leadership_composite": row.get("sector_leadership_composite"),
                "dual_leadership_composite": row.get("dual_leadership_composite"),
                "next_open_gap_pct": row.get("next_open_gap_pct"),
                "net_return_pct": row.get("net_return_pct"),
            }
            for row in rows[:12]
        ],
    }


def render_markdown(payload):
    lines = [
        "# Entry Relative Feature Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- dataset_path: `{payload['dataset_path']}`",
        f"- dataset_row_count: `{payload['dataset_row_count']}`",
        "",
        "## Ranker Results",
        "",
    ]
    for row in payload["ranker_rows"]:
        lines.extend([
            f"### `{row['ranker_name']}`",
            f"- candidate_count: `{row['candidate_count']}`",
            f"- strict_positive_rate: `{row['strict_positive_rate']}`",
            f"- strict_negative_rate: `{row['strict_negative_rate']}`",
            f"- nontradable_favorable_rate: `{row['nontradable_favorable_rate']}`",
            f"- executable_entry_label_counts: `{row['executable_entry_label_counts']}`",
            f"- symbol_concentration: `{row['symbol_concentration']}`",
            f"- month_concentration: `{row['month_concentration']}`",
            f"- sector_concentration: `{row['sector_concentration']}`",
            "",
        ])
    return "\n".join(lines) + "\n"


def build_entry_relative_feature_study(dataset_path):
    dataset = load_json(dataset_path)
    rows = dataset.get("rows") or []
    rows = _enrich_relative_features(rows)
    ranker_rows = []
    for ranker in RANKER_SPECS:
        selected_rows = _select_rows(rows, ranker)
        summary = _summary_for_rows(selected_rows)
        ranker_rows.append({
            "ranker_name": ranker["name"],
            "group_keys": ranker["group_keys"],
            "sort_keys": ranker["sort_keys"],
            **summary,
        })

    ranker_rows.sort(
        key=lambda item: (
            item["strict_positive_rate"] or -1,
            -1 * (item["strict_negative_rate"] if item["strict_negative_rate"] is not None else 1),
            -1 * (item["nontradable_favorable_rate"] if item["nontradable_favorable_rate"] is not None else 1),
            -item["candidate_count"],
        ),
        reverse=True,
    )

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "dataset_row_count": len(rows),
        "ranker_rows": ranker_rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_relative_feature_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_relative_feature_study_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_relative_feature_study(dataset_path)
    print(json.dumps({
        "best_ranker": payload["ranker_rows"][0]["ranker_name"] if payload["ranker_rows"] else None,
        "best_ranker_strict_positive_rate": payload["ranker_rows"][0]["strict_positive_rate"] if payload["ranker_rows"] else None,
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
