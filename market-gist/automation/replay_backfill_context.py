"""
Helpers for loading replay-safe historical context backfills.
"""
import os
from functools import lru_cache

from config import VALIDATION_DIR, load_json_file
from replay_cross_section import load_replay_sector_map


BACKFILL_DIR = os.path.join(VALIDATION_DIR, "historical_context_backfills")


def _normalize_key(value):
    text = str(value or "").upper()
    return "".join(character for character in text if character.isalnum())


@lru_cache(maxsize=16)
def _load_official_backfill(year):
    path = os.path.join(BACKFILL_DIR, f"latest__{year}__official_replay_context_backfill_v1.json")
    payload = load_json_file(path, {})
    benchmark_rows = {}
    sector_rows = {}

    for item in ((payload.get("benchmark_history") or {}).get("index_history_rows") or []):
        benchmark_rows[_normalize_key(item.get("index_name"))] = {
            row.get("businessDate"): row for row in (item.get("rows") or [])
        }

    for item in ((payload.get("sector_index_history") or {}).get("index_history_rows") or []):
        key_candidates = {
            _normalize_key(item.get("sector_name")),
            _normalize_key(item.get("index_name")),
            _normalize_key(item.get("index_code")),
        }
        per_date = {row.get("businessDate"): row for row in (item.get("rows") or [])}
        for key in key_candidates:
            if key:
                sector_rows[key] = per_date

    market_summary_rows = {
        row.get("businessDate"): row
        for row in ((payload.get("benchmark_history") or {}).get("market_summary_history_rows") or [])
    }

    return {
        "notes": payload.get("notes") or [],
        "market_summary_rows": market_summary_rows,
        "benchmark_rows": benchmark_rows,
        "sector_rows": sector_rows,
    }


@lru_cache(maxsize=32)
def _load_derived_backfill(year, list_name):
    if not list_name:
        return {}
    clean_list_name = str(list_name).lstrip("@")
    path = os.path.join(BACKFILL_DIR, f"latest__{year}__{clean_list_name}__derived_replay_context_backfill_v1.json")
    payload = load_json_file(path, {})
    market_rows = {
        row.get("businessDate"): row
        for row in (payload.get("market_context_rows") or [])
    }
    sector_rows = {
        _normalize_key(sector_name): {
            row.get("businessDate"): row for row in (rows or [])
        }
        for sector_name, rows in (payload.get("sector_context_rows") or {}).items()
    }
    return {
        "notes": payload.get("notes") or [],
        "market_rows": market_rows,
        "sector_rows": sector_rows,
    }


def load_replay_context_bundle(symbol, session_date, replay_context_list_name=None):
    year = int(str(session_date)[:4])
    symbol = str(symbol).upper()
    sector_map = load_replay_sector_map()
    sector_name = sector_map.get(symbol, "UNKNOWN")
    normalized_sector_name = _normalize_key(sector_name)

    official = _load_official_backfill(year)
    derived = _load_derived_backfill(year, replay_context_list_name)

    return {
        "sector_name": sector_name,
        "official_context": {
            "notes": official.get("notes") or [],
            "market_summary": (official.get("market_summary_rows") or {}).get(session_date),
            "benchmark_nepse_index": ((official.get("benchmark_rows") or {}).get(_normalize_key("NEPSE Index")) or {}).get(session_date),
            "sector_index": ((official.get("sector_rows") or {}).get(normalized_sector_name) or {}).get(session_date),
        },
        "derived_context": {
            "notes": derived.get("notes") or [],
            "market": (derived.get("market_rows") or {}).get(session_date),
            "sector": ((derived.get("sector_rows") or {}).get(normalized_sector_name) or {}).get(session_date),
        },
    }
