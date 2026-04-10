"""
Monitor repeated positive and negative slices inside the next-open enterable universe.

This helps answer:
- after shifting the decision point to the next open, where does the positive edge actually live?
- are there repeated slice-level pockets worth deeper entry research?

Usage:
    python entry_next_open_slice_monitor.py
    python entry_next_open_slice_monitor.py DATASET_JSON_PATH
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


def _bucket_key(row):
    return " | ".join([
        row.get("sector_name") or "UNKNOWN",
        row.get("calendar_phase") or "no_named_phase",
        row.get("event_state") or "unknown",
        row.get("confidence_label") or "unknown",
        row.get("action") or "unknown",
    ])


def _slice_rows(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[_bucket_key(row)].append(row)

    positive_rows = []
    negative_rows = []
    for slice_name, items in grouped.items():
        positive_count = sum(1 for item in items if item["executable_entry_label"] == "tradable_positive_after_costs")
        negative_count = sum(1 for item in items if item["executable_entry_label"] == "tradable_negative_after_costs")
        summary = {
            "slice": slice_name,
            "count": len(items),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "positive_rate": _rate(positive_count, len(items)),
            "negative_rate": _rate(negative_count, len(items)),
            "symbols": Counter(item["symbol"] for item in items).most_common(5),
            "months": Counter(item["month_key"] for item in items).most_common(5),
            "leadership_labels": Counter(item.get("leadership_label") or "UNKNOWN" for item in items).most_common(5),
        }
        if positive_count:
            positive_rows.append(summary)
        if negative_count:
            negative_rows.append(summary)

    positive_rows.sort(
        key=lambda item: (item["positive_rate"] or -1, item["positive_count"], -item["negative_count"], item["count"]),
        reverse=True,
    )
    negative_rows.sort(
        key=lambda item: (item["negative_rate"] or -1, item["negative_count"], -item["positive_count"], item["count"]),
        reverse=True,
    )
    return positive_rows, negative_rows


def render_markdown(payload):
    lines = [
        "# Entry Next-Open Slice Monitor",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- dataset_path: `{payload['dataset_path']}`",
        f"- enterable_count: `{payload['enterable_count']}`",
        "",
        "## Top Positive Slices",
        "",
    ]
    for row in payload["top_positive_slices"]:
        lines.append(
            f"- `{row['slice']}`: count `{row['count']}`, positive `{row['positive_count']}`, "
            f"negative `{row['negative_count']}`, positive_rate `{row['positive_rate']}`, "
            f"symbols `{row['symbols']}`, months `{row['months']}`, leadership `{row['leadership_labels']}`"
        )

    lines.extend(["", "## Top Negative Slices", ""])
    for row in payload["top_negative_slices"]:
        lines.append(
            f"- `{row['slice']}`: count `{row['count']}`, positive `{row['positive_count']}`, "
            f"negative `{row['negative_count']}`, negative_rate `{row['negative_rate']}`, "
            f"symbols `{row['symbols']}`, months `{row['months']}`, leadership `{row['leadership_labels']}`"
        )

    return "\n".join(lines) + "\n"


def build_entry_next_open_slice_monitor(dataset_path):
    dataset = load_json(dataset_path)
    rows = dataset.get("rows") or []
    enterable_rows = [row for row in rows if row.get("entry_executed")]
    positive_rows, negative_rows = _slice_rows(enterable_rows)
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "enterable_count": len(enterable_rows),
        "top_positive_slices": positive_rows[:15],
        "top_negative_slices": negative_rows[:15],
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_next_open_slice_monitor_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_next_open_slice_monitor_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_next_open_slice_monitor(dataset_path)
    print(json.dumps({
        "enterable_count": payload["enterable_count"],
        "top_positive_slice": payload["top_positive_slices"][0]["slice"] if payload["top_positive_slices"] else None,
        "top_negative_slice": payload["top_negative_slices"][0]["slice"] if payload["top_negative_slices"] else None,
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
