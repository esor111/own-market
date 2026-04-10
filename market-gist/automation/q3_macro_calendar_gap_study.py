"""
Study whether macro/calendar context explains the Q3 2024 vs Q3 2025 bank gap.

Focus:
- 2024 bank cases where the promoted calendar-confidence rule worsened outcomes
- 2024 bank cases where it created defensive churn without quality gain
- 2025 bank cases where it improved outcomes

Usage:
    python q3_macro_calendar_gap_study.py
"""
import json
import os
from collections import Counter
from datetime import datetime

from bank_hostile_window_gap_study import COMPARE_GROUPS, build_rows
from config import VALIDATION_DIR


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _avg(values):
    clean = [float(value) for value in values if isinstance(value, (int, float))]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 3)


def _months_diff(later_year_month, earlier_year_month):
    try:
        later_year, later_month = map(int, str(later_year_month).split("-"))
        earlier_year, earlier_month = map(int, str(earlier_year_month).split("-"))
    except Exception:
        return None
    return (later_year - earlier_year) * 12 + (later_month - earlier_month)


def _top_counts(rows, fn, limit=8):
    counter = Counter(fn(row) for row in rows)
    return [{"label": label, "count": count} for label, count in counter.most_common(limit)]


def _metric_value(row, metric_name, value_key="current_value"):
    metric = (((row.get("macro_snapshot") or {}).get("metrics") or {}).get(metric_name) or {})
    return metric.get(value_key)


def summarize_slice(label, rows):
    return {
        "label": label,
        "count": len(rows),
        "calendar_phase": _top_counts(rows, lambda row: row.get("calendar_phase") or "UNKNOWN", 8),
        "session_month": _top_counts(rows, lambda row: str(row.get("session_date") or "")[:7] or "UNKNOWN", 8),
        "macro_upload_year_month": _top_counts(rows, lambda row: (row.get("macro_snapshot") or {}).get("upload_year_month") or "UNKNOWN", 8),
        "macro_period_end_year_month": _top_counts(rows, lambda row: (row.get("macro_snapshot") or {}).get("period_end_year_month") or "UNKNOWN", 8),
        "avg_macro_upload_lag_months": _avg(
            _months_diff(str(row.get("session_date") or "")[:7], (row.get("macro_snapshot") or {}).get("upload_year_month"))
            for row in rows
        ),
        "avg_macro_period_lag_months": _avg(
            _months_diff(str(row.get("session_date") or "")[:7], (row.get("macro_snapshot") or {}).get("period_end_year_month"))
            for row in rows
        ),
        "avg_interbank_rate_pct": _avg(_metric_value(row, "interbank_rate_pct") for row in rows),
        "avg_remittance_yoy_pct": _avg(((row.get("macro_derived") or {}).get("remittance_yoy_pct")) for row in rows),
        "avg_private_credit_yoy_pct": _avg(_metric_value(row, "claims_private_sector_yoy_pct") for row in rows),
        "avg_private_credit_billion": _avg(_metric_value(row, "private_credit_billion") for row in rows),
        "avg_return_5d_pct": _avg(((row.get("metrics") or {}).get("return_5d_pct")) for row in rows),
        "avg_return_20d_pct": _avg(((row.get("metrics") or {}).get("return_20d_pct")) for row in rows),
        "avg_raw_confidence": _avg(((row.get("decision") or {}).get("confidence")) for row in rows),
        "avg_calibrated_confidence_pct": _avg(((row.get("record") or {}).get("calibrated_confidence_pct")) for row in rows),
    }


def build_findings(slices):
    worsened_2024 = slices["2024_worsened_bank"]
    churn_2024 = slices["2024_defensive_churn_bank"]
    improved_2025 = slices["2025_improved_bank"]
    findings = []

    findings.append(
        "Calendar phase does not explain the Q3 gap by itself: both years are dominated by the same hostile windows (`fiscal_year_end_window`, then smaller `post_fiscal_results_window`)."
    )
    findings.append(
        f"Q3 2024 bank problem cases used much staler macro context than Q3 2025: upload lag `{worsened_2024['avg_macro_upload_lag_months']}` to `{churn_2024['avg_macro_upload_lag_months']}` months vs `{improved_2025['avg_macro_upload_lag_months']}` in 2025 improvements."
    )
    findings.append(
        f"The replay-safe macro snapshots themselves were materially different: 2024 slices saw lower interbank `{worsened_2024['avg_interbank_rate_pct']}` and lower credit growth `{worsened_2024['avg_private_credit_yoy_pct']}`, while 2025 improvements saw higher interbank `{improved_2025['avg_interbank_rate_pct']}` and higher credit growth `{improved_2025['avg_private_credit_yoy_pct']}`."
    )
    findings.append(
        f"Remittance growth moved the other way: 2024 problem slices were paired with much stronger remittance yoy `{worsened_2024['avg_remittance_yoy_pct']}`, while 2025 improvements were paired with lower remittance yoy `{improved_2025['avg_remittance_yoy_pct']}`."
    )
    findings.append(
        "So macro regime differences are real, but the current monthly macro layer is too lagged in early fiscal windows to become a clean direct rule driver. It is better as regime explanation than as immediate action logic."
    )
    return findings


def build_markdown(payload):
    lines = [
        "# Q3 Macro Calendar Gap Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        "",
        "## Main Findings",
    ]
    for finding in payload.get("findings") or []:
        lines.append(f"- {finding}")

    for key in ("2024_worsened_bank", "2024_defensive_churn_bank", "2025_improved_bank"):
        summary = payload["slices"][key]
        lines.extend([
            "",
            f"## {key}",
            f"- count: `{summary['count']}`",
            f"- calendar_phase: `{summary['calendar_phase']}`",
            f"- session_month: `{summary['session_month']}`",
            f"- macro_upload_year_month: `{summary['macro_upload_year_month']}`",
            f"- macro_period_end_year_month: `{summary['macro_period_end_year_month']}`",
            f"- avg_macro_upload_lag_months: `{summary['avg_macro_upload_lag_months']}`",
            f"- avg_macro_period_lag_months: `{summary['avg_macro_period_lag_months']}`",
            f"- avg_interbank_rate_pct: `{summary['avg_interbank_rate_pct']}`",
            f"- avg_remittance_yoy_pct: `{summary['avg_remittance_yoy_pct']}`",
            f"- avg_private_credit_yoy_pct: `{summary['avg_private_credit_yoy_pct']}`",
            f"- avg_private_credit_billion: `{summary['avg_private_credit_billion']}`",
            f"- avg_return_5d_pct: `{summary['avg_return_5d_pct']}`",
            f"- avg_return_20d_pct: `{summary['avg_return_20d_pct']}`",
            f"- avg_raw_confidence: `{summary['avg_raw_confidence']}`",
            f"- avg_calibrated_confidence_pct: `{summary['avg_calibrated_confidence_pct']}`",
        ])
    return "\n".join(lines).strip() + "\n"


def run_study():
    rows_2024 = build_rows(COMPARE_GROUPS["2024_q3"])
    rows_2025 = build_rows(COMPARE_GROUPS["2025_q3"])

    slices = {
        "2024_worsened_bank": summarize_slice(
            "2024_worsened_bank",
            [row for row in rows_2024 if row["outcome_direction"] == "worsened"],
        ),
        "2024_defensive_churn_bank": summarize_slice(
            "2024_defensive_churn_bank",
            [row for row in rows_2024 if row["outcome_direction"] in {"changed_same_quality", "unchanged_quality"}],
        ),
        "2025_improved_bank": summarize_slice(
            "2025_improved_bank",
            [row for row in rows_2025 if row["outcome_direction"] == "improved"],
        ),
    }

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "compare_groups": COMPARE_GROUPS,
        "slices": slices,
    }
    payload["findings"] = build_findings(slices)

    dated_json = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__q3_macro_calendar_gap_study_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__q3_macro_calendar_gap_study_v1.json")
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")
    save_json(dated_json, payload)
    save_json(latest_json, payload)
    markdown = build_markdown(payload)
    save_text(dated_md, markdown)
    save_text(latest_md, markdown)
    return dated_json, latest_json, dated_md, latest_md, payload


def main():
    dated_json, latest_json, dated_md, latest_md, payload = run_study()
    print(json.dumps({
        "dated_json": dated_json,
        "latest_json": latest_json,
        "dated_md": dated_md,
        "latest_md": latest_md,
        "findings": payload["findings"],
    }, indent=2))


if __name__ == "__main__":
    main()
