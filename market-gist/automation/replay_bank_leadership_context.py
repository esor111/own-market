"""
Commercial-bank leadership context helpers for replay sessions.
"""


def _rank_desc(items, value_fn):
    sortable = []
    for item in items:
        value = value_fn(item)
        if value is None:
            continue
        sortable.append((float(value), item.get("symbol")))
    sortable.sort(key=lambda pair: (-pair[0], pair[1] or ""))
    return {symbol: index + 1 for index, (_value, symbol) in enumerate(sortable)}


def enrich_session_cases_with_bank_leadership_context(session_cases):
    """
    Add per-session commercial-bank leadership ranks derived from:
    - return_5d_pct
    - volume_ratio_5d
    - close_position_20d
    """
    if not session_cases:
        return session_cases

    bank_cases = []
    for case in session_cases:
        frozen_case = case.get("frozen_case") or {}
        sector_name = str(frozen_case.get("sector_name") or "").upper()
        if sector_name == "COMMERCIAL BANKS":
            bank_cases.append(case)

    if not bank_cases:
        return session_cases

    return_5d_rank = _rank_desc(bank_cases, lambda item: ((item.get("frozen_case") or {}).get("metrics") or {}).get("return_5d_pct"))
    volume_ratio_rank = _rank_desc(bank_cases, lambda item: ((item.get("frozen_case") or {}).get("metrics") or {}).get("volume_ratio_5d"))
    close_position_rank = _rank_desc(bank_cases, lambda item: ((item.get("frozen_case") or {}).get("metrics") or {}).get("close_position_20d"))

    for case in bank_cases:
        frozen_case = case.get("frozen_case") or {}
        symbol = str(frozen_case.get("symbol") or case.get("symbol") or "").upper()
        ranks = [
            return_5d_rank.get(symbol),
            volume_ratio_rank.get(symbol),
            close_position_rank.get(symbol),
        ]
        known_ranks = [rank for rank in ranks if rank is not None]
        leadership_top2_count = sum(1 for rank in known_ranks if rank <= 2)
        leadership_composite_rank = round(sum(known_ranks) / len(known_ranks), 4) if known_ranks else None
        frozen_case["bank_leadership_context"] = {
            "bank_member_count": len(bank_cases),
            "return_5d_rank": return_5d_rank.get(symbol),
            "volume_ratio_rank": volume_ratio_rank.get(symbol),
            "close_position_rank": close_position_rank.get(symbol),
            "leadership_top2_count": leadership_top2_count,
            "leadership_composite_rank": leadership_composite_rank,
            "leader_like": leadership_top2_count >= 1,
        }
        case["frozen_case"] = frozen_case

    return session_cases
