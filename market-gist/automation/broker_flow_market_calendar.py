"""
Lightweight market-day context helpers for the broker-flow lane.

This keeps the broker ledger honest about empty days:
- weekend/non-trading weekday checks
- optional local holiday overrides
- best-effort official NEPSE holiday lookup
"""
from __future__ import annotations

import html
import json
import re
import ssl
import urllib.error
import urllib.request
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from config import BASE_DIR
from nepse_trading_calendar import is_trading_weekday


USER_AGENT = "Mozilla/5.0 (compatible; MarketGistBot/1.0)"
UNVERIFIED_SSL_CONTEXT = ssl._create_unverified_context()
BROKER_LEDGER_ROOT = Path(BASE_DIR) / "broker_flow_ledger"
CALENDAR_OVERRIDE_DIR = BROKER_LEDGER_ROOT / "calendar_overrides"


def _clean_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_iso_date(value: str) -> datetime.date:
    return datetime.strptime(str(value or "").strip(), "%Y-%m-%d").date()


def is_nepal_trading_weekday(value: str) -> bool:
    return is_trading_weekday(parse_iso_date(value))


def _override_path(year: int) -> Path:
    return CALENDAR_OVERRIDE_DIR / f"{year}.json"


@lru_cache(maxsize=8)
def _load_override_rows(year: int) -> Dict[str, object]:
    path = _override_path(year)
    if not path.exists():
        return {"status": "missing", "rows": [], "path": str(path)}

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:
        return {"status": "invalid", "rows": [], "path": str(path), "error": str(exc)}

    rows = payload if isinstance(payload, list) else payload.get("rows", [])
    normalized: List[Dict[str, str]] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        event_date = str(row.get("event_date") or row.get("date") or "").strip()[:10]
        title = _clean_text(str(row.get("title") or row.get("name") or ""))
        if event_date:
            normalized.append({"event_date": event_date, "title": title})
    return {"status": "ok", "rows": normalized, "path": str(path)}


@lru_cache(maxsize=8)
def _load_official_rows(year: int) -> Dict[str, object]:
    url = f"https://www.nepalstock.com/api/nots/holiday/list?year={year}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30, context=UNVERIFIED_SSL_CONTEXT) as response:
            payload = json.loads(response.read().decode("utf-8", errors="ignore"))
    except urllib.error.HTTPError as exc:
        return {
            "status": "unavailable",
            "rows": [],
            "url": url,
            "error": f"http_{exc.code}",
        }
    except Exception as exc:
        return {
            "status": "unavailable",
            "rows": [],
            "url": url,
            "error": exc.__class__.__name__,
        }

    normalized: List[Dict[str, str]] = []
    for item in payload or []:
        if not isinstance(item, dict):
            continue
        event_date = _clean_text(str(item.get("holidayDate") or ""))[:10]
        title = _clean_text(str(item.get("holidayDescription") or ""))
        if event_date:
            normalized.append({"event_date": event_date, "title": title})
    return {"status": "ok", "rows": normalized, "url": url, "error": None}


def get_market_day_context(run_date: str) -> Dict[str, object]:
    normalized_date = str(run_date or "").strip()[:10]
    parsed_date = parse_iso_date(normalized_date)
    weekday_candidate = is_trading_weekday(parsed_date)
    override_payload = _load_override_rows(parsed_date.year)
    official_payload = _load_official_rows(parsed_date.year)

    override_match = next(
        (row for row in (override_payload.get("rows") or []) if row.get("event_date") == normalized_date),
        None,
    )
    official_match = next(
        (row for row in (official_payload.get("rows") or []) if row.get("event_date") == normalized_date),
        None,
    )

    if override_match:
        holiday_title = override_match.get("title")
        holiday_validation_status = "local_override"
        is_official_holiday = True
        expected_market_session = False
        holiday_source = override_payload.get("path")
    elif official_payload.get("status") == "ok":
        holiday_title = (official_match or {}).get("title")
        holiday_validation_status = "official_api"
        is_official_holiday = bool(official_match)
        expected_market_session = weekday_candidate and not is_official_holiday
        holiday_source = official_payload.get("url")
    else:
        holiday_title = None
        holiday_validation_status = "weekday_only_unverified"
        is_official_holiday = None
        expected_market_session = weekday_candidate
        holiday_source = official_payload.get("url")

    return {
        "run_date": normalized_date,
        "weekday_name": parsed_date.strftime("%A"),
        "is_nepal_trading_weekday": weekday_candidate,
        "holiday_validation_status": holiday_validation_status,
        "is_official_holiday": is_official_holiday,
        "holiday_title": holiday_title,
        "holiday_source": holiday_source,
        "official_holiday_fetch_error": official_payload.get("error"),
        "override_status": override_payload.get("status"),
        "expected_market_session": expected_market_session,
    }


def classify_empty_day_reason(market_day_context: Dict[str, object]) -> str:
    if not market_day_context.get("is_nepal_trading_weekday"):
        return "non_trading_weekday"
    if market_day_context.get("is_official_holiday") is True:
        return "official_holiday_no_market"
    if market_day_context.get("holiday_validation_status") == "weekday_only_unverified":
        return "empty_weekday_unverified"
    return "unexpected_empty_trading_day"
