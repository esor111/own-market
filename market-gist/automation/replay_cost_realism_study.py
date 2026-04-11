"""
Research-only cost realism study for frozen replay champion runs.

Usage:
    python replay_cost_realism_study.py
    python replay_cost_realism_study.py REPLAY_ID [REPLAY_ID ...]

Default behavior:
    - loads replay IDs from latest__aggregate_replay_validation_v1.json
    - studies actionable replay cases only (`buy` and `watch_only`)
    - re-enters at the next tradable session open
    - applies Nepal equity transaction cost scenarios
    - does not change any replay action or verdict files
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from glob import glob
from statistics import mean

from config import REPLAYS_DIR, VALIDATION_DIR
from data_sources import get_truth_source
from entry_label_taxonomy import executable_entry_label, survival_label
from replay_calendar import is_nepal_trading_weekday


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DEFAULT_AGGREGATE_REPLAY_VALIDATION_PATH = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__aggregate_replay_validation_v1.json",
)
ACTIONABLE_ACTIONS = {"buy", "watch_only"}
SEBON_TRANSACTION_FEE_PCT = 0.015
DP_CHARGE_NPR = 25.0
EQUITY_COST_SCENARIOS = [
    {
        "scenario_name": "retail_50k",
        "ticket_notional_npr": 50_000.0,
        "notes": "small retail ticket; upper commission tier still applies",
    },
    {
        "scenario_name": "active_200k",
        "ticket_notional_npr": 200_000.0,
        "notes": "mid-size retail / swing ticket",
    },
    {
        "scenario_name": "large_1m",
        "ticket_notional_npr": 1_000_000.0,
        "notes": "larger discretionary ticket",
    },
]
# Current post-May 14, 2024 Nepal equity commission tiers from live broker fee pages.
CURRENT_EQUITY_COMMISSION_TIERS = [
    (50_000.0, 0.36),
    (500_000.0, 0.33),
    (2_000_000.0, 0.31),
    (10_000_000.0, 0.27),
    (float("inf"), 0.24),
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


def _parse_date(value):
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _calendar_phase_label(frozen_case):
    macro_context = ((frozen_case.get("historical_context") or {}).get("macro_calendar_context") or {})
    phase_labels = ((macro_context.get("calendar_flags") or {}).get("phase_labels")) or []
    if not phase_labels:
        return "no_named_phase"
    return "+".join(sorted(str(item) for item in phase_labels))


def _load_default_replay_ids():
    payload = load_json(DEFAULT_AGGREGATE_REPLAY_VALIDATION_PATH)
    return payload.get("replay_ids") or []


def _load_future_bars(symbol, session_date, truth_source_name="sharesansar_local", horizon_sessions=10):
    source = get_truth_source(truth_source_name)
    if not hasattr(source, "_iter_available_dates"):
        raise RuntimeError(f"Truth source does not expose replay sessions: {truth_source_name}")

    session_dt = _parse_date(session_date)
    future_sessions = [
        item for item in source._iter_available_dates(session_dt + timedelta(days=1), None)
        if is_nepal_trading_weekday(item)
    ][:horizon_sessions]
    if not future_sessions:
        return []

    payload = source.get_ticker_history(
        symbol,
        future_sessions[0].isoformat(),
        future_sessions[-1].isoformat(),
    )
    rows = (((payload or {}).get("history") or {}).get("content") or [])
    rows = sorted(rows, key=lambda row: row.get("businessDate") or "")
    future_bars = []
    for row in rows:
        business_date = row.get("businessDate")
        future_bars.append({
            "time": business_date,
            "open": row.get("openPrice"),
            "high": row.get("highPrice"),
            "low": row.get("lowPrice"),
            "close": row.get("closePrice"),
        })
    return future_bars


def _commission_pct_for_notional(notional_npr):
    for upper_bound, pct in CURRENT_EQUITY_COMMISSION_TIERS:
        if float(notional_npr) <= upper_bound:
            return pct
    return CURRENT_EQUITY_COMMISSION_TIERS[-1][1]


def _rr_bucket(value):
    if value is None:
        return "unknown"
    if value < 0.75:
        return "<0.75"
    if value < 1.2:
        return "0.75-1.19"
    if value < 2.0:
        return "1.20-1.99"
    return "2.00+"


def _pct_change(current, previous):
    if current in (None, 0) or previous in (None, 0):
        return None
    return round(((float(current) / float(previous)) - 1.0) * 100, 4)


def _cost_components(entry_price, exit_price, ticket_notional_npr):
    entry_notional = float(ticket_notional_npr)
    exit_notional = float(ticket_notional_npr) * (float(exit_price) / float(entry_price))
    buy_commission_pct = _commission_pct_for_notional(entry_notional)
    sell_commission_pct = _commission_pct_for_notional(exit_notional)
    dp_charge_pct = round((DP_CHARGE_NPR / exit_notional) * 100, 4) if exit_notional > 0 else None
    total_cost_pct = round(
        buy_commission_pct
        + sell_commission_pct
        + SEBON_TRANSACTION_FEE_PCT
        + SEBON_TRANSACTION_FEE_PCT
        + (dp_charge_pct or 0.0),
        4,
    )
    return {
        "buy_commission_pct": buy_commission_pct,
        "sell_commission_pct": sell_commission_pct,
        "sebon_fee_buy_pct": SEBON_TRANSACTION_FEE_PCT,
        "sebon_fee_sell_pct": SEBON_TRANSACTION_FEE_PCT,
        "dp_charge_pct": dp_charge_pct,
        "total_cost_pct": total_cost_pct,
        "entry_notional_npr": round(entry_notional, 2),
        "exit_notional_npr": round(exit_notional, 2),
    }


def _simulate_case(decision, future_bars, ticket_notional_npr):
    entry_zone = decision.get("entry_zone") or []
    stop_level = decision.get("invalidation_level") or decision.get("stop_loss")
    targets = decision.get("targets") or []
    first_target = targets[0] if targets else None
    optimistic_entry = entry_zone[0] if entry_zone else None

    if not entry_zone or stop_level is None or first_target is None:
        return {
            "status": "not_actionable_trade_plan",
            "entry_price": None,
            "exit_price": None,
            "exit_type": None,
            "gross_return_pct": None,
            "net_return_pct": None,
            "next_open_gap_pct_vs_optimistic_entry": None,
            "recomputed_rr_at_entry": None,
            "cost_components": None,
        }

    if not future_bars:
        return {
            "status": "no_future_bars",
            "entry_price": None,
            "exit_price": None,
            "exit_type": None,
            "gross_return_pct": None,
            "net_return_pct": None,
            "next_open_gap_pct_vs_optimistic_entry": None,
            "recomputed_rr_at_entry": None,
            "cost_components": None,
        }

    next_open = future_bars[0].get("open")
    if next_open in (None, 0):
        return {
            "status": "missing_next_open",
            "entry_price": None,
            "exit_price": None,
            "exit_type": None,
            "gross_return_pct": None,
            "net_return_pct": None,
            "next_open_gap_pct_vs_optimistic_entry": None,
            "recomputed_rr_at_entry": None,
            "cost_components": None,
        }

    next_open_gap_pct = _pct_change(next_open, optimistic_entry)
    if next_open <= stop_level:
        return {
            "status": "skip_gap_below_stop",
            "entry_price": None,
            "exit_price": None,
            "exit_type": None,
            "gross_return_pct": None,
            "net_return_pct": None,
            "next_open_gap_pct_vs_optimistic_entry": next_open_gap_pct,
            "recomputed_rr_at_entry": None,
            "cost_components": None,
        }
    if next_open >= first_target:
        return {
            "status": "skip_gap_above_first_target",
            "entry_price": None,
            "exit_price": None,
            "exit_type": None,
            "gross_return_pct": None,
            "net_return_pct": None,
            "next_open_gap_pct_vs_optimistic_entry": next_open_gap_pct,
            "recomputed_rr_at_entry": None,
            "cost_components": None,
        }

    entry_price = float(next_open)
    risk = entry_price - float(stop_level)
    recomputed_rr = None
    if risk > 0:
        recomputed_rr = round((float(first_target) - entry_price) / risk, 4)

    exit_price = None
    exit_type = None
    for bar_index, bar in enumerate(future_bars):
        bar_open = bar.get("open")
        bar_high = bar.get("high")
        bar_low = bar.get("low")

        if bar_index > 0 and bar_open is not None and bar_open <= stop_level:
            exit_price = float(bar_open)
            exit_type = "gap_stop"
            break
        if bar_index > 0 and bar_open is not None and bar_open >= first_target:
            exit_price = float(first_target)
            exit_type = "gap_target_1"
            break
        if bar_low is not None and bar_low <= stop_level:
            exit_price = float(stop_level)
            exit_type = "stop_hit"
            break
        if bar_high is not None and bar_high >= first_target:
            exit_price = float(first_target)
            exit_type = "target_1_hit"
            break

    if exit_price is None:
        last_close = future_bars[-1].get("close")
        if last_close in (None, 0):
            return {
                "status": "missing_horizon_close",
                "entry_price": entry_price,
                "exit_price": None,
                "exit_type": None,
                "gross_return_pct": None,
                "net_return_pct": None,
                "next_open_gap_pct_vs_optimistic_entry": next_open_gap_pct,
                "recomputed_rr_at_entry": recomputed_rr,
                "cost_components": None,
            }
        exit_price = float(last_close)
        exit_type = "horizon_close"

    gross_return_pct = round(((exit_price / entry_price) - 1.0) * 100, 4)
    cost_components = _cost_components(entry_price, exit_price, ticket_notional_npr)
    net_return_pct = round(gross_return_pct - cost_components["total_cost_pct"], 4)

    return {
        "status": "entered",
        "entry_price": round(entry_price, 4),
        "exit_price": round(exit_price, 4),
        "exit_type": exit_type,
        "gross_return_pct": gross_return_pct,
        "net_return_pct": net_return_pct,
        "next_open_gap_pct_vs_optimistic_entry": next_open_gap_pct,
        "recomputed_rr_at_entry": recomputed_rr,
        "cost_components": cost_components,
    }


def collect_actionable_records(replay_ids, sector_names=None):
    records = []
    normalized_sector_names = {str(item).upper() for item in (sector_names or [])}
    for replay_id in replay_ids:
        replay_root = os.path.join(REPLAYS_DIR, replay_id)
        decision_paths = glob(os.path.join(replay_root, "sessions", "*", "*", "derived", "*__replay_decision_v1.json"))
        for decision_path in sorted(decision_paths):
            decision = load_json(decision_path)
            action = decision.get("action")
            if action not in ACTIONABLE_ACTIONS:
                continue

            comparison_path = decision_path.replace(f"{os.sep}derived{os.sep}", f"{os.sep}comparisons{os.sep}").replace(
                "__replay_decision_v1.json", "__comparison_v1.json"
            )
            frozen_case_path = decision_path.replace(f"{os.sep}derived{os.sep}", f"{os.sep}normalized{os.sep}").replace(
                "__replay_decision_v1.json", "__frozen_case_v1.json"
            )
            if not os.path.exists(comparison_path) or not os.path.exists(frozen_case_path):
                continue

            comparison = load_json(comparison_path)
            frozen_case = load_json(frozen_case_path)
            sector_name = frozen_case.get("sector_name") or "UNKNOWN"
            if normalized_sector_names and str(sector_name).upper() not in normalized_sector_names:
                continue
            symbol = decision.get("symbol")
            session_date = decision.get("run_date")
            future_bars = _load_future_bars(symbol, session_date, truth_source_name="sharesansar_local", horizon_sessions=10)

            records.append({
                "replay_id": replay_id,
                "decision": decision,
                "decision_path": decision_path,
                "comparison_path": comparison_path,
                "session_id": decision.get("session_id"),
                "session_date": session_date,
                "symbol": symbol,
                "sector_name": sector_name,
                "calendar_phase": _calendar_phase_label(frozen_case),
                "action": action,
                "setup_type": decision.get("setup_type"),
                "score": decision.get("score"),
                "confidence": decision.get("confidence"),
                "risk_reward_ratio": decision.get("risk_reward_ratio"),
                "rr_bucket": _rr_bucket(decision.get("risk_reward_ratio")),
                "comparison_verdict": comparison.get("comparison_verdict"),
                "future_bars": future_bars,
            })
    return records


def _build_bucket_rows(records, bucket_key, condition_field):
    grouped = defaultdict(list)
    for record in records:
        grouped[record.get(bucket_key) or "unknown"].append(record)

    rows = []
    for bucket_name, items in sorted(grouped.items()):
        entered = [item for item in items if item["simulation"]["status"] == "entered"]
        positive = [item for item in entered if (item["simulation"].get("net_return_pct") or 0) > 0]
        rows.append({
            "bucket": bucket_name,
            "count": len(items),
            "entered_count": len(entered),
            "positive_count": len(positive),
            "positive_rate": round(len(positive) / len(entered), 4) if entered else None,
            "good_call_count": sum(1 for item in items if item["comparison_verdict"] == "good_call"),
            "good_call_survived_count": sum(1 for item in items if item[condition_field] == "good_call_survived"),
            "good_call_survival_rate": round(
                sum(1 for item in items if item[condition_field] == "good_call_survived")
                / sum(1 for item in items if item["comparison_verdict"] == "good_call"),
                4,
            ) if sum(1 for item in items if item["comparison_verdict"] == "good_call") else None,
        })
    return rows


def _render_markdown(summary):
    lines = [
        "# Replay Cost Realism Study",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- replay_id_count: `{summary['replay_id_count']}`",
        f"- actionable_case_count: `{summary['actionable_case_count']}`",
        "",
        "## Assumptions",
        "",
    ]
    for note in summary.get("assumption_notes", []):
        lines.append(f"- {note}")

    lines.extend(["", "## Replay Inputs", ""])
    for replay_id in summary.get("replay_ids", []):
        lines.append(f"- `{replay_id}`")

    for scenario_name, scenario_summary in summary.get("scenarios", {}).items():
        lines.extend([
            "",
            f"## Scenario `{scenario_name}`",
            "",
            f"- ticket_notional_npr: `{scenario_summary['ticket_notional_npr']}`",
            f"- actionables_entered: `{scenario_summary['entered_trade_count']}` / `{scenario_summary['actionable_count']}`",
            f"- profitable_after_costs: `{scenario_summary['profitable_after_costs_count']}`",
            f"- profitable_after_costs_rate: `{scenario_summary['profitable_after_costs_rate']}`",
            f"- original_good_call_count: `{scenario_summary['original_good_call_count']}`",
            f"- original_good_call_survived_count: `{scenario_summary['original_good_call_survived_count']}`",
            f"- original_good_call_survival_rate: `{scenario_summary['original_good_call_survival_rate']}`",
            f"- original_good_call_untradeable_gap_count: `{scenario_summary['original_good_call_untradeable_gap_count']}`",
            f"- original_good_call_untradeable_gap_rate: `{scenario_summary['original_good_call_untradeable_gap_rate']}`",
            f"- original_good_call_collapsed_count: `{scenario_summary['original_good_call_collapsed_count']}`",
            f"- skip_gap_below_stop_count: `{scenario_summary['skip_gap_below_stop_count']}`",
            f"- skip_gap_above_first_target_count: `{scenario_summary['skip_gap_above_first_target_count']}`",
            f"- average_next_open_gap_pct: `{scenario_summary['average_next_open_gap_pct']}`",
            f"- average_recomputed_rr: `{scenario_summary['average_recomputed_rr']}`",
            f"- average_gross_return_pct: `{scenario_summary['average_gross_return_pct']}`",
            f"- average_net_return_pct: `{scenario_summary['average_net_return_pct']}`",
            f"- executable_entry_label_counts: `{scenario_summary['executable_entry_label_counts']}`",
            f"- survival_label_counts: `{scenario_summary['survival_label_counts']}`",
            "",
            "### RR Buckets",
            "",
        ])
        for row in scenario_summary.get("rr_bucket_rows", []):
            lines.append(
                f"- `{row['bucket']}`: count `{row['count']}`, entered `{row['entered_count']}`, "
                f"positive_rate `{row['positive_rate']}`, good_call_survival_rate `{row['good_call_survival_rate']}`"
            )

        lines.extend(["", "### Sector Rows", ""])
        for row in scenario_summary.get("sector_rows", [])[:10]:
            lines.append(
                f"- `{row['bucket']}`: count `{row['count']}`, entered `{row['entered_count']}`, "
                f"positive_rate `{row['positive_rate']}`, good_call_survival_rate `{row['good_call_survival_rate']}`"
            )

        lines.extend(["", "### Biggest Paper-Win Collapses", ""])
        for row in scenario_summary.get("top_collapsed_good_calls", []):
            lines.append(
                f"- `{row['session_date']} {row['symbol']}`: action `{row['action']}`, rr `{row['risk_reward_ratio']}`, "
                f"next_open_gap `{row['next_open_gap_pct']}`, gross `{row['gross_return_pct']}`, net `{row['net_return_pct']}`, "
                f"exit `{row['exit_type']}`"
            )
    return "\n".join(lines) + "\n"


def build_replay_cost_realism_study(replay_ids):
    records = collect_actionable_records(replay_ids)
    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_id_count": len(replay_ids),
        "replay_ids": replay_ids,
        "actionable_case_count": len(records),
        "assumption_notes": [
            "uses frozen replay decisions from existing champion month runs; no action logic changes are made",
            "earliest executable entry is next tradable session open, not same-session close or lower entry-zone edge",
            "if next open is already below stop or above first target, the trade is treated as skipped / untradeable",
            "target fills are capped at the first target price; stop fills use worse-of-gap-open or planned stop when price gaps down",
            "cost scenarios use live Nepal equity commission tiers plus 0.015% SEBON transaction fee and Rs 25 DP charge",
            "study excludes capital-gains tax and extra discretionary slippage because those are investor-specific or lack point-in-time order-book support",
        ],
        "scenarios": {},
        "records": [],
    }

    for scenario in EQUITY_COST_SCENARIOS:
        scenario_records = []
        for record in records:
            simulation = _simulate_case(
                decision=record["decision"],
                future_bars=record["future_bars"],
                ticket_notional_npr=scenario["ticket_notional_npr"],
            )
            executable_label = executable_entry_label(simulation)
            record_survival_label = survival_label(record["comparison_verdict"], simulation)
            scenario_record = {
                **record,
                "scenario_name": scenario["scenario_name"],
                "ticket_notional_npr": scenario["ticket_notional_npr"],
                "simulation": simulation,
                "executable_entry_label": executable_label,
                "survival_label": record_survival_label,
            }
            scenario_records.append(scenario_record)

        entered = [item for item in scenario_records if item["simulation"]["status"] == "entered"]
        profitable = [item for item in entered if (item["simulation"].get("net_return_pct") or 0) > 0]
        good_calls = [item for item in scenario_records if item["comparison_verdict"] == "good_call"]
        survived_good_calls = [item for item in scenario_records if item["survival_label"] == "good_call_survived"]
        untradeable_good_calls = [
            item for item in scenario_records
            if item["comparison_verdict"] == "good_call" and item["survival_label"] == "untradeable_gap"
        ]
        collapsed_good_calls = [item for item in scenario_records if item["survival_label"] == "good_call_collapsed"]
        skipped_below_stop = [item for item in scenario_records if item["simulation"]["status"] == "skip_gap_below_stop"]
        skipped_above_target = [item for item in scenario_records if item["simulation"]["status"] == "skip_gap_above_first_target"]

        top_collapsed = sorted(
            collapsed_good_calls,
            key=lambda item: (
                item["simulation"].get("net_return_pct") if item["simulation"].get("net_return_pct") is not None else 999,
                item["simulation"].get("gross_return_pct") if item["simulation"].get("gross_return_pct") is not None else -999,
            ),
        )[:10]

        summary["scenarios"][scenario["scenario_name"]] = {
            "scenario_name": scenario["scenario_name"],
            "ticket_notional_npr": scenario["ticket_notional_npr"],
            "notes": scenario["notes"],
            "actionable_count": len(scenario_records),
            "buy_count": sum(1 for item in scenario_records if item["action"] == "buy"),
            "watch_only_count": sum(1 for item in scenario_records if item["action"] == "watch_only"),
            "entered_trade_count": len(entered),
            "profitable_after_costs_count": len(profitable),
            "profitable_after_costs_rate": round(len(profitable) / len(entered), 4) if entered else None,
            "original_good_call_count": len(good_calls),
            "original_good_call_survived_count": len(survived_good_calls),
            "original_good_call_survival_rate": round(len(survived_good_calls) / len(good_calls), 4) if good_calls else None,
            "original_good_call_untradeable_gap_count": len(untradeable_good_calls),
            "original_good_call_untradeable_gap_rate": round(len(untradeable_good_calls) / len(good_calls), 4) if good_calls else None,
            "original_good_call_collapsed_count": len(collapsed_good_calls),
            "skip_gap_below_stop_count": len(skipped_below_stop),
            "skip_gap_above_first_target_count": len(skipped_above_target),
            "average_next_open_gap_pct": round(mean(
                item["simulation"]["next_open_gap_pct_vs_optimistic_entry"]
                for item in scenario_records
                if item["simulation"].get("next_open_gap_pct_vs_optimistic_entry") is not None
            ), 4) if any(item["simulation"].get("next_open_gap_pct_vs_optimistic_entry") is not None for item in scenario_records) else None,
            "average_recomputed_rr": round(mean(
                item["simulation"]["recomputed_rr_at_entry"]
                for item in entered
                if item["simulation"].get("recomputed_rr_at_entry") is not None
            ), 4) if any(item["simulation"].get("recomputed_rr_at_entry") is not None for item in entered) else None,
            "average_gross_return_pct": round(mean(
                item["simulation"]["gross_return_pct"]
                for item in entered
                if item["simulation"].get("gross_return_pct") is not None
            ), 4) if entered else None,
            "average_net_return_pct": round(mean(
                item["simulation"]["net_return_pct"]
                for item in entered
                if item["simulation"].get("net_return_pct") is not None
            ), 4) if entered else None,
            "status_counts": dict(Counter(item["simulation"]["status"] for item in scenario_records)),
            "executable_entry_label_counts": dict(Counter(item["executable_entry_label"] for item in scenario_records)),
            "survival_label_counts": dict(Counter(item["survival_label"] for item in scenario_records)),
            "rr_bucket_rows": _build_bucket_rows(scenario_records, "rr_bucket", "survival_label"),
            "sector_rows": _build_bucket_rows(scenario_records, "sector_name", "survival_label"),
            "top_collapsed_good_calls": [
                {
                    "session_id": item["session_id"],
                    "session_date": item["session_date"],
                    "symbol": item["symbol"],
                    "sector_name": item["sector_name"],
                    "calendar_phase": item["calendar_phase"],
                    "action": item["action"],
                    "risk_reward_ratio": item["risk_reward_ratio"],
                    "next_open_gap_pct": item["simulation"].get("next_open_gap_pct_vs_optimistic_entry"),
                    "gross_return_pct": item["simulation"].get("gross_return_pct"),
                    "net_return_pct": item["simulation"].get("net_return_pct"),
                    "exit_type": item["simulation"].get("exit_type"),
                }
                for item in top_collapsed
            ],
        }

        for item in scenario_records:
            summary["records"].append({
                "replay_id": item["replay_id"],
                "session_id": item["session_id"],
                "session_date": item["session_date"],
                "symbol": item["symbol"],
                "sector_name": item["sector_name"],
                "calendar_phase": item["calendar_phase"],
                "action": item["action"],
                "setup_type": item["setup_type"],
                "score": item["score"],
                "confidence": item["confidence"],
                "comparison_verdict": item["comparison_verdict"],
                "risk_reward_ratio": item["risk_reward_ratio"],
                "rr_bucket": item["rr_bucket"],
                "scenario_name": item["scenario_name"],
                "ticket_notional_npr": item["ticket_notional_npr"],
                "simulation": item["simulation"],
                "executable_entry_label": item["executable_entry_label"],
                "survival_label": item["survival_label"],
            })

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__replay_cost_realism_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__replay_cost_realism_study_v1.json",
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
    replay_ids = sys.argv[1:] if len(sys.argv) > 1 else _load_default_replay_ids()
    if not replay_ids:
        print("No replay IDs available for cost realism study.")
        sys.exit(1)

    summary, latest_json_path, latest_md_path = build_replay_cost_realism_study(replay_ids)
    print(json.dumps({
        "replay_id_count": summary["replay_id_count"],
        "actionable_case_count": summary["actionable_case_count"],
        "scenario_names": list(summary["scenarios"].keys()),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
