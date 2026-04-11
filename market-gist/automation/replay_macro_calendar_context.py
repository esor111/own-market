"""
Helpers for loading replay-safe NRB macro context and deterministic calendar flags.
"""
import os
from functools import lru_cache
from glob import glob

from config import VALIDATION_DIR, load_json_file


BACKFILL_DIR = os.path.join(VALIDATION_DIR, "historical_context_backfills")


def _parse_year_month(value):
    text = str(value or "")
    if len(text) != 7 or text[4] != "-":
        return None
    try:
        year = int(text[:4])
        month = int(text[5:7])
    except ValueError:
        return None
    if month < 1 or month > 12:
        return None
    return year, month


def _month_diff(later_ym, earlier_ym):
    later = _parse_year_month(later_ym)
    earlier = _parse_year_month(earlier_ym)
    if later is None or earlier is None:
        return None
    later_year, later_month = later
    earlier_year, earlier_month = earlier
    return (later_year - earlier_year) * 12 + (later_month - earlier_month)


@lru_cache(maxsize=1)
def _load_all_macro_records():
    records = []
    paths = sorted(glob(os.path.join(BACKFILL_DIR, "latest__*__nrb_macro_context_backfill_v1.json")))
    for path in paths:
        payload = load_json_file(path, {})
        for item in (payload.get("records") or []):
            if item.get("period_end_year_month") and item.get("upload_year_month"):
                records.append(item)
    records.sort(
        key=lambda item: (
            str(item.get("upload_year_month") or ""),
            str(item.get("period_end_year_month") or ""),
            str(item.get("subcategory") or ""),
        )
    )
    return records


def _calendar_flags(session_date):
    month = int(str(session_date)[5:7])
    labels = []
    if month == 1:
        labels.append("poush_results_window")
    if month == 6:
        labels.append("pre_fiscal_positioning_window")
    if month == 7:
        labels.append("fiscal_year_end_window")
    if month == 8:
        labels.append("post_fiscal_results_window")
    if month in {9, 10}:
        labels.append("dividend_positioning_window")
    if month in {9, 10, 11}:
        labels.append("book_closure_window")
    return {
        "session_year_month": str(session_date)[:7],
        "calendar_month": month,
        "phase_labels": labels,
        "is_poush_results_window": month == 1,
        "is_pre_fiscal_positioning_window": month == 6,
        "is_fiscal_year_end_window": month == 7,
        "is_post_fiscal_results_window": month == 8,
        "is_dividend_positioning_window": month in {9, 10},
        "is_book_closure_window": month in {9, 10, 11},
    }


def load_replay_macro_calendar_context(session_date):
    session_year_month = str(session_date)[:7]
    records = _load_all_macro_records()
    eligible = [
        item for item in records
        if str(item.get("upload_year_month") or "") <= session_year_month
    ]

    latest_snapshot = eligible[-1] if eligible else None
    metrics = (latest_snapshot or {}).get("metrics") or {}
    derived_metrics = (latest_snapshot or {}).get("derived_metrics") or {}

    return {
        "calendar_flags": _calendar_flags(session_date),
        "has_macro_snapshot": latest_snapshot is not None,
        "latest_available_snapshot": {
            "fy_token": (latest_snapshot or {}).get("fy_token"),
            "label": (latest_snapshot or {}).get("label"),
            "subcategory": (latest_snapshot or {}).get("subcategory"),
            "period_end_year_month": (latest_snapshot or {}).get("period_end_year_month"),
            "upload_year_month": (latest_snapshot or {}).get("upload_year_month"),
            "availability_lag_months": _month_diff(
                (latest_snapshot or {}).get("upload_year_month"),
                (latest_snapshot or {}).get("period_end_year_month"),
            ) if latest_snapshot else None,
            "metrics": metrics,
            "derived_metrics": derived_metrics,
            "asset_url": (latest_snapshot or {}).get("asset_url"),
        },
        "notes": [
            "calendar flags are descriptive only and are not action rules",
            "macro snapshot uses the latest record whose upload month is not after the session month",
            "macro context is replay-safe but still context-only until diagnostics prove value",
        ],
    }
