"""
Build a compact buy-side validation scorecard from replay artifacts.

Usage:
    python replay_buy_side_scorecard.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean

from config import VALIDATION_DIR
from entry_label_taxonomy import executable_entry_label, next_open_label as legacy_next_open_label
from replay_confidence_remap import lookup_replay_calibrated_confidence
from replay_cost_realism_study import collect_actionable_records, _simulate_case


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


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _avg(values):
    values = [value for value in values if isinstance(value, (int, float))]
    if not values:
        return None
    return round(mean(values), 4)


def _success(verdict):
    if verdict == "good_call":
        return True
    if verdict == "bad_call":
        return False
    return None


def _confidence_bucket(value):
    if value is None:
        return "unknown"
    start = int(value // 10) * 10
    end = min(start + 9, 100)
    return f"{start}-{end}"


def _build_rows(replay_ids):
    rows = []
    for record in collect_actionable_records(replay_ids):
        decision = record["decision"]
        comparison_verdict = record["comparison_verdict"]
        confidence_view = lookup_replay_calibrated_confidence(
            decision.get("action"),
            decision.get("confidence"),
        )
        simulation = _simulate_case(decision, record["future_bars"], DEFAULT_TICKET_NOTIONAL_NPR)
        next_open_label = legacy_next_open_label(simulation)
        executable_label = executable_entry_label(simulation)
        rows.append({
            "replay_id": record["replay_id"],
            "replay_month": str(record["replay_id"]).split("__")[0],
            "session_id": record["session_id"],
            "session_date": record["session_date"],
            "symbol": record["symbol"],
            "sector_name": record["sector_name"],
            "calendar_phase": record["calendar_phase"],
            "action": record["action"],
            "setup_type": record["setup_type"],
            "score": record["score"],
            "raw_confidence": record["confidence"],
            "calibrated_confidence_pct": confidence_view.get("calibrated_confidence_pct"),
            "confidence_interpretation_label": confidence_view.get("confidence_interpretation_label"),
            "risk_reward_ratio": record["risk_reward_ratio"],
            "comparison_verdict": comparison_verdict,
            "success": _success(comparison_verdict),
            "next_open_label": next_open_label,
            "executable_entry_label": executable_label,
            "gross_return_pct": simulation.get("gross_return_pct"),
            "net_return_pct": simulation.get("net_return_pct"),
            "recomputed_rr_at_entry": simulation.get("recomputed_rr_at_entry"),
            "next_open_gap_pct": simulation.get("next_open_gap_pct_vs_optimistic_entry"),
        })
    return rows


def _group_summary(rows):
    verdict_counts = Counter(row["comparison_verdict"] for row in rows)
    next_open_counts = Counter(row["next_open_label"] for row in rows)
    executable_counts = Counter(row["executable_entry_label"] for row in rows)
    usable = [row for row in rows if row["success"] is not None]
    success_count = sum(1 for row in usable if row["success"] is True)
    entered_rows = [row for row in rows if row["next_open_label"] in {"tradable_positive_gross", "tradable_negative_gross"}]
    positive_after_entry = [row for row in entered_rows if (row.get("net_return_pct") or 0) > 0]
    good_calls = [row for row in rows if row["comparison_verdict"] == "good_call"]
    good_calls_survived = [
        row for row in good_calls
        if row["executable_entry_label"] == "tradable_positive_after_costs"
    ]
    return {
        "count": len(rows),
        "verdict_counts": dict(verdict_counts),
        "good_call_rate": _rate(verdict_counts.get("good_call", 0), len(rows)),
        "bad_or_mixed_rate": _rate(verdict_counts.get("bad_call", 0) + verdict_counts.get("mixed_call", 0), len(rows)),
        "usable_success_rate": _rate(success_count, len(usable)),
        "next_open_label_counts": dict(next_open_counts),
        "executable_entry_label_counts": dict(executable_counts),
        "entered_count": len(entered_rows),
        "entered_positive_rate": _rate(len(positive_after_entry), len(entered_rows)),
        "good_call_count": len(good_calls),
        "good_call_survival_rate": _rate(len(good_calls_survived), len(good_calls)),
        "avg_raw_confidence": _avg([row["raw_confidence"] for row in rows]),
        "avg_calibrated_confidence_pct": _avg([row["calibrated_confidence_pct"] for row in rows]),
        "avg_risk_reward_ratio": _avg([row["risk_reward_ratio"] for row in rows]),
    }


def _bucket_summary(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or "unknown")].append(row)
    bucket_rows = []
    for bucket_name, bucket_items in sorted(grouped.items()):
        summary = _group_summary(bucket_items)
        bucket_rows.append({
            "bucket": bucket_name,
            "count": summary["count"],
            "good_call_rate": summary["good_call_rate"],
            "bad_or_mixed_rate": summary["bad_or_mixed_rate"],
            "usable_success_rate": summary["usable_success_rate"],
            "entered_positive_rate": summary["entered_positive_rate"],
            "good_call_survival_rate": summary["good_call_survival_rate"],
            "avg_raw_confidence": summary["avg_raw_confidence"],
            "avg_calibrated_confidence_pct": summary["avg_calibrated_confidence_pct"],
        })
    bucket_rows.sort(key=lambda item: (item["count"], item["good_call_rate"] or -1), reverse=True)
    return bucket_rows


def _confidence_bucket_summary(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[_confidence_bucket(row.get("raw_confidence"))].append(row)
    bucket_rows = []
    for bucket_name, bucket_items in sorted(grouped.items()):
        usable = [item for item in bucket_items if item["success"] is not None]
        success_count = sum(1 for item in usable if item["success"] is True)
        observed_hit_rate = _rate(success_count, len(usable))
        avg_raw = _avg([item["raw_confidence"] for item in bucket_items])
        avg_calibrated = _avg([item["calibrated_confidence_pct"] for item in bucket_items])
        calibration_gap = None
        if observed_hit_rate is not None and avg_raw is not None:
            calibration_gap = round((observed_hit_rate * 100) - avg_raw, 2)
        bucket_rows.append({
            "bucket": bucket_name,
            "count": len(bucket_items),
            "usable_count": len(usable),
            "observed_hit_rate": observed_hit_rate,
            "avg_raw_confidence": avg_raw,
            "avg_calibrated_confidence_pct": avg_calibrated,
            "raw_gap_pct": calibration_gap,
        })
    return bucket_rows


def _render_markdown(summary):
    lines = [
        "# Replay Buy-Side Validation Scorecard",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- replay_id_count: `{len(summary['replay_ids'])}`",
        f"- actionable_count: `{summary['actionable']['count']}`",
        f"- buy_count: `{summary['buy']['count']}`",
        f"- watch_only_count: `{summary['watch_only']['count']}`",
        f"- buy_sample_warning: `{summary['buy_sample_warning']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in summary["replay_ids"]:
        lines.append(f"- `{replay_id}`")

    def add_group(title, payload):
        lines.extend([
            "",
            f"## {title}",
            f"- count: `{payload['count']}`",
            f"- verdict_counts: `{payload['verdict_counts']}`",
            f"- good_call_rate: `{payload['good_call_rate']}`",
            f"- bad_or_mixed_rate: `{payload['bad_or_mixed_rate']}`",
            f"- usable_success_rate: `{payload['usable_success_rate']}`",
            f"- next_open_label_counts: `{payload['next_open_label_counts']}`",
            f"- executable_entry_label_counts: `{payload['executable_entry_label_counts']}`",
            f"- entered_positive_rate: `{payload['entered_positive_rate']}`",
            f"- good_call_survival_rate: `{payload['good_call_survival_rate']}`",
            f"- avg_raw_confidence: `{payload['avg_raw_confidence']}`",
            f"- avg_calibrated_confidence_pct: `{payload['avg_calibrated_confidence_pct']}`",
            f"- avg_risk_reward_ratio: `{payload['avg_risk_reward_ratio']}`",
        ])

    add_group("Actionable", summary["actionable"])
    add_group("Buy Only", summary["buy"])
    add_group("Watch Only", summary["watch_only"])

    lines.extend(["", "## Buy By Sector", ""])
    for row in summary["buy_sector_rows"]:
        lines.append(
            f"- `{row['bucket']}`: count `{row['count']}`, good_call_rate `{row['good_call_rate']}`, "
            f"bad_or_mixed_rate `{row['bad_or_mixed_rate']}`, good_call_survival_rate `{row['good_call_survival_rate']}`"
        )

    lines.extend(["", "## Buy By Calendar Phase", ""])
    for row in summary["buy_calendar_rows"]:
        lines.append(
            f"- `{row['bucket']}`: count `{row['count']}`, good_call_rate `{row['good_call_rate']}`, "
            f"bad_or_mixed_rate `{row['bad_or_mixed_rate']}`, good_call_survival_rate `{row['good_call_survival_rate']}`"
        )

    lines.extend(["", "## Buy Confidence Buckets", ""])
    for row in summary["buy_confidence_rows"]:
        lines.append(
            f"- `{row['bucket']}`: count `{row['count']}`, usable `{row['usable_count']}`, "
            f"observed_hit_rate `{row['observed_hit_rate']}`, avg_raw `{row['avg_raw_confidence']}`, "
            f"avg_calibrated `{row['avg_calibrated_confidence_pct']}`, raw_gap_pct `{row['raw_gap_pct']}`"
        )

    return "\n".join(lines) + "\n"


def build_buy_side_scorecard(replay_ids):
    rows = _build_rows(replay_ids)
    buy_rows = [row for row in rows if row["action"] == "buy"]
    watch_rows = [row for row in rows if row["action"] == "watch_only"]
    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_ids": replay_ids,
        "actionable": _group_summary(rows),
        "buy": _group_summary(buy_rows),
        "watch_only": _group_summary(watch_rows),
        "buy_sample_warning": len(buy_rows) < 25,
        "buy_sector_rows": _bucket_summary(buy_rows, "sector_name"),
        "buy_calendar_rows": _bucket_summary(buy_rows, "calendar_phase"),
        "buy_confidence_rows": _confidence_bucket_summary(buy_rows),
        "rows": rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__replay_buy_side_scorecard_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__replay_buy_side_scorecard_v1.json",
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
    if len(sys.argv) < 2:
        print("Usage: python replay_buy_side_scorecard.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    summary, latest_json_path, latest_md_path = build_buy_side_scorecard(sys.argv[1:])
    print(json.dumps({
        "actionable_count": summary["actionable"]["count"],
        "buy_count": summary["buy"]["count"],
        "watch_only_count": summary["watch_only"]["count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
