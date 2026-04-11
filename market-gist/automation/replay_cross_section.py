"""
Cross-sectional replay context helpers.
"""
import math
from statistics import mean

from config import REPLAY_SECTOR_GROUPS_FILE, load_json_file


def load_replay_sector_map():
    raw = load_json_file(REPLAY_SECTOR_GROUPS_FILE, {})
    return {str(symbol).upper(): str(sector).upper() for symbol, sector in raw.items()}


def _rank_desc(items, key_name):
    sortable = []
    for item in items:
        value = item.get(key_name)
        if value is None:
            continue
        sortable.append((float(value), item.get("symbol")))
    sortable.sort(key=lambda pair: (-pair[0], pair[1] or ""))
    return {symbol: idx + 1 for idx, (_, symbol) in enumerate(sortable)}


def _percentile_from_rank(rank, total):
    if not rank or not total or total <= 1:
        return None
    return round(1 - ((rank - 1) / (total - 1)), 3)


def _leadership_label(basket_rank, basket_total, sector_rank, sector_total):
    top_cut = max(1, math.ceil(basket_total * 0.25)) if basket_total else None
    bottom_cut = max(1, math.ceil(basket_total * 0.25)) if basket_total else None

    basket_leader = basket_rank is not None and top_cut is not None and basket_rank <= top_cut
    basket_laggard = basket_rank is not None and bottom_cut is not None and basket_rank > max(0, basket_total - bottom_cut)
    sector_leader = sector_total and sector_total > 1 and sector_rank == 1

    if basket_leader and sector_leader:
        return "both_leader"
    if basket_leader:
        return "basket_leader"
    if sector_leader:
        return "sector_leader"
    if basket_laggard:
        return "basket_laggard"
    return "middle"


def enrich_session_cases_with_cross_section(session_cases):
    """
    Add basket-relative and sector-relative context to a session's replay cases.

    Each session case dict must contain:
    - symbol
    - frozen_case
    - decision
    """
    if not session_cases:
        return session_cases

    sector_map = load_replay_sector_map()
    rows = []
    for case in session_cases:
        frozen_case = case.get("frozen_case") or {}
        metrics = frozen_case.get("metrics") or {}
        symbol = str(frozen_case.get("symbol") or case.get("symbol") or "").upper()
        sector_name = sector_map.get(symbol, "UNKNOWN")
        row = {
            "symbol": symbol,
            "sector_name": sector_name,
            "return_20d_pct": metrics.get("return_20d_pct"),
            "score": (case.get("decision") or {}).get("score"),
            "avg_value_20d": metrics.get("avg_value_20d"),
            "trend_label": metrics.get("trend_label"),
            "close_position_20d": metrics.get("close_position_20d"),
        }
        rows.append(row)

    basket_return_mean = mean([row["return_20d_pct"] for row in rows if row["return_20d_pct"] is not None]) if any(row["return_20d_pct"] is not None for row in rows) else None
    basket_score_mean = mean([row["score"] for row in rows if row["score"] is not None]) if any(row["score"] is not None for row in rows) else None

    basket_return_rank = _rank_desc(rows, "return_20d_pct")
    basket_score_rank = _rank_desc(rows, "score")
    basket_value_rank = _rank_desc(rows, "avg_value_20d")

    sector_groups = {}
    for row in rows:
        sector_groups.setdefault(row["sector_name"], []).append(row)

    sector_return_rank = {}
    sector_score_rank = {}
    sector_return_mean = {}
    for sector_name, sector_rows in sector_groups.items():
        sector_return_rank[sector_name] = _rank_desc(sector_rows, "return_20d_pct")
        sector_score_rank[sector_name] = _rank_desc(sector_rows, "score")
        if any(item["return_20d_pct"] is not None for item in sector_rows):
            sector_return_mean[sector_name] = mean([item["return_20d_pct"] for item in sector_rows if item["return_20d_pct"] is not None])
        else:
            sector_return_mean[sector_name] = None

    basket_total = len(rows)
    for case in session_cases:
        frozen_case = case.get("frozen_case") or {}
        metrics = frozen_case.get("metrics") or {}
        symbol = str(frozen_case.get("symbol") or case.get("symbol") or "").upper()
        sector_name = sector_map.get(symbol, "UNKNOWN")
        sector_rows = sector_groups.get(sector_name, [])
        sector_total = len(sector_rows)

        current_return_20d = metrics.get("return_20d_pct")
        basket_rank = basket_return_rank.get(symbol)
        sector_rank = (sector_return_rank.get(sector_name) or {}).get(symbol)
        leadership_label = _leadership_label(basket_rank, basket_total, sector_rank, sector_total)

        cross_context = {
            "sector_name": sector_name,
            "basket_member_count": basket_total,
            "basket_return_20d_rank": basket_rank,
            "basket_return_20d_percentile": _percentile_from_rank(basket_rank, basket_total),
            "basket_score_rank": basket_score_rank.get(symbol),
            "basket_value_rank": basket_value_rank.get(symbol),
            "basket_return_20d_mean": round(basket_return_mean, 2) if basket_return_mean is not None else None,
            "relative_return_vs_basket": round(current_return_20d - basket_return_mean, 2) if current_return_20d is not None and basket_return_mean is not None else None,
            "relative_score_vs_basket": round((case.get("decision") or {}).get("score", 0) - basket_score_mean, 2) if basket_score_mean is not None else None,
            "sector_member_count": sector_total,
            "sector_return_20d_rank": sector_rank,
            "sector_score_rank": (sector_score_rank.get(sector_name) or {}).get(symbol),
            "sector_return_20d_mean": round(sector_return_mean.get(sector_name), 2) if sector_return_mean.get(sector_name) is not None else None,
            "relative_return_vs_sector": round(current_return_20d - sector_return_mean[sector_name], 2) if current_return_20d is not None and sector_return_mean.get(sector_name) is not None else None,
            "leadership_label": leadership_label,
        }
        frozen_case["sector_name"] = sector_name
        frozen_case["cross_sectional_context"] = cross_context
        case["frozen_case"] = frozen_case

    return session_cases
