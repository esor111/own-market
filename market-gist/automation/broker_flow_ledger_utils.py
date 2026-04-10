"""
Helpers for exporting a simple broker-flow ledger from existing manual packages.

The goal is to keep this layer file-based and low-risk:
- read one daily manual_package.json
- write one normalized ledger JSON per symbol/day
- preserve raw broker/floorsheet context alongside derived signals
"""
from __future__ import annotations

import copy
import json
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from artifact_io import save_json_atomic
from config import BASE_DIR, get_run_directories, load_json_file


BROKER_LEDGER_ROOT = os.path.join(BASE_DIR, "broker_flow_ledger")
DEFAULT_TIMEFRAME = "1D"
DEFAULT_SCHEMA_VERSION = "1.0"


def _is_nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def _coerce_symbol(value: str) -> str:
    return str(value or "").upper().strip()


def _coerce_date(value: str) -> str:
    return str(value or "").strip()


def _load_json(path: str, default: Any = None) -> Any:
    if default is None:
        default = {}
    return load_json_file(path, default)


def find_manual_package_path(
    symbol: str,
    run_date: str,
    timeframe: str = DEFAULT_TIMEFRAME,
    manual_package_path: Optional[str] = None,
) -> str:
    """
    Resolve the most likely manual package path for a symbol/date/timeframe.

    A direct path can be provided, otherwise we use the repo's run directory
    layout created by manual_llm_package.py.
    """
    if manual_package_path:
        return manual_package_path

    run_dirs = get_run_directories(symbol, run_date)
    filename = f"{run_date}__{_coerce_symbol(symbol)}__{str(timeframe).upper()}__manual_package.json"
    candidate = os.path.join(run_dirs["raw_tables"], filename)
    if os.path.exists(candidate):
        return candidate
    return candidate


def load_manual_package(
    symbol: str,
    run_date: str,
    timeframe: str = DEFAULT_TIMEFRAME,
    manual_package_path: Optional[str] = None,
) -> Dict[str, Any]:
    package_path = find_manual_package_path(symbol, run_date, timeframe, manual_package_path)
    package = _load_json(package_path, {})
    if not package:
        raise FileNotFoundError(f"Manual package not found: {package_path}")
    package["_source_path"] = package_path
    return package


def _safe_copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _listify_rows(rows: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            normalized.append(_safe_copy(row))
    return normalized


def _first_value(*values: Any) -> Any:
    for value in values:
        if _is_nonempty(value):
            return value
    return None


def _classify_quality(missing_fields: List[str], floorsheet_available: bool, holdings_available: bool, holding_changes_available: bool) -> str:
    if floorsheet_available and holdings_available and holding_changes_available and not missing_fields:
        return "complete"
    if floorsheet_available or holdings_available or holding_changes_available:
        return "partial"
    return "insufficient"


def _first_row_value(rows: List[Dict[str, Any]], key: str) -> Any:
    if not rows:
        return None
    first_row = rows[0]
    if not isinstance(first_row, dict):
        return None
    return first_row.get(key)


def build_broker_flow_ledger(package: Dict[str, Any]) -> Dict[str, Any]:
    symbol = _coerce_symbol(package.get("symbol"))
    run_date = _coerce_date(package.get("run_date"))
    timeframe = str(package.get("timeframe") or DEFAULT_TIMEFRAME).upper()
    source_path = package.get("_source_path")

    floorsheet = _safe_copy(package.get("floorsheet") or {})
    broker_holdings = _safe_copy(package.get("broker_holdings") or {})
    broker_holding_changes = _safe_copy(package.get("broker_holding_changes") or {})
    broker_edge_summary = _safe_copy(package.get("broker_edge_summary") or {})
    trader_volume_sentiment = _safe_copy(package.get("trader_volume_sentiment") or {})

    parsed = floorsheet.get("parsed") or {}
    buyer_side = floorsheet.get("buyer_side") or {}
    seller_side = floorsheet.get("seller_side") or {}
    last_15_minutes = floorsheet.get("last_15_minutes") or {}
    weekly = broker_holdings.get("weekly") or {}
    monthly = broker_holdings.get("monthly") or {}
    weekly_top_buyers = _safe_copy(weekly.get("top_buyers") or [])
    weekly_top_sellers = _safe_copy(weekly.get("top_sellers") or [])
    monthly_top_buyers = _safe_copy(monthly.get("top_buyers") or [])
    monthly_top_sellers = _safe_copy(monthly.get("top_sellers") or [])
    buyer_rows = _listify_rows(buyer_side.get("rows"))
    seller_rows = _listify_rows(seller_side.get("rows"))
    rises = _listify_rows(broker_holding_changes.get("rises"))
    falls = _listify_rows(broker_holding_changes.get("falls"))
    last_15_rows = _listify_rows(last_15_minutes.get("rows"))

    raw_snapshot = {
        "floorsheet": floorsheet,
        "broker_holdings": broker_holdings,
        "broker_holding_changes": broker_holding_changes,
        "broker_edge_summary": broker_edge_summary,
        "trader_volume_sentiment": trader_volume_sentiment,
    }

    floorsheet_available = any(_is_nonempty(value) for value in (parsed, buyer_rows, seller_rows, last_15_rows))
    broker_holdings_available = any(
        _is_nonempty(value)
        for value in (weekly_top_buyers, weekly_top_sellers, monthly_top_buyers, monthly_top_sellers)
    )
    holding_changes_available = any(
        _is_nonempty(value)
        for value in (rises, falls, broker_holding_changes.get("net_change_signal"))
    )

    derived_snapshot = {
        "activity_label": _first_value(
            broker_edge_summary.get("headline"),
            broker_holding_changes.get("net_change_signal"),
            "mixed",
        ),
        "phase_hint": _first_value(broker_holding_changes.get("net_change_signal"), "mixed"),
        "closing_flow": _first_value(broker_edge_summary.get("closing_flow"), last_15_minutes.get("closing_strength_hint")),
        "concentration_signal": _first_value(broker_edge_summary.get("concentration_signal"), "balanced"),
        "weekly_holdings_signal": _first_value(broker_edge_summary.get("weekly_holdings_signal"), "balanced"),
        "monthly_holdings_signal": _first_value(broker_edge_summary.get("monthly_holdings_signal"), "balanced"),
        "holding_change_signal": _first_value(broker_edge_summary.get("holding_change_signal"), broker_holding_changes.get("net_change_signal"), "mixed"),
        "top_buyer_broker": _first_value(_first_row_value(buyer_rows, "broker"), weekly.get("dominant_buyer")),
        "top_seller_broker": _first_value(_first_row_value(seller_rows, "broker"), weekly.get("dominant_seller")),
        "buyer_top3_concentration_pct": buyer_side.get("top3_share_pct_total"),
        "seller_top3_concentration_pct": seller_side.get("top3_share_pct_total"),
        "visible_buyer_count": buyer_side.get("visible_broker_count"),
        "visible_seller_count": seller_side.get("visible_broker_count"),
        "visible_last_15_trade_count": last_15_minutes.get("trade_count_visible"),
        "latest_trade_time": last_15_minutes.get("latest_trade_time"),
        "latest_trade_rate": last_15_minutes.get("latest_rate"),
        "last_15m_trade_rows": last_15_rows,
        "total_turnover": parsed.get("total_turnover"),
        "total_traded_quantity": parsed.get("total_traded_quantity"),
        "total_transactions": parsed.get("total_transaction"),
        "higher_range_pct": parsed.get("higher_range_pct"),
        "lower_range_pct": parsed.get("lower_range_pct"),
        "weekly_top_buyer_net_qty": weekly.get("top_buyer_net_qty"),
        "weekly_top_seller_net_qty": weekly.get("top_seller_net_qty"),
        "monthly_top_buyer_net_qty": monthly.get("top_buyer_net_qty"),
        "monthly_top_seller_net_qty": monthly.get("top_seller_net_qty"),
        "broker_persistence_note": "derive_from_time_series",
    }

    missing_fields: List[str] = []
    if not _is_nonempty(parsed):
        missing_fields.append("floorsheet.parsed")
    if not _is_nonempty(buyer_rows):
        missing_fields.append("floorsheet.buyer_side.rows")
    if not _is_nonempty(seller_rows):
        missing_fields.append("floorsheet.seller_side.rows")
    if not _is_nonempty(last_15_rows):
        missing_fields.append("floorsheet.last_15_minutes.rows")
    if not _is_nonempty(weekly_top_buyers):
        missing_fields.append("broker_holdings.weekly.top_buyers")
    if not _is_nonempty(weekly_top_sellers):
        missing_fields.append("broker_holdings.weekly.top_sellers")
    if not _is_nonempty(monthly_top_buyers):
        missing_fields.append("broker_holdings.monthly.top_buyers")
    if not _is_nonempty(monthly_top_sellers):
        missing_fields.append("broker_holdings.monthly.top_sellers")
    if not holding_changes_available:
        missing_fields.append("broker_holding_changes.available")

    quality_flags = {
        "manual_package_found": bool(package),
        "source_package_path": source_path,
        "floorsheet_available": floorsheet_available,
        "broker_holdings_available": broker_holdings_available,
        "broker_holding_changes_available": holding_changes_available,
        "backfill_ready": floorsheet_available,
        "source_quality_label": _classify_quality(
            missing_fields,
            floorsheet_available,
            broker_holdings_available,
            holding_changes_available,
        ),
        "missing_fields": missing_fields,
        "missing_field_count": len(missing_fields),
    }

    field_provenance = {
        "raw_fields": [
            "floorsheet",
            "broker_holdings",
            "broker_holding_changes",
            "broker_edge_summary",
            "trader_volume_sentiment",
        ],
        "derived_fields": list(derived_snapshot.keys()),
        "missing_fields": missing_fields,
    }

    ledger = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "ledger_type": "broker_flow_daily",
        "generated_at": datetime.now().isoformat(),
        "symbol": symbol,
        "run_date": run_date,
        "timeframe": timeframe,
        "source": {
            "kind": "manual_package",
            "manual_package_path": source_path,
        },
        "quality_flags": quality_flags,
        "field_provenance": field_provenance,
        "raw_snapshot": raw_snapshot,
        "derived_snapshot": derived_snapshot,
        "notes": [
            "This ledger is a file-based export from the existing manual package.",
            "Raw broker/floorsheet data is preserved as-is; phase and persistence are derived later.",
            "Do not treat this file as a prediction prompt input until the ledger has enough history.",
        ],
    }

    return ledger


def write_json(path: str, payload: Dict[str, Any], overwrite: bool = False) -> bool:
    if os.path.exists(path) and not overwrite:
        return False
    save_json_atomic(path, payload)
    return True


def build_ledger_output_path(symbol: str, run_date: str) -> str:
    return os.path.join(BROKER_LEDGER_ROOT, _coerce_symbol(symbol), _coerce_date(run_date) + ".json")
