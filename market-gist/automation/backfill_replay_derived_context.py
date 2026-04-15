"""
Build replay-safe derived market and sector context from the local 2025 CSV archive.

This complements the official replay-context backfill by filling the full-year gaps
left by rolling official NEPSE history.

Usage:
    python backfill_replay_derived_context.py 2025
    python backfill_replay_derived_context.py 2025 '@replay_basket_v1'
"""
import json
import os
import statistics
import sys
from datetime import datetime

from config import VALIDATION_DIR
from data_sources.sharesansar_csv_source import SharesansarCsvTruthSource
from nepse_trading_calendar import is_trading_weekday


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def load_symbol_list(name):
    list_name = name.lstrip("@")
    path = os.path.join(os.path.dirname(__file__), "symbol_lists.json")
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if list_name not in payload:
        raise KeyError(f"Unknown symbol list: {name}")
    return payload[list_name]


def load_replay_sector_groups():
    path = os.path.join(os.path.dirname(__file__), "replay_sector_groups.json")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _safe_number(value):
    return value if isinstance(value, (int, float)) else 0


def _median(values):
    clean = [value for value in values if isinstance(value, (int, float))]
    return statistics.median(clean) if clean else None


def _date_in_scope(business_date, year):
    return business_date.year == year and is_trading_weekday(business_date)


def _market_day_summary(rows):
    advancers = 0
    decliners = 0
    unchanged = 0
    total_turnover = 0.0
    total_trades = 0
    total_volume = 0.0
    diff_pct_values = []
    range_pct_values = []
    zero_return_count = 0
    turnover_values = []

    for row in rows:
        diff_pct = row.get("percentageChange")
        range_pct = row.get("rangePercentage")
        turnover = _safe_number(row.get("totalTradedValue"))
        trades = _safe_number(row.get("totalTrades"))
        volume = _safe_number(row.get("totalTradedQuantity"))

        if isinstance(diff_pct, (int, float)):
            if diff_pct > 0:
                advancers += 1
            elif diff_pct < 0:
                decliners += 1
            else:
                unchanged += 1
                zero_return_count += 1
            diff_pct_values.append(diff_pct)
        else:
            unchanged += 1

        if isinstance(range_pct, (int, float)):
            range_pct_values.append(range_pct)
        total_turnover += turnover
        total_trades += int(trades)
        total_volume += volume
        turnover_values.append(turnover)

    top_turnover_share = None
    if total_turnover > 0 and turnover_values:
        top_turnover_share = round(sum(sorted(turnover_values, reverse=True)[:5]) / total_turnover, 6)

    return {
        "listed_symbol_count": len(rows),
        "advancers": advancers,
        "decliners": decliners,
        "unchanged": unchanged,
        "advance_decline_ratio": round(advancers / decliners, 4) if decliners else None,
        "total_turnover": round(total_turnover, 2),
        "total_trades": total_trades,
        "total_volume": round(total_volume, 2),
        "median_diff_pct": _median(diff_pct_values),
        "median_range_pct": _median(range_pct_values),
        "zero_return_count": zero_return_count,
        "top_5_turnover_share": top_turnover_share,
    }


def _sector_day_summary(rows):
    if not rows:
        return None

    summary = _market_day_summary(rows)
    summary["average_diff_pct"] = round(
        sum(row.get("percentageChange") for row in rows if isinstance(row.get("percentageChange"), (int, float)))
        / max(1, len([row for row in rows if isinstance(row.get("percentageChange"), (int, float))])),
        4,
    )
    return summary


def _build_markdown(payload):
    lines = [
        "# Replay Derived Context Backfill",
        "",
        f"- year: `{payload['year']}`",
        f"- symbol list: `{payload['symbol_list_name']}`",
        f"- built at: `{payload['built_at']}`",
        "",
        "## Coverage",
        "",
        f"- trading sessions: `{payload['coverage']['trading_session_count']}`",
        f"- symbol list size: `{payload['coverage']['symbol_count']}`",
        f"- sector families covered: `{payload['coverage']['sector_family_count']}`",
        "",
        "## Notes",
        "",
    ]
    for note in payload.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) < 2:
        print("Usage: python backfill_replay_derived_context.py YEAR [@SYMBOL_LIST]")
        sys.exit(1)

    year = int(sys.argv[1])
    symbol_list_name = sys.argv[2] if len(sys.argv) >= 3 else "@replay_basket_v1"
    tracked_symbols = {symbol.upper() for symbol in load_symbol_list(symbol_list_name)}
    sector_groups = load_replay_sector_groups()
    source = SharesansarCsvTruthSource()

    market_rows = []
    sector_rows = {}

    for business_date in source._iter_available_dates():
        if not _date_in_scope(business_date, year):
            continue
        rows = [source._normalize_row(row, business_date) for row in source._load_rows_for_date(business_date)]
        if not rows:
            continue

        market_rows.append({
            "businessDate": business_date.strftime("%Y-%m-%d"),
            **_market_day_summary(rows),
        })

        tracked_rows = [row for row in rows if row.get("symbol") in tracked_symbols]
        by_sector = {}
        for row in tracked_rows:
            sector = sector_groups.get(row["symbol"], "UNKNOWN")
            by_sector.setdefault(sector, []).append(row)

        for sector_name, sector_group_rows in by_sector.items():
            sector_rows.setdefault(sector_name, []).append({
                "businessDate": business_date.strftime("%Y-%m-%d"),
                **_sector_day_summary(sector_group_rows),
            })

    notes = [
        "derived context is built from the local Sharesansar daily archive and fills the full-year gap left by rolling official NEPSE histories",
        "market breadth and turnover concentration are replay-safe because they use only same-day archive snapshots",
    ]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "year": year,
        "symbol_list_name": symbol_list_name.lstrip("@"),
        "notes": notes,
        "coverage": {
            "trading_session_count": len(market_rows),
            "symbol_count": len(tracked_symbols),
            "sector_family_count": len(sector_rows),
        },
        "market_context_rows": market_rows,
        "sector_context_rows": sector_rows,
    }

    target_dir = os.path.join(VALIDATION_DIR, "historical_context_backfills")
    base = f"{year}__{symbol_list_name.lstrip('@')}__derived_replay_context_backfill_v1"
    json_path = os.path.join(target_dir, f"{base}.json")
    latest_json_path = os.path.join(target_dir, f"latest__{base}.json")
    md_path = os.path.join(target_dir, f"{base}.md")
    latest_md_path = os.path.join(target_dir, f"latest__{base}.md")
    markdown = _build_markdown(payload)

    save_json(json_path, payload)
    save_json(latest_json_path, payload)
    save_text(md_path, markdown)
    save_text(latest_md_path, markdown)

    print(json.dumps({
        "saved_json": os.path.abspath(json_path),
        "saved_latest_json": os.path.abspath(latest_json_path),
        "saved_md": os.path.abspath(md_path),
        "saved_latest_md": os.path.abspath(latest_md_path),
        "trading_session_count": len(market_rows),
        "sector_family_count": len(sector_rows),
    }, indent=2))


if __name__ == "__main__":
    main()
