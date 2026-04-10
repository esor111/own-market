"""
Aggregate liquidity diagnostics across replay runs, but only for actionable cases.

Usage:
    python aggregate_liquidity_slice_diagnostics.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from glob import glob

from config import VALIDATION_DIR, REPLAYS_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
ACTIONABLE_ACTIONS = {"buy", "watch_only"}
FRAGILE_VERDICTS = {"bad_call", "mixed_call"}
SUCCESS_VERDICTS = {"good_call"}
METRIC_NAMES = [
    "turnover_ratio_5d_to_20d",
    "trades_ratio_5d_to_20d",
    "turnover_cv_20d",
    "trades_cv_20d",
    "avg_abs_gap_pct_20d",
    "latest_turnover_surprise_vs20d",
    "latest_trades_surprise_vs20d",
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


def _avg(values):
    clean = [float(value) for value in values if isinstance(value, (int, float))]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 4)


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _metric_profile(records):
    success_records = [record for record in records if record["comparison_verdict"] in SUCCESS_VERDICTS]
    fragile_records = [record for record in records if record["comparison_verdict"] in FRAGILE_VERDICTS]

    metric_deltas = {}
    for metric_name in METRIC_NAMES:
        success_avg = _avg(record["metrics"].get(metric_name) for record in success_records)
        fragile_avg = _avg(record["metrics"].get(metric_name) for record in fragile_records)
        delta = None
        if success_avg is not None and fragile_avg is not None:
            delta = round(success_avg - fragile_avg, 4)
        metric_deltas[metric_name] = {
            "good_call_avg": success_avg,
            "fragile_avg": fragile_avg,
            "delta_good_minus_fragile": delta,
        }
    return metric_deltas


def _build_slice_profiles(records, key_name, min_case_count=6, min_dual_side_count=1):
    groups = defaultdict(list)
    for record in records:
        groups[record.get(key_name) or "unknown"].append(record)

    profiles = []
    for slice_name, slice_records in sorted(groups.items()):
        good_call_count = sum(1 for record in slice_records if record["comparison_verdict"] in SUCCESS_VERDICTS)
        fragile_count = sum(1 for record in slice_records if record["comparison_verdict"] in FRAGILE_VERDICTS)
        if len(slice_records) < min_case_count:
            continue
        profile = {
            key_name: slice_name,
            "case_count": len(slice_records),
            "good_call_count": good_call_count,
            "fragile_count": fragile_count,
            "good_call_rate": _rate(good_call_count, len(slice_records)),
            "fragile_rate": _rate(fragile_count, len(slice_records)),
            "months_seen": sorted({record["replay_month"] for record in slice_records}),
            "metric_profiles": _metric_profile(slice_records),
        }
        profile["has_two_sided_sample"] = good_call_count >= min_dual_side_count and fragile_count >= min_dual_side_count
        profiles.append(profile)

    profiles.sort(
        key=lambda item: (
            0 if item["has_two_sided_sample"] else 1,
            -(item["case_count"] or 0),
            str(item.get(key_name) or ""),
        )
    )
    return profiles


def collect_actionable_liquidity_records(replay_ids):
    records = []
    for replay_id in replay_ids:
        replay_root = os.path.join(REPLAYS_DIR, replay_id)
        comparison_paths = glob(os.path.join(replay_root, "sessions", "*", "*", "comparisons", "*__comparison_v1.json"))
        for comparison_path in sorted(comparison_paths):
            comparison = load_json(comparison_path)
            action = ((comparison.get("prediction") or {}).get("action"))
            if action not in ACTIONABLE_ACTIONS:
                continue
            frozen_case_path = comparison_path.replace(f"{os.sep}comparisons{os.sep}", f"{os.sep}normalized{os.sep}").replace(
                "__comparison_v1.json", "__frozen_case_v1.json"
            )
            if not os.path.exists(frozen_case_path):
                continue
            frozen_case = load_json(frozen_case_path)
            regime = frozen_case.get("regime_context") or {}
            liquidity_context = (((frozen_case.get("historical_context") or {}).get("liquidity_execution_context")) or {})
            metrics = liquidity_context.get("metrics") or {}
            records.append({
                "replay_id": replay_id,
                "replay_month": replay_id[:7],
                "session_date": comparison.get("session_date"),
                "symbol": comparison.get("symbol"),
                "sector_name": frozen_case.get("sector_name") or "UNKNOWN",
                "alignment_label": regime.get("alignment_label") or "unknown",
                "market_regime": ((regime.get("market_proxy") or {}).get("regime_label")) or "unknown",
                "comparison_verdict": comparison.get("comparison_verdict"),
                "action": action,
                "metrics": metrics,
            })
    return records


def _render_markdown(summary):
    lines = [
        "# Aggregate Actionable Liquidity Slice Diagnostics",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- replay_id_count: `{summary['replay_id_count']}`",
        f"- actionable_case_count: `{summary['actionable_case_count']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in summary.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")

    lines.extend(["", "## Notes", ""])
    for note in summary.get("notes", []):
        lines.append(f"- {note}")

    lines.extend(["", "## Overall Metric Differences", ""])
    for metric_name, metric_profile in summary.get("overall_metric_profile", {}).items():
        lines.append(
            f"- `{metric_name}`: good_call_avg `{metric_profile['good_call_avg']}`, "
            f"fragile_avg `{metric_profile['fragile_avg']}`, delta `{metric_profile['delta_good_minus_fragile']}`"
        )

    lines.extend(["", "## Sector Profiles", ""])
    for item in summary.get("sector_profiles", [])[:8]:
        lines.append(
            f"- `{item['sector_name']}`: count `{item['case_count']}`, good_call_rate `{item['good_call_rate']}`, "
            f"fragile_rate `{item['fragile_rate']}`, two_sided `{item['has_two_sided_sample']}`"
        )

    lines.extend(["", "## Alignment Profiles", ""])
    for item in summary.get("alignment_profiles", [])[:8]:
        lines.append(
            f"- `{item['alignment_label']}`: count `{item['case_count']}`, good_call_rate `{item['good_call_rate']}`, "
            f"fragile_rate `{item['fragile_rate']}`, two_sided `{item['has_two_sided_sample']}`"
        )

    lines.extend(["", "## Sector+Alignment Profiles", ""])
    for item in summary.get("sector_alignment_profiles", [])[:12]:
        lines.append(
            f"- `{item['sector_alignment']}`: count `{item['case_count']}`, good_call_rate `{item['good_call_rate']}`, "
            f"fragile_rate `{item['fragile_rate']}`, two_sided `{item['has_two_sided_sample']}`"
        )
    return "\n".join(lines) + "\n"


def build_aggregate_liquidity_slice_diagnostics(replay_ids):
    records = collect_actionable_liquidity_records(replay_ids)
    for record in records:
        record["sector_alignment"] = f"{record['sector_name']} | {record['alignment_label']}"

    summary = {
        "schema_version": "1.0",
        "aggregate_id": f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_actionable_liquidity_slice_diagnostics_v1",
        "built_at": datetime.now().isoformat(),
        "replay_id_count": len(replay_ids),
        "replay_ids": replay_ids,
        "actionable_case_count": len(records),
        "notes": [
            "this diagnostic looks only at actionable replay cases (buy/watch_only)",
            "it is intended to test liquidity context inside comparable decision situations, not to create a rule directly",
        ],
        "overall_metric_profile": _metric_profile(records),
        "sector_profiles": _build_slice_profiles(records, "sector_name"),
        "alignment_profiles": _build_slice_profiles(records, "alignment_label"),
        "sector_alignment_profiles": _build_slice_profiles(records, "sector_alignment"),
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_actionable_liquidity_slice_diagnostics_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__aggregate_actionable_liquidity_slice_diagnostics_v1.json",
    )
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_actionable_liquidity_slice_diagnostics_v1.md",
    )
    latest_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__aggregate_actionable_liquidity_slice_diagnostics_v1.md",
    )
    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python aggregate_liquidity_slice_diagnostics.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    replay_ids = sys.argv[1:]
    summary, latest_json_path, latest_md_path = build_aggregate_liquidity_slice_diagnostics(replay_ids)
    print(json.dumps({
        "replay_id_count": summary["replay_id_count"],
        "actionable_case_count": summary["actionable_case_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
