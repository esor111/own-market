"""
Measure whether replay-safe macro and calendar context helps explain replay outcomes.

Usage:
    python replay_macro_context_diagnostics.py REPLAY_ID
"""
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from glob import glob

from config import REPLAYS_DIR


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


def _bucket_label(index, bucket_count):
    labels = {0: "low", 1: "mid", 2: "high"}
    if bucket_count == 3:
        return labels.get(index, f"bucket_{index + 1}")
    return f"bucket_{index + 1}"


def _quantile_buckets(values, bucket_count=3):
    ordered = sorted(
        [(float(item["value"]), item["id"]) for item in values if item.get("value") is not None],
        key=lambda pair: pair[0],
    )
    if not ordered:
        return {}, []

    buckets = {}
    boundaries = []
    total = len(ordered)
    for idx, (_, item_id) in enumerate(ordered):
        bucket_index = min(bucket_count - 1, math.floor(idx * bucket_count / total))
        buckets[item_id] = bucket_index

    for boundary_idx in range(1, bucket_count):
        cut_index = math.ceil(total * boundary_idx / bucket_count) - 1
        cut_index = min(max(cut_index, 0), total - 1)
        boundaries.append(round(ordered[cut_index][0], 4))
    return buckets, boundaries


def _summarize_records(records):
    verdict_counts = Counter(item["comparison_verdict"] for item in records)
    actionable = [item for item in records if item["action"] in {"buy", "watch_only"}]
    avoids = [item for item in records if item["action"] == "avoid"]
    return {
        "count": len(records),
        "verdict_counts": dict(verdict_counts),
        "actionable_count": len(actionable),
        "good_call_rate": _rate(sum(1 for item in actionable if item["comparison_verdict"] == "good_call"), len(actionable)),
        "bad_or_mixed_call_rate": _rate(sum(1 for item in actionable if item["comparison_verdict"] in {"bad_call", "mixed_call"}), len(actionable)),
        "avoid_count": len(avoids),
        "missed_opportunity_rate": _rate(sum(1 for item in avoids if item["comparison_verdict"] == "missed_opportunity"), len(avoids)),
        "good_avoid_rate": _rate(sum(1 for item in avoids if item["comparison_verdict"] == "good_avoid"), len(avoids)),
        "top_symbols": Counter(item["symbol"] for item in records).most_common(5),
    }


def _calendar_phase_label(record):
    phase_labels = ((record.get("calendar_flags") or {}).get("phase_labels")) or []
    if not phase_labels:
        return "no_named_phase"
    return "+".join(sorted(str(item) for item in phase_labels))


def _extract_metric_value(record, metric_name):
    snapshot = record.get("latest_available_snapshot") or {}
    metrics = snapshot.get("metrics") or {}
    derived_metrics = snapshot.get("derived_metrics") or {}

    if metric_name in derived_metrics:
        value = derived_metrics.get(metric_name)
        return float(value) if value is not None else None

    metric_payload = metrics.get(metric_name)
    if isinstance(metric_payload, dict):
        value = metric_payload.get("current_value")
    else:
        value = metric_payload
    return float(value) if value is not None else None


def _build_metric_summary(records, metric_name):
    values = []
    for record in records:
        metric_value = _extract_metric_value(record, metric_name)
        values.append({"id": record["record_id"], "value": metric_value})
    distinct_values = sorted({round(item["value"], 8) for item in values if item["value"] is not None})
    if len(distinct_values) < 2:
        single_value_records = [record for record in records if _extract_metric_value(record, metric_name) is not None]
        if not single_value_records:
            return {
                "metric": metric_name,
                "distinct_value_count": 0,
                "bucket_boundaries": [],
                "buckets": [],
            }

        summary = _summarize_records(single_value_records)
        single_value = _extract_metric_value(single_value_records[0], metric_name)
        return {
            "metric": metric_name,
            "distinct_value_count": len(distinct_values),
            "bucket_boundaries": [],
            "buckets": [
                {
                    "bucket": "single_value_context",
                    "count": summary["count"],
                    "value_min": round(single_value, 4) if single_value is not None else None,
                    "value_max": round(single_value, 4) if single_value is not None else None,
                    "actionable_count": summary["actionable_count"],
                    "good_call_rate": summary["good_call_rate"],
                    "bad_or_mixed_call_rate": summary["bad_or_mixed_call_rate"],
                    "avoid_count": summary["avoid_count"],
                    "missed_opportunity_rate": summary["missed_opportunity_rate"],
                    "good_avoid_rate": summary["good_avoid_rate"],
                    "verdict_counts": summary["verdict_counts"],
                    "top_symbols": summary["top_symbols"],
                }
            ],
        }

    if len(distinct_values) <= 3:
        value_to_bucket = {}
        sorted_values = sorted(distinct_values)
        if len(sorted_values) == 2:
            labels = ["low", "high"]
        else:
            labels = ["low", "mid", "high"]
        for idx, value in enumerate(sorted_values):
            value_to_bucket[value] = labels[idx]

        grouped = defaultdict(list)
        for record in records:
            metric_value = _extract_metric_value(record, metric_name)
            if metric_value is None:
                continue
            grouped[value_to_bucket[round(metric_value, 8)]].append(record)

        buckets = []
        for label in labels:
            bucket_records = grouped.get(label) or []
            if not bucket_records:
                continue
            metric_values = [
                _extract_metric_value(record, metric_name)
                for record in bucket_records
                if _extract_metric_value(record, metric_name) is not None
            ]
            summary = _summarize_records(bucket_records)
            buckets.append({
                "bucket": label,
                "count": summary["count"],
                "value_min": round(min(metric_values), 4) if metric_values else None,
                "value_max": round(max(metric_values), 4) if metric_values else None,
                "actionable_count": summary["actionable_count"],
                "good_call_rate": summary["good_call_rate"],
                "bad_or_mixed_call_rate": summary["bad_or_mixed_call_rate"],
                "avoid_count": summary["avoid_count"],
                "missed_opportunity_rate": summary["missed_opportunity_rate"],
                "good_avoid_rate": summary["good_avoid_rate"],
                "verdict_counts": summary["verdict_counts"],
                "top_symbols": summary["top_symbols"],
            })
        return {
            "metric": metric_name,
            "distinct_value_count": len(distinct_values),
            "bucket_boundaries": [round(value, 4) for value in sorted_values],
            "buckets": buckets,
        }

    bucket_map, boundaries = _quantile_buckets(values, bucket_count=3)
    grouped = defaultdict(list)
    for record in records:
        bucket_index = bucket_map.get(record["record_id"])
        if bucket_index is None:
            continue
        grouped[bucket_index].append(record)

    buckets = []
    for bucket_index in sorted(grouped):
        bucket_records = grouped[bucket_index]
        metric_values = [
            _extract_metric_value(record, metric_name)
            for record in bucket_records
            if _extract_metric_value(record, metric_name) is not None
        ]
        summary = _summarize_records(bucket_records)
        buckets.append({
            "bucket": _bucket_label(bucket_index, 3),
            "count": summary["count"],
            "value_min": round(min(metric_values), 4) if metric_values else None,
            "value_max": round(max(metric_values), 4) if metric_values else None,
            "actionable_count": summary["actionable_count"],
            "good_call_rate": summary["good_call_rate"],
            "bad_or_mixed_call_rate": summary["bad_or_mixed_call_rate"],
            "avoid_count": summary["avoid_count"],
            "missed_opportunity_rate": summary["missed_opportunity_rate"],
            "good_avoid_rate": summary["good_avoid_rate"],
            "verdict_counts": summary["verdict_counts"],
            "top_symbols": summary["top_symbols"],
        })

    return {
        "metric": metric_name,
        "distinct_value_count": len(distinct_values),
        "bucket_boundaries": boundaries,
        "buckets": buckets,
    }


def _render_markdown(summary):
    lines = [
        "# Replay Macro Context Diagnostics",
        "",
        f"- replay_id: `{summary['replay_id']}`",
        f"- built_at: `{summary['built_at']}`",
        f"- comparison_count: `{summary['comparison_count']}`",
        f"- records_with_macro_context: `{summary['records_with_macro_context']}`",
        "",
        "## Notes",
        "",
    ]
    for note in summary.get("notes", []):
        lines.append(f"- {note}")

    lines.extend(["", "## Calendar Phase Profiles", ""])
    for item in summary.get("calendar_phase_profiles", []):
        lines.append(
            f"- `{item['calendar_phase']}`: count `{item['count']}`, actionable `{item['actionable_count']}`, "
            f"good_call_rate `{item['good_call_rate']}`, bad_or_mixed_call_rate `{item['bad_or_mixed_call_rate']}`, "
            f"missed_opportunity_rate `{item['missed_opportunity_rate']}`, good_avoid_rate `{item['good_avoid_rate']}`"
        )

    lines.extend(["", "## Macro Metric Buckets", ""])
    for metric_summary in summary.get("macro_metric_summaries", []):
        lines.append(f"### `{metric_summary['metric']}`")
        lines.append("")
        lines.append(f"- distinct replay values: `{metric_summary.get('distinct_value_count')}`")
        lines.append(f"- bucket boundaries: `{metric_summary['bucket_boundaries']}`")
        for bucket in metric_summary.get("buckets", []):
            lines.append(
                f"- `{bucket['bucket']}`: count `{bucket['count']}`, value_range `[{bucket['value_min']}, {bucket['value_max']}]`, "
                f"good_call_rate `{bucket['good_call_rate']}`, bad_or_mixed_call_rate `{bucket['bad_or_mixed_call_rate']}`, "
                f"missed_opportunity_rate `{bucket['missed_opportunity_rate']}`, good_avoid_rate `{bucket['good_avoid_rate']}`"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def collect_macro_context_records(replay_id):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    comparison_paths = glob(os.path.join(replay_root, "sessions", "*", "*", "comparisons", "*__comparison_v1.json"))

    records = []
    for path in sorted(comparison_paths):
        comparison = load_json(path)
        frozen_case_path = path.replace(f"{os.sep}comparisons{os.sep}", f"{os.sep}normalized{os.sep}").replace(
            "__comparison_v1.json", "__frozen_case_v1.json"
        )
        frozen_case = load_json(frozen_case_path) if os.path.exists(frozen_case_path) else {}
        macro_context = (((frozen_case.get("historical_context") or {}).get("macro_calendar_context")) or {})
        if not macro_context:
            continue

        latest_snapshot = macro_context.get("latest_available_snapshot") or {}
        records.append({
            "record_id": f"{comparison.get('session_id')}::{comparison.get('comparison_verdict')}",
            "symbol": comparison.get("symbol"),
            "session_date": comparison.get("session_date"),
            "comparison_verdict": comparison.get("comparison_verdict"),
            "action": ((comparison.get("prediction") or {}).get("action")),
            "calendar_flags": macro_context.get("calendar_flags") or {},
            "has_macro_snapshot": bool(macro_context.get("has_macro_snapshot")),
            "latest_available_snapshot": latest_snapshot,
        })

    return records


def summarize_macro_context_records(records, replay_id, notes=None):
    records_with_macro = [record for record in records if record.get("has_macro_snapshot")]

    phase_groups = defaultdict(list)
    for record in records_with_macro:
        phase_groups[_calendar_phase_label(record)].append(record)

    calendar_phase_profiles = []
    for phase_name, phase_records in sorted(phase_groups.items()):
        summary = _summarize_records(phase_records)
        calendar_phase_profiles.append({
            "calendar_phase": phase_name,
            "count": summary["count"],
            "actionable_count": summary["actionable_count"],
            "good_call_rate": summary["good_call_rate"],
            "bad_or_mixed_call_rate": summary["bad_or_mixed_call_rate"],
            "avoid_count": summary["avoid_count"],
            "missed_opportunity_rate": summary["missed_opportunity_rate"],
            "good_avoid_rate": summary["good_avoid_rate"],
            "verdict_counts": summary["verdict_counts"],
            "top_symbols": summary["top_symbols"],
        })

    metric_names = [
        "interbank_rate_pct",
        "remittance_yoy_pct",
        "claims_private_sector_yoy_pct",
        "private_credit_billion",
    ]
    macro_metric_summaries = [
        _build_metric_summary(records_with_macro, metric_name)
        for metric_name in metric_names
    ]

    return {
        "schema_version": "1.0",
        "replay_id": replay_id,
        "built_at": datetime.now().isoformat(),
        "comparison_count": len(records),
        "records_with_macro_context": len(records_with_macro),
        "notes": notes or [],
        "calendar_phase_profiles": calendar_phase_profiles,
        "macro_metric_summaries": macro_metric_summaries,
    }


def build_macro_context_diagnostics(replay_id):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    records = collect_macro_context_records(replay_id)
    notes = [
        "this diagnostic is descriptive only and does not change any replay rule",
        "calendar phase profiles are exclusive combinations of the active phase labels for a session",
        "macro metric buckets are replay-sample terciles, not hand-tuned thresholds",
        "macro snapshots use the latest record whose upload month is not after the replay session month",
        "single-month replays often have only one macro value, so cross-month aggregation is the real test for macro features",
    ]
    summary = summarize_macro_context_records(records, replay_id, notes=notes)

    summaries_dir = os.path.join(replay_root, "summaries")
    dated_json_path = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__macro_context_diagnostics_v1.json",
    )
    latest_json_path = os.path.join(summaries_dir, "latest__macro_context_diagnostics_v1.json")
    dated_md_path = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__macro_context_diagnostics_v1.md",
    )
    latest_md_path = os.path.join(summaries_dir, "latest__macro_context_diagnostics_v1.md")

    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_macro_context_diagnostics.py REPLAY_ID")
        sys.exit(1)

    replay_id = sys.argv[1]
    summary, latest_json_path, latest_md_path = build_macro_context_diagnostics(replay_id)
    print(json.dumps({
        "replay_id": replay_id,
        "comparison_count": summary["comparison_count"],
        "records_with_macro_context": summary["records_with_macro_context"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
