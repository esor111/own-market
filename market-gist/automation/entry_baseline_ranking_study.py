"""
First-pass baseline ranking study for Entry Research v1.

This tests simple candidate generators on the executable-entry dataset before
any complex modeling.

Usage:
    python entry_baseline_ranking_study.py
    python entry_baseline_ranking_study.py DATASET_JSON_PATH
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
        "name": "score_top1_global",
        "group_keys": ["session_date"],
        "sort_keys": [("score", True), ("calibrated_confidence_pct", True), ("raw_confidence", True)],
        "top_n": 1,
    },
    {
        "name": "calibrated_confidence_top1_global",
        "group_keys": ["session_date"],
        "sort_keys": [("calibrated_confidence_pct", True), ("score", True), ("raw_confidence", True)],
        "top_n": 1,
    },
    {
        "name": "return_5d_top1_global",
        "group_keys": ["session_date"],
        "sort_keys": [("return_5d_pct", True), ("score", True), ("calibrated_confidence_pct", True)],
        "top_n": 1,
    },
    {
        "name": "volume_ratio_top1_global",
        "group_keys": ["session_date"],
        "sort_keys": [("volume_ratio_5d", True), ("score", True), ("calibrated_confidence_pct", True)],
        "top_n": 1,
    },
    {
        "name": "score_top1_by_sector",
        "group_keys": ["session_date", "sector_name"],
        "sort_keys": [("score", True), ("calibrated_confidence_pct", True), ("raw_confidence", True)],
        "top_n": 1,
    },
    {
        "name": "calibrated_confidence_top1_by_sector",
        "group_keys": ["session_date", "sector_name"],
        "sort_keys": [("calibrated_confidence_pct", True), ("score", True), ("raw_confidence", True)],
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
                "score": row.get("score"),
                "calibrated_confidence_pct": row.get("calibrated_confidence_pct"),
                "return_5d_pct": row.get("return_5d_pct"),
                "volume_ratio_5d": row.get("volume_ratio_5d"),
                "next_open_gap_pct": row.get("next_open_gap_pct"),
                "net_return_pct": row.get("net_return_pct"),
            }
            for row in rows[:12]
        ],
    }


def render_markdown(payload):
    lines = [
        "# Entry Baseline Ranking Study",
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


def build_entry_baseline_ranking_study(dataset_path):
    dataset = load_json(dataset_path)
    rows = dataset.get("rows") or []
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
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_baseline_ranking_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_baseline_ranking_study_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_baseline_ranking_study(dataset_path)
    print(json.dumps({
        "best_ranker": payload["ranker_rows"][0]["ranker_name"] if payload["ranker_rows"] else None,
        "best_ranker_strict_positive_rate": payload["ranker_rows"][0]["strict_positive_rate"] if payload["ranker_rows"] else None,
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
