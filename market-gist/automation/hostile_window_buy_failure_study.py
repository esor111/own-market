"""
Study hostile-window buy outcomes across one or more promoted replay runs.

Usage:
    python hostile_window_buy_failure_study.py REPLAY_ID [REPLAY_ID ...]
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


def _next_open_gap_pct(frozen_case, future_bars):
    close_price = ((frozen_case.get("metrics") or {}).get("close_price"))
    if close_price in (None, 0) or not future_bars:
        return None
    next_open = (future_bars[0] or {}).get("open")
    if next_open in (None, 0):
        return None
    return round(((float(next_open) / float(close_price)) - 1.0) * 100, 4)


def _target_distance_close_pct(frozen_case):
    metrics = frozen_case.get("metrics") or {}
    trade_plan = frozen_case.get("trade_plan") or {}
    close_price = metrics.get("close_price")
    targets = trade_plan.get("targets") or []
    if close_price in (None, 0) or not targets:
        return None
    target_1 = targets[0]
    if target_1 in (None, 0):
        return None
    return round(((float(target_1) / float(close_price)) - 1.0) * 100, 4)


def _build_record(replay_id, item):
    session_date = item.get("session_date")
    symbol = item.get("symbol")
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    symbol_root = os.path.join(replay_root, "sessions", session_date, symbol)
    frozen_case = load_json(os.path.join(symbol_root, "normalized", f"{session_date}__{symbol}__frozen_case_v1.json"))
    decision = load_json(os.path.join(symbol_root, "derived", f"{session_date}__{symbol}__replay_decision_v1.json"))
    future_payload = load_json(os.path.join(symbol_root, "raw", f"{session_date}__{symbol}__future_bars.json"))
    future_bars = future_payload.get("future_bars") or []
    metrics = frozen_case.get("metrics") or {}
    trade_plan = frozen_case.get("trade_plan") or {}
    bank_context = frozen_case.get("bank_leadership_context") or {}

    return {
        "replay_id": replay_id,
        "session_date": session_date,
        "symbol": symbol,
        "sector_name": item.get("sector_name"),
        "calendar_phase": item.get("calendar_phase"),
        "event_state": item.get("event_state"),
        "comparison_verdict": item.get("comparison_verdict"),
        "confidence_interpretation_label": item.get("confidence_interpretation_label"),
        "raw_confidence": item.get("raw_confidence"),
        "calibrated_confidence_pct": item.get("calibrated_confidence_pct"),
        "leadership_label": item.get("leadership_label"),
        "risk_reward_ratio": decision.get("risk_reward_ratio"),
        "target_distance_close_pct": _target_distance_close_pct(frozen_case),
        "next_open_gap_pct": _next_open_gap_pct(frozen_case, future_bars),
        "return_5d_pct": metrics.get("return_5d_pct"),
        "return_20d_pct": metrics.get("return_20d_pct"),
        "volume_ratio_5d": metrics.get("volume_ratio_5d"),
        "close_position_20d": metrics.get("close_position_20d"),
        "close_position_60d": metrics.get("close_position_60d"),
        "bank_leadership_top2_count": bank_context.get("leadership_top2_count"),
        "bank_return_5d_rank": bank_context.get("return_5d_rank"),
        "bank_close_position_rank": bank_context.get("close_position_rank"),
        "bank_volume_ratio_rank": bank_context.get("volume_ratio_rank"),
        "targets": trade_plan.get("targets") or [],
    }


def _cohort_summary(name, rows):
    return {
        "name": name,
        "count": len(rows),
        "symbols": _counts(rows, "symbol"),
        "sectors": _counts(rows, "sector_name"),
        "event_states": _counts(rows, "event_state"),
        "confidence_labels": _counts(rows, "confidence_interpretation_label"),
        "leadership_labels": _counts(rows, "leadership_label"),
        "avg_raw_confidence": _avg(rows, "raw_confidence"),
        "avg_calibrated_confidence_pct": _avg(rows, "calibrated_confidence_pct"),
        "avg_risk_reward_ratio": _avg(rows, "risk_reward_ratio"),
        "avg_target_distance_close_pct": _avg(rows, "target_distance_close_pct"),
        "avg_next_open_gap_pct": _avg(rows, "next_open_gap_pct"),
        "avg_return_5d_pct": _avg(rows, "return_5d_pct"),
        "avg_return_20d_pct": _avg(rows, "return_20d_pct"),
        "avg_volume_ratio_5d": _avg(rows, "volume_ratio_5d"),
        "avg_close_position_20d": _avg(rows, "close_position_20d"),
    }


def _render_markdown(payload):
    lines = [
        "# Hostile-Window Buy Failure Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- replay_count: `{len(payload['replay_ids'])}`",
        f"- hostile_buy_count: `{payload['hostile_buy_count']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in payload.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")

    lines.extend(["", "## Cohorts", ""])
    for key in ("buy_winners", "buy_failures"):
        cohort = payload.get("cohorts", {}).get(key) or {}
        lines.extend([
            f"### `{key}`",
            f"- count: `{cohort.get('count')}`",
            f"- symbols: `{cohort.get('symbols')}`",
            f"- sectors: `{cohort.get('sectors')}`",
            f"- event_states: `{cohort.get('event_states')}`",
            f"- confidence_labels: `{cohort.get('confidence_labels')}`",
            f"- avg_raw_confidence: `{cohort.get('avg_raw_confidence')}`",
            f"- avg_calibrated_confidence_pct: `{cohort.get('avg_calibrated_confidence_pct')}`",
            f"- avg_risk_reward_ratio: `{cohort.get('avg_risk_reward_ratio')}`",
            f"- avg_target_distance_close_pct: `{cohort.get('avg_target_distance_close_pct')}`",
            f"- avg_next_open_gap_pct: `{cohort.get('avg_next_open_gap_pct')}`",
            f"- avg_return_5d_pct: `{cohort.get('avg_return_5d_pct')}`",
            f"- avg_return_20d_pct: `{cohort.get('avg_return_20d_pct')}`",
            f"- avg_volume_ratio_5d: `{cohort.get('avg_volume_ratio_5d')}`",
            f"- avg_close_position_20d: `{cohort.get('avg_close_position_20d')}`",
            "",
        ])

    lines.extend(["## Case Rows", ""])
    for row in payload.get("rows", []):
        lines.append(
            f"- `{row['session_date']} {row['symbol']}`: verdict `{row['comparison_verdict']}`, "
            f"event `{row['event_state']}`, confidence `{row['confidence_interpretation_label']}`, "
            f"rr `{row['risk_reward_ratio']}`, target_distance `{row['target_distance_close_pct']}`, "
            f"next_open_gap `{row['next_open_gap_pct']}`, return_20d `{row['return_20d_pct']}`"
        )

    return "\n".join(lines) + "\n"


def build_hostile_window_buy_failure_study(replay_ids):
    rows = []
    for replay_id in replay_ids:
        summary = load_json(os.path.join(REPLAYS_DIR, replay_id, "summaries", "latest__replay_summary_v1.json"))
        for item in summary.get("records") or []:
            if item.get("action") != "buy":
                continue
            if (item.get("calendar_phase") or "") not in HOSTILE_PHASES:
                continue
            rows.append(_build_record(replay_id, item))

    buy_winners = [row for row in rows if row.get("comparison_verdict") == "good_call"]
    buy_failures = [row for row in rows if row.get("comparison_verdict") in {"bad_call", "mixed_call"}]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_ids": replay_ids,
        "hostile_buy_count": len(rows),
        "cohorts": {
            "buy_winners": _cohort_summary("buy_winners", buy_winners),
            "buy_failures": _cohort_summary("buy_failures", buy_failures),
        },
        "rows": rows,
    }

    dated_json = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__hostile_window_buy_failure_study_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__hostile_window_buy_failure_study_v1.json")
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
        print("Usage: python hostile_window_buy_failure_study.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    payload, latest_json, latest_md = build_hostile_window_buy_failure_study(sys.argv[1:])
    print(json.dumps({
        "hostile_buy_count": payload["hostile_buy_count"],
        "latest_json": latest_json,
        "latest_md": latest_md,
        "buy_winner_count": payload["cohorts"]["buy_winners"]["count"],
        "buy_failure_count": payload["cohorts"]["buy_failures"]["count"],
    }, indent=2))


if __name__ == "__main__":
    main()
