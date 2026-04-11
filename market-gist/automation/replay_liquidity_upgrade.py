"""
Derive replay-safe liquidity and execution context from local symbol history.

This layer is descriptive only. It does not change replay rules on its own.
"""
import statistics
from datetime import datetime


THURSDAY_WEEKDAY = 3  # Python weekday: Monday=0 ... Sunday=6


def _clean_numbers(values):
    return [float(value) for value in values if isinstance(value, (int, float))]


def _avg(values):
    clean = _clean_numbers(values)
    if not clean:
        return None
    return round(sum(clean) / len(clean), 4)


def _share(rows, predicate, length):
    window = list(rows[-length:]) if length else list(rows)
    if not window:
        return None
    matched = sum(1 for row in window if predicate(row))
    return round(matched / len(window), 4)


def _safe_ratio(numerator, denominator):
    if numerator in (None, 0) or denominator in (None, 0):
        return None
    return round(float(numerator) / float(denominator), 4)


def _coefficient_of_variation(values):
    clean = _clean_numbers(values)
    if len(clean) < 2:
        return None
    mean_value = statistics.mean(clean)
    if mean_value == 0:
        return None
    return round(statistics.pstdev(clean) / mean_value, 4)


def _gap_pct(row):
    open_price = row.get("openPrice")
    previous_close = row.get("previousDayClosePrice")
    if open_price in (None, 0) or previous_close in (None, 0):
        return None
    return round(abs((float(open_price) / float(previous_close)) - 1.0) * 100, 4)


def _range_pct(row):
    high_price = row.get("highPrice")
    low_price = row.get("lowPrice")
    previous_close = row.get("previousDayClosePrice")
    if high_price is None or low_price is None or previous_close in (None, 0):
        return None
    return round(((float(high_price) - float(low_price)) / float(previous_close)) * 100, 4)


def _flag_list(metrics):
    flags = []
    if (metrics.get("zero_return_share_20d") or 0) >= 0.1:
        flags.append("high_zero_return_share")
    if (metrics.get("zero_trade_share_20d") or 0) > 0:
        flags.append("has_zero_trade_days")
    if (metrics.get("turnover_cv_20d") or 0) >= 1.0:
        flags.append("unstable_turnover")
    if (metrics.get("trades_cv_20d") or 0) >= 1.0:
        flags.append("unstable_trade_count")
    if (metrics.get("gap_over_2pct_share_20d") or 0) >= 0.25:
        flags.append("frequent_large_gaps")
    if metrics.get("is_thursday_close"):
        flags.append("weekend_gap_carry")
    return flags


def build_replay_liquidity_execution_context(history_rows, session_date):
    rows = list(history_rows or [])

    avg_turnover_5d = _avg(row.get("totalTradedValue") for row in rows[-5:])
    avg_turnover_20d = _avg(row.get("totalTradedValue") for row in rows[-20:])
    avg_turnover_60d = _avg(row.get("totalTradedValue") for row in rows[-60:])
    avg_trades_5d = _avg(row.get("totalTrades") for row in rows[-5:])
    avg_trades_20d = _avg(row.get("totalTrades") for row in rows[-20:])
    avg_trades_60d = _avg(row.get("totalTrades") for row in rows[-60:])
    avg_volume_5d = _avg(row.get("totalTradedQuantity") for row in rows[-5:])
    avg_volume_20d = _avg(row.get("totalTradedQuantity") for row in rows[-20:])

    gap_values_20d = _clean_numbers(_gap_pct(row) for row in rows[-20:])
    range_values_20d = _clean_numbers(_range_pct(row) for row in rows[-20:])

    metrics = {
        "bar_count": len(rows),
        "zero_return_share_20d": _share(rows, lambda row: (row.get("percentageChange") or 0) == 0, 20),
        "zero_return_share_60d": _share(rows, lambda row: (row.get("percentageChange") or 0) == 0, 60),
        "zero_trade_share_20d": _share(rows, lambda row: (row.get("totalTrades") or 0) <= 0, 20),
        "zero_trade_share_60d": _share(rows, lambda row: (row.get("totalTrades") or 0) <= 0, 60),
        "turnover_ratio_5d_to_20d": _safe_ratio(avg_turnover_5d, avg_turnover_20d),
        "turnover_ratio_20d_to_60d": _safe_ratio(avg_turnover_20d, avg_turnover_60d),
        "trades_ratio_5d_to_20d": _safe_ratio(avg_trades_5d, avg_trades_20d),
        "trades_ratio_20d_to_60d": _safe_ratio(avg_trades_20d, avg_trades_60d),
        "volume_ratio_5d_to_20d": _safe_ratio(avg_volume_5d, avg_volume_20d),
        "turnover_cv_20d": _coefficient_of_variation(row.get("totalTradedValue") for row in rows[-20:]),
        "trades_cv_20d": _coefficient_of_variation(row.get("totalTrades") for row in rows[-20:]),
        "avg_abs_gap_pct_20d": round(sum(gap_values_20d) / len(gap_values_20d), 4) if gap_values_20d else None,
        "gap_over_2pct_share_20d": _share(rows, lambda row: (_gap_pct(row) or 0) >= 2.0, 20),
        "avg_range_pct_20d": round(sum(range_values_20d) / len(range_values_20d), 4) if range_values_20d else None,
        "latest_turnover_surprise_vs20d": _safe_ratio((rows[-1].get("totalTradedValue") if rows else None), avg_turnover_20d),
        "latest_trades_surprise_vs20d": _safe_ratio((rows[-1].get("totalTrades") if rows else None), avg_trades_20d),
        "latest_volume_surprise_vs20d": _safe_ratio((rows[-1].get("totalTradedQuantity") if rows else None), avg_volume_20d),
        "is_thursday_close": datetime.strptime(str(session_date), "%Y-%m-%d").date().weekday() == THURSDAY_WEEKDAY,
    }

    return {
        "schema_version": "1.0",
        "session_date": session_date,
        "notes": [
            "liquidity/execution context is descriptive only and does not change replay rules",
            "features are derived from point-in-time local symbol history already available at the replay session close",
        ],
        "metrics": metrics,
        "context_flags": _flag_list(metrics),
    }
