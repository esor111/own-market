"""
Study the strongest positive commercial-bank watch_only candidate slice.

Target slice:
    COMMERCIAL BANKS
    no_named_phase
    no_symbol_event_match
    strongly_overconfident
    watch_only

Goal:
    Compare realistic successes vs failures and test whether any clean
    decision-time separator exists before opening a new buy-side branch.
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import VALIDATION_DIR
from entry_label_taxonomy import executable_entry_label, next_open_label as legacy_next_open_label
from replay_confidence_remap import lookup_replay_calibrated_confidence
from replay_cost_realism_study import collect_actionable_records, _simulate_case


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DEFAULT_TICKET_NOTIONAL_NPR = 200_000.0
DEFAULT_REPLAY_IDS = [
    "2023-12-01_to_2023-12-31__EBL__NABIL__SANIMA__JBBL__MNBBL__API__AKPL__UPPER__dec2023_promoted_calendar_v1",
    "2025-05-01_to_2025-05-31__replay_basket_v1__daily_truth_replay_may_champion_v1",
    "2025-06-01_to_2025-06-30__replay_basket_v1__daily_truth_replay_june_champion_v1",
    "2025-09-01_to_2025-09-30__replay_basket_v1__daily_truth_replay_september_promotedchampion_v1",
]
DISCOVERY_MONTHS = {"2023-12", "2025-05"}
VALIDATION_MONTHS = {"2025-06", "2025-09"}


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


def _event_state(frozen_case):
    corporate_context = ((frozen_case.get("historical_context") or {}).get("corporate_action_context") or {})
    if corporate_context.get("has_active_event"):
        return "active_event"
    if int(corporate_context.get("recent_event_count_90d") or 0) > 0:
        return "recent_event_no_active"
    if int(corporate_context.get("matched_event_count") or 0) > 0:
        return "matched_but_stale"
    return "no_symbol_event_match"


def _cohort_summary(name, rows):
    return {
        "name": name,
        "count": len(rows),
        "symbols": _counts(rows, "symbol"),
        "months": _counts(rows, "month_key"),
        "next_open_labels": _counts(rows, "next_open_label"),
        "comparison_verdicts": _counts(rows, "comparison_verdict"),
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


def _candidate_thresholds(rows, key):
    return sorted(
        set(
            round(float(row[key]), 4)
            for row in rows
            if row.get(key) is not None
        )
    )


def _search_single_feature(positive_rows, comparison_rows, feature_name, min_positive_hits=4):
    candidates = []
    thresholds = _candidate_thresholds(positive_rows + comparison_rows, feature_name)
    for threshold in thresholds:
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


def _evaluate_candidate(rows, candidate):
    matched = [
        row for row in rows
        if row.get(candidate["feature_name"]) is not None
        and (
            row[candidate["feature_name"]] <= candidate["threshold"]
            if candidate["comparator"] == "<="
            else row[candidate["feature_name"]] >= candidate["threshold"]
        )
    ]
    success_count = sum(1 for row in matched if row["is_success"])
    return {
        "matched_count": len(matched),
        "success_count": success_count,
        "failure_count": len(matched) - success_count,
        "success_rate": _rate(success_count, len(matched)),
        "symbols": _counts(matched, "symbol"),
        "months": _counts(matched, "month_key"),
        "next_open_labels": _counts(matched, "next_open_label"),
    }


def _collect_rows(replay_ids):
    rows = []
    for record in collect_actionable_records(replay_ids):
        decision = record["decision"]
        if record.get("sector_name") != "COMMERCIAL BANKS" or decision.get("action") != "watch_only":
            continue
        frozen_case_path = record["decision_path"].replace(f"{os.sep}derived{os.sep}", f"{os.sep}normalized{os.sep}").replace(
            "__replay_decision_v1.json", "__frozen_case_v1.json"
        )
        with open(frozen_case_path, "r", encoding="utf-8") as handle:
            frozen_case = json.load(handle)
        confidence_view = lookup_replay_calibrated_confidence(decision.get("action"), decision.get("confidence"))
        if (
            record.get("calendar_phase") != "no_named_phase"
            or _event_state(frozen_case) != "no_symbol_event_match"
            or confidence_view.get("confidence_interpretation_label") != "strongly_overconfident"
        ):
            continue
        simulation = _simulate_case(decision, record["future_bars"], DEFAULT_TICKET_NOTIONAL_NPR)
        next_open_label = legacy_next_open_label(simulation)
        executable_label = executable_entry_label(simulation)
        metrics = frozen_case.get("metrics") or {}
        is_success = (
            record["comparison_verdict"] == "good_call"
            and executable_label == "tradable_positive_after_costs"
        )
        rows.append({
            "replay_id": record["replay_id"],
            "month_key": str(record["session_date"])[:7],
            "session_date": record["session_date"],
            "symbol": record["symbol"],
            "comparison_verdict": record["comparison_verdict"],
            "next_open_label": next_open_label,
            "executable_entry_label": executable_label,
            "raw_confidence": record["confidence"],
            "calibrated_confidence_pct": confidence_view.get("calibrated_confidence_pct"),
            "score": record["score"],
            "risk_reward_ratio": record["risk_reward_ratio"],
            "return_1d_pct": metrics.get("return_1d_pct"),
            "return_5d_pct": metrics.get("return_5d_pct"),
            "return_20d_pct": metrics.get("return_20d_pct"),
            "volume_ratio_5d": metrics.get("volume_ratio_5d"),
            "close_position_20d": metrics.get("close_position_20d"),
            "close_position_60d": metrics.get("close_position_60d"),
            "next_open_gap_pct": simulation.get("next_open_gap_pct_vs_optimistic_entry"),
            "recomputed_rr_at_entry": simulation.get("recomputed_rr_at_entry"),
            "net_return_pct": simulation.get("net_return_pct"),
            "is_success": is_success,
        })
    return rows


def _render_markdown(payload):
    lines = [
        "# Commercial Bank Non-Hostile Watch Success Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- replay_id_count: `{len(payload['replay_ids'])}`",
        f"- slice_count: `{payload['slice_count']}`",
        "",
        "## Split Design",
        "",
        f"- discovery_months: `{payload['split_design']['discovery_months']}`",
        f"- validation_months: `{payload['split_design']['validation_months']}`",
        "",
        "## Cohorts",
        "",
    ]
    for key in ("discovery_success", "discovery_failure", "validation_success", "validation_failure"):
        cohort = payload["cohorts"][key]
        lines.extend([
            f"### `{key}`",
            f"- count: `{cohort['count']}`",
            f"- symbols: `{cohort['symbols']}`",
            f"- months: `{cohort['months']}`",
            f"- next_open_labels: `{cohort['next_open_labels']}`",
            f"- comparison_verdicts: `{cohort['comparison_verdicts']}`",
            f"- avg_return_5d_pct: `{cohort['avg_return_5d_pct']}`",
            f"- avg_return_20d_pct: `{cohort['avg_return_20d_pct']}`",
            f"- avg_volume_ratio_5d: `{cohort['avg_volume_ratio_5d']}`",
            f"- avg_close_position_20d: `{cohort['avg_close_position_20d']}`",
            f"- avg_next_open_gap_pct: `{cohort['avg_next_open_gap_pct']}`",
            f"- avg_recomputed_rr_at_entry: `{cohort['avg_recomputed_rr_at_entry']}`",
            "",
        ])

    lines.extend(["## Top Decision-Time Separators", ""])
    for row in payload.get("top_decision_time_separators", []):
        lines.append(
            f"- `{row['feature_name']} {row['comparator']} {row['threshold']}`: success_hits `{row['positive_hits']}`, "
            f"failure_hits `{row['comparison_hits']}`, success_hit_rate `{row['positive_hit_rate']}`, failure_leak_rate `{row['comparison_leak_rate']}`"
        )

    if payload.get("best_candidate"):
        best = payload["best_candidate"]
        lines.extend([
            "",
            "## Best Candidate Validation",
            "",
            f"- candidate: `{best['feature_name']} {best['comparator']} {best['threshold']}`",
            f"- discovery_metrics: `{best['discovery_metrics']}`",
            f"- validation_metrics: `{best['validation_metrics']}`",
        ])
    return "\n".join(lines) + "\n"


def build_study(replay_ids):
    rows = _collect_rows(replay_ids)
    discovery_rows = [row for row in rows if row["month_key"] in DISCOVERY_MONTHS]
    validation_rows = [row for row in rows if row["month_key"] in VALIDATION_MONTHS]

    discovery_success = [row for row in discovery_rows if row["is_success"]]
    discovery_failure = [row for row in discovery_rows if not row["is_success"]]
    validation_success = [row for row in validation_rows if row["is_success"]]
    validation_failure = [row for row in validation_rows if not row["is_success"]]

    decision_features = [
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
    candidate_rows = []
    for feature_name in decision_features:
        candidate_rows.extend(_search_single_feature(discovery_success, discovery_failure, feature_name))
    candidate_rows.sort(
        key=lambda item: (
            item["positive_hit_rate"] or -1,
            -1 * (item["comparison_leak_rate"] if item["comparison_leak_rate"] is not None else 1),
            item["positive_hits"],
        ),
        reverse=True,
    )

    best_candidate = None
    if candidate_rows:
        best_candidate = dict(candidate_rows[0])
        best_candidate["discovery_metrics"] = _evaluate_candidate(discovery_rows, best_candidate)
        best_candidate["validation_metrics"] = _evaluate_candidate(validation_rows, best_candidate)

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_ids": replay_ids,
        "slice_count": len(rows),
        "split_design": {
            "discovery_months": sorted(DISCOVERY_MONTHS),
            "validation_months": sorted(VALIDATION_MONTHS),
        },
        "cohorts": {
            "discovery_success": _cohort_summary("discovery_success", discovery_success),
            "discovery_failure": _cohort_summary("discovery_failure", discovery_failure),
            "validation_success": _cohort_summary("validation_success", validation_success),
            "validation_failure": _cohort_summary("validation_failure", validation_failure),
        },
        "top_decision_time_separators": candidate_rows[:12],
        "best_candidate": best_candidate,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__commercial_bank_nonhostile_watch_success_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__commercial_bank_nonhostile_watch_success_study_v1.json",
    )
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__commercial_bank_nonhostile_watch_success_study_v1.md",
    )
    latest_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__commercial_bank_nonhostile_watch_success_study_v1.md",
    )

    markdown = _render_markdown(payload)
    for path in (dated_json_path, latest_json_path):
        save_json(path, payload)
    for path in (dated_md_path, latest_md_path):
        save_text(path, markdown)
    return payload, latest_json_path, latest_md_path


def main(argv=None):
    argv = argv or sys.argv[1:]
    replay_ids = argv or DEFAULT_REPLAY_IDS
    payload, latest_json_path, latest_md_path = build_study(replay_ids)
    print(json.dumps({
        "slice_count": payload["slice_count"],
        "best_candidate": payload["best_candidate"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
