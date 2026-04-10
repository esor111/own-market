"""
Aggregate replay context review across one or more replay runs.

Usage:
    python aggregate_replay_context_review.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from glob import glob

from config import REPLAYS_DIR, VALIDATION_DIR
from replay_confidence_remap import lookup_replay_calibrated_confidence
from replay_validated_sector_guidance import resolve_validated_sector_guidance


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")


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


def _event_state_label(context):
    if context.get("has_active_event"):
        return "active_event"
    if int(context.get("recent_event_count_90d") or 0) > 0:
        return "recent_event_no_active"
    if int(context.get("matched_event_count") or 0) > 0:
        return "matched_but_stale"
    return "no_symbol_event_match"


def _calendar_phase_label(context):
    phase_labels = ((context.get("calendar_flags") or {}).get("phase_labels")) or []
    if not phase_labels:
        return "no_named_phase"
    return "+".join(sorted(str(item) for item in phase_labels))


def _liquidity_profile(context):
    metrics = context.get("metrics") or {}
    flags = set(context.get("context_flags") or [])

    if "has_zero_trade_days" in flags or "high_zero_return_share" in flags:
        return "illiquid_or_inactive"
    if (metrics.get("turnover_ratio_5d_to_20d") or 0) < 0.8 or (metrics.get("trades_ratio_5d_to_20d") or 0) < 0.8:
        return "weak_short_term_participation"
    if (
        (metrics.get("latest_turnover_surprise_vs20d") or 0) >= 2.0
        and (metrics.get("latest_trades_surprise_vs20d") or 0) >= 2.0
    ):
        return "participation_spike"
    if "frequent_large_gaps" in flags or "weekend_gap_carry" in flags:
        return "gap_risk_or_weekend_carry"
    return "stable_or_normal"


def _sector_context_labels(frozen_case):
    regime = frozen_case.get("regime_context") or {}
    guidance = resolve_validated_sector_guidance(
        frozen_case.get("sector_name"),
        regime.get("alignment_label"),
    )
    sector_guidance = (guidance.get("sector_guidance") or {}).get("guidance_label") or "no_sector_guidance"
    alignment_guidance = (guidance.get("alignment_guidance") or {}).get("guidance_label") or "no_alignment_guidance"
    return sector_guidance, alignment_guidance


def _slice_key(record):
    return " | ".join([
        f"calendar={record['calendar_phase']}",
        f"sector={record['sector_guidance_label']}",
        f"event={record['event_state']}",
        f"liquidity={record['liquidity_profile']}",
        f"confidence={record['confidence_interpretation_label']}",
    ])


def _build_slice_summary(records, success_verdicts, failure_verdicts, primary="failure", min_total=3):
    grouped = defaultdict(list)
    for record in records:
        grouped[_slice_key(record)].append(record)

    rows = []
    for slice_name, slice_records in grouped.items():
        total = len(slice_records)
        if total < min_total:
            continue
        verdict_counter = Counter(item["comparison_verdict"] for item in slice_records)
        success_count = sum(verdict_counter.get(item, 0) for item in success_verdicts)
        failure_count = sum(verdict_counter.get(item, 0) for item in failure_verdicts)
        row = {
            "slice": slice_name,
            "count": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": _rate(success_count, total),
            "failure_rate": _rate(failure_count, total),
            "verdict_counts": dict(verdict_counter),
            "top_symbols": Counter(item["symbol"] for item in slice_records).most_common(5),
        }
        if primary == "success" and success_count <= 0:
            continue
        if primary == "failure" and failure_count <= 0:
            continue
        rows.append(row)

    if primary == "success":
        rows.sort(key=lambda item: (item["success_count"], item["success_rate"], -item["failure_count"], item["count"]), reverse=True)
    else:
        rows.sort(key=lambda item: (item["failure_count"], item["failure_rate"], -item["success_count"], item["count"]), reverse=True)
    return rows[:15]


def _render_markdown(summary):
    lines = [
        "# Aggregate Replay Context Review",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- replay_count: `{len(summary['replay_ids'])}`",
        f"- comparison_count: `{summary['comparison_count']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in summary.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")

    lines.extend(["", "## Context Verdict Counts", ""])
    for section_name in (
        "sector_guidance_verdict_counts",
        "alignment_guidance_verdict_counts",
        "event_state_verdict_counts",
        "liquidity_profile_verdict_counts",
        "calendar_phase_verdict_counts",
        "confidence_interpretation_verdict_counts",
    ):
        lines.append(f"### `{section_name}`")
        for key, value in list((summary.get(section_name) or {}).items())[:15]:
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")

    lines.extend(["## Top Actionable Failure Slices", ""])
    for item in summary.get("top_actionable_failure_slices", []):
        lines.append(
            f"- `{item['slice']}`: count `{item['count']}`, failure_rate `{item['failure_rate']}`, "
            f"success_rate `{item['success_rate']}`, verdicts `{item['verdict_counts']}`"
        )

    lines.extend(["", "## Top Actionable Success Slices", ""])
    for item in summary.get("top_actionable_success_slices", []):
        lines.append(
            f"- `{item['slice']}`: count `{item['count']}`, success_rate `{item['success_rate']}`, "
            f"failure_rate `{item['failure_rate']}`, verdicts `{item['verdict_counts']}`"
        )

    lines.extend(["", "## Top Avoid Failure Slices", ""])
    for item in summary.get("top_avoid_failure_slices", []):
        lines.append(
            f"- `{item['slice']}`: count `{item['count']}`, failure_rate `{item['failure_rate']}`, "
            f"success_rate `{item['success_rate']}`, verdicts `{item['verdict_counts']}`"
        )

    lines.extend(["", "## Top Good Avoid Slices", ""])
    for item in summary.get("top_good_avoid_slices", []):
        lines.append(
            f"- `{item['slice']}`: count `{item['count']}`, success_rate `{item['success_rate']}`, "
            f"failure_rate `{item['failure_rate']}`, verdicts `{item['verdict_counts']}`"
        )
    return "\n".join(lines) + "\n"


def build_aggregate_replay_context_review(replay_ids):
    records = []
    sector_guidance_counter = Counter()
    alignment_guidance_counter = Counter()
    event_state_counter = Counter()
    liquidity_profile_counter = Counter()
    calendar_phase_counter = Counter()
    confidence_interpretation_counter = Counter()

    for replay_id in replay_ids:
        replay_root = os.path.join(REPLAYS_DIR, replay_id)
        comparison_paths = glob(os.path.join(replay_root, "sessions", "*", "*", "comparisons", "*__comparison_v1.json"))

        for path in sorted(comparison_paths):
            try:
                comparison = load_json(path)
            except FileNotFoundError:
                continue
            frozen_case_path = path.replace(f"{os.sep}comparisons{os.sep}", f"{os.sep}normalized{os.sep}").replace(
                "__comparison_v1.json", "__frozen_case_v1.json"
            )
            if not os.path.exists(frozen_case_path):
                continue
            try:
                frozen_case = load_json(frozen_case_path)
            except FileNotFoundError:
                continue

            historical = frozen_case.get("historical_context") or {}
            event_context = historical.get("corporate_action_context") or {}
            liquidity_context = historical.get("liquidity_execution_context") or {}
            macro_context = historical.get("macro_calendar_context") or {}
            sector_guidance_label, alignment_guidance_label = _sector_context_labels(frozen_case)
            prediction = comparison.get("prediction") or {}
            calibrated = lookup_replay_calibrated_confidence(
                prediction.get("action"),
                prediction.get("confidence"),
            )

            record = {
                "replay_id": replay_id,
                "symbol": comparison.get("symbol"),
                "session_date": comparison.get("session_date"),
                "action": prediction.get("action"),
                "comparison_verdict": comparison.get("comparison_verdict"),
                "reason_codes": comparison.get("reason_codes") or [],
                "return_10d_pct": (comparison.get("horizon_returns") or {}).get("return_10d_pct"),
                "sector_name": frozen_case.get("sector_name") or "UNKNOWN",
                "sector_guidance_label": sector_guidance_label,
                "alignment_guidance_label": alignment_guidance_label,
                "event_state": _event_state_label(event_context),
                "dominant_event_type": event_context.get("dominant_event_type"),
                "liquidity_profile": _liquidity_profile(liquidity_context),
                "liquidity_flags": liquidity_context.get("context_flags") or [],
                "calendar_phase": _calendar_phase_label(macro_context),
                "raw_confidence": prediction.get("confidence"),
                "calibrated_confidence_pct": calibrated.get("calibrated_confidence_pct"),
                "confidence_interpretation_label": calibrated.get("confidence_interpretation_label") or "unknown",
                "confidence_reference_group": calibrated.get("reference_group"),
                "comparison_path": path,
            }
            records.append(record)

            verdict = record["comparison_verdict"] or "unknown"
            sector_guidance_counter[f"{record['sector_guidance_label']}:{verdict}"] += 1
            alignment_guidance_counter[f"{record['alignment_guidance_label']}:{verdict}"] += 1
            event_state_counter[f"{record['event_state']}:{verdict}"] += 1
            liquidity_profile_counter[f"{record['liquidity_profile']}:{verdict}"] += 1
            calendar_phase_counter[f"{record['calendar_phase']}:{verdict}"] += 1
            confidence_interpretation_counter[f"{record['confidence_interpretation_label']}:{verdict}"] += 1

    actionable_records = [item for item in records if item["action"] in {"buy", "watch_only"}]
    avoid_records = [item for item in records if item["action"] == "avoid"]

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_ids": replay_ids,
        "comparison_count": len(records),
        "sector_guidance_verdict_counts": dict(sector_guidance_counter),
        "alignment_guidance_verdict_counts": dict(alignment_guidance_counter),
        "event_state_verdict_counts": dict(event_state_counter),
        "liquidity_profile_verdict_counts": dict(liquidity_profile_counter),
        "calendar_phase_verdict_counts": dict(calendar_phase_counter),
        "confidence_interpretation_verdict_counts": dict(confidence_interpretation_counter),
        "top_actionable_failure_slices": _build_slice_summary(
            actionable_records,
            success_verdicts={"good_call"},
            failure_verdicts={"bad_call", "mixed_call"},
            primary="failure",
        ),
        "top_actionable_success_slices": _build_slice_summary(
            actionable_records,
            success_verdicts={"good_call"},
            failure_verdicts={"bad_call", "mixed_call"},
            primary="success",
        ),
        "top_avoid_failure_slices": _build_slice_summary(
            avoid_records,
            success_verdicts={"good_avoid"},
            failure_verdicts={"missed_opportunity"},
            primary="failure",
        ),
        "top_good_avoid_slices": _build_slice_summary(
            avoid_records,
            success_verdicts={"good_avoid"},
            failure_verdicts={"missed_opportunity"},
            primary="success",
        ),
        "records": records,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__aggregate_replay_context_review_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_replay_context_review_v1.json")
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
        print("Usage: python aggregate_replay_context_review.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    replay_ids = sys.argv[1:]
    summary, latest_json_path, latest_md_path = build_aggregate_replay_context_review(replay_ids)
    print(json.dumps({
        "replay_count": len(replay_ids),
        "comparison_count": summary["comparison_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
