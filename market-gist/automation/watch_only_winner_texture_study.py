"""
Study realistic watch_only winners versus fragile watch_only cases.

Usage:
    python watch_only_winner_texture_study.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import REPLAYS_DIR, VALIDATION_DIR
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


def _avg(rows, key):
    values = [row.get(key) for row in rows if isinstance(row.get(key), (int, float))]
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _counts(rows, key, top_n=10):
    counter = Counter(str(row.get(key) or "UNKNOWN") for row in rows)
    return dict(counter.most_common(top_n))


def _cohort_summary(name, rows):
    return {
        "name": name,
        "count": len(rows),
        "sectors": _counts(rows, "sector_name"),
        "calendar_phases": _counts(rows, "calendar_phase"),
        "event_states": _counts(rows, "event_state"),
        "confidence_labels": _counts(rows, "confidence_interpretation_label"),
        "trend_labels": _counts(rows, "trend_label"),
        "liquidity_labels": _counts(rows, "liquidity_label"),
        "avg_raw_confidence": _avg(rows, "raw_confidence"),
        "avg_calibrated_confidence_pct": _avg(rows, "calibrated_confidence_pct"),
        "avg_score": _avg(rows, "score"),
        "avg_risk_reward_ratio": _avg(rows, "risk_reward_ratio"),
        "avg_return_1d_pct": _avg(rows, "return_1d_pct"),
        "avg_return_5d_pct": _avg(rows, "return_5d_pct"),
        "avg_return_20d_pct": _avg(rows, "return_20d_pct"),
        "avg_volume_ratio_5d": _avg(rows, "volume_ratio_5d"),
        "avg_close_position_20d": _avg(rows, "close_position_20d"),
        "avg_close_position_60d": _avg(rows, "close_position_60d"),
        "avg_next_open_gap_pct": _avg(rows, "next_open_gap_pct"),
        "avg_recomputed_rr_at_entry": _avg(rows, "recomputed_rr_at_entry"),
    }


def _candidate_thresholds(values):
    values = sorted(set(round(float(value), 4) for value in values if value is not None))
    return values


def _search_single_feature(positive_rows, comparison_rows, feature_name, min_positive_hits=8):
    candidates = []
    values = [row.get(feature_name) for row in positive_rows + comparison_rows if row.get(feature_name) is not None]
    for threshold in _candidate_thresholds(values):
        for comparator in ("<=", ">="):
            if comparator == "<=":
                positive_match = [row for row in positive_rows if row.get(feature_name) is not None and row[feature_name] <= threshold]
                comparison_match = [row for row in comparison_rows if row.get(feature_name) is not None and row[feature_name] <= threshold]
            else:
                positive_match = [row for row in positive_rows if row.get(feature_name) is not None and row[feature_name] >= threshold]
                comparison_match = [row for row in comparison_rows if row.get(feature_name) is not None and row[feature_name] >= threshold]
            if len(positive_match) < min_positive_hits:
                continue
            candidates.append({
                "feature_name": feature_name,
                "comparator": comparator,
                "threshold": threshold,
                "positive_hits": len(positive_match),
                "comparison_hits": len(comparison_match),
                "positive_hit_rate": _rate(len(positive_match), len(positive_rows)),
                "comparison_leak_rate": _rate(len(comparison_match), len(comparison_rows)),
            })
    candidates.sort(
        key=lambda item: (
            item["positive_hit_rate"] or -1,
            -1 * (item["comparison_leak_rate"] if item["comparison_leak_rate"] is not None else 1),
            item["positive_hits"],
        ),
        reverse=True,
    )
    return candidates[:10]


def _render_markdown(payload):
    lines = [
        "# Watch-Only Winner Texture Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- replay_id_count: `{len(payload['replay_ids'])}`",
        f"- watch_only_count: `{payload['watch_only_count']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in payload.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")

    lines.extend(["", "## Cohorts", ""])
    for key in ("realistic_watch_winners", "fragile_watch_cases", "hydropower_realistic_winners", "hydropower_fragile_watch_cases"):
        cohort = payload["cohorts"].get(key) or {}
        lines.extend([
            f"### `{key}`",
            f"- count: `{cohort.get('count')}`",
            f"- sectors: `{cohort.get('sectors')}`",
            f"- calendar_phases: `{cohort.get('calendar_phases')}`",
            f"- event_states: `{cohort.get('event_states')}`",
            f"- confidence_labels: `{cohort.get('confidence_labels')}`",
            f"- trend_labels: `{cohort.get('trend_labels')}`",
            f"- liquidity_labels: `{cohort.get('liquidity_labels')}`",
            f"- avg_raw_confidence: `{cohort.get('avg_raw_confidence')}`",
            f"- avg_calibrated_confidence_pct: `{cohort.get('avg_calibrated_confidence_pct')}`",
            f"- avg_risk_reward_ratio: `{cohort.get('avg_risk_reward_ratio')}`",
            f"- avg_return_5d_pct: `{cohort.get('avg_return_5d_pct')}`",
            f"- avg_return_20d_pct: `{cohort.get('avg_return_20d_pct')}`",
            f"- avg_volume_ratio_5d: `{cohort.get('avg_volume_ratio_5d')}`",
            f"- avg_close_position_20d: `{cohort.get('avg_close_position_20d')}`",
            f"- avg_next_open_gap_pct: `{cohort.get('avg_next_open_gap_pct')}`",
            f"- avg_recomputed_rr_at_entry: `{cohort.get('avg_recomputed_rr_at_entry')}`",
            "",
        ])

    lines.extend(["## Top Decision-Time Winner Separators", ""])
    for item in payload.get("top_decision_time_separators", []):
        lines.append(
            f"- `{item['feature_name']} {item['comparator']} {item['threshold']}`: "
            f"winner_hits `{item['positive_hits']}`, fragile_hits `{item['comparison_hits']}`, "
            f"winner_hit_rate `{item['positive_hit_rate']}`, fragile_leak_rate `{item['comparison_leak_rate']}`"
        )

    lines.extend(["", "## Top After-Open Explanatory Separators", ""])
    for item in payload.get("top_after_open_separators", []):
        lines.append(
            f"- `{item['feature_name']} {item['comparator']} {item['threshold']}`: "
            f"winner_hits `{item['positive_hits']}`, fragile_hits `{item['comparison_hits']}`, "
            f"winner_hit_rate `{item['positive_hit_rate']}`, fragile_leak_rate `{item['comparison_leak_rate']}`"
        )

    lines.extend(["", "## Sample Winner Rows", ""])
    for row in payload.get("sample_winner_rows", []):
        lines.append(
            f"- `{row['session_date']} {row['symbol']}`: sector `{row['sector_name']}`, phase `{row['calendar_phase']}`, "
            f"confidence `{row['confidence_interpretation_label']}`, return_20d `{row['return_20d_pct']}`, "
            f"volume_ratio_5d `{row['volume_ratio_5d']}`, rr `{row['risk_reward_ratio']}`, "
            f"next_open_gap `{row['next_open_gap_pct']}`, net_return `{row['net_return_pct']}`"
        )

    return "\n".join(lines) + "\n"


def build_watch_only_winner_texture_study(replay_ids):
    rows = []
    for record in collect_actionable_records(replay_ids):
        if record.get("action") != "watch_only":
            continue
        decision = record["decision"]
        session_date = record["session_date"]
        symbol = record["symbol"]
        frozen_case_path = record["decision_path"].replace(f"{os.sep}derived{os.sep}", f"{os.sep}normalized{os.sep}").replace(
            "__replay_decision_v1.json", "__frozen_case_v1.json"
        )
        with open(frozen_case_path, "r", encoding="utf-8") as handle:
            frozen_case = json.load(handle)
        metrics = frozen_case.get("metrics") or {}
        confidence_view = lookup_replay_calibrated_confidence(decision.get("action"), decision.get("confidence"))
        simulation = _simulate_case(decision, record["future_bars"], DEFAULT_TICKET_NOTIONAL_NPR)
        corporate_context = ((frozen_case.get("historical_context") or {}).get("corporate_action_context") or {})
        if corporate_context.get("has_active_event"):
            event_state = "active_event"
        elif int(corporate_context.get("recent_event_count_90d") or 0) > 0:
            event_state = "recent_event_no_active"
        elif int(corporate_context.get("matched_event_count") or 0) > 0:
            event_state = "matched_but_stale"
        else:
            event_state = "no_symbol_event_match"

        next_open_label = legacy_next_open_label(simulation)
        executable_label = executable_entry_label(simulation)
        rows.append({
            "replay_id": record["replay_id"],
            "session_id": record["session_id"],
            "session_date": session_date,
            "symbol": symbol,
            "sector_name": record["sector_name"],
            "calendar_phase": record["calendar_phase"],
            "event_state": event_state,
            "comparison_verdict": record["comparison_verdict"],
            "next_open_label": next_open_label,
            "executable_entry_label": executable_label,
            "gross_return_pct": simulation.get("gross_return_pct"),
            "net_return_pct": simulation.get("net_return_pct"),
            "next_open_gap_pct": simulation.get("next_open_gap_pct_vs_optimistic_entry"),
            "recomputed_rr_at_entry": simulation.get("recomputed_rr_at_entry"),
            "raw_confidence": record["confidence"],
            "calibrated_confidence_pct": confidence_view.get("calibrated_confidence_pct"),
            "confidence_interpretation_label": confidence_view.get("confidence_interpretation_label"),
            "score": record["score"],
            "risk_reward_ratio": record["risk_reward_ratio"],
            "return_1d_pct": metrics.get("return_1d_pct"),
            "return_5d_pct": metrics.get("return_5d_pct"),
            "return_20d_pct": metrics.get("return_20d_pct"),
            "volume_ratio_5d": metrics.get("volume_ratio_5d"),
            "close_position_20d": metrics.get("close_position_20d"),
            "close_position_60d": metrics.get("close_position_60d"),
            "trend_label": metrics.get("trend_label"),
            "liquidity_label": metrics.get("liquidity_label"),
        })

    realistic_watch_winners = [
        row for row in rows
        if row["comparison_verdict"] == "good_call"
        and row["executable_entry_label"] == "tradable_positive_after_costs"
    ]
    fragile_watch_cases = [row for row in rows if row["comparison_verdict"] in {"bad_call", "mixed_call"}]
    hydropower_realistic_winners = [row for row in realistic_watch_winners if row["sector_name"] == "HYDROPOWER"]
    hydropower_fragile_watch_cases = [row for row in fragile_watch_cases if row["sector_name"] == "HYDROPOWER"]

    decision_time_features = [
        "raw_confidence",
        "calibrated_confidence_pct",
        "score",
        "risk_reward_ratio",
        "return_1d_pct",
        "return_5d_pct",
        "return_20d_pct",
        "volume_ratio_5d",
        "close_position_20d",
        "close_position_60d",
    ]
    after_open_features = [
        "next_open_gap_pct",
        "recomputed_rr_at_entry",
    ]

    decision_time_rows = []
    for feature_name in decision_time_features:
        decision_time_rows.extend(
            _search_single_feature(hydropower_realistic_winners, hydropower_fragile_watch_cases, feature_name)
        )
    decision_time_rows.sort(
        key=lambda item: (
            item["positive_hit_rate"] or -1,
            -1 * (item["comparison_leak_rate"] if item["comparison_leak_rate"] is not None else 1),
            item["positive_hits"],
        ),
        reverse=True,
    )

    after_open_rows = []
    for feature_name in after_open_features:
        after_open_rows.extend(
            _search_single_feature(hydropower_realistic_winners, hydropower_fragile_watch_cases, feature_name)
        )
    after_open_rows.sort(
        key=lambda item: (
            item["positive_hit_rate"] or -1,
            -1 * (item["comparison_leak_rate"] if item["comparison_leak_rate"] is not None else 1),
            item["positive_hits"],
        ),
        reverse=True,
    )

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_ids": replay_ids,
        "watch_only_count": len(rows),
        "cohorts": {
            "realistic_watch_winners": _cohort_summary("realistic_watch_winners", realistic_watch_winners),
            "fragile_watch_cases": _cohort_summary("fragile_watch_cases", fragile_watch_cases),
            "hydropower_realistic_winners": _cohort_summary("hydropower_realistic_winners", hydropower_realistic_winners),
            "hydropower_fragile_watch_cases": _cohort_summary("hydropower_fragile_watch_cases", hydropower_fragile_watch_cases),
        },
        "top_decision_time_separators": decision_time_rows[:12],
        "top_after_open_separators": after_open_rows[:12],
        "sample_winner_rows": sorted(
            hydropower_realistic_winners,
            key=lambda row: (row["session_date"], row["symbol"])
        )[:20],
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__watch_only_winner_texture_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__watch_only_winner_texture_study_v1.json",
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")
    markdown = _render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python watch_only_winner_texture_study.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    payload, latest_json_path, latest_md_path = build_watch_only_winner_texture_study(sys.argv[1:])
    print(json.dumps({
        "watch_only_count": payload["watch_only_count"],
        "realistic_watch_winner_count": payload["cohorts"]["realistic_watch_winners"]["count"],
        "hydropower_realistic_winner_count": payload["cohorts"]["hydropower_realistic_winners"]["count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
