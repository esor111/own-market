"""
Research-only study of next-open tradability for frozen replay champion actionables.

Usage:
    python replay_next_open_tradability_study.py
    python replay_next_open_tradability_study.py REPLAY_ID [REPLAY_ID ...]
    python replay_next_open_tradability_study.py --output-id bank_hostile_windows REPLAY_ID [REPLAY_ID ...]
    python replay_next_open_tradability_study.py --output-id bank_hostile_windows --sector-name "COMMERCIAL BANKS" REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean

from config import VALIDATION_DIR
from entry_label_taxonomy import executable_entry_label, next_open_label as legacy_next_open_label
from replay_cost_realism_study import _load_default_replay_ids, _simulate_case, collect_actionable_records, load_json


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DEFAULT_TICKET_NOTIONAL_NPR = 200_000.0


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _pct_distance(level, reference):
    if level in (None, 0) or reference in (None, 0):
        return None
    return round(((float(level) / float(reference)) - 1.0) * 100, 4)


def _target_distance_bucket(value):
    if value is None:
        return "unknown"
    if value < 1.0:
        return "<1%"
    if value < 2.0:
        return "1-1.99%"
    if value < 4.0:
        return "2-3.99%"
    if value < 6.0:
        return "4-5.99%"
    return "6%+"


def _close_position_bucket(value):
    if value is None:
        return "unknown"
    if value >= 0.9:
        return "0.90+"
    if value >= 0.8:
        return "0.80-0.89"
    if value >= 0.7:
        return "0.70-0.79"
    return "<0.70"


def _volume_ratio_bucket(value):
    if value is None:
        return "unknown"
    if value < 0.9:
        return "<0.90"
    if value < 1.1:
        return "0.90-1.09"
    if value < 1.4:
        return "1.10-1.39"
    return "1.40+"


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _bucket_rows(records, bucket_key, positive_label="tradable_positive_gross"):
    grouped = defaultdict(list)
    for record in records:
        grouped[record.get(bucket_key) or "unknown"].append(record)

    rows = []
    for bucket_name, items in sorted(grouped.items()):
        label_counts = Counter(item["next_open_label"] for item in items)
        rows.append({
            "bucket": bucket_name,
            "count": len(items),
            "gap_above_target_count": label_counts.get("gap_above_target", 0),
            "gap_above_target_rate": _rate(label_counts.get("gap_above_target", 0), len(items)),
            "gap_below_stop_count": label_counts.get("gap_below_stop", 0),
            "gap_below_stop_rate": _rate(label_counts.get("gap_below_stop", 0), len(items)),
            "tradable_positive_count": label_counts.get(positive_label, 0),
            "tradable_positive_rate": _rate(label_counts.get(positive_label, 0), len(items)),
            "tradable_negative_count": label_counts.get("tradable_negative_gross", 0),
            "average_target_distance_pct": round(mean(
                item["target_distance_close_pct"] for item in items if item["target_distance_close_pct"] is not None
            ), 4) if any(item["target_distance_close_pct"] is not None for item in items) else None,
        })
    return rows


def _candidate_thresholds(values):
    values = sorted(set(round(float(value), 4) for value in values if value is not None))
    if not values:
        return []
    if len(values) <= 25:
        return values
    percentiles = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9]
    indices = sorted(set(min(len(values) - 1, max(0, int((len(values) - 1) * percentile))) for percentile in percentiles))
    return [values[index] for index in indices]


def _search_signatures(records, positive_label, min_support=10, min_true_positive=8):
    positives = [record for record in records if record["next_open_label"] == positive_label]
    if not positives:
        return []

    feature_names = [
        "target_distance_close_pct",
        "risk_reward_ratio",
        "return_1d_pct",
        "return_5d_pct",
        "return_20d_pct",
        "close_position_20d",
        "volume_ratio_5d",
    ]
    rows = []
    positive_count = len(positives)

    for feature_name in feature_names:
        values = [record.get(feature_name) for record in records if record.get(feature_name) is not None]
        for threshold in _candidate_thresholds(values):
            for comparator in ("<=", ">="):
                if comparator == "<=":
                    matched = [record for record in records if record.get(feature_name) is not None and record[feature_name] <= threshold]
                else:
                    matched = [record for record in records if record.get(feature_name) is not None and record[feature_name] >= threshold]

                support = len(matched)
                if support < min_support:
                    continue
                true_positive = sum(1 for record in matched if record["next_open_label"] == positive_label)
                if true_positive < min_true_positive:
                    continue
                precision = true_positive / support
                recall = true_positive / positive_count
                if precision + recall == 0:
                    f1 = 0.0
                else:
                    f1 = 2 * precision * recall / (precision + recall)
                rows.append({
                    "feature_name": feature_name,
                    "comparator": comparator,
                    "threshold": threshold,
                    "support": support,
                    "true_positive": true_positive,
                    "precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "f1": round(f1, 4),
                })

    rows.sort(key=lambda item: (item["f1"], item["precision"], item["support"], item["recall"]), reverse=True)
    return rows[:10]


def _output_file_paths(output_id=None):
    suffix = "" if not output_id else f"__{output_id}"
    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__replay_next_open_tradability_study{suffix}_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"latest__replay_next_open_tradability_study{suffix}_v1.json",
    )
    return dated_json_path, latest_json_path, dated_json_path.replace(".json", ".md"), latest_json_path.replace(".json", ".md")


def build_next_open_tradability_study(replay_ids, output_id=None, sector_names=None):
    base_records = collect_actionable_records(replay_ids, sector_names=sector_names)
    records = []
    for record in base_records:
        decision = record["decision"]
        frozen_case_path = record["decision_path"].replace(f"{os.sep}derived{os.sep}", f"{os.sep}normalized{os.sep}").replace(
            "__replay_decision_v1.json", "__frozen_case_v1.json"
        )
        frozen_case = load_json(frozen_case_path)
        metrics = frozen_case.get("metrics") or {}
        latest_close = ((frozen_case.get("latest_row") or {}).get("closePrice"))
        targets = decision.get("targets") or []
        first_target = targets[0] if targets else None
        stop_level = decision.get("invalidation_level") or decision.get("stop_loss")
        simulation = _simulate_case(decision, record["future_bars"], DEFAULT_TICKET_NOTIONAL_NPR)
        next_open_label = legacy_next_open_label(simulation)
        executable_label = executable_entry_label(simulation)

        records.append({
            "replay_id": record["replay_id"],
            "session_id": record["session_id"],
            "session_date": record["session_date"],
            "symbol": record["symbol"],
            "sector_name": record["sector_name"],
            "calendar_phase": record["calendar_phase"],
            "action": record["action"],
            "setup_type": record["setup_type"],
            "score": record["score"],
            "confidence": record["confidence"],
            "comparison_verdict": record["comparison_verdict"],
            "risk_reward_ratio": record["risk_reward_ratio"],
            "rr_bucket": record["rr_bucket"],
            "target_distance_close_pct": _pct_distance(first_target, latest_close),
            "stop_distance_close_pct": _pct_distance(stop_level, latest_close),
            "target_distance_bucket": _target_distance_bucket(_pct_distance(first_target, latest_close)),
            "close_position_20d": metrics.get("close_position_20d"),
            "close_position_bucket": _close_position_bucket(metrics.get("close_position_20d")),
            "volume_ratio_5d": metrics.get("volume_ratio_5d"),
            "volume_ratio_bucket": _volume_ratio_bucket(metrics.get("volume_ratio_5d")),
            "return_1d_pct": metrics.get("return_1d_pct"),
            "return_5d_pct": metrics.get("return_5d_pct"),
            "return_20d_pct": metrics.get("return_20d_pct"),
            "trend_label": metrics.get("trend_label"),
            "liquidity_label": metrics.get("liquidity_label"),
            "next_open_gap_pct": simulation.get("next_open_gap_pct_vs_optimistic_entry"),
            "recomputed_rr_at_entry": simulation.get("recomputed_rr_at_entry"),
            "simulation": simulation,
            "next_open_label": next_open_label,
            "executable_entry_label": executable_label,
        })

    original_good_calls = [record for record in records if record["comparison_verdict"] == "good_call"]
    tradable_positive_good_calls = [record for record in original_good_calls if record["next_open_label"] == "tradable_positive_gross"]
    tradable_negative_good_calls = [record for record in original_good_calls if record["next_open_label"] == "tradable_negative_gross"]
    gap_above_good_calls = [record for record in original_good_calls if record["next_open_label"] == "gap_above_target"]
    gap_below_good_calls = [record for record in original_good_calls if record["next_open_label"] == "gap_below_stop"]

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_id_count": len(replay_ids),
        "replay_ids": replay_ids,
        "ticket_notional_for_status_reference_npr": DEFAULT_TICKET_NOTIONAL_NPR,
        "actionable_case_count": len(records),
        "original_good_call_count": len(original_good_calls),
        "next_open_label_counts": dict(Counter(record["next_open_label"] for record in records)),
        "executable_entry_label_counts": dict(Counter(record["executable_entry_label"] for record in records)),
        "original_good_call_next_open_label_counts": dict(Counter(record["next_open_label"] for record in original_good_calls)),
        "original_good_call_executable_entry_label_counts": dict(Counter(record["executable_entry_label"] for record in original_good_calls)),
        "average_target_distance_close_pct": round(mean(
            record["target_distance_close_pct"] for record in records if record["target_distance_close_pct"] is not None
        ), 4) if any(record["target_distance_close_pct"] is not None for record in records) else None,
        "average_recomputed_rr_tradable": round(mean(
            record["recomputed_rr_at_entry"] for record in records
            if record["recomputed_rr_at_entry"] is not None and record["next_open_label"] in {"tradable_positive_gross", "tradable_negative_gross"}
        ), 4) if any(record["recomputed_rr_at_entry"] is not None and record["next_open_label"] in {"tradable_positive_gross", "tradable_negative_gross"} for record in records) else None,
        "target_distance_bucket_rows_all_actionables": _bucket_rows(records, "target_distance_bucket"),
        "target_distance_bucket_rows_original_good_calls": _bucket_rows(original_good_calls, "target_distance_bucket"),
        "rr_bucket_rows_original_good_calls": _bucket_rows(original_good_calls, "rr_bucket"),
        "sector_rows_original_good_calls": _bucket_rows(original_good_calls, "sector_name"),
        "calendar_phase_rows_original_good_calls": _bucket_rows(original_good_calls, "calendar_phase"),
        "close_position_rows_original_good_calls": _bucket_rows(original_good_calls, "close_position_bucket"),
        "volume_ratio_rows_original_good_calls": _bucket_rows(original_good_calls, "volume_ratio_bucket"),
        "top_gap_above_target_signatures": _search_signatures(original_good_calls, "gap_above_target"),
        "top_tradable_positive_signatures": _search_signatures(original_good_calls, "tradable_positive_gross"),
        "top_gap_above_target_examples": [
            {
                "session_date": record["session_date"],
                "symbol": record["symbol"],
                "sector_name": record["sector_name"],
                "calendar_phase": record["calendar_phase"],
                "action": record["action"],
                "risk_reward_ratio": record["risk_reward_ratio"],
                "target_distance_close_pct": record["target_distance_close_pct"],
                "close_position_20d": record["close_position_20d"],
                "return_5d_pct": record["return_5d_pct"],
                "next_open_gap_pct": record["next_open_gap_pct"],
            }
            for record in sorted(gap_above_good_calls, key=lambda item: (item["target_distance_close_pct"] or 999, -(item["next_open_gap_pct"] or -999)))[:10]
        ],
        "top_tradable_positive_examples": [
            {
                "session_date": record["session_date"],
                "symbol": record["symbol"],
                "sector_name": record["sector_name"],
                "calendar_phase": record["calendar_phase"],
                "action": record["action"],
                "risk_reward_ratio": record["risk_reward_ratio"],
                "target_distance_close_pct": record["target_distance_close_pct"],
                "recomputed_rr_at_entry": record["recomputed_rr_at_entry"],
                "close_position_20d": record["close_position_20d"],
                "return_5d_pct": record["return_5d_pct"],
            }
            for record in sorted(tradable_positive_good_calls, key=lambda item: (-(item["target_distance_close_pct"] or -999), -(item["recomputed_rr_at_entry"] or -999)))[:10]
        ],
        "records": records,
    }

    dated_json_path, latest_json_path, dated_md_path, latest_md_path = _output_file_paths(output_id)

    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def _render_markdown(summary):
    lines = [
        "# Replay Next-Open Tradability Study",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- replay_id_count: `{summary['replay_id_count']}`",
        f"- actionable_case_count: `{summary['actionable_case_count']}`",
        f"- original_good_call_count: `{summary['original_good_call_count']}`",
        f"- reference_ticket_notional_npr: `{summary['ticket_notional_for_status_reference_npr']}`",
        "",
        "## Main Counts",
        "",
    ]
    for label, count in summary.get("next_open_label_counts", {}).items():
        lines.append(f"- all actionables `{label}`: `{count}`")
    lines.append("")
    for label, count in summary.get("executable_entry_label_counts", {}).items():
        lines.append(f"- all actionables executable `{label}`: `{count}`")
    lines.append("")
    for label, count in summary.get("original_good_call_next_open_label_counts", {}).items():
        lines.append(f"- original good calls `{label}`: `{count}`")
    lines.append("")
    for label, count in summary.get("original_good_call_executable_entry_label_counts", {}).items():
        lines.append(f"- original good calls executable `{label}`: `{count}`")

    lines.extend(["", "## Target Distance Buckets For Original Good Calls", ""])
    for row in summary.get("target_distance_bucket_rows_original_good_calls", []):
        lines.append(
            f"- `{row['bucket']}`: count `{row['count']}`, gap_above_target_rate `{row['gap_above_target_rate']}`, "
            f"tradable_positive_rate `{row['tradable_positive_rate']}`, avg_target_distance `{row['average_target_distance_pct']}`"
        )

    lines.extend(["", "## RR Buckets For Original Good Calls", ""])
    for row in summary.get("rr_bucket_rows_original_good_calls", []):
        lines.append(
            f"- `{row['bucket']}`: count `{row['count']}`, gap_above_target_rate `{row['gap_above_target_rate']}`, "
            f"tradable_positive_rate `{row['tradable_positive_rate']}`"
        )

    lines.extend(["", "## Top Gap-Above-Target Signatures", ""])
    for row in summary.get("top_gap_above_target_signatures", []):
        lines.append(
            f"- `{row['feature_name']} {row['comparator']} {row['threshold']}`: support `{row['support']}`, "
            f"tp `{row['true_positive']}`, precision `{row['precision']}`, recall `{row['recall']}`, f1 `{row['f1']}`"
        )

    lines.extend(["", "## Top Tradable-Positive Signatures", ""])
    for row in summary.get("top_tradable_positive_signatures", []):
        lines.append(
            f"- `{row['feature_name']} {row['comparator']} {row['threshold']}`: support `{row['support']}`, "
            f"tp `{row['true_positive']}`, precision `{row['precision']}`, recall `{row['recall']}`, f1 `{row['f1']}`"
        )

    lines.extend(["", "## Example Gap-Above-Target Good Calls", ""])
    for row in summary.get("top_gap_above_target_examples", []):
        lines.append(
            f"- `{row['session_date']} {row['symbol']}`: target_distance `{row['target_distance_close_pct']}`, "
            f"rr `{row['risk_reward_ratio']}`, close_position `{row['close_position_20d']}`, "
            f"return_5d `{row['return_5d_pct']}`, next_open_gap `{row['next_open_gap_pct']}`"
        )

    lines.extend(["", "## Example Tradable Positive Good Calls", ""])
    for row in summary.get("top_tradable_positive_examples", []):
        lines.append(
            f"- `{row['session_date']} {row['symbol']}`: target_distance `{row['target_distance_close_pct']}`, "
            f"rr `{row['risk_reward_ratio']}`, recomputed_rr `{row['recomputed_rr_at_entry']}`, "
            f"close_position `{row['close_position_20d']}`, return_5d `{row['return_5d_pct']}`"
        )
    return "\n".join(lines) + "\n"


def main():
    args = list(sys.argv[1:])
    output_id = None
    sector_names = []
    replay_ids = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--output-id":
            if index + 1 >= len(args):
                print("Missing value after --output-id")
                sys.exit(1)
            output_id = args[index + 1]
            index += 2
            continue
        if arg == "--sector-name":
            if index + 1 >= len(args):
                print("Missing value after --sector-name")
                sys.exit(1)
            sector_names.append(args[index + 1])
            index += 2
            continue
        replay_ids.append(arg)
        index += 1

    replay_ids = replay_ids if replay_ids else _load_default_replay_ids()
    if not replay_ids:
        print("No replay IDs available for next-open tradability study.")
        sys.exit(1)

    summary, latest_json_path, latest_md_path = build_next_open_tradability_study(
        replay_ids,
        output_id=output_id,
        sector_names=sector_names,
    )
    print(json.dumps({
        "replay_id_count": summary["replay_id_count"],
        "actionable_case_count": summary["actionable_case_count"],
        "original_good_call_count": summary["original_good_call_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
