"""
Build a replay calendar from the historical local truth source.

Usage:
    python replay_calendar.py 2025-12-21 2025-12-31
"""
import json
import sys
from datetime import datetime

from data_sources import get_truth_source
from nepse_trading_calendar import is_trading_weekday as _is_trading_weekday


def _parse_date(value):
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def is_nepal_trading_weekday(session_date):
    """Return True if the session date is a NEPSE trading weekday under the active schedule.

    Transition-aware: Sun-Thu before 2026-04-10, Mon-Fri from 2026-04-10 onward.
    See nepse_trading_calendar for details.
    """
    return _is_trading_weekday(session_date)


def load_replay_sessions(start_date, end_date, truth_source_name="sharesansar_local"):
    source = get_truth_source(truth_source_name)
    if not hasattr(source, "_iter_available_dates"):
        raise RuntimeError(f"Truth source does not expose replay sessions: {truth_source_name}")

    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)
    sessions = [
        session.isoformat()
        for session in source._iter_available_dates(start_dt, end_dt)
        if is_nepal_trading_weekday(session)
    ]
    return {
        "truth_source": truth_source_name,
        "start_date": start_date,
        "end_date": end_date,
        "session_count": len(sessions),
        "sessions": sessions,
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python replay_calendar.py START_DATE END_DATE [TRUTH_SOURCE]")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]
    truth_source_name = sys.argv[3] if len(sys.argv) > 3 else "sharesansar_local"
    print(json.dumps(load_replay_sessions(start_date, end_date, truth_source_name), indent=2))


if __name__ == "__main__":
    main()
