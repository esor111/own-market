"""
Research-only study of after-close label drift in the strongest slices.

Usage:
    python replay_after_close_label_drift_study.py
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime
from statistics import mean

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
LATEST_TRADABILITY_STUDY_PATH = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__replay_next_open_tradability_study_v1.json",
)


SLICE_DEFINITIONS = [
    {
        "slice_name": "commercial_banks",
        "description": "all commercial-bank actionables",
        "predicate": lambda record: record.get("sector_name") == "COMMERCIAL BANKS",
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

FEATURES = [
    "target_distance_close_pct",
    "risk_reward_ratio",
    "return_1d_pct",
    "return_5d_pct",
    "return_20d_pct",
    "close_position_20d",
    "volume_ratio_5d",
    "next_open_gap_pct",
]
LABELS = [
    "gap_above_target",
    "gap_below_stop",
    "tradable_negative_gross",
    "tradable_positive_gross",
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


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _mean(records, field):
    values = [record.get(field) for record in records if record.get(field) is not None]
    return round(mean(values), 4) if values else None


def _label_feature_summary(records):
    rows = {}
    for label in LABELS:
        subset = [record for record in records if record.get("next_open_label") == label]
        rows[label] = {
            "count": len(subset),
            "feature_means": {
                feature: _mean(subset, feature)
                for feature in FEATURES
            },
            "top_symbols": Counter(record.get("symbol") for record in subset).most_common(5),
        }
    return rows


def _overall_feature_means(records):
    return {feature: _mean(records, feature) for feature in FEATURES}


def _feature_drift(discovery_records, validation_records):
    rows = []
    for feature in FEATURES:
        discovery_mean = _mean(discovery_records, feature)
        validation_mean = _mean(validation_records, feature)
        if discovery_mean is None or validation_mean is None:
            continue
        rows.append({
            "feature_name": feature,
            "discovery_mean": discovery_mean,
            "validation_mean": validation_mean,
            "delta": round(validation_mean - discovery_mean, 4),
        })
    rows.sort(key=lambda row: abs(row["delta"]), reverse=True)
    return rows


def _failure_mix(records):
    total = len(records)
    counts = Counter(record.get("next_open_label") for record in records)
    return {
        "counts": dict(counts),
        "gap_above_target_rate": _rate(counts.get("gap_above_target", 0), total),
        "gap_below_stop_rate": _rate(counts.get("gap_below_stop", 0), total),
        "tradable_negative_gross_rate": _rate(counts.get("tradable_negative_gross", 0), total),
        "tradable_positive_gross_rate": _rate(counts.get("tradable_positive_gross", 0), total),
    }


def _dominant_label(records):
    if not records:
        return None
    return Counter(record.get("next_open_label") for record in records).most_common(1)[0][0]


def _render_markdown(summary):
    lines = [
        "# Replay After-Close Label Drift Study",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- source_path: `{summary['source_path']}`",
        "",
    ]
    for row in summary.get("slices", []):
        lines.extend([
            f"## Slice `{row['slice_name']}`",
            "",
            f"- description: {row['description']}",
            f"- discovery_count: `{row['discovery_count']}`",
            f"- validation_count: `{row['validation_count']}`",
            f"- discovery_dominant_label: `{row['discovery_dominant_label']}`",
            f"- validation_dominant_label: `{row['validation_dominant_label']}`",
            f"- discovery_failure_mix: `{row['discovery_failure_mix']}`",
            f"- validation_failure_mix: `{row['validation_failure_mix']}`",
            f"- discovery_months: `{row['discovery_months']}`",
            f"- validation_months: `{row['validation_months']}`",
            f"- discovery_symbols: `{row['discovery_symbols']}`",
            f"- validation_symbols: `{row['validation_symbols']}`",
            "",
            "### Strongest Feature Drift",
            "",
        ])
        for feature in row.get("feature_drift", [])[:8]:
            lines.append(
                f"- `{feature['feature_name']}`: discovery `{feature['discovery_mean']}`, "
                f"validation `{feature['validation_mean']}`, delta `{feature['delta']}`"
            )
        lines.extend(["", "### Discovery Label Means", ""])
        for label, payload in row.get("discovery_label_features", {}).items():
            lines.append(f"- `{label}`: count `{payload['count']}`, means `{payload['feature_means']}`")
        lines.extend(["", "### Validation Label Means", ""])
        for label, payload in row.get("validation_label_features", {}).items():
            lines.append(f"- `{label}`: count `{payload['count']}`, means `{payload['feature_means']}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_after_close_label_drift_study():
    payload = load_json(LATEST_TRADABILITY_STUDY_PATH)
    records = payload.get("records") or []
    summary_rows = []

    for definition in SLICE_DEFINITIONS:
        slice_records = [record for record in records if definition["predicate"](record)]
        discovery_records = [record for record in slice_records if _split_name(record) == "discovery"]
        validation_records = [record for record in slice_records if _split_name(record) == "validation"]

        summary_rows.append({
            "slice_name": definition["slice_name"],
            "description": definition["description"],
            "discovery_count": len(discovery_records),
            "validation_count": len(validation_records),
            "discovery_dominant_label": _dominant_label(discovery_records),
            "validation_dominant_label": _dominant_label(validation_records),
            "discovery_failure_mix": _failure_mix(discovery_records),
            "validation_failure_mix": _failure_mix(validation_records),
            "discovery_months": dict(Counter(str(record.get("session_date") or "")[:7] for record in discovery_records)),
            "validation_months": dict(Counter(str(record.get("session_date") or "")[:7] for record in validation_records)),
            "discovery_symbols": Counter(record.get("symbol") for record in discovery_records).most_common(10),
            "validation_symbols": Counter(record.get("symbol") for record in validation_records).most_common(10),
            "discovery_feature_means": _overall_feature_means(discovery_records),
            "validation_feature_means": _overall_feature_means(validation_records),
            "feature_drift": _feature_drift(discovery_records, validation_records),
            "discovery_label_features": _label_feature_summary(discovery_records),
            "validation_label_features": _label_feature_summary(validation_records),
        })

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_path": LATEST_TRADABILITY_STUDY_PATH,
        "slices": summary_rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__replay_after_close_label_drift_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__replay_after_close_label_drift_study_v1.json",
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

    summary, latest_json_path, latest_md_path = build_after_close_label_drift_study()
    print(json.dumps({
        "slice_count": len(summary["slices"]),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
