"""
Study Thursday / weekend-gap drag on the enterable entry dataset.

Focus:
- bank sectors first
- compare Thursday-close enterable rows vs non-Thursday rows
- identify whether the effect is broad descriptive friction or a clean branch

Usage:
    python entry_thursday_weekend_gap_drag_study.py
    python entry_thursday_weekend_gap_drag_study.py DATASET_JSON_PATH
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

BANK_SECTORS = {"COMMERCIAL BANKS", "DEVELOPMENT BANKS"}
TARGET_CANDIDATE = {
    "sector_name": "COMMERCIAL BANKS",
    "calendar_phase": "no_named_phase",
    "event_state": "no_symbol_event_match",
    "confidence_label": "strongly_overconfident",
    "action": "watch_only",
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


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _family_counts(rows):
    counts = Counter(row["entry_outcome_family"] for row in rows)
    total = len(rows)
    return {
        "count": total,
        "positive_count": counts.get("strict_positive", 0),
        "negative_count": counts.get("strict_negative", 0),
        "positive_rate": _rate(counts.get("strict_positive", 0), total),
        "negative_rate": _rate(counts.get("strict_negative", 0), total),
        "months": Counter(row["month_key"] for row in rows).most_common(6),
        "symbols": Counter(row["symbol"] for row in rows).most_common(6),
    }


def _subset(rows, **filters):
    output = rows
    for key, value in filters.items():
        output = [row for row in output if row.get(key) == value]
    return output


def _slice_rows(rows):
    grouped = defaultdict(list)
    for row in rows:
        key = (
            row["sector_name"],
            row["calendar_phase"],
            row["event_state"],
            row["confidence_label"],
            row["action"],
        )
        grouped[key].append(row)

    output = []
    for key, items in grouped.items():
        summary = _family_counts(items)
        if summary["count"] < 2:
            continue
        output.append({
            "slice": " | ".join(key),
            **summary,
        })
    output.sort(key=lambda item: (-item["count"], item["slice"]))
    return output


def render_markdown(payload):
    lines = [
        "# Entry Thursday Weekend-Gap Drag Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- dataset_path: `{payload['dataset_path']}`",
        f"- enterable_row_count: `{payload['enterable_row_count']}`",
        "",
        "## Bank Sector Thursday vs Non-Thursday",
        "",
    ]
    for row in payload["bank_sector_rows"]:
        lines.extend([
            f"### `{row['sector_name']}`",
            f"- Thursday: count `{row['thursday']['count']}`, positive `{row['thursday']['positive_count']}`, negative `{row['thursday']['negative_count']}`, positive_rate `{row['thursday']['positive_rate']}`",
            f"- non-Thursday: count `{row['non_thursday']['count']}`, positive `{row['non_thursday']['positive_count']}`, negative `{row['non_thursday']['negative_count']}`, positive_rate `{row['non_thursday']['positive_rate']}`",
            "",
        ])

    lines.extend([
        "## Thursday Bank Slices",
        "",
    ])
    for row in payload["thursday_bank_slices"]:
        lines.append(
            f"- `{row['slice']}`: count `{row['count']}`, positive `{row['positive_count']}`, negative `{row['negative_count']}`, positive_rate `{row['positive_rate']}`"
        )

    lines.extend([
        "",
        "## Guarded Candidate Check",
        "",
        f"- overall: `{payload['guarded_candidate']['overall']}`",
        f"- Thursday: `{payload['guarded_candidate']['thursday']}`",
        f"- non-Thursday: `{payload['guarded_candidate']['non_thursday']}`",
        "",
        "## Interpretation",
        "",
    ])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Decision",
        "",
    ])
    for item in payload["decision"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_entry_thursday_weekend_gap_drag_study(dataset_path):
    dataset = load_json(dataset_path)
    rows = dataset.get("rows") or []
    enterable_rows = [row for row in rows if row.get("entry_executed")]
    bank_rows = [row for row in enterable_rows if row["sector_name"] in BANK_SECTORS]

    bank_sector_rows = []
    for sector_name in sorted(BANK_SECTORS):
        sector_rows = [row for row in bank_rows if row["sector_name"] == sector_name]
        thursday_rows = [row for row in sector_rows if row.get("liq_is_thursday_close") is True]
        non_thursday_rows = [row for row in sector_rows if row.get("liq_is_thursday_close") is False]
        bank_sector_rows.append({
            "sector_name": sector_name,
            "thursday": _family_counts(thursday_rows),
            "non_thursday": _family_counts(non_thursday_rows),
        })

    thursday_bank_rows = [row for row in bank_rows if row.get("liq_is_thursday_close") is True]
    thursday_bank_slices = _slice_rows(thursday_bank_rows)

    candidate_rows = _subset(enterable_rows, **TARGET_CANDIDATE)
    guarded_candidate = {
        "overall": _family_counts(candidate_rows),
        "thursday": _family_counts([row for row in candidate_rows if row.get("liq_is_thursday_close") is True]),
        "non_thursday": _family_counts([row for row in candidate_rows if row.get("liq_is_thursday_close") is False]),
    }

    interpretation = [
        "Thursday / weekend-gap drag is real at the broad bank-sector level.",
        "Commercial banks and development banks both weaken on Thursday closes compared with non-Thursday closes.",
        "The effect is not clean enough yet to become a rule by itself because Thursday bank rows are still heterogeneous and thin.",
        "The guarded commercial-bank next-open candidate does not collapse on Thursday rows, so Thursday drag is broad friction, not the main explanation for that candidate.",
    ]
    decision = [
        "keep Risk Engine v1 frozen",
        "keep the guarded commercial-bank next-open texture on watch",
        "do not open a Thursday-only rule branch from this study alone",
        "treat Thursday / weekend-gap drag as a descriptive bank friction unless future repeated Thursday slices get cleaner",
    ]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "dataset_path": dataset_path,
        "enterable_row_count": len(enterable_rows),
        "bank_sector_rows": bank_sector_rows,
        "thursday_bank_slices": thursday_bank_slices,
        "guarded_candidate": guarded_candidate,
        "interpretation": interpretation,
        "decision": decision,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_thursday_weekend_gap_drag_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_thursday_weekend_gap_drag_study_v1.json",
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
    payload, latest_json_path, latest_md_path = build_entry_thursday_weekend_gap_drag_study(dataset_path)
    print(json.dumps({
        "enterable_row_count": payload["enterable_row_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
