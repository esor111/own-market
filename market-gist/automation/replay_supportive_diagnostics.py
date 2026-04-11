"""
Analyze regime-supportive replay cases to separate strong follow-through from weak supportive setups.

Usage:
    python replay_supportive_diagnostics.py REPLAY_ID
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from glob import glob

from config import REPLAYS_DIR


TARGET_ALIGNMENT = "both_supportive"


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _group_name(verdict):
    if verdict == "good_call":
        return "strong_followthrough"
    if verdict in {"bad_call", "mixed_call"}:
        return "fragile_actionable"
    return "supportive_but_filtered"


def _mean(values):
    clean = [float(value) for value in values if value is not None]
    return round(sum(clean) / len(clean), 3) if clean else None


def _top_counts(records, key_name, limit=5):
    counter = Counter(record.get(key_name) or "unknown" for record in records)
    return counter.most_common(limit)


def load_supportive_records(replay_id, alignment_filter=TARGET_ALIGNMENT):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    comparison_paths = sorted(glob(os.path.join(replay_root, "sessions", "*", "*", "comparisons", "*__comparison_v1.json")))

    supportive_records = []
    for comparison_path in comparison_paths:
        comparison = load_json(comparison_path)
        frozen_case_path = comparison_path.replace(
            f"{os.sep}comparisons{os.sep}",
            f"{os.sep}normalized{os.sep}",
        ).replace("__comparison_v1.json", "__frozen_case_v1.json")
        if not os.path.exists(frozen_case_path):
            continue
        frozen_case = load_json(frozen_case_path)
        regime = frozen_case.get("regime_context") or {}
        if regime.get("alignment_label") != alignment_filter:
            continue
        cross = frozen_case.get("cross_sectional_context") or {}
        metrics = frozen_case.get("metrics") or {}
        supportive_records.append({
            "symbol": comparison.get("symbol"),
            "session_date": comparison.get("session_date"),
            "verdict": comparison.get("comparison_verdict"),
            "group": _group_name(comparison.get("comparison_verdict")),
            "action": (comparison.get("prediction") or {}).get("action"),
            "score": (comparison.get("prediction") or {}).get("score"),
            "risk_reward_ratio": (comparison.get("prediction") or {}).get("risk_reward_ratio"),
            "trend_label": metrics.get("trend_label"),
            "liquidity_label": metrics.get("liquidity_label"),
            "return_5d_pct": metrics.get("return_5d_pct"),
            "return_20d_pct": metrics.get("return_20d_pct"),
            "close_position_20d": metrics.get("close_position_20d"),
            "volume_ratio_5d": metrics.get("volume_ratio_5d"),
            "leadership_label": cross.get("leadership_label"),
            "sector_name": frozen_case.get("sector_name"),
            "reason_codes": comparison.get("reason_codes") or [],
        })
    return supportive_records


def build_supportive_diagnostics(replay_id):
    supportive_records = load_supportive_records(replay_id, alignment_filter=TARGET_ALIGNMENT)

    grouped = defaultdict(list)
    for record in supportive_records:
        grouped[record["group"]].append(record)

    metric_keys = [
        "score",
        "risk_reward_ratio",
        "return_5d_pct",
        "return_20d_pct",
        "close_position_20d",
        "volume_ratio_5d",
    ]

    group_summaries = {}
    for group_name, records in grouped.items():
        group_summaries[group_name] = {
            "count": len(records),
            "verdict_counts": dict(Counter(record["verdict"] for record in records)),
            "action_counts": dict(Counter(record["action"] for record in records)),
            "metric_averages": {
                key: _mean(record.get(key) for record in records)
                for key in metric_keys
            },
            "top_symbols": _top_counts(records, "symbol"),
            "top_leadership": _top_counts(records, "leadership_label"),
            "top_trends": _top_counts(records, "trend_label"),
            "top_liquidity": _top_counts(records, "liquidity_label"),
            "top_reason_codes": Counter(
                reason
                for record in records
                for reason in (record.get("reason_codes") or [])
            ).most_common(10),
        }

    strong = group_summaries.get("strong_followthrough", {}).get("metric_averages", {})
    fragile = group_summaries.get("fragile_actionable", {}).get("metric_averages", {})
    filtered = group_summaries.get("supportive_but_filtered", {}).get("metric_averages", {})
    metric_deltas = {
        "strong_minus_fragile": {
            key: (
                round(strong[key] - fragile[key], 3)
                if strong.get(key) is not None and fragile.get(key) is not None
                else None
            )
            for key in metric_keys
        },
        "strong_minus_filtered": {
            key: (
                round(strong[key] - filtered[key], 3)
                if strong.get(key) is not None and filtered.get(key) is not None
                else None
            )
            for key in metric_keys
        },
    }

    summary = {
        "schema_version": "1.0",
        "replay_id": replay_id,
        "alignment_filter": TARGET_ALIGNMENT,
        "built_at": datetime.now().isoformat(),
        "supportive_case_count": len(supportive_records),
        "verdict_counts": dict(Counter(record["verdict"] for record in supportive_records)),
        "group_summaries": group_summaries,
        "metric_deltas": metric_deltas,
    }

    summaries_dir = os.path.join(replay_root, "summaries")
    dated_path = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__supportive_diagnostics_v1.json",
    )
    latest_path = os.path.join(
        summaries_dir,
        "latest__supportive_diagnostics_v1.json",
    )
    save_json(dated_path, summary)
    save_json(latest_path, summary)
    return dated_path, latest_path, summary


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_supportive_diagnostics.py REPLAY_ID")
        sys.exit(1)

    replay_id = sys.argv[1]
    dated_path, latest_path, summary = build_supportive_diagnostics(replay_id)
    print(json.dumps({
        "replay_id": replay_id,
        "dated_path": dated_path,
        "latest_path": latest_path,
        "supportive_case_count": summary["supportive_case_count"],
        "verdict_counts": summary["verdict_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
