"""
NEPSE trading-day calendar, transition-aware.

On 2026-04-05 the NEPSE Board of Directors approved a schedule change from
Sunday-Thursday trading to Monday-Friday trading, in response to the Nepal
Government's declaration of a two-day weekend (Saturday and Sunday) for fuel
conservation. The first Friday session under the new schedule was 2026-04-10;
the first closed Sunday is expected to be 2026-04-12.

This module is the single source of truth for "is this date a NEPSE trading
weekday?" Every other automation file should import from here instead of
hardcoding weekday sets. It is transition-aware:

    - Dates strictly before TRANSITION_DATE use the old Sunday-Thursday schedule.
    - Dates on or after TRANSITION_DATE use the new Monday-Friday schedule.

Holiday resolution is a separate concern and lives in broker_flow_market_calendar.

Sources:
    https://www.sharesansar.com/newsdetail/nepse-to-open-for-trading-on-fridays-board-approves-new-5-day-schedule-2026-04-05
    https://eng.bajarkochirfar.com/2026/04/10/nepse-is-also-opening-today-friday/
"""
from __future__ import annotations

from datetime import date, datetime
from typing import FrozenSet, Union

# First session under the new Monday-Friday schedule (inclusive).
TRANSITION_DATE = date(2026, 4, 10)

# Python weekday() convention: 0=Mon 1=Tue 2=Wed 3=Thu 4=Fri 5=Sat 6=Sun
OLD_TRADING_WEEKDAYS: FrozenSet[int] = frozenset({6, 0, 1, 2, 3})  # Sun-Thu
NEW_TRADING_WEEKDAYS: FrozenSet[int] = frozenset({0, 1, 2, 3, 4})  # Mon-Fri


DateLike = Union[date, datetime, str]


def _coerce_date(value: DateLike) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
    raise TypeError(f"Unsupported date input: {type(value).__name__}")


def trading_weekdays_for(value: DateLike) -> FrozenSet[int]:
    """Return the set of Python weekday ints that are trading days on the given date."""
    d = _coerce_date(value)
    return NEW_TRADING_WEEKDAYS if d >= TRANSITION_DATE else OLD_TRADING_WEEKDAYS


def is_trading_weekday(value: DateLike) -> bool:
    """True iff the given date is a NEPSE trading weekday under the schedule active that day.

    This ignores holidays; it only answers the weekday question. Use
    broker_flow_market_calendar.get_market_day_context for holiday-aware resolution.
    """
    d = _coerce_date(value)
    return d.weekday() in trading_weekdays_for(d)


def is_non_trading_weekday(value: DateLike) -> bool:
    return not is_trading_weekday(value)


def is_last_trading_day_of_week(value: DateLike) -> bool:
    """True iff the given date is the weekly close (last trading weekday) under the active schedule.

    Under Sun-Thu schedule: Thursday.
    Under Mon-Fri schedule: Friday.
    """
    d = _coerce_date(value)
    if d >= TRANSITION_DATE:
        return d.weekday() == 4  # Friday
    return d.weekday() == 3  # Thursday


def session_window_label(value: DateLike) -> str:
    """Human-readable session window label for the date-active schedule."""
    d = _coerce_date(value)
    if d >= TRANSITION_DATE:
        return "Monday-Friday 11:00-15:00 NPT"
    return "Sunday-Thursday 11:00-15:00 NPT"
