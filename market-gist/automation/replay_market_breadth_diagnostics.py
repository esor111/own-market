"""
Measure whether derived replay market breadth context helps explain replay outcomes.

Usage:
    python replay_market_breadth_diagnostics.py REPLAY_ID
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


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _build_metric_summary(records, key_name):
    values = [
        {"id": record["record_id"], "value": record["market"].get(key_name)}
        for record in records
        if record.get("market")
    ]
    bucket_map, boundaries = _quantile_buckets(values, bucket_count=3)
    grouped = defaultdict(list)
    for record in records:
        bucket_index = bucket_map.get(record["record_id"])
        if bucket_index is None:
            continue
        grouped[bucket_index].append(record)

    summaries = []
    for bucket_index in sorted(grouped):
        bucket_records = grouped[bucket_index]
        verdict_counts = Counter(item["comparison_verdict"] for item in bucket_records)
        action_counts = Counter(item["action"] for item in bucket_records)
        actionable = [item for item in bucket_records if item["action"] in {"buy", "watch_only"}]
        avoids = [item for item in bucket_records if item["action"] == "avoid"]
        good_calls = sum(1 for item in actionable if item["comparison_verdict"] == "good_call")
        bad_or_mixed = sum(1 for item in actionable if item["comparison_verdict"] in {"bad_call", "mixed_call"})
        missed_opportunity = sum(1 for item in avoids if item["comparison_verdict"] == "missed_opportunity")
        good_avoid = sum(1 for item in avoids if item["comparison_verdict"] == "good_avoid")

        summaries.append({
            "bucket": _bucket_label(bucket_index, 3),
            "record_count": len(bucket_records),
            "value_min": min(item["market"].get(key_name) for item in bucket_records if item.get("market", {}).get(key_name) is not None),
            "value_max": max(item["market"].get(key_name) for item in bucket_records if item.get("market", {}).get(key_name) is not None),
            "action_counts": dict(action_counts),
            "verdict_counts": dict(verdict_counts),
            "actionable_case_count": len(actionable),
            "good_call_rate": _rate(good_calls, len(actionable)),
            "bad_or_mixed_call_rate": _rate(bad_or_mixed, len(actionable)),
            "avoid_case_count": len(avoids),
            "missed_opportunity_rate": _rate(missed_opportunity, len(avoids)),
            "good_avoid_rate": _rate(good_avoid, len(avoids)),
        })

    return {
        "metric": key_name,
        "bucket_boundaries": boundaries,
        "buckets": summaries,
    }


def _build_markdown(summary):
    lines = [
        "# Replay Market Breadth Diagnostics",
        "",
        f"- replay_id: `{summary['replay_id']}`",
        f"- built_at: `{summary['built_at']}`",
        f"- comparison_count: `{summary['comparison_count']}`",
        f"- records_with_market_context: `{summary['records_with_market_context']}`",
        "",
        "## Notes",
        "",
    ]
    for note in summary.get("notes", []):
        lines.append(f"- {note}")
    lines.extend(["", "## Metric Buckets", ""])
    for metric_summary in summary.get("metric_summaries", []):
        lines.append(f"### `{metric_summary['metric']}`")
        lines.append("")
        lines.append(f"- bucket boundaries: `{metric_summary['bucket_boundaries']}`")
        for bucket in metric_summary.get("buckets", []):
            lines.append(
                f"- `{bucket['bucket']}`: count `{bucket['record_count']}`, actionable `{bucket['actionable_case_count']}`, "
                f"good_call_rate `{bucket['good_call_rate']}`, bad_or_mixed_call_rate `{bucket['bad_or_mixed_call_rate']}`, "
                f"missed_opportunity_rate `{bucket['missed_opportunity_rate']}`, good_avoid_rate `{bucket['good_avoid_rate']}`"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def build_market_breadth_diagnostics(replay_id):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    comparison_paths = glob(os.path.join(replay_root, "sessions", "*", "*", "comparisons", "*__comparison_v1.json"))

    records = []
    for path in sorted(comparison_paths):
        comparison = load_json(path)
        frozen_case_path = path.replace(f"{os.sep}comparisons{os.sep}", f"{os.sep}normalized{os.sep}").replace(
            "__comparison_v1.json", "__frozen_case_v1.json"
        )
        frozen_case = load_json(frozen_case_path) if os.path.exists(frozen_case_path) else {}
        derived_market = (((frozen_case.get("historical_context") or {}).get("derived_context") or {}).get("market") or {})
        records.append({
            "record_id": f"{comparison.get('session_id')}::{comparison.get('comparison_verdict')}",
            "symbol": comparison.get("symbol"),
            "session_date": comparison.get("session_date"),
            "comparison_verdict": comparison.get("comparison_verdict"),
            "action": ((comparison.get("prediction") or {}).get("action")),
            "market": derived_market,
        })

    records_with_market = [record for record in records if record.get("market")]
    metric_names = [
        "advance_decline_ratio",
        "median_diff_pct",
        "top_5_turnover_share",
        "zero_return_count",
        "total_turnover",
        "total_trades",
    ]
    metric_summaries = [
        _build_metric_summary(records_with_market, key_name)
        for key_name in metric_names
    ]

    notes = [
        "this diagnostic is descriptive only and does not change any replay rule",
        "bucket splits are sample terciles from the replay itself, not fixed hand-tuned thresholds",
    ]

    summary = {
        "schema_version": "1.0",
        "replay_id": replay_id,
        "built_at": datetime.now().isoformat(),
        "comparison_count": len(records),
        "records_with_market_context": len(records_with_market),
        "notes": notes,
        "metric_summaries": metric_summaries,
    }

    summaries_dir = os.path.join(replay_root, "summaries")
    dated_json_path = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__market_breadth_diagnostics_v1.json",
    )
    latest_json_path = os.path.join(summaries_dir, "latest__market_breadth_diagnostics_v1.json")
    dated_md_path = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__market_breadth_diagnostics_v1.md",
    )
    latest_md_path = os.path.join(summaries_dir, "latest__market_breadth_diagnostics_v1.md")

    markdown = _build_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_market_breadth_diagnostics.py REPLAY_ID")
        sys.exit(1)

    replay_id = sys.argv[1]
    summary, latest_json_path, latest_md_path = build_market_breadth_diagnostics(replay_id)
    print(json.dumps({
        "replay_id": replay_id,
        "comparison_count": summary["comparison_count"],
        "records_with_market_context": summary["records_with_market_context"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
