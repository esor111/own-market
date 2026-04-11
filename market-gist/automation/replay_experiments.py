"""
Run targeted replay experiments and compare their summaries.

Usage:
    python replay_experiments.py 2025-02-01 2025-02-28 EBL NABIL SANIMA JBBL
"""
import json
import os
import sys
from datetime import datetime

from config import VALIDATION_DIR, get_latest_validation_filename
from walk_forward_replay import run_walk_forward_replay
from replay_case_critique import build_replay_case_critiques
from replay_review_summary import build_replay_review_summary


EXPERIMENT_SCENARIOS = [
    {
        "name": "baseline",
        "suffix": "daily_truth_replay_baseline_v1",
        "rules": {},
        "purpose": "Current replay rules as the control case.",
    },
    {
        "name": "rr_watch_1_2",
        "suffix": "daily_truth_replay_rrwatch12_v1",
        "rules": {
            "watch_rr_min": 1.2,
        },
        "purpose": "Require at least 1.2 RR even for watch-only setups.",
    },
    {
        "name": "rr_watch_1_5",
        "suffix": "daily_truth_replay_rrwatch15_v1",
        "rules": {
            "watch_rr_min": 1.5,
        },
        "purpose": "Require stronger RR for actionable watch setups.",
    },
    {
        "name": "strict_buy_gate",
        "suffix": "daily_truth_replay_strictbuy_v1",
        "rules": {
            "buy_rr_min": 1.5,
            "buy_volume_ratio_min": 1.0,
            "buy_score_min": 65,
        },
        "purpose": "Make buy classification stricter without heavily changing watch logic.",
    },
    {
        "name": "easier_improving_watch",
        "suffix": "daily_truth_replay_improvingwatch_v1",
        "rules": {
            "improving_watch_close_position_min": 0.45,
            "watch_score_min": 35,
        },
        "purpose": "Allow improving setups with acceptable liquidity onto the watchlist sooner.",
    },
]


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _scenario_result(result, review_summary, scenario):
    summary = result["summary"]
    return {
        "scenario": scenario["name"],
        "purpose": scenario["purpose"],
        "replay_id": result["replay_id"],
        "rules": result["rules"],
        "case_count": summary["case_count"],
        "action_counts": summary["action_counts"],
        "verdict_counts": summary["comparison_verdict_counts"],
        "average_return_10d_pct": summary["average_return_10d_pct"],
        "top_reason_codes": summary["top_reason_codes"][:5],
        "top_proposals": review_summary.get("top_proposals", [])[:5],
        "high_priority_candidates": review_summary.get("high_priority_candidates", [])[:5],
    }


def run_replay_experiments(start_date, end_date, symbols):
    scenario_results = []

    for scenario in EXPERIMENT_SCENARIOS:
        result = run_walk_forward_replay(
            start_date,
            end_date,
            symbols,
            rule_overrides=scenario["rules"],
            replay_suffix=scenario["suffix"],
        )
        build_replay_case_critiques(result["replay_id"])
        _, _, review_summary = build_replay_review_summary(result["replay_id"])
        scenario_results.append(_scenario_result(result, review_summary, scenario))

    dated_path = os.path.join(
        VALIDATION_DIR,
        "learning_reviews",
        f"{datetime.now().strftime('%Y-%m-%d')}__replay_experiments_v1.json",
    )
    latest_path = os.path.join(
        VALIDATION_DIR,
        "learning_reviews",
        get_latest_validation_filename("replay_experiments_v1"),
    )
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "start_date": start_date,
        "end_date": end_date,
        "symbols": symbols,
        "scenario_count": len(scenario_results),
        "scenarios": scenario_results,
    }
    save_json(dated_path, payload)
    save_json(latest_path, payload)
    return dated_path, latest_path, payload


def main():
    if len(sys.argv) < 4:
        print("Usage: python replay_experiments.py START_DATE END_DATE SYMBOL_OR_LIST ...")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]
    symbols = sys.argv[3:]
    dated_path, latest_path, payload = run_replay_experiments(start_date, end_date, symbols)
    print(json.dumps({
        "dated_path": dated_path,
        "latest_path": latest_path,
        "scenario_names": [item["scenario"] for item in payload["scenarios"]],
    }, indent=2))


if __name__ == "__main__":
    main()
