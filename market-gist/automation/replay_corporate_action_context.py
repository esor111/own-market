"""
Helpers for loading replay-safe corporate action context.
"""
import os
from datetime import datetime
from functools import lru_cache

from config import VALIDATION_DIR, load_json_file


BACKFILL_DIR = os.path.join(VALIDATION_DIR, "historical_context_backfills")


def _days_between(event_date, session_date):
    try:
        event_dt = datetime.strptime(str(event_date), "%Y-%m-%d").date()
        session_dt = datetime.strptime(str(session_date), "%Y-%m-%d").date()
    except ValueError:
        return None
    return (session_dt - event_dt).days


@lru_cache(maxsize=32)
def _load_timeline(year, list_name):
    clean_list_name = str(list_name or "").lstrip("@")
    if not clean_list_name:
        return {}
    path = os.path.join(BACKFILL_DIR, f"latest__{year}__{clean_list_name}__corporate_action_timeline_v1.json")
    return load_json_file(path, {})


def load_replay_corporate_action_context(symbol, session_date, replay_context_list_name=None):
    year = int(str(session_date)[:4])
    payload = _load_timeline(year, replay_context_list_name)
    records = payload.get("records") or []
    symbol = str(symbol).upper()

    matched = [record for record in records if str(record.get("symbol") or "").upper() == symbol]
    active_events = []
    recent_events = []
    for record in matched:
        days_since = _days_between(record.get("event_date"), session_date)
        if days_since is None:
            continue
        contextual_record = {
            **record,
            "days_since_event": days_since,
        }
        if 0 <= days_since <= int(record.get("impact_window_days") or 0):
            active_events.append(contextual_record)
        if 0 <= days_since <= 90:
            recent_events.append(contextual_record)

    active_events.sort(key=lambda item: (item["days_since_event"], -(item.get("impact_window_days") or 0)))
    recent_events.sort(key=lambda item: (item["days_since_event"], item.get("event_type") or ""))
    dominant = active_events[0] if active_events else recent_events[0] if recent_events else None

    notes = list(payload.get("notes") or [])
    if not matched:
        notes.append("no symbol-level corporate action match found in the current replay-safe timeline")

    return {
        "timeline_available": bool(payload),
        "timeline_notes": notes,
        "matched_event_count": len(matched),
        "active_event_count": len(active_events),
        "recent_event_count_90d": len(recent_events),
        "has_active_event": bool(active_events),
        "dominant_event_type": (dominant or {}).get("event_type"),
        "dominant_event_status": (dominant or {}).get("event_status"),
        "active_events": active_events,
        "recent_events": recent_events[:10],
        "coverage_quality": "matched_symbol" if matched else "no_symbol_match",
    }
