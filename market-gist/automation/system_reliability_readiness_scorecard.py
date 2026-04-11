"""
Build a compact readiness scorecard for system trust.

This is not a trading-rule script. It answers:
- where the system is strong
- what thresholds are currently passed
- what still blocks higher-trust overall prediction
- what still blocks higher-trust buy-side prediction

Usage:
    python system_reliability_readiness_scorecard.py
"""
import json
import os
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
MONITORING_CYCLE_SUMMARY_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__monitoring_cycle_summary_v1.json")
HOSTILE_MONITOR_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__aggregate_hostile_window_monitor_v1.json")
BUY_SIDE_SCORECARD_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__replay_buy_side_scorecard_v1.json")


PROVISIONAL_THRESHOLDS = {
    "monitoring": {
        "decision_must_be": "keep_frozen",
        "hostile_warning_worsened_max": 0,
        "buy_positive_worsened_max": 0,
        "hostile_emergent_candidates_max": 0,
        "buy_positive_emergent_candidates_max": 0,
    },
    "caution_engine": {
        "triggered_case_count_min": 100,
        "triggered_good_avoid_rate_min": 0.45,
    },
    "actionable_side": {
        "actionable_count_min": 150,
        "good_call_rate_min": 0.40,
        "good_call_survival_rate_min": 0.50,
        "calibrated_vs_observed_gap_pct_max": 15.0,
    },
    "strict_buy_side": {
        "buy_count_min": 20,
        "buy_good_call_rate_min": 0.40,
        "buy_good_call_survival_rate_min": 0.50,
    },
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


def _check(metric_name, actual, threshold, comparator):
    if actual is None:
        return {
            "metric": metric_name,
            "actual": actual,
            "threshold": threshold,
            "status": "fail",
            "comparator": comparator,
        }

    if comparator == "eq":
        passed = actual == threshold
    elif comparator == "lte":
        passed = actual <= threshold
    elif comparator == "gte":
        passed = actual >= threshold
    else:
        raise ValueError(f"Unsupported comparator: {comparator}")

    return {
        "metric": metric_name,
        "actual": actual,
        "threshold": threshold,
        "status": "pass" if passed else "fail",
        "comparator": comparator,
    }


def _section_status(checks):
    return "pass" if all(item["status"] == "pass" for item in checks) else "fail"


def _observed_actionable_hit_rate_pct(scorecard):
    actionable = scorecard.get("actionable") or {}
    rate = actionable.get("good_call_rate")
    if rate is None:
        return None
    return round(rate * 100, 2)


def _calibrated_gap_pct(scorecard):
    actionable = scorecard.get("actionable") or {}
    calibrated = actionable.get("avg_calibrated_confidence_pct")
    observed_pct = _observed_actionable_hit_rate_pct(scorecard)
    if calibrated is None or observed_pct is None:
        return None
    return round(abs(calibrated - observed_pct), 4)


def render_markdown(payload):
    lines = [
        "# System Reliability Readiness Scorecard",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- overall_prediction_readiness: `{payload['overall_prediction_readiness']}`",
        f"- buy_side_readiness: `{payload['buy_side_readiness']}`",
        "",
        "## Section Status",
        "",
        f"- monitoring_discipline: `{payload['sections']['monitoring_discipline']['status']}`",
        f"- caution_engine: `{payload['sections']['caution_engine']['status']}`",
        f"- actionable_side: `{payload['sections']['actionable_side']['status']}`",
        f"- strict_buy_side: `{payload['sections']['strict_buy_side']['status']}`",
        "",
        "## Monitoring Discipline Checks",
        "",
    ]
    for row in payload["sections"]["monitoring_discipline"]["checks"]:
        lines.append(
            f"- `{row['metric']}`: actual `{row['actual']}`, threshold `{row['threshold']}`, status `{row['status']}`"
        )

    lines.extend(["", "## Caution Engine Checks", ""])
    for row in payload["sections"]["caution_engine"]["checks"]:
        lines.append(
            f"- `{row['metric']}`: actual `{row['actual']}`, threshold `{row['threshold']}`, status `{row['status']}`"
        )

    lines.extend(["", "## Actionable-Side Checks", ""])
    for row in payload["sections"]["actionable_side"]["checks"]:
        lines.append(
            f"- `{row['metric']}`: actual `{row['actual']}`, threshold `{row['threshold']}`, status `{row['status']}`"
        )

    lines.extend(["", "## Strict Buy-Side Checks", ""])
    for row in payload["sections"]["strict_buy_side"]["checks"]:
        lines.append(
            f"- `{row['metric']}`: actual `{row['actual']}`, threshold `{row['threshold']}`, status `{row['status']}`"
        )

    lines.extend(["", "## Main Blockers", ""])
    for blocker in payload.get("main_blockers") or []:
        lines.append(f"- {blocker}")

    lines.extend(["", "## Next Steps", ""])
    for step in payload.get("next_steps") or []:
        lines.append(f"- {step}")

    return "\n".join(lines) + "\n"


def build_scorecard():
    monitoring = load_json(MONITORING_CYCLE_SUMMARY_PATH)
    hostile_monitor = load_json(HOSTILE_MONITOR_PATH)
    buy_scorecard = load_json(BUY_SIDE_SCORECARD_PATH)

    triggered_case_count = hostile_monitor.get("triggered_case_count")
    triggered_good_avoid_count = hostile_monitor.get("triggered_good_avoid_count")
    triggered_good_avoid_rate = None
    if triggered_case_count:
        triggered_good_avoid_rate = round(triggered_good_avoid_count / triggered_case_count, 4)

    actionable = buy_scorecard.get("actionable") or {}
    strict_buy = buy_scorecard.get("buy") or {}
    actionable_gap_pct = _calibrated_gap_pct(buy_scorecard)

    monitoring_checks = [
        _check("decision", monitoring.get("decision"), PROVISIONAL_THRESHOLDS["monitoring"]["decision_must_be"], "eq"),
        _check("hostile_warning_worsened", monitoring.get("hostile_warning_worsened"), PROVISIONAL_THRESHOLDS["monitoring"]["hostile_warning_worsened_max"], "lte"),
        _check("buy_positive_worsened", monitoring.get("buy_positive_worsened"), PROVISIONAL_THRESHOLDS["monitoring"]["buy_positive_worsened_max"], "lte"),
        _check("hostile_emergent_candidates", monitoring.get("hostile_emergent_candidates"), PROVISIONAL_THRESHOLDS["monitoring"]["hostile_emergent_candidates_max"], "lte"),
        _check("buy_positive_emergent_candidates", monitoring.get("buy_positive_emergent_candidates"), PROVISIONAL_THRESHOLDS["monitoring"]["buy_positive_emergent_candidates_max"], "lte"),
    ]
    caution_checks = [
        _check("triggered_case_count", triggered_case_count, PROVISIONAL_THRESHOLDS["caution_engine"]["triggered_case_count_min"], "gte"),
        _check("triggered_good_avoid_rate", triggered_good_avoid_rate, PROVISIONAL_THRESHOLDS["caution_engine"]["triggered_good_avoid_rate_min"], "gte"),
    ]
    actionable_checks = [
        _check("actionable_count", actionable.get("count"), PROVISIONAL_THRESHOLDS["actionable_side"]["actionable_count_min"], "gte"),
        _check("actionable_good_call_rate", actionable.get("good_call_rate"), PROVISIONAL_THRESHOLDS["actionable_side"]["good_call_rate_min"], "gte"),
        _check("actionable_good_call_survival_rate", actionable.get("good_call_survival_rate"), PROVISIONAL_THRESHOLDS["actionable_side"]["good_call_survival_rate_min"], "gte"),
        _check("actionable_calibrated_vs_observed_gap_pct", actionable_gap_pct, PROVISIONAL_THRESHOLDS["actionable_side"]["calibrated_vs_observed_gap_pct_max"], "lte"),
    ]
    strict_buy_checks = [
        _check("buy_count", strict_buy.get("count"), PROVISIONAL_THRESHOLDS["strict_buy_side"]["buy_count_min"], "gte"),
        _check("buy_good_call_rate", strict_buy.get("good_call_rate"), PROVISIONAL_THRESHOLDS["strict_buy_side"]["buy_good_call_rate_min"], "gte"),
        _check("buy_good_call_survival_rate", strict_buy.get("good_call_survival_rate"), PROVISIONAL_THRESHOLDS["strict_buy_side"]["buy_good_call_survival_rate_min"], "gte"),
    ]

    sections = {
        "monitoring_discipline": {
            "status": _section_status(monitoring_checks),
            "checks": monitoring_checks,
        },
        "caution_engine": {
            "status": _section_status(caution_checks),
            "checks": caution_checks,
        },
        "actionable_side": {
            "status": _section_status(actionable_checks),
            "checks": actionable_checks,
        },
        "strict_buy_side": {
            "status": _section_status(strict_buy_checks),
            "checks": strict_buy_checks,
        },
    }

    overall_prediction_readiness = "not_ready"
    if (
        sections["monitoring_discipline"]["status"] == "pass"
        and sections["caution_engine"]["status"] == "pass"
        and sections["actionable_side"]["status"] == "pass"
        and sections["strict_buy_side"]["status"] == "pass"
    ):
        overall_prediction_readiness = "high_trust_ready"

    buy_side_readiness = "not_ready"
    if sections["actionable_side"]["status"] == "pass" and sections["strict_buy_side"]["status"] == "pass":
        buy_side_readiness = "high_trust_ready"
    elif sections["actionable_side"]["status"] == "pass":
        buy_side_readiness = "moderate_only"

    main_blockers = []
    if sections["actionable_side"]["status"] != "pass":
        main_blockers.append("actionable-side hit rate and next-open survival are still below the provisional high-trust thresholds")
    if sections["strict_buy_side"]["status"] != "pass":
        main_blockers.append("strict buy side does not have enough clean sample or enough observed success to be trusted")
    if sections["caution_engine"]["status"] != "pass":
        main_blockers.append("caution engine has not yet met the provisional trigger-quality thresholds")

    next_steps = [
        "keep the champion frozen",
        "continue running refresh_monitoring_stack.py on new replay refreshes",
        "use the buy-side watchlist to wait for a repeated positive slice before opening buy-side research",
    ]
    if sections["actionable_side"]["status"] != "pass" or sections["strict_buy_side"]["status"] != "pass":
        next_steps.append("treat buy-side improvement as the main open trust gap, not caution-side rule invention")

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "provisional_thresholds": PROVISIONAL_THRESHOLDS,
        "overall_prediction_readiness": overall_prediction_readiness,
        "buy_side_readiness": buy_side_readiness,
        "sections": sections,
        "main_blockers": main_blockers,
        "next_steps": next_steps,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__system_reliability_readiness_scorecard_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__system_reliability_readiness_scorecard_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__system_reliability_readiness_scorecard_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__system_reliability_readiness_scorecard_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_scorecard()
    print(json.dumps({
        "overall_prediction_readiness": payload["overall_prediction_readiness"],
        "buy_side_readiness": payload["buy_side_readiness"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
