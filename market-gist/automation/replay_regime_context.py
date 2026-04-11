"""
Replay-specific market and sector regime context helpers.
"""
from statistics import mean


def _share(items, predicate):
    if not items:
        return None
    hits = sum(1 for item in items if predicate(item))
    return round(hits / len(items), 3)


def _mean_metric(items, key):
    values = [item.get(key) for item in items if item.get(key) is not None]
    return round(mean(values), 2) if values else None


def _regime_label(return_20d_mean, return_5d_mean, positive_share, constructive_share):
    if None in {return_20d_mean, positive_share, constructive_share}:
        return "unknown"
    if return_20d_mean >= 4 and positive_share >= 0.65 and constructive_share >= 0.6:
        return "bullish"
    if return_20d_mean <= -4 and positive_share <= 0.35 and constructive_share <= 0.35:
        return "bearish"
    if (
        return_20d_mean is not None and return_20d_mean > 0
        and return_5d_mean is not None and return_5d_mean >= -1
        and positive_share >= 0.5
    ):
        return "improving"
    if (
        return_20d_mean is not None and return_20d_mean < 0
        and return_5d_mean is not None and return_5d_mean <= 1
        and positive_share < 0.5
    ):
        return "weak"
    return "mixed"


def _alignment_label(symbol_trend, market_regime, sector_regime):
    supportive_regimes = {"bullish", "improving"}
    hostile_regimes = {"bearish", "weak"}
    constructive_trends = {"uptrend", "improving"}
    fragile_trends = {"mixed", "downtrend", "unknown"}

    if symbol_trend in constructive_trends and market_regime in supportive_regimes and sector_regime in supportive_regimes:
        return "both_supportive"
    if symbol_trend in constructive_trends and (market_regime in supportive_regimes or sector_regime in supportive_regimes):
        return "partly_supportive"
    if symbol_trend in fragile_trends and market_regime in hostile_regimes and sector_regime in hostile_regimes:
        return "both_headwind"
    if market_regime in hostile_regimes or sector_regime in hostile_regimes:
        return "headwind"
    return "mixed"


def _build_group_regime(rows):
    return_5d_mean = _mean_metric(rows, "return_5d_pct")
    return_20d_mean = _mean_metric(rows, "return_20d_pct")
    positive_20d_share = _share(rows, lambda row: (row.get("return_20d_pct") or 0) > 0)
    constructive_trend_share = _share(
        rows,
        lambda row: row.get("trend_label") in {"uptrend", "improving"},
    )
    strong_liquidity_share = _share(
        rows,
        lambda row: row.get("liquidity_label") in {"acceptable", "strong"},
    )
    regime_label = _regime_label(
        return_20d_mean,
        return_5d_mean,
        positive_20d_share,
        constructive_trend_share,
    )
    return {
        "member_count": len(rows),
        "return_5d_mean": return_5d_mean,
        "return_20d_mean": return_20d_mean,
        "positive_20d_share": positive_20d_share,
        "constructive_trend_share": constructive_trend_share,
        "strong_liquidity_share": strong_liquidity_share,
        "regime_label": regime_label,
    }


def enrich_session_cases_with_regime_context(session_cases):
    """
    Add market-proxy and sector-proxy regime context to one replay session.

    Each session case dict must contain:
    - symbol
    - frozen_case
    - decision
    """
    if not session_cases:
        return session_cases

    rows = []
    for case in session_cases:
        frozen_case = case.get("frozen_case") or {}
        metrics = frozen_case.get("metrics") or {}
        rows.append({
            "symbol": str(frozen_case.get("symbol") or case.get("symbol") or "").upper(),
            "sector_name": frozen_case.get("sector_name") or "UNKNOWN",
            "return_5d_pct": metrics.get("return_5d_pct"),
            "return_20d_pct": metrics.get("return_20d_pct"),
            "trend_label": metrics.get("trend_label"),
            "liquidity_label": metrics.get("liquidity_label"),
        })

    market_regime = _build_group_regime(rows)

    sector_groups = {}
    for row in rows:
        sector_groups.setdefault(row["sector_name"], []).append(row)

    sector_regimes = {
        sector_name: _build_group_regime(items)
        for sector_name, items in sector_groups.items()
    }

    for case in session_cases:
        frozen_case = case.get("frozen_case") or {}
        metrics = frozen_case.get("metrics") or {}
        sector_name = frozen_case.get("sector_name") or "UNKNOWN"
        sector_regime = sector_regimes.get(sector_name, _build_group_regime([]))
        alignment_label = _alignment_label(
            metrics.get("trend_label"),
            market_regime.get("regime_label"),
            sector_regime.get("regime_label"),
        )
        frozen_case["regime_context"] = {
            "market_proxy": market_regime,
            "sector_proxy": sector_regime,
            "alignment_label": alignment_label,
        }
        case["frozen_case"] = frozen_case

    return session_cases
