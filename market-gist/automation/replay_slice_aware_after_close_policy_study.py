"""
Research-only slice-aware study for after-close next-open entry policy candidates.

Usage:
    python replay_slice_aware_after_close_policy_study.py
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import VALIDATION_DIR
from replay_after_close_entry_policy_study import (
    LATEST_TRADABILITY_STUDY_PATH,
    RR_THRESHOLDS,
    TARGET_DISTANCE_THRESHOLDS,
    _candidate_sort_key,
    _evaluate_policy,
)


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")


SLICE_DEFINITIONS = [
    {
        "slice_name": "commercial_banks",
        "description": "all commercial-bank actionables",
        "predicate": lambda record: record.get("sector_name") == "COMMERCIAL BANKS",
    },
    {
        "slice_name": "hydropower",
        "description": "all hydropower actionables",
        "predicate": lambda record: record.get("sector_name") == "HYDROPOWER",
    },
    {
        "slice_name": "uptrend",
        "description": "actionables with uptrend label",
        "predicate": lambda record: record.get("trend_label") == "uptrend",
    },
    {
        "slice_name": "strong_liquidity",
        "description": "actionables with strong liquidity label",
        "predicate": lambda record: record.get("liquidity_label") == "strong",
    },
    {
        "slice_name": "return20_ge_5",
        "description": "actionables with return_20d_pct >= 5",
        "predicate": lambda record: record.get("return_20d_pct") is not None and record["return_20d_pct"] >= 5,
    },
    {
        "slice_name": "volume_ratio_ge_1_4",
        "description": "actionables with volume_ratio_5d >= 1.4",
        "predicate": lambda record: record.get("volume_ratio_5d") is not None and record["volume_ratio_5d"] >= 1.4,
    },
    {
        "slice_name": "volume_ratio_ge_1_6",
        "description": "actionables with volume_ratio_5d >= 1.6",
        "predicate": lambda record: record.get("volume_ratio_5d") is not None and record["volume_ratio_5d"] >= 1.6,
    },
    {
        "slice_name": "banks_volume_ratio_ge_1_4",
        "description": "commercial-bank actionables with volume_ratio_5d >= 1.4",
        "predicate": lambda record: (
            record.get("sector_name") == "COMMERCIAL BANKS"
            and record.get("volume_ratio_5d") is not None
            and record["volume_ratio_5d"] >= 1.4
        ),
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


def _split_name(record):
    month = str(record.get("session_date") or "")[:7]
    return "discovery" if month <= "2025-06" else "validation"


def _label_counts(records):
    return dict(Counter(record.get("next_open_label") for record in records))


def _good_call_counts(records):
    return dict(Counter(record.get("next_open_label") for record in records if record.get("comparison_verdict") == "good_call"))


def _assess_stability(validated_row):
    val_bal = validated_row.get("validation_balanced_accuracy")
    val_keep = validated_row.get("validation_good_call_tradable_positive_recall")
    val_block = validated_row.get("validation_good_call_gap_above_block_rate")
    if val_bal is None:
        return "insufficient_validation"
    if val_bal >= 0.58 and (val_keep or 0) >= 0.45 and (val_block or 0) >= 0.7:
        return "promising_but_not_promoted"
    if val_bal >= 0.52 and ((val_keep or 0) >= 0.35 or (val_block or 0) >= 0.75):
        return "mixed_or_unstable"
    return "weak_or_drifted"


def _render_markdown(summary):
    lines = [
        "# Replay Slice-Aware After-Close Policy Study",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- source_path: `{summary['source_path']}`",
        "",
    ]
    for slice_row in summary.get("slices", []):
        lines.extend([
            f"## Slice `{slice_row['slice_name']}`",
            "",
            f"- description: {slice_row['description']}",
            f"- discovery_count: `{slice_row['discovery_count']}`",
            f"- validation_count: `{slice_row['validation_count']}`",
            f"- discovery_labels: `{slice_row['discovery_label_counts']}`",
            f"- validation_labels: `{slice_row['validation_label_counts']}`",
            f"- discovery_good_call_labels: `{slice_row['discovery_good_call_label_counts']}`",
            f"- validation_good_call_labels: `{slice_row['validation_good_call_label_counts']}`",
        ])
        top = slice_row.get("best_validated_candidate")
        if top:
            lines.extend([
                f"- best_candidate: `target_distance >= {top['target_distance_min']}` and `rr >= {top['rr_min']}`",
                f"- discovery_bal_acc: `{top['discovery_balanced_accuracy']}`",
                f"- validation_bal_acc: `{top['validation_balanced_accuracy']}`",
                f"- validation_allow_precision: `{top['validation_allow_precision']}`",
                f"- validation_gap_block: `{top['validation_good_call_gap_above_block_rate']}`",
                f"- validation_tradable_keep: `{top['validation_good_call_tradable_positive_recall']}`",
                f"- stability_label: `{top['stability_label']}`",
            ])
        else:
            lines.append("- best_candidate: `none`")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_slice_aware_after_close_policy_study():
    payload = load_json(LATEST_TRADABILITY_STUDY_PATH)
    records = payload.get("records") or []
    summary_rows = []

    for definition in SLICE_DEFINITIONS:
        slice_records = [record for record in records if definition["predicate"](record)]
        discovery_records = [record for record in slice_records if _split_name(record) == "discovery"]
        validation_records = [record for record in slice_records if _split_name(record) == "validation"]

        discovery_rows = []
        if discovery_records and validation_records:
            for target_distance_min in TARGET_DISTANCE_THRESHOLDS:
                for rr_min in RR_THRESHOLDS:
                    discovery_rows.append(_evaluate_policy(discovery_records, target_distance_min, rr_min))
            discovery_rows.sort(key=_candidate_sort_key, reverse=True)

        validated_rows = []
        for row in discovery_rows[:12]:
            validation_row = _evaluate_policy(validation_records, row["target_distance_min"], row["rr_min"])
            validated_rows.append({
                "target_distance_min": row["target_distance_min"],
                "rr_min": row["rr_min"],
                "discovery_balanced_accuracy": row["balanced_accuracy"],
                "discovery_allow_precision": row["allow_precision"],
                "discovery_good_call_gap_above_block_rate": row["good_call_gap_above_block_rate"],
                "discovery_good_call_tradable_positive_recall": row["good_call_tradable_positive_recall"],
                "validation_balanced_accuracy": validation_row["balanced_accuracy"],
                "validation_allow_precision": validation_row["allow_precision"],
                "validation_nonpositive_block_rate": validation_row["nonpositive_block_rate"],
                "validation_tradable_positive_recall": validation_row["tradable_positive_recall"],
                "validation_good_call_gap_above_block_rate": validation_row["good_call_gap_above_block_rate"],
                "validation_good_call_tradable_positive_recall": validation_row["good_call_tradable_positive_recall"],
            })

        validated_rows.sort(
            key=lambda row: (
                row.get("validation_balanced_accuracy") if row.get("validation_balanced_accuracy") is not None else -1,
                row.get("validation_allow_precision") if row.get("validation_allow_precision") is not None else -1,
                row.get("validation_good_call_gap_above_block_rate") if row.get("validation_good_call_gap_above_block_rate") is not None else -1,
                row.get("validation_good_call_tradable_positive_recall") if row.get("validation_good_call_tradable_positive_recall") is not None else -1,
            ),
            reverse=True,
        )

        best = validated_rows[0] if validated_rows else None
        if best:
            best = {**best, "stability_label": _assess_stability(best)}

        summary_rows.append({
            "slice_name": definition["slice_name"],
            "description": definition["description"],
            "discovery_count": len(discovery_records),
            "validation_count": len(validation_records),
            "discovery_label_counts": _label_counts(discovery_records),
            "validation_label_counts": _label_counts(validation_records),
            "discovery_good_call_label_counts": _good_call_counts(discovery_records),
            "validation_good_call_label_counts": _good_call_counts(validation_records),
            "top_discovery_candidates": discovery_rows[:12],
            "validated_top_candidates": validated_rows[:12],
            "best_validated_candidate": best,
        })

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_path": LATEST_TRADABILITY_STUDY_PATH,
        "slices": summary_rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__replay_slice_aware_after_close_policy_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__replay_slice_aware_after_close_policy_study_v1.json",
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")

    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) > 1:
        print("This study takes no positional arguments.")
        sys.exit(1)

    summary, latest_json_path, latest_md_path = build_slice_aware_after_close_policy_study()
    print(json.dumps({
        "slice_count": len(summary["slices"]),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
