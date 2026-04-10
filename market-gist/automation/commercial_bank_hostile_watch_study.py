"""
Study hostile-window commercial-bank watch_only cases across one or more replay runs.

Usage:
    python commercial_bank_hostile_watch_study.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import REPLAYS_DIR, VALIDATION_DIR


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
HOSTILE_PHASES = {
    "fiscal_year_end_window",
    "post_fiscal_results_window",
}
TARGET_SECTOR = "COMMERCIAL BANKS"


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


def _avg(rows, key):
    values = [row.get(key) for row in rows if isinstance(row.get(key), (int, float))]
    return round(sum(values) / len(values), 4) if values else None


def _counts(rows, key):
    counter = Counter()
    for row in rows:
        counter[str(row.get(key) or "UNKNOWN")] += 1
    return dict(counter.most_common(10))


def _build_record(replay_id, item):
    session_date = item.get("session_date")
    symbol = item.get("symbol")
    symbol_root = os.path.join(REPLAYS_DIR, replay_id, "sessions", session_date, symbol)
    frozen_case = load_json(os.path.join(symbol_root, "normalized", f"{session_date}__{symbol}__frozen_case_v1.json"))
    decision = load_json(os.path.join(symbol_root, "derived", f"{session_date}__{symbol}__replay_decision_v1.json"))
    metrics = frozen_case.get("metrics") or {}
    bank_context = frozen_case.get("bank_leadership_context") or {}

    return {
        "replay_id": replay_id,
        "session_date": session_date,
        "symbol": symbol,
        "calendar_phase": item.get("calendar_phase"),
        "event_state": item.get("event_state"),
        "comparison_verdict": item.get("comparison_verdict"),
        "confidence_interpretation_label": item.get("confidence_interpretation_label"),
        "raw_confidence": item.get("raw_confidence"),
        "calibrated_confidence_pct": item.get("calibrated_confidence_pct"),
        "leadership_label": item.get("leadership_label"),
        "alignment_label": item.get("alignment_label"),
        "risk_reward_ratio": decision.get("risk_reward_ratio"),
        "return_5d_pct": metrics.get("return_5d_pct"),
        "return_20d_pct": metrics.get("return_20d_pct"),
        "volume_ratio_5d": metrics.get("volume_ratio_5d"),
        "close_position_20d": metrics.get("close_position_20d"),
        "close_position_60d": metrics.get("close_position_60d"),
        "bank_leadership_top2_count": bank_context.get("leadership_top2_count"),
        "bank_return_5d_rank": bank_context.get("return_5d_rank"),
        "bank_close_position_rank": bank_context.get("close_position_rank"),
        "bank_volume_ratio_rank": bank_context.get("volume_ratio_rank"),
    }


def _cohort_summary(name, rows):
    return {
        "name": name,
        "count": len(rows),
        "symbols": _counts(rows, "symbol"),
        "calendar_phases": _counts(rows, "calendar_phase"),
        "event_states": _counts(rows, "event_state"),
        "confidence_labels": _counts(rows, "confidence_interpretation_label"),
        "leadership_labels": _counts(rows, "leadership_label"),
        "alignment_labels": _counts(rows, "alignment_label"),
        "avg_raw_confidence": _avg(rows, "raw_confidence"),
        "avg_calibrated_confidence_pct": _avg(rows, "calibrated_confidence_pct"),
        "avg_risk_reward_ratio": _avg(rows, "risk_reward_ratio"),
        "avg_return_5d_pct": _avg(rows, "return_5d_pct"),
        "avg_return_20d_pct": _avg(rows, "return_20d_pct"),
        "avg_volume_ratio_5d": _avg(rows, "volume_ratio_5d"),
        "avg_close_position_20d": _avg(rows, "close_position_20d"),
        "avg_close_position_60d": _avg(rows, "close_position_60d"),
        "avg_bank_leadership_top2_count": _avg(rows, "bank_leadership_top2_count"),
        "avg_bank_return_5d_rank": _avg(rows, "bank_return_5d_rank"),
        "avg_bank_close_position_rank": _avg(rows, "bank_close_position_rank"),
        "avg_bank_volume_ratio_rank": _avg(rows, "bank_volume_ratio_rank"),
    }


def _render_markdown(payload):
    lines = [
        "# Commercial-Bank Hostile Watch Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- replay_count: `{len(payload['replay_ids'])}`",
        f"- hostile_watch_count: `{payload['hostile_watch_count']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in payload.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")

    lines.extend(["", "## Cohorts", ""])
    for key in ("watch_winners", "watch_failures", "exact_failure_slice"):
        cohort = payload.get("cohorts", {}).get(key) or {}
        lines.extend([
            f"### `{key}`",
            f"- count: `{cohort.get('count')}`",
            f"- symbols: `{cohort.get('symbols')}`",
            f"- calendar_phases: `{cohort.get('calendar_phases')}`",
            f"- event_states: `{cohort.get('event_states')}`",
            f"- confidence_labels: `{cohort.get('confidence_labels')}`",
            f"- leadership_labels: `{cohort.get('leadership_labels')}`",
            f"- alignment_labels: `{cohort.get('alignment_labels')}`",
            f"- avg_raw_confidence: `{cohort.get('avg_raw_confidence')}`",
            f"- avg_calibrated_confidence_pct: `{cohort.get('avg_calibrated_confidence_pct')}`",
            f"- avg_risk_reward_ratio: `{cohort.get('avg_risk_reward_ratio')}`",
            f"- avg_return_5d_pct: `{cohort.get('avg_return_5d_pct')}`",
            f"- avg_return_20d_pct: `{cohort.get('avg_return_20d_pct')}`",
            f"- avg_volume_ratio_5d: `{cohort.get('avg_volume_ratio_5d')}`",
            f"- avg_close_position_20d: `{cohort.get('avg_close_position_20d')}`",
            f"- avg_bank_return_5d_rank: `{cohort.get('avg_bank_return_5d_rank')}`",
            "",
        ])

    lines.extend(["## Case Rows", ""])
    for row in payload.get("rows", []):
        lines.append(
            f"- `{row['session_date']} {row['symbol']}`: verdict `{row['comparison_verdict']}`, "
            f"event `{row['event_state']}`, confidence `{row['confidence_interpretation_label']}`, "
            f"leadership `{row['leadership_label']}`, return_20d `{row['return_20d_pct']}`, "
            f"volume_ratio_5d `{row['volume_ratio_5d']}`, close_position_20d `{row['close_position_20d']}`"
        )

    return "\n".join(lines) + "\n"


def build_commercial_bank_hostile_watch_study(replay_ids):
    rows = []
    for replay_id in replay_ids:
        summary = load_json(os.path.join(REPLAYS_DIR, replay_id, "summaries", "latest__replay_summary_v1.json"))
        for item in summary.get("records") or []:
            if item.get("sector_name") != TARGET_SECTOR:
                continue
            if item.get("action") != "watch_only":
                continue
            if (item.get("calendar_phase") or "") not in HOSTILE_PHASES:
                continue
            rows.append(_build_record(replay_id, item))

    watch_winners = [row for row in rows if row.get("comparison_verdict") == "good_call"]
    watch_failures = [row for row in rows if row.get("comparison_verdict") in {"bad_call", "mixed_call"}]
    exact_failure_slice = [
        row for row in watch_failures
        if row.get("event_state") == "matched_but_stale"
        and row.get("confidence_interpretation_label") == "strongly_overconfident"
    ]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_ids": replay_ids,
        "hostile_watch_count": len(rows),
        "cohorts": {
            "watch_winners": _cohort_summary("watch_winners", watch_winners),
            "watch_failures": _cohort_summary("watch_failures", watch_failures),
            "exact_failure_slice": _cohort_summary("exact_failure_slice", exact_failure_slice),
        },
        "rows": rows,
    }

    dated_json = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__commercial_bank_hostile_watch_study_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__commercial_bank_hostile_watch_study_v1.json")
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")
    markdown = _render_markdown(payload)

    save_json(dated_json, payload)
    save_json(latest_json, payload)
    save_text(dated_md, markdown)
    save_text(latest_md, markdown)
    return payload, latest_json, latest_md


def main():
    if len(sys.argv) < 2:
        print("Usage: python commercial_bank_hostile_watch_study.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    payload, latest_json, latest_md = build_commercial_bank_hostile_watch_study(sys.argv[1:])
    print(json.dumps({
        "hostile_watch_count": payload["hostile_watch_count"],
        "watch_winner_count": payload["cohorts"]["watch_winners"]["count"],
        "watch_failure_count": payload["cohorts"]["watch_failures"]["count"],
        "exact_failure_slice_count": payload["cohorts"]["exact_failure_slice"]["count"],
        "latest_json": latest_json,
        "latest_md": latest_md,
    }, indent=2))


if __name__ == "__main__":
    main()
