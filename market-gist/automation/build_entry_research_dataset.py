"""
Build the first reusable Entry Research v1 dataset.

This dataset is execution-aware by default:
- decision made at session close
- executable entry evaluated at next tradable open
- canonical labels come from the shared entry taxonomy

Usage:
    python build_entry_research_dataset.py
    python build_entry_research_dataset.py REPLAY_ID [REPLAY_ID ...]
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
from replay_cost_realism_study import (
    _load_default_replay_ids as load_default_replay_validation_ids,
    _simulate_case,
    collect_actionable_records,
    load_json,
)


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DEFAULT_BUY_MONITOR_PATH = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__aggregate_buy_side_pattern_monitor_v1.json",
)
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
    clean_values = [value for value in values if isinstance(value, (int, float))]
    if not clean_values:
        return None
    return round(mean(clean_values), 4)


def _pct_distance(level, reference):
    if level in (None, 0) or reference in (None, 0):
        return None
    return round(((float(level) / float(reference)) - 1.0) * 100, 4)


def _load_default_replay_ids():
    if os.path.exists(DEFAULT_BUY_MONITOR_PATH):
        payload = load_json(DEFAULT_BUY_MONITOR_PATH)
        replay_ids = payload.get("replay_ids") or []
        if replay_ids:
            return replay_ids
    return load_default_replay_validation_ids()


def _event_context(frozen_case):
    corporate_context = ((frozen_case.get("historical_context") or {}).get("corporate_action_context") or {})
    matched_event_count = int(corporate_context.get("matched_event_count") or 0)
    recent_event_count_90d = int(corporate_context.get("recent_event_count_90d") or 0)
    has_active_event = bool(corporate_context.get("has_active_event"))
    if has_active_event:
        event_state = "active_event"
    elif recent_event_count_90d > 0:
        event_state = "recent_event_no_active"
    elif matched_event_count > 0:
        event_state = "matched_but_stale"
    else:
        event_state = "no_symbol_event_match"
    return {
        "event_state": event_state,
        "has_active_event": has_active_event,
        "recent_event_count_90d": recent_event_count_90d,
        "matched_event_count": matched_event_count,
    }


def _entry_outcome_family(label):
    if label == "tradable_positive_after_costs":
        return "strict_positive"
    if label in {"tradable_negative_after_costs", "untradeable_gap_below_stop"}:
        return "strict_negative"
    if label == "untradeable_gap_above_target":
        return "nontradable_favorable"
    return "unresolved"


def _concentration_summary(rows, key):
    counter = Counter(str(row.get(key) or "UNKNOWN") for row in rows)
    total = len(rows)
    if not total:
        return {
            "unique_count": 0,
            "top_1_key": None,
            "top_1_count": 0,
            "top_1_share": None,
            "top_5": [],
        }
    top_key, top_count = counter.most_common(1)[0]
    return {
        "unique_count": len(counter),
        "top_1_key": top_key,
        "top_1_count": top_count,
        "top_1_share": _rate(top_count, total),
        "top_5": counter.most_common(5),
    }


def _verdict_executable_matrix(rows):
    matrix = defaultdict(Counter)
    for row in rows:
        matrix[row["comparison_verdict"]][row["executable_entry_label"]] += 1
    return {
        verdict: dict(counter)
        for verdict, counter in sorted(matrix.items())
    }


def _action_summary(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["action"]].append(row)
    output = {}
    for action, items in sorted(grouped.items()):
        output[action] = {
            "count": len(items),
            "executable_entry_label_counts": dict(Counter(item["executable_entry_label"] for item in items)),
            "entry_outcome_family_counts": dict(Counter(item["entry_outcome_family"] for item in items)),
            "symbol_concentration": _concentration_summary(items, "symbol"),
            "month_concentration": _concentration_summary(items, "month_key"),
            "sector_concentration": _concentration_summary(items, "sector_name"),
        }
    return output


def _build_rows(replay_ids):
    rows = []
    for record in collect_actionable_records(replay_ids):
        decision = record["decision"]
        frozen_case_path = record["decision_path"].replace(
            f"{os.sep}derived{os.sep}",
            f"{os.sep}normalized{os.sep}",
        ).replace("__replay_decision_v1.json", "__frozen_case_v1.json")
        frozen_case = load_json(frozen_case_path)
        historical_context = frozen_case.get("historical_context") or {}
        metrics = frozen_case.get("metrics") or {}
        cross_context = frozen_case.get("cross_sectional_context") or {}
        liquidity_context = historical_context.get("liquidity_execution_context") or {}
        liquidity_metrics = liquidity_context.get("metrics") or {}
        derived_market = ((historical_context.get("derived_context") or {}).get("market")) or {}
        official_context = historical_context.get("official_context") or {}
        benchmark_context = official_context.get("benchmark_nepse_index") or {}
        sector_index_context = official_context.get("sector_index") or {}
        market_summary_context = official_context.get("market_summary") or {}
        latest_close = ((frozen_case.get("latest_row") or {}).get("closePrice"))
        entry_zone = decision.get("entry_zone") or []
        targets = decision.get("targets") or []
        first_target = targets[0] if targets else None
        stop_level = decision.get("invalidation_level") or decision.get("stop_loss")
        confidence_view = lookup_replay_calibrated_confidence(record["action"], record["confidence"])
        simulation = _simulate_case(decision, record["future_bars"], DEFAULT_TICKET_NOTIONAL_NPR)
        next_open_label = legacy_next_open_label(simulation)
        executable_label = executable_entry_label(simulation)
        event_context = _event_context(frozen_case)

        rows.append({
            "replay_id": record["replay_id"],
            "month_key": str(record["session_date"])[:7],
            "session_id": record["session_id"],
            "session_date": record["session_date"],
            "symbol": record["symbol"],
            "sector_name": record["sector_name"],
            "calendar_phase": record["calendar_phase"],
            "event_state": event_context["event_state"],
            "has_active_event": event_context["has_active_event"],
            "recent_event_count_90d": event_context["recent_event_count_90d"],
            "matched_event_count": event_context["matched_event_count"],
            "action": record["action"],
            "setup_type": record["setup_type"],
            "comparison_verdict": record["comparison_verdict"],
            "score": record["score"],
            "raw_confidence": record["confidence"],
            "calibrated_confidence_pct": confidence_view.get("calibrated_confidence_pct"),
            "confidence_label": confidence_view.get("confidence_interpretation_label"),
            "confidence_gap_pct": round(
                (confidence_view.get("calibrated_confidence_pct") or 0.0) - float(record["confidence"] or 0.0),
                4,
            ) if confidence_view.get("calibrated_confidence_pct") is not None and record.get("confidence") is not None else None,
            "risk_reward_ratio": record["risk_reward_ratio"],
            "rr_bucket": record["rr_bucket"],
            "return_1d_pct": metrics.get("return_1d_pct"),
            "return_5d_pct": metrics.get("return_5d_pct"),
            "return_20d_pct": metrics.get("return_20d_pct"),
            "volume_ratio_5d": metrics.get("volume_ratio_5d"),
            "close_position_20d": metrics.get("close_position_20d"),
            "close_position_60d": metrics.get("close_position_60d"),
            "trend_label": metrics.get("trend_label"),
            "liquidity_label": metrics.get("liquidity_label"),
            "liq_zero_return_share_20d": liquidity_metrics.get("zero_return_share_20d"),
            "liq_zero_trade_share_20d": liquidity_metrics.get("zero_trade_share_20d"),
            "liq_turnover_ratio_5d_to_20d": liquidity_metrics.get("turnover_ratio_5d_to_20d"),
            "liq_turnover_cv_20d": liquidity_metrics.get("turnover_cv_20d"),
            "liq_avg_abs_gap_pct_20d": liquidity_metrics.get("avg_abs_gap_pct_20d"),
            "liq_gap_over_2pct_share_20d": liquidity_metrics.get("gap_over_2pct_share_20d"),
            "liq_latest_turnover_surprise_vs20d": liquidity_metrics.get("latest_turnover_surprise_vs20d"),
            "liq_latest_trades_surprise_vs20d": liquidity_metrics.get("latest_trades_surprise_vs20d"),
            "liq_is_thursday_close": liquidity_metrics.get("is_thursday_close"),
            "market_advance_decline_ratio": derived_market.get("advance_decline_ratio"),
            "market_median_diff_pct": derived_market.get("median_diff_pct"),
            "market_top_5_turnover_share": derived_market.get("top_5_turnover_share"),
            "market_total_turnover": derived_market.get("total_turnover"),
            "official_benchmark_pct_change": benchmark_context.get("percentageChange"),
            "official_sector_pct_change": sector_index_context.get("percentageChange"),
            "official_market_total_transactions": market_summary_context.get("totalTransactions"),
            "leadership_label": cross_context.get("leadership_label"),
            "basket_member_count": cross_context.get("basket_member_count"),
            "basket_return_20d_rank": cross_context.get("basket_return_20d_rank"),
            "basket_return_20d_percentile": cross_context.get("basket_return_20d_percentile"),
            "basket_score_rank": cross_context.get("basket_score_rank"),
            "basket_value_rank": cross_context.get("basket_value_rank"),
            "basket_return_20d_mean": cross_context.get("basket_return_20d_mean"),
            "relative_return_vs_basket": cross_context.get("relative_return_vs_basket"),
            "relative_score_vs_basket": cross_context.get("relative_score_vs_basket"),
            "sector_member_count": cross_context.get("sector_member_count"),
            "sector_return_20d_rank": cross_context.get("sector_return_20d_rank"),
            "sector_score_rank": cross_context.get("sector_score_rank"),
            "sector_return_20d_mean": cross_context.get("sector_return_20d_mean"),
            "relative_return_vs_sector": cross_context.get("relative_return_vs_sector"),
            "planned_entry_reference": entry_zone[0] if entry_zone else None,
            "first_target": first_target,
            "stop_level": stop_level,
            "target_distance_close_pct": _pct_distance(first_target, latest_close),
            "stop_distance_close_pct": _pct_distance(stop_level, latest_close),
            "simulation_status": simulation.get("status"),
            "next_open_label": next_open_label,
            "executable_entry_label": executable_label,
            "entry_outcome_family": _entry_outcome_family(executable_label),
            "entry_executed": simulation.get("status") == "entered",
            "next_open_gap_pct": simulation.get("next_open_gap_pct_vs_optimistic_entry"),
            "recomputed_rr_at_entry": simulation.get("recomputed_rr_at_entry"),
            "entry_price": simulation.get("entry_price"),
            "exit_price": simulation.get("exit_price"),
            "exit_type": simulation.get("exit_type"),
            "gross_return_pct": simulation.get("gross_return_pct"),
            "net_return_pct": simulation.get("net_return_pct"),
        })
    rows.sort(key=lambda item: (item["session_date"], item["symbol"], item["action"]))
    return rows


def render_markdown(summary):
    lines = [
        "# Entry Research Dataset",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- replay_id_count: `{len(summary['replay_ids'])}`",
        f"- row_count: `{summary['row_count']}`",
        f"- ticket_notional_npr: `{summary['ticket_notional_npr']}`",
        "",
        "## Replay Inputs",
        "",
    ]
    for replay_id in summary["replay_ids"]:
        lines.append(f"- `{replay_id}`")

    lines.extend([
        "",
        "## Executable Label Counts",
        "",
        f"- executable_entry_label_counts: `{summary['executable_entry_label_counts']}`",
        f"- entry_outcome_family_counts: `{summary['entry_outcome_family_counts']}`",
        f"- comparison_verdict_counts: `{summary['comparison_verdict_counts']}`",
        "",
        "## Verdict vs Executable Label",
        "",
    ])
    for verdict, counts in summary["comparison_verdict_by_executable_label"].items():
        lines.append(f"- `{verdict}`: `{counts}`")

    lines.extend([
        "",
        "## Action Summaries",
        "",
    ])
    for action, payload in summary["action_summaries"].items():
        lines.append(
            f"- `{action}`: count `{payload['count']}`, executable `{payload['executable_entry_label_counts']}`, "
            f"families `{payload['entry_outcome_family_counts']}`"
        )

    lines.extend([
        "",
        "## Overall Concentration",
        "",
        f"- symbol_concentration: `{summary['overall_symbol_concentration']}`",
        f"- month_concentration: `{summary['overall_month_concentration']}`",
        f"- sector_concentration: `{summary['overall_sector_concentration']}`",
        "",
        "## Strict Positive Concentration",
        "",
        f"- symbol_concentration: `{summary['strict_positive_symbol_concentration']}`",
        f"- month_concentration: `{summary['strict_positive_month_concentration']}`",
        f"- sector_concentration: `{summary['strict_positive_sector_concentration']}`",
        "",
        "## Geometry / Execution Snapshot",
        "",
        f"- avg_target_distance_close_pct: `{summary['avg_target_distance_close_pct']}`",
        f"- avg_stop_distance_close_pct: `{summary['avg_stop_distance_close_pct']}`",
        f"- avg_next_open_gap_pct: `{summary['avg_next_open_gap_pct']}`",
        f"- avg_recomputed_rr_at_entry: `{summary['avg_recomputed_rr_at_entry']}`",
        "",
        "## Sample Strict Positive Rows",
        "",
    ])
    for row in summary["sample_strict_positive_rows"]:
        lines.append(
            f"- `{row['session_date']} {row['symbol']}`: action `{row['action']}`, phase `{row['calendar_phase']}`, "
            f"event `{row['event_state']}`, confidence `{row['confidence_label']}`, "
            f"label `{row['executable_entry_label']}`, next_open_gap `{row['next_open_gap_pct']}`, "
            f"net `{row['net_return_pct']}`"
        )

    lines.extend([
        "",
        "## Sample Nontradable Favorable Rows",
        "",
    ])
    for row in summary["sample_nontradable_favorable_rows"]:
        lines.append(
            f"- `{row['session_date']} {row['symbol']}`: action `{row['action']}`, phase `{row['calendar_phase']}`, "
            f"event `{row['event_state']}`, confidence `{row['confidence_label']}`, "
            f"label `{row['executable_entry_label']}`, next_open_gap `{row['next_open_gap_pct']}`, "
            f"target_distance `{row['target_distance_close_pct']}`"
        )

    return "\n".join(lines) + "\n"


def build_entry_research_dataset(replay_ids):
    rows = _build_rows(replay_ids)
    strict_positive_rows = [row for row in rows if row["entry_outcome_family"] == "strict_positive"]
    nontradable_favorable_rows = [row for row in rows if row["entry_outcome_family"] == "nontradable_favorable"]
    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_ids": replay_ids,
        "row_count": len(rows),
        "ticket_notional_npr": DEFAULT_TICKET_NOTIONAL_NPR,
        "executable_entry_label_counts": dict(Counter(row["executable_entry_label"] for row in rows)),
        "entry_outcome_family_counts": dict(Counter(row["entry_outcome_family"] for row in rows)),
        "comparison_verdict_counts": dict(Counter(row["comparison_verdict"] for row in rows)),
        "comparison_verdict_by_executable_label": _verdict_executable_matrix(rows),
        "action_summaries": _action_summary(rows),
        "overall_symbol_concentration": _concentration_summary(rows, "symbol"),
        "overall_month_concentration": _concentration_summary(rows, "month_key"),
        "overall_sector_concentration": _concentration_summary(rows, "sector_name"),
        "strict_positive_symbol_concentration": _concentration_summary(strict_positive_rows, "symbol"),
        "strict_positive_month_concentration": _concentration_summary(strict_positive_rows, "month_key"),
        "strict_positive_sector_concentration": _concentration_summary(strict_positive_rows, "sector_name"),
        "avg_target_distance_close_pct": _avg([row["target_distance_close_pct"] for row in rows]),
        "avg_stop_distance_close_pct": _avg([row["stop_distance_close_pct"] for row in rows]),
        "avg_next_open_gap_pct": _avg([row["next_open_gap_pct"] for row in rows]),
        "avg_recomputed_rr_at_entry": _avg([row["recomputed_rr_at_entry"] for row in rows]),
        "sample_strict_positive_rows": strict_positive_rows[:12],
        "sample_nontradable_favorable_rows": nontradable_favorable_rows[:12],
        "rows": rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__entry_research_dataset_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__entry_research_dataset_v1.json",
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")

    markdown = render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main(argv=None):
    argv = argv or sys.argv[1:]
    replay_ids = argv or _load_default_replay_ids()
    if not replay_ids:
        print("No replay IDs available for entry dataset build.")
        sys.exit(1)

    summary, latest_json_path, latest_md_path = build_entry_research_dataset(replay_ids)
    print(json.dumps({
        "row_count": summary["row_count"],
        "executable_entry_label_counts": summary["executable_entry_label_counts"],
        "entry_outcome_family_counts": summary["entry_outcome_family_counts"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
