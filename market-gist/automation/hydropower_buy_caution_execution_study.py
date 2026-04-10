"""
Research-only execution study for changed cases from the hydropower hostile-window
buy caution challenger.

Usage:
    python hydropower_buy_caution_execution_study.py
    python hydropower_buy_caution_execution_study.py VALIDATION_SUMMARY_JSON
"""
import json
import os
import sys
from datetime import datetime

from config import REPLAYS_DIR, VALIDATION_DIR
from replay_cost_realism_study import _simulate_case, load_json
from replay_next_open_tradability_study import DEFAULT_TICKET_NOTIONAL_NPR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DEFAULT_VALIDATION_SUMMARY_JSON = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__hydrobuystudy_hydrobuycaution_v1__replay_challenger_validation_summary_v1.json",
)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _case_paths(replay_id, session_date, symbol):
    symbol_root = os.path.join(REPLAYS_DIR, replay_id, "sessions", session_date, symbol)
    return {
        "decision_path": os.path.join(symbol_root, "derived", f"{session_date}__{symbol}__replay_decision_v1.json"),
        "frozen_case_path": os.path.join(symbol_root, "normalized", f"{session_date}__{symbol}__frozen_case_v1.json"),
        "future_bars_path": os.path.join(symbol_root, "raw", f"{session_date}__{symbol}__future_bars.json"),
    }


def _execution_interpretation(simulation):
    status = simulation.get("status")
    if status == "skip_gap_below_stop":
        return "demotion_avoids_immediate_gap_down_damage"
    if status == "entered":
        gross_return = simulation.get("gross_return_pct")
        if gross_return is not None and gross_return < 0:
            return "demotion_avoids_losing_trade"
        if gross_return is not None and gross_return > 0:
            return "demotion_skips_profitable_trade"
        return "demotion_changes_label_only"
    if status == "skip_gap_above_first_target":
        return "demotion_skips_untradeable_gap_up"
    return "demotion_effect_unclear"


def _render_markdown(payload):
    lines = [
        "# Hydropower Buy Caution Execution Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- changed_case_count: `{payload['changed_case_count']}`",
        f"- source_validation_summary: `{payload['source_validation_summary']}`",
        "",
        "## Execution Interpretation Counts",
        "",
    ]
    for key, value in payload.get("execution_interpretation_counts", {}).items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend([
        "",
        "## Next-Open Status Counts",
        "",
    ])
    for key, value in payload.get("next_open_status_counts", {}).items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend([
        "",
        "## Changed Cases",
        "",
    ])
    for row in payload.get("rows", []):
        lines.extend([
            f"### `{row['session_date']} {row['symbol']}`",
            f"- replay_id: `{row['replay_id']}`",
            f"- champion_action: `{row['champion_action']}`",
            f"- challenger_action: `{row['challenger_action']}`",
            f"- champion_verdict: `{row['champion_verdict']}`",
            f"- challenger_verdict: `{row['challenger_verdict']}`",
            f"- next_open_status: `{row['next_open_status']}`",
            f"- execution_interpretation: `{row['execution_interpretation']}`",
            f"- next_open_gap_pct: `{row['next_open_gap_pct']}`",
            f"- recomputed_rr_at_entry: `{row['recomputed_rr_at_entry']}`",
            f"- gross_return_pct: `{row['gross_return_pct']}`",
            f"- net_return_pct: `{row['net_return_pct']}`",
            f"- return_20d_pct: `{row['return_20d_pct']}`",
            f"- close_position_20d: `{row['close_position_20d']}`",
            "",
        ])
    return "\n".join(lines) + "\n"


def build_hydropower_buy_caution_execution_study(validation_summary_json):
    validation_summary = load_json(validation_summary_json)
    compare_paths = validation_summary.get("source_compare_paths") or []
    compare_lookup = {}
    for path in compare_paths:
        payload = load_json(path)
        compare_lookup[payload.get("challenger_replay_id")] = payload

    rows = []
    for changed_case in validation_summary.get("changed_cases") or []:
        month_label = changed_case.get("month_label")
        challenger_replay_id = None
        for replay_id in compare_lookup:
            if month_label and month_label in replay_id:
                challenger_replay_id = replay_id
                break
        if not challenger_replay_id:
            continue

        session_date = changed_case["session_date"]
        symbol = changed_case["symbol"]
        paths = _case_paths(challenger_replay_id, session_date, symbol)
        decision = load_json(paths["decision_path"])
        frozen_case = load_json(paths["frozen_case_path"])
        future_payload = load_json(paths["future_bars_path"])
        future_bars = future_payload.get("future_bars") or []
        simulation = _simulate_case(decision, future_bars, DEFAULT_TICKET_NOTIONAL_NPR)
        metrics = frozen_case.get("metrics") or {}

        rows.append({
            "replay_id": challenger_replay_id,
            "session_date": session_date,
            "symbol": symbol,
            "champion_action": changed_case.get("champion_action"),
            "challenger_action": changed_case.get("challenger_action"),
            "champion_verdict": changed_case.get("champion_verdict"),
            "challenger_verdict": changed_case.get("challenger_verdict"),
            "next_open_status": simulation.get("status"),
            "execution_interpretation": _execution_interpretation(simulation),
            "next_open_gap_pct": simulation.get("next_open_gap_pct_vs_optimistic_entry"),
            "recomputed_rr_at_entry": simulation.get("recomputed_rr_at_entry"),
            "gross_return_pct": simulation.get("gross_return_pct"),
            "net_return_pct": simulation.get("net_return_pct"),
            "return_20d_pct": metrics.get("return_20d_pct"),
            "close_position_20d": metrics.get("close_position_20d"),
        })

    next_open_status_counts = {}
    execution_interpretation_counts = {}
    for row in rows:
        next_open_status_counts[row["next_open_status"]] = next_open_status_counts.get(row["next_open_status"], 0) + 1
        execution_interpretation_counts[row["execution_interpretation"]] = execution_interpretation_counts.get(row["execution_interpretation"], 0) + 1

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_validation_summary": validation_summary_json,
        "changed_case_count": len(rows),
        "next_open_status_counts": next_open_status_counts,
        "execution_interpretation_counts": execution_interpretation_counts,
        "rows": rows,
    }

    dated_json = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__hydropower_buy_caution_execution_study_v1.json",
    )
    latest_json = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__hydropower_buy_caution_execution_study_v1.json",
    )
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")
    markdown = _render_markdown(payload)
    save_json(dated_json, payload)
    save_json(latest_json, payload)
    save_text(dated_md, markdown)
    save_text(latest_md, markdown)
    return payload, latest_json, latest_md


def main():
    validation_summary_json = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VALIDATION_SUMMARY_JSON
    payload, latest_json, latest_md = build_hydropower_buy_caution_execution_study(validation_summary_json)
    print(json.dumps({
        "changed_case_count": payload["changed_case_count"],
        "next_open_status_counts": payload["next_open_status_counts"],
        "execution_interpretation_counts": payload["execution_interpretation_counts"],
        "latest_json": latest_json,
        "latest_md": latest_md,
    }, indent=2))


if __name__ == "__main__":
    main()
