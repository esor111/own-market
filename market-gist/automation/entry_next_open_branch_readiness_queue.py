"""
Rank repeated positive slices inside the next-open enterable universe.

This is the entry-track version of the old buy-side readiness queue. It does
not open a branch by itself. It answers:
- which next-open positive slice is the best candidate for deeper entry research
- which slices are still too month-locked or symbol-concentrated to trust

Usage:
    python entry_next_open_branch_readiness_queue.py
    python entry_next_open_branch_readiness_queue.py DATASET_JSON_PATH
"""
import json
import math
import os
import sys
from datetime import datetime

from config import VALIDATION_DIR
from entry_next_open_slice_monitor import DEFAULT_DATASET_PATH, _slice_rows, load_json


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
ENTRY_POSITIVE_SLICE_COUNT_MIN = 5
ENTRY_POSITIVE_SLICE_RATE_MIN = 0.50
ENTRY_POSITIVE_SLICE_MONTH_MIN = 2


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _top_share(pairs, total_count):
    if not pairs or not total_count:
        return None
    return round((pairs[0][1] or 0) / total_count, 4)


def _additional_clean_successes_needed(row):
    success_count = row.get("positive_count") or 0
    count = row.get("count") or 0
    count_gap = max(0, ENTRY_POSITIVE_SLICE_COUNT_MIN - success_count)
    if (
        success_count >= ENTRY_POSITIVE_SLICE_COUNT_MIN
        and (row.get("positive_rate") or 0) >= ENTRY_POSITIVE_SLICE_RATE_MIN
    ):
        return 0
    rate_gap = max(
        0,
        math.ceil(
            (
                ENTRY_POSITIVE_SLICE_RATE_MIN * count
                - success_count
            ) / (1 - ENTRY_POSITIVE_SLICE_RATE_MIN)
        ),
    )
    return max(count_gap, rate_gap)


def _quality_risks(row):
    risks = []
    count = row.get("count") or 0
    symbol_pairs = row.get("symbols") or []
    month_pairs = row.get("months") or []
    symbol_share = _top_share(symbol_pairs, count)
    month_share = _top_share(month_pairs, count)
    negative_rate = row.get("negative_rate") or 0

    if count < 8:
        risks.append("thin_sample")
    if len(symbol_pairs) < 2:
        risks.append("single_symbol")
    if len(month_pairs) < ENTRY_POSITIVE_SLICE_MONTH_MIN:
        risks.append("single_month")
    if symbol_share is not None and symbol_share > 0.6:
        risks.append("symbol_concentration")
    if month_share is not None and month_share > 0.5:
        risks.append("month_concentration")
    if (row.get("positive_rate") or 0) < ENTRY_POSITIVE_SLICE_RATE_MIN:
        risks.append("below_positive_rate_gate")
    if negative_rate >= 0.3:
        risks.append("material_negative_leakage")
    return risks


def _readiness_bucket(row):
    positive_count = row.get("positive_count") or 0
    positive_rate = row.get("positive_rate") or 0
    month_count = len(row.get("months") or [])

    if (
        positive_count >= ENTRY_POSITIVE_SLICE_COUNT_MIN
        and positive_rate >= ENTRY_POSITIVE_SLICE_RATE_MIN
        and month_count >= ENTRY_POSITIVE_SLICE_MONTH_MIN
    ):
        return "gate_ready_multi_month"
    if (
        positive_count >= ENTRY_POSITIVE_SLICE_COUNT_MIN
        and positive_rate >= ENTRY_POSITIVE_SLICE_RATE_MIN
    ):
        return "gate_ready_but_month_locked"
    needed = row.get("additional_clean_successes_needed") or 0
    if needed <= 2 and month_count >= ENTRY_POSITIVE_SLICE_MONTH_MIN:
        return "near_gate"
    if needed <= 2:
        return "near_gate_but_month_locked"
    return "watch_only_candidate"


def _quality_status(row):
    risks = row.get("quality_risks") or []
    if not risks:
        return "clean_candidate"
    if row.get("readiness_bucket") == "gate_ready_multi_month":
        return "gate_ready_but_guarded"
    return "guarded_candidate"


def _render_markdown(payload):
    lines = [
        "# Entry Next-Open Branch Readiness Queue",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- dataset_path: `{payload['dataset_path']}`",
        f"- enterable_count: `{payload['enterable_count']}`",
        f"- positive_count_gate: `{payload['positive_count_gate']}`",
        f"- positive_rate_gate: `{payload['positive_rate_gate']}`",
        f"- month_count_gate: `{payload['month_count_gate']}`",
        "",
        "## Queue",
        "",
    ]
    for row in payload.get("queue_rows") or []:
        lines.append(
            f"- `{row['slice']}`: readiness `{row['readiness_bucket']}`, quality `{row['quality_status']}`, "
            f"positive `{row['positive_count']}`, negative `{row['negative_count']}`, positive_rate `{row['positive_rate']}`, "
            f"unique_symbols `{row['unique_symbol_count']}`, unique_months `{row['unique_month_count']}`, "
            f"additional_clean_successes_needed `{row['additional_clean_successes_needed']}`, "
            f"top_symbol_share `{row['top_symbol_share']}`, top_month_share `{row['top_month_share']}`, "
            f"quality_risks `{row['quality_risks']}`, symbols `{row['symbols']}`, months `{row['months']}`"
        )

    lines.extend([
        "",
        "## Current Decision",
        "",
        "- keep `Risk Engine v1` frozen",
        "- do not open an entry branch from this queue alone",
        "- use this queue to decide which repeated next-open positive slice deserves the next focused study",
    ])
    return "\n".join(lines) + "\n"


def build_entry_next_open_branch_readiness_queue(dataset_path):
    dataset = load_json(dataset_path)
    rows = dataset.get("rows") or []
    enterable_rows = [row for row in rows if row.get("entry_executed")]
    positive_rows, _ = _slice_rows(enterable_rows)

    queue_rows = []
    for row in positive_rows:
        enriched = dict(row)
        enriched["unique_symbol_count"] = len(row.get("symbols") or [])
        enriched["unique_month_count"] = len(row.get("months") or [])
        enriched["top_symbol_share"] = _top_share(row.get("symbols") or [], row.get("count") or 0)
        enriched["top_month_share"] = _top_share(row.get("months") or [], row.get("count") or 0)
        enriched["additional_clean_successes_needed"] = _additional_clean_successes_needed(row)
        enriched["quality_risks"] = _quality_risks(enriched)
        enriched["readiness_bucket"] = _readiness_bucket(enriched)
        enriched["quality_status"] = _quality_status(enriched)
        queue_rows.append(enriched)

    readiness_rank = {
        "gate_ready_multi_month": 0,
        "gate_ready_but_month_locked": 1,
        "near_gate": 2,
        "near_gate_but_month_locked": 3,
        "watch_only_candidate": 4,
    }
    queue_rows.sort(
        key=lambda item: (
            readiness_rank.get(item["readiness_bucket"], 99),
            item["additional_clean_successes_needed"],
            -(item.get("positive_rate") or 0),
            -(item.get("positive_count") or 0),
            item.get("top_symbol_share") or 0,
        )
    )

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "enterable_count": len(enterable_rows),
        "positive_count_gate": ENTRY_POSITIVE_SLICE_COUNT_MIN,
        "positive_rate_gate": ENTRY_POSITIVE_SLICE_RATE_MIN,
        "month_count_gate": ENTRY_POSITIVE_SLICE_MONTH_MIN,
        "queue_rows": queue_rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_branch_readiness_queue_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_branch_readiness_queue_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_next_open_branch_readiness_queue(dataset_path)
    top_row = (payload.get("queue_rows") or [{}])[0]
    print(json.dumps({
        "queue_size": len(payload.get("queue_rows") or []),
        "top_slice": top_row.get("slice"),
        "top_slice_readiness": top_row.get("readiness_bucket"),
        "top_slice_quality": top_row.get("quality_status"),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
