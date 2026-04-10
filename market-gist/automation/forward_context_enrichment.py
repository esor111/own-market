"""
Helpers for forward-shadow context enrichment.

This module keeps two high-ROI additions in one place:
- official-ish NRB macro snapshot loading for the current session
- automatic manual_context overlay discovery for live forward runs
- best-effort secondary-site enrichments for event timing and market breadth
"""
import json
import os
from glob import glob
from io import StringIO

import pandas as pd
import requests

from config import BASE_DIR, VALIDATION_DIR, load_json_file, normalize_timeframe_token


BACKFILL_DIR = os.path.join(VALIDATION_DIR, "historical_context_backfills")
MACRO_CONTEXT_PATH = os.path.join(BASE_DIR, "data", "macro_context.json")
MANUAL_CONTEXT_DIR = os.path.join(
    BASE_DIR,
    "shadow_book",
    "commercial_banks_pilot",
    "manual_context",
)
DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; market-gist-forward-context/1.0)"}
DEFAULT_TIMEOUT = 45
MEROLAGANI_LATEST_MARKET_URL = "https://merolagani.com/LatestMarket.aspx"
SHARESANSAR_COMPANY_URL = "https://www.sharesansar.com/company/{symbol}"


def _save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _parse_year_month(value):
    text = str(value or "")
    if len(text) != 7 or text[4] != "-":
        return None
    try:
        year = int(text[:4])
        month = int(text[5:7])
    except ValueError:
        return None
    if not 1 <= month <= 12:
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


def _current_metric(metric_map, key):
    values = (metric_map or {}).get(key) or {}
    return values.get("current_value")


def _load_manual_macro_context():
    payload = load_json_file(MACRO_CONTEXT_PATH, {})
    return payload if isinstance(payload, dict) else {}


def _coerce_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _fetch_html(url):
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.text


def _latest_backfill_paths():
    return sorted(glob(os.path.join(BACKFILL_DIR, "latest__*__nrb_macro_context_backfill_v1.json")))


def _load_all_backfill_records():
    records = []
    for path in _latest_backfill_paths():
        payload = load_json_file(path, {})
        for item in payload.get("records") or []:
            if item.get("upload_year_month") and item.get("period_end_year_month"):
                records.append(item)
    records.sort(
        key=lambda item: (
            str(item.get("upload_year_month") or ""),
            str(item.get("period_end_year_month") or ""),
            str(item.get("subcategory") or ""),
        )
    )
    return records


def ensure_nrb_macro_backfill_year(target_year):
    """
    Ensure a latest NRB macro backfill file exists for the given Gregorian year.

    Reuses the replay-side builder instead of inventing a new live-only parser.
    """
    latest_path = os.path.join(BACKFILL_DIR, f"latest__{target_year}__nrb_macro_context_backfill_v1.json")
    if os.path.isfile(latest_path):
        return latest_path

    try:
        from backfill_nrb_macro_context import build_nrb_macro_backfill
    except Exception:
        return None

    try:
        summary = build_nrb_macro_backfill(int(target_year))
    except Exception:
        return None

    _save_json(latest_path, summary)
    return latest_path if os.path.isfile(latest_path) else None


def load_live_nrb_macro_snapshot(run_date):
    """
    Load the latest available NRB macro snapshot for a live session date.

    Uses replay-safe monthly backfills if available, and will try to build the
    current year on first use if it is missing.
    """
    manual_macro = _load_manual_macro_context()

    try:
        target_year = int(str(run_date)[:4])
    except ValueError:
        return {
            "available": False,
            "run_date": run_date,
            "latest_snapshot": {},
            "manual_macro_context": manual_macro,
            "notes": ["invalid run_date; could not derive NRB macro snapshot"],
        }

    ensure_nrb_macro_backfill_year(target_year)

    session_year_month = str(run_date)[:7]
    records = _load_all_backfill_records()
    eligible = [
        item for item in records
        if str(item.get("upload_year_month") or "") <= session_year_month
    ]
    latest = eligible[-1] if eligible else None

    metrics = (latest or {}).get("metrics") or {}
    derived = (latest or {}).get("derived_metrics") or {}

    snapshot = {
        "available": latest is not None,
        "run_date": run_date,
        "latest_snapshot": {
            "label": (latest or {}).get("label"),
            "subcategory": (latest or {}).get("subcategory"),
            "period_end_year_month": (latest or {}).get("period_end_year_month"),
            "upload_year_month": (latest or {}).get("upload_year_month"),
            "availability_lag_months": _month_diff(
                (latest or {}).get("upload_year_month"),
                (latest or {}).get("period_end_year_month"),
            ) if latest else None,
            "age_months_vs_session": _month_diff(
                session_year_month,
                (latest or {}).get("upload_year_month"),
            ) if latest else None,
            "interbank_rate_pct": _current_metric(metrics, "interbank_rate_pct"),
            "remittance_billion": _current_metric(metrics, "remittance_billion"),
            "remittance_yoy_pct": derived.get("remittance_yoy_pct"),
            "private_credit_billion": _current_metric(metrics, "private_credit_billion"),
            "claims_private_sector_yoy_pct": _current_metric(metrics, "claims_private_sector_yoy_pct"),
            "asset_url": (latest or {}).get("asset_url"),
        },
        "manual_macro_context": manual_macro,
        "notes": [],
    }

    if latest is None:
        snapshot["notes"].append("no eligible NRB macro backfill record found for this session month")
    if manual_macro:
        snapshot["notes"].append("manual macro_context.json is also available and should be treated as a human override/context layer")

    return snapshot


def build_nrb_macro_lines(snapshot, indent=""):
    """
    Return concise human-readable lines for the NRB macro snapshot.
    """
    lines = []
    latest = (snapshot or {}).get("latest_snapshot") or {}
    manual = (snapshot or {}).get("manual_macro_context") or {}

    if (snapshot or {}).get("available"):
        lines.extend([
            f"{indent}- Automated NRB snapshot month: {latest.get('period_end_year_month') or 'unknown'}",
            f"{indent}- NRB availability month: {latest.get('upload_year_month') or 'unknown'}",
            f"{indent}- Interbank rate pct: {latest.get('interbank_rate_pct') if latest.get('interbank_rate_pct') is not None else 'unknown'}",
            f"{indent}- Remittance YoY pct: {latest.get('remittance_yoy_pct') if latest.get('remittance_yoy_pct') is not None else 'unknown'}",
            f"{indent}- Private credit YoY pct: {latest.get('claims_private_sector_yoy_pct') if latest.get('claims_private_sector_yoy_pct') is not None else 'unknown'}",
            f"{indent}- Private credit amount (billion): {latest.get('private_credit_billion') if latest.get('private_credit_billion') is not None else 'unknown'}",
        ])
        if latest.get("asset_url"):
            lines.append(f"{indent}- NRB source asset: {latest['asset_url']}")
    else:
        lines.append(f"{indent}- Automated NRB macro snapshot: unavailable")

    if manual:
        for key in (
            "nrb_policy",
            "interbank_rate",
            "banking_earnings",
            "remittance_trend",
            "credit_growth",
            "market_cycle_position",
            "nepse_vs_key_levels",
            "notes",
        ):
            value = manual.get(key)
            if value:
                label = key.replace("_", " ").title()
                lines.append(f"{indent}- Manual {label}: {value}")

    return lines


def load_merolagani_market_breadth():
    """
    Load broad market participation and turnover context from Merolagani.

    This is a convenience source, not an official truth source.
    """
    result = {
        "available": False,
        "source_url": MEROLAGANI_LATEST_MARKET_URL,
        "advance_count": None,
        "decline_count": None,
        "unchanged_count": None,
        "breadth_ratio": None,
        "breadth_tone": "unknown",
        "top_turnover": [],
        "top_sectors_by_turnover": [],
        "error": None,
    }

    try:
        html = _fetch_html(MEROLAGANI_LATEST_MARKET_URL)
        tables = pd.read_html(StringIO(html))
    except Exception as exc:
        result["error"] = str(exc)
        return result

    try:
        latest_market = tables[0] if len(tables) >= 1 else None
        top_turnover = tables[3] if len(tables) >= 4 else None
        sector_turnover = tables[4] if len(tables) >= 5 else None

        if latest_market is not None and "% Change" in latest_market.columns:
            changes = pd.to_numeric(latest_market["% Change"], errors="coerce")
            advance_count = int((changes > 0).sum())
            decline_count = int((changes < 0).sum())
            unchanged_count = int((changes == 0).sum())
            breadth_ratio = round(advance_count / max(decline_count, 1), 3)
            if advance_count >= decline_count * 1.5:
                breadth_tone = "broad_positive"
            elif decline_count >= advance_count * 1.5:
                breadth_tone = "broad_negative"
            else:
                breadth_tone = "mixed"
            result.update({
                "advance_count": advance_count,
                "decline_count": decline_count,
                "unchanged_count": unchanged_count,
                "breadth_ratio": breadth_ratio,
                "breadth_tone": breadth_tone,
            })

        if top_turnover is not None:
            rows = []
            for _, row in top_turnover.head(5).iterrows():
                rows.append({
                    "symbol": str(row.get("Symbol") or "").strip(),
                    "turnover": _coerce_float(row.get("Turnover")),
                    "ltp": _coerce_float(row.get("LTP")),
                })
            result["top_turnover"] = rows

        if sector_turnover is not None:
            rows = []
            for _, row in sector_turnover.head(5).iterrows():
                rows.append({
                    "sector": str(row.get("Sector") or "").strip(),
                    "turnover": _coerce_float(row.get("Turnover")),
                })
            result["top_sectors_by_turnover"] = rows

        result["available"] = True
        return result
    except Exception as exc:
        result["error"] = str(exc)
        return result


def _table_to_key_value_map(df):
    mapping = {}
    for _, row in df.iterrows():
        if len(row) < 2:
            continue
        key = str(row.iloc[0]).strip()
        value = str(row.iloc[1]).strip()
        if key:
            mapping[key] = value
    return mapping


def load_sharesansar_company_event_timing(symbol):
    """
    Load best-effort event timing context from a ShareSansar company page.

    This is a convenience / scan source for timing, not the official truth layer.
    """
    symbol = str(symbol).lower()
    url = SHARESANSAR_COMPANY_URL.format(symbol=symbol)
    result = {
        "available": False,
        "source_url": url,
        "latest_dividend": {},
        "right_share": {},
        "notes": [],
        "error": None,
    }

    try:
        html = _fetch_html(url)
        tables = pd.read_html(StringIO(html))
    except Exception as exc:
        result["error"] = str(exc)
        return result

    try:
        if len(tables) >= 1:
            dividend_map = _table_to_key_value_map(tables[0])
            result["latest_dividend"] = {
                "bonus_share_pct": dividend_map.get("Bonus Share"),
                "cash_dividend_pct": dividend_map.get("Cash Dividend"),
                "year": dividend_map.get("Year"),
                "book_close_date": dividend_map.get("Book Close Date"),
            }
            if any(result["latest_dividend"].values()):
                result["notes"].append("latest dividend block found on ShareSansar company page")

        if len(tables) >= 2:
            right_share_map = _table_to_key_value_map(tables[1])
            result["right_share"] = {
                "ratio": right_share_map.get("Ratio"),
                "units": right_share_map.get("Units"),
                "book_close_date": right_share_map.get("Book Close Date"),
                "opening_closing_date": right_share_map.get("Opening Date / Closing Date"),
            }
            if any(result["right_share"].values()):
                result["notes"].append("right-share timing block found on ShareSansar company page")

        result["available"] = bool(result["latest_dividend"] or result["right_share"])
        return result
    except Exception as exc:
        result["error"] = str(exc)
        return result


def manual_context_path(symbol, run_date, timeframe):
    filename = f"{run_date}__{str(symbol).upper()}__{normalize_timeframe_token(timeframe)}__manual_context_v1.json"
    return os.path.join(MANUAL_CONTEXT_DIR, filename)


def load_manual_context_overlay(symbol, run_date, timeframe):
    path = manual_context_path(symbol, run_date, timeframe)
    if not os.path.isfile(path):
        return {
            "available": False,
            "path": path,
            "payload": {},
            "error": None,
        }

    try:
        payload = load_json_file(path, {})
    except Exception as exc:
        return {
            "available": False,
            "path": path,
            "payload": {},
            "error": str(exc),
        }

    if not isinstance(payload, dict):
        return {
            "available": False,
            "path": path,
            "payload": {},
            "error": "manual context file is not a JSON object",
        }

    return {
        "available": True,
        "path": path,
        "payload": payload,
        "error": None,
    }


def format_manual_context_block(overlay, heading="15. Manual Context Overlay (auto-loaded)"):
    if not (overlay or {}).get("available"):
        return ""

    payload = (overlay or {}).get("payload") or {}
    lines = [
        heading,
        f"- Summary: {payload.get('summary') or 'unknown'}",
        f"- Status: {payload.get('status') or 'unknown'}",
        f"- Confidence impact: {payload.get('confidence_impact') or 'unknown'}",
        f"- Suggested attention: {payload.get('suggested_attention') or 'unknown'}",
    ]

    list_fields = (
        ("Market observations", "market_observations"),
        ("Sector observations", "sector_observations"),
        ("Symbol-specific observations", "symbol_specific_observations"),
        ("Event timing notes", "event_timing_notes"),
        ("Liquidity / execution notes", "liquidity_execution_notes"),
        ("Macro / policy notes", "macro_policy_notes"),
    )
    for label, key in list_fields:
        values = payload.get(key) or []
        if values:
            lines.append(f"- {label}:")
            for item in values:
                lines.append(f"  - {item}")

    if payload.get("notes_for_agents"):
        lines.append(f"- Notes for agents: {payload['notes_for_agents']}")
    if payload.get("notes_for_scoring_review"):
        lines.append(f"- Notes for scoring review: {payload['notes_for_scoring_review']}")

    source_links = payload.get("source_links") or []
    if source_links:
        lines.append("- Source links:")
        for link in source_links:
            lines.append(f"  - {link}")

    return "\n".join(lines)


def build_market_breadth_lines(snapshot, indent=""):
    if not (snapshot or {}).get("available"):
        return [f"{indent}- Market breadth snapshot: unavailable"]

    lines = [
        f"{indent}- Breadth tone: {snapshot.get('breadth_tone') or 'unknown'}",
        f"{indent}- Advances: {snapshot.get('advance_count') if snapshot.get('advance_count') is not None else 'unknown'}",
        f"{indent}- Declines: {snapshot.get('decline_count') if snapshot.get('decline_count') is not None else 'unknown'}",
        f"{indent}- Unchanged: {snapshot.get('unchanged_count') if snapshot.get('unchanged_count') is not None else 'unknown'}",
        f"{indent}- Breadth ratio: {snapshot.get('breadth_ratio') if snapshot.get('breadth_ratio') is not None else 'unknown'}",
    ]
    top_turnover = snapshot.get("top_turnover") or []
    if top_turnover:
        lines.append(f"{indent}- Top turnover leaders: {top_turnover}")
    top_sectors = snapshot.get("top_sectors_by_turnover") or []
    if top_sectors:
        lines.append(f"{indent}- Top sectors by turnover: {top_sectors}")
    return lines


def build_sharesansar_event_lines(snapshot, indent=""):
    if not (snapshot or {}).get("available"):
        return [f"{indent}- ShareSansar event timing snapshot: unavailable"]

    latest_dividend = snapshot.get("latest_dividend") or {}
    right_share = snapshot.get("right_share") or {}
    lines = []
    if latest_dividend:
        lines.extend([
            f"{indent}- Latest dividend year: {latest_dividend.get('year') or 'unknown'}",
            f"{indent}- Latest dividend bonus share pct: {latest_dividend.get('bonus_share_pct') or 'unknown'}",
            f"{indent}- Latest dividend cash pct: {latest_dividend.get('cash_dividend_pct') or 'unknown'}",
            f"{indent}- Latest dividend book close date: {latest_dividend.get('book_close_date') or 'unknown'}",
        ])
    if right_share:
        lines.extend([
            f"{indent}- Right-share ratio: {right_share.get('ratio') or 'unknown'}",
            f"{indent}- Right-share units: {right_share.get('units') or 'unknown'}",
            f"{indent}- Right-share book close date: {right_share.get('book_close_date') or 'unknown'}",
            f"{indent}- Right-share opening/closing date: {right_share.get('opening_closing_date') or 'unknown'}",
        ])
    return lines or [f"{indent}- ShareSansar event timing snapshot: unavailable"]
