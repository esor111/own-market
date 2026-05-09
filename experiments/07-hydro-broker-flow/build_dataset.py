from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from statistics import mean
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]
CONFIG_PATH = SCRIPT_DIR / "config.json"
PRICE_DIR = ROOT_DIR / "sharesansar_datascrape" / "data"
RAW_FLOORSHEET_DIR = ROOT_DIR / "market-gist" / "broker_flow_ledger" / "raw_merolagani"
DATA_DIR = SCRIPT_DIR / "data"
RESULTS_DIR = SCRIPT_DIR / "results"


@dataclass
class BrokerDay:
    raw_qty: int = 0
    raw_amount: float = 0.0
    raw_rows: int = 0
    unique_buyers: int = 0
    unique_sellers: int = 0
    unique_brokers: int = 0
    same_broker_qty: int = 0
    top_buyer: str = ""
    top_buyer_qty: int = 0
    top_buyer_pct: float | None = None
    top3_buyer_pct: float | None = None
    top_seller: str = ""
    top_seller_qty: int = 0
    top_seller_pct: float | None = None
    top3_seller_pct: float | None = None
    top_net_buyers: str = ""
    top_net_sellers: str = ""


def main() -> int:
    args = parse_args()
    config = read_json(CONFIG_PATH)
    symbols = [s.upper() for s in (args.symbols or config["symbols"])]
    horizons = [int(h) for h in config.get("horizons", [1, 3, 5, 10])]
    start_date = parse_iso_date(args.start_date) if args.start_date else None
    end_date = parse_iso_date(args.end_date) if args.end_date else None

    prices_by_symbol = load_price_archive(symbols, start_date, end_date)
    broker_by_symbol_date = load_broker_days(symbols, start_date, end_date)
    rows = build_daily_rows(prices_by_symbol, broker_by_symbol_date, horizons)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    daily_csv = DATA_DIR / "hydro_broker_flow_daily.csv"
    peer_summary_csv = DATA_DIR / "current_window_peer_summary.csv"
    summary_json = DATA_DIR / "hydro_broker_flow_summary.json"
    findings_md = RESULTS_DIR / "findings.md"

    write_csv(daily_csv, rows)
    peer_summary = build_recent_peer_summary(rows, symbols)
    write_csv(peer_summary_csv, peer_summary)
    summary = build_summary(symbols, prices_by_symbol, broker_by_symbol_date, rows, horizons, peer_summary)
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    findings_md.write_text(build_findings(summary, rows, horizons), encoding="utf-8")

    print(f"Wrote {daily_csv} ({len(rows)} rows)")
    print(f"Wrote {peer_summary_csv} ({len(peer_summary)} rows)")
    print(f"Wrote {summary_json}")
    print(f"Wrote {findings_md}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build clean hydro broker-flow experiment dataset.")
    parser.add_argument("--symbols", nargs="*", help="Optional symbol override.")
    parser.add_argument("--start-date", help="Inclusive YYYY-MM-DD lower bound.")
    parser.add_argument("--end-date", help="Inclusive YYYY-MM-DD upper bound.")
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_mmddyyyy_path(path: Path) -> date | None:
    try:
        return datetime.strptime(path.stem, "%m_%d_%Y").date()
    except ValueError:
        return None


def include_date(value: date, start_date: date | None, end_date: date | None) -> bool:
    if start_date and value < start_date:
        return False
    if end_date and value > end_date:
        return False
    return True


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if not text or text == "-":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: Any) -> int:
    number = parse_number(value)
    return int(number) if number is not None else 0


def pct(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return round((numerator / denominator) * 100, 4)


def load_price_archive(
    symbols: list[str],
    start_date: date | None,
    end_date: date | None,
) -> dict[str, list[dict[str, Any]]]:
    wanted = set(symbols)
    prices: dict[str, list[dict[str, Any]]] = {symbol: [] for symbol in symbols}
    dated_paths = []
    for path in PRICE_DIR.glob("*.csv"):
        business_date = parse_mmddyyyy_path(path)
        if business_date and include_date(business_date, start_date, end_date):
            dated_paths.append((business_date, path))

    for business_date, path in sorted(dated_paths):
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for raw in reader:
                symbol = str(raw.get("Symbol") or "").upper().strip()
                if symbol not in wanted:
                    continue
                row = {
                    "date": business_date.isoformat(),
                    "symbol": symbol,
                    "open": parse_number(raw.get("Open")),
                    "high": parse_number(raw.get("High")),
                    "low": parse_number(raw.get("Low")),
                    "close": parse_number(raw.get("Close")) or parse_number(raw.get("LTP")),
                    "ltp": parse_number(raw.get("LTP")),
                    "vwap": parse_number(raw.get("VWAP")),
                    "volume": parse_number(raw.get("Vol")),
                    "turnover": parse_number(raw.get("Turnover")),
                    "trades": parse_number(raw.get("Trans.")),
                }
                if row["close"] is not None:
                    prices[symbol].append(row)

    return {symbol: collapse_duplicate_sessions(rows) for symbol, rows in prices.items()}


def collapse_duplicate_sessions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    collapsed: list[dict[str, Any]] = []
    previous_signature: tuple[Any, ...] | None = None
    for row in rows:
        signature = tuple(row.get(key) for key in ("open", "high", "low", "close", "volume", "turnover", "trades"))
        if signature != previous_signature:
            collapsed.append(row)
        previous_signature = signature
    return collapsed


def load_broker_days(
    symbols: list[str],
    start_date: date | None,
    end_date: date | None,
) -> dict[tuple[str, str], BrokerDay]:
    result: dict[tuple[str, str], BrokerDay] = {}
    for symbol in symbols:
        symbol_dir = RAW_FLOORSHEET_DIR / symbol
        if not symbol_dir.exists():
            continue
        for path in sorted(symbol_dir.glob("*.json")):
            try:
                run_date = parse_iso_date(path.stem)
            except ValueError:
                continue
            if not include_date(run_date, start_date, end_date):
                continue
            payload = read_json(path)
            result[(symbol, path.stem)] = summarize_broker_rows(payload.get("rows") or [])
    return result


def summarize_broker_rows(rows: list[dict[str, Any]]) -> BrokerDay:
    buy: dict[str, dict[str, float]] = defaultdict(lambda: {"qty": 0, "amount": 0.0})
    sell: dict[str, dict[str, float]] = defaultdict(lambda: {"qty": 0, "amount": 0.0})
    raw_qty = 0
    raw_amount = 0.0
    same_broker_qty = 0

    for row in rows:
        qty = parse_int(row.get("quantity"))
        amount = parse_number(row.get("amount")) or 0.0
        buyer = str(row.get("buyer_broker") or "").strip()
        seller = str(row.get("seller_broker") or "").strip()

        raw_qty += qty
        raw_amount += amount
        if buyer and seller and buyer == seller:
            same_broker_qty += qty
        if buyer:
            buy[buyer]["qty"] += qty
            buy[buyer]["amount"] += amount
        if seller:
            sell[seller]["qty"] += qty
            sell[seller]["amount"] += amount

    top_buyers = sorted(buy.items(), key=lambda item: (item[1]["qty"], item[1]["amount"]), reverse=True)
    top_sellers = sorted(sell.items(), key=lambda item: (item[1]["qty"], item[1]["amount"]), reverse=True)
    broker_ids = set(buy) | set(sell)

    net_rows = []
    for broker in broker_ids:
        buy_qty = int(buy.get(broker, {}).get("qty", 0))
        sell_qty = int(sell.get(broker, {}).get("qty", 0))
        net_rows.append((broker, buy_qty - sell_qty))

    top_net_buyers = sorted(net_rows, key=lambda item: item[1], reverse=True)
    top_net_sellers = sorted(net_rows, key=lambda item: item[1])

    return BrokerDay(
        raw_qty=raw_qty,
        raw_amount=round(raw_amount, 2),
        raw_rows=len(rows),
        unique_buyers=len(buy),
        unique_sellers=len(sell),
        unique_brokers=len(broker_ids),
        same_broker_qty=same_broker_qty,
        top_buyer=top_buyers[0][0] if top_buyers else "",
        top_buyer_qty=int(top_buyers[0][1]["qty"]) if top_buyers else 0,
        top_buyer_pct=pct(top_buyers[0][1]["qty"], raw_qty) if top_buyers else None,
        top3_buyer_pct=pct(sum(item[1]["qty"] for item in top_buyers[:3]), raw_qty) if top_buyers else None,
        top_seller=top_sellers[0][0] if top_sellers else "",
        top_seller_qty=int(top_sellers[0][1]["qty"]) if top_sellers else 0,
        top_seller_pct=pct(top_sellers[0][1]["qty"], raw_qty) if top_sellers else None,
        top3_seller_pct=pct(sum(item[1]["qty"] for item in top_sellers[:3]), raw_qty) if top_sellers else None,
        top_net_buyers="|".join(f"{broker}:{net}" for broker, net in top_net_buyers[:5] if net > 0),
        top_net_sellers="|".join(f"{broker}:{net}" for broker, net in top_net_sellers[:5] if net < 0),
    )


def build_daily_rows(
    prices_by_symbol: dict[str, list[dict[str, Any]]],
    broker_by_symbol_date: dict[tuple[str, str], BrokerDay],
    horizons: list[int],
) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []

    for symbol, price_rows in prices_by_symbol.items():
        recent_volumes: list[float] = []
        recent_broker_rows: list[int] = []
        symbol_rows: list[dict[str, Any]] = []
        previous_close: float | None = None

        for price in price_rows:
            business_date = price["date"]
            close = price["close"]
            open_price = price.get("open")
            high = price.get("high")
            low = price.get("low")
            volume = price.get("volume") or 0
            broker = broker_by_symbol_date.get((symbol, business_date))

            avg_volume_20 = mean(recent_volumes[-20:]) if recent_volumes else None
            avg_broker_rows_20 = mean(recent_broker_rows[-20:]) if recent_broker_rows else None

            row = {
                "date": business_date,
                "symbol": symbol,
                "open": round_float(open_price),
                "high": round_float(high),
                "low": round_float(low),
                "close": round_float(close),
                "volume": round_float(volume),
                "turnover": round_float(price.get("turnover")),
                "trades": round_float(price.get("trades")),
                "return_pct": round_float(((close - previous_close) / previous_close) * 100 if previous_close else None),
                "open_to_close_pct": round_float(((close - open_price) / open_price) * 100 if close and open_price else None),
                "range_pct": round_float(((high - low) / close) * 100 if high and low and close else None),
                "close_position": round_float((close - low) / (high - low) if high and low and high != low else None),
                "volume_ratio_20d": round_float(volume / avg_volume_20 if avg_volume_20 else None),
                "broker_available": 1 if broker and broker.raw_rows > 0 else 0,
            }
            row.update(broker_to_row(broker, volume, avg_broker_rows_20))
            add_pattern_flags(row)
            symbol_rows.append(row)

            previous_close = close
            if volume:
                recent_volumes.append(float(volume))
            if broker and broker.raw_rows > 0:
                recent_broker_rows.append(broker.raw_rows)

        add_forward_returns(symbol_rows, horizons)
        output_rows.extend(symbol_rows)

    return sorted(output_rows, key=lambda row: (row["symbol"], row["date"]))


def broker_to_row(
    broker: BrokerDay | None,
    price_volume: float,
    avg_broker_rows_20: float | None,
) -> dict[str, Any]:
    if not broker:
        return {
            "raw_qty": "",
            "raw_amount": "",
            "raw_rows": "",
            "unique_buyers": "",
            "unique_sellers": "",
            "unique_brokers": "",
            "same_broker_pct": "",
            "top_buyer": "",
            "top_buyer_qty": "",
            "top_buyer_pct": "",
            "top3_buyer_pct": "",
            "top_seller": "",
            "top_seller_qty": "",
            "top_seller_pct": "",
            "top3_seller_pct": "",
            "buyer_seller_top3_gap": "",
            "broker_rows_ratio_20d": "",
            "raw_qty_vs_price_volume_pct": "",
            "top_net_buyers": "",
            "top_net_sellers": "",
        }

    return {
        "raw_qty": broker.raw_qty,
        "raw_amount": broker.raw_amount,
        "raw_rows": broker.raw_rows,
        "unique_buyers": broker.unique_buyers,
        "unique_sellers": broker.unique_sellers,
        "unique_brokers": broker.unique_brokers,
        "same_broker_pct": round_float(pct(broker.same_broker_qty, broker.raw_qty)),
        "top_buyer": broker.top_buyer,
        "top_buyer_qty": broker.top_buyer_qty,
        "top_buyer_pct": round_float(broker.top_buyer_pct),
        "top3_buyer_pct": round_float(broker.top3_buyer_pct),
        "top_seller": broker.top_seller,
        "top_seller_qty": broker.top_seller_qty,
        "top_seller_pct": round_float(broker.top_seller_pct),
        "top3_seller_pct": round_float(broker.top3_seller_pct),
        "buyer_seller_top3_gap": round_float(
            (broker.top3_buyer_pct or 0.0) - (broker.top3_seller_pct or 0.0)
        ),
        "broker_rows_ratio_20d": round_float(broker.raw_rows / avg_broker_rows_20 if avg_broker_rows_20 else None),
        "raw_qty_vs_price_volume_pct": round_float(pct(broker.raw_qty - price_volume, price_volume)) if price_volume else "",
        "top_net_buyers": broker.top_net_buyers,
        "top_net_sellers": broker.top_net_sellers,
    }


def add_pattern_flags(row: dict[str, Any]) -> None:
    return_pct = as_float(row.get("return_pct"))
    volume_ratio = as_float(row.get("volume_ratio_20d"))
    broker_rows_ratio = as_float(row.get("broker_rows_ratio_20d"))
    close_position = as_float(row.get("close_position"))
    buyer_top3 = as_float(row.get("top3_buyer_pct"))
    seller_top3 = as_float(row.get("top3_seller_pct"))
    top3_gap = as_float(row.get("buyer_seller_top3_gap"))

    high_volume = volume_ratio is not None and volume_ratio >= 1.5
    broker_activity_spike = broker_rows_ratio is not None and broker_rows_ratio >= 1.5

    flags = {
        "high_volume_up": high_volume and return_pct is not None and return_pct > 0,
        "high_volume_down": high_volume and return_pct is not None and return_pct < 0,
        "buyer_concentrated": buyer_top3 is not None and buyer_top3 >= 25,
        "seller_concentrated": seller_top3 is not None and seller_top3 >= 25,
        "supply_pressure": return_pct is not None and return_pct < 0 and seller_top3 is not None and seller_top3 >= 25,
        "absorption_attempt": (
            return_pct is not None
            and return_pct >= 0
            and buyer_top3 is not None
            and buyer_top3 >= 25
            and close_position is not None
            and close_position >= 0.55
        ),
        "failed_rally_candidate": (
            return_pct is not None
            and return_pct >= 2
            and (high_volume or broker_activity_spike)
            and close_position is not None
            and close_position < 0.75
        ),
        "two_sided_churn": (
            return_pct is not None
            and abs(return_pct) <= 1
            and (high_volume or broker_activity_spike)
            and buyer_top3 is not None
            and seller_top3 is not None
            and min(buyer_top3, seller_top3) >= 18
        ),
        "distribution_like": (
            return_pct is not None
            and return_pct <= 0
            and seller_top3 is not None
            and buyer_top3 is not None
            and seller_top3 - buyer_top3 >= 3
            and (volume_ratio is None or volume_ratio >= 0.8)
        ),
        "accumulation_like": (
            return_pct is not None
            and return_pct >= 0
            and top3_gap is not None
            and top3_gap >= 3
            and close_position is not None
            and close_position >= 0.6
            and (volume_ratio is None or volume_ratio >= 0.8)
        ),
    }
    for key, value in flags.items():
        row[key] = 1 if value else 0


def add_forward_returns(rows: list[dict[str, Any]], horizons: list[int]) -> None:
    for idx, row in enumerate(rows):
        close = as_float(row.get("close"))
        for horizon in horizons:
            key = f"fwd_{horizon}d_return_pct"
            if close is None or idx + horizon >= len(rows):
                row[key] = ""
                continue
            future_close = as_float(rows[idx + horizon].get("close"))
            row[key] = round_float(((future_close - close) / close) * 100 if future_close else None)


def build_summary(
    symbols: list[str],
    prices_by_symbol: dict[str, list[dict[str, Any]]],
    broker_by_symbol_date: dict[tuple[str, str], BrokerDay],
    rows: list[dict[str, Any]],
    horizons: list[int],
    peer_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    coverage = []
    for symbol in symbols:
        price_rows = prices_by_symbol.get(symbol, [])
        raw_dates = sorted(date_text for (sym, date_text), day in broker_by_symbol_date.items() if sym == symbol)
        broker_dates = sorted(date_text for (sym, date_text), day in broker_by_symbol_date.items() if sym == symbol and day.raw_rows)
        empty_raw_dates = sorted(date_text for (sym, date_text), day in broker_by_symbol_date.items() if sym == symbol and not day.raw_rows)
        joined_days = sum(1 for row in rows if row["symbol"] == symbol and row.get("broker_available") == 1)
        coverage.append({
            "symbol": symbol,
            "price_days": len(price_rows),
            "price_first": price_rows[0]["date"] if price_rows else None,
            "price_last": price_rows[-1]["date"] if price_rows else None,
            "raw_files_checked": len(raw_dates),
            "empty_raw_files": len(empty_raw_dates),
            "empty_raw_dates": empty_raw_dates,
            "broker_days_with_rows": len(broker_dates),
            "broker_first": broker_dates[0] if broker_dates else None,
            "broker_last": broker_dates[-1] if broker_dates else None,
            "joined_price_broker_days": joined_days,
        })

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "symbols": symbols,
        "horizons": horizons,
        "price_dir": str(PRICE_DIR),
        "raw_floorsheet_dir": str(RAW_FLOORSHEET_DIR),
        "row_count": len(rows),
        "broker_available_rows": sum(1 for row in rows if row.get("broker_available") == 1),
        "coverage": coverage,
        "current_window_peer_summary": peer_summary,
        "pattern_summary": build_pattern_summary(rows, horizons),
        "latest_upper": latest_symbol_row(rows, "UPPER"),
    }


def build_recent_peer_summary(rows: list[dict[str, Any]], symbols: list[str]) -> list[dict[str, Any]]:
    dates_by_symbol = {}
    for symbol in symbols:
        dates_by_symbol[symbol] = {
            row["date"]
            for row in rows
            if row["symbol"] == symbol and row.get("broker_available") == 1
        }
    common_dates = sorted(set.intersection(*dates_by_symbol.values())) if dates_by_symbol else []
    if not common_dates:
        return []

    rows_by_symbol = {
        symbol: [row for row in rows if row["symbol"] == symbol and row["date"] in common_dates]
        for symbol in symbols
    }
    output: list[dict[str, Any]] = []
    pattern_columns = [
        "high_volume_up",
        "high_volume_down",
        "buyer_concentrated",
        "seller_concentrated",
        "supply_pressure",
        "absorption_attempt",
        "failed_rally_candidate",
        "two_sided_churn",
        "distribution_like",
        "accumulation_like",
    ]

    for symbol in symbols:
        symbol_rows = sorted(rows_by_symbol[symbol], key=lambda row: row["date"])
        if not symbol_rows:
            continue
        first = symbol_rows[0]
        last = symbol_rows[-1]
        first_close = as_float(first.get("close"))
        last_close = as_float(last.get("close"))
        max_row = max(symbol_rows, key=lambda row: as_float(row.get("raw_rows")) or 0)
        latest_flags = [key for key in pattern_columns if last.get(key) == 1]

        output.append({
            "symbol": symbol,
            "window_start": common_dates[0],
            "window_end": common_dates[-1],
            "days": len(symbol_rows),
            "start_close": round_float(first_close),
            "end_close": round_float(last_close),
            "window_return_pct": round_float(((last_close - first_close) / first_close) * 100 if first_close and last_close else None),
            "total_volume": int(sum(as_float(row.get("volume")) or 0 for row in symbol_rows)),
            "total_raw_qty": int(sum(as_float(row.get("raw_qty")) or 0 for row in symbol_rows)),
            "total_raw_rows": int(sum(as_float(row.get("raw_rows")) or 0 for row in symbol_rows)),
            "avg_raw_rows": round_float(mean([as_float(row.get("raw_rows")) or 0 for row in symbol_rows])),
            "avg_top3_buyer_pct": round_float(mean([as_float(row.get("top3_buyer_pct")) or 0 for row in symbol_rows])),
            "avg_top3_seller_pct": round_float(mean([as_float(row.get("top3_seller_pct")) or 0 for row in symbol_rows])),
            "max_raw_rows": max_row.get("raw_rows"),
            "max_raw_rows_date": max_row.get("date"),
            "latest_close": last.get("close"),
            "latest_return_pct": last.get("return_pct"),
            "latest_top_net_buyers": last.get("top_net_buyers"),
            "latest_top_net_sellers": last.get("top_net_sellers"),
            "latest_labels": ", ".join(latest_flags),
        })

    return sorted(output, key=lambda row: (as_float(row.get("window_return_pct")) or 0), reverse=True)


def build_pattern_summary(rows: list[dict[str, Any]], horizons: list[int]) -> list[dict[str, Any]]:
    pattern_columns = [
        "high_volume_up",
        "high_volume_down",
        "buyer_concentrated",
        "seller_concentrated",
        "supply_pressure",
        "absorption_attempt",
        "failed_rally_candidate",
        "two_sided_churn",
        "distribution_like",
        "accumulation_like",
    ]
    summary = []
    eligible_rows = [row for row in rows if row.get("broker_available") == 1]
    for pattern in pattern_columns:
        matches = [row for row in eligible_rows if row.get(pattern) == 1]
        item: dict[str, Any] = {
            "pattern": pattern,
            "count": len(matches),
            "symbol_count": len({row["symbol"] for row in matches}),
            "upper_count": sum(1 for row in matches if row["symbol"] == "UPPER"),
        }
        for horizon in horizons:
            values = [as_float(row.get(f"fwd_{horizon}d_return_pct")) for row in matches]
            values = [value for value in values if value is not None]
            item[f"fwd_{horizon}d_mean_return_pct"] = round_float(mean(values)) if values else None
            item[f"fwd_{horizon}d_positive_rate"] = round_float(sum(1 for value in values if value > 0) / len(values)) if values else None
            item[f"fwd_{horizon}d_n"] = len(values)
        summary.append(item)
    return summary


def latest_symbol_row(rows: list[dict[str, Any]], symbol: str) -> dict[str, Any] | None:
    symbol_rows = [row for row in rows if row["symbol"] == symbol]
    return symbol_rows[-1] if symbol_rows else None


def build_findings(summary: dict[str, Any], rows: list[dict[str, Any]], horizons: list[int]) -> str:
    lines = [
        "# Hydro Broker-Flow Pattern Lab Findings",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "This is a clean experiment lane. It reads raw local data and does not change the live prediction or persistence shadow systems.",
        "",
        "## Coverage",
        "",
        "| Symbol | Price days | Price range | Raw checks | Empty raw | Broker days | Broker range | Joined days |",
        "|---|---:|---|---:|---:|---:|---|---:|",
    ]
    for item in summary["coverage"]:
        lines.append(
            f"| {item['symbol']} | {item['price_days']} | "
            f"{item['price_first']} to {item['price_last']} | "
            f"{item['raw_files_checked']} | "
            f"{item['empty_raw_files']} | "
            f"{item['broker_days_with_rows']} | "
            f"{item['broker_first']} to {item['broker_last']} | "
            f"{item['joined_price_broker_days']} |"
        )

    empty_items = [item for item in summary["coverage"] if item.get("empty_raw_files")]
    if empty_items:
        lines.extend([
            "",
            "Empty raw checks mean the source was queried and returned no floorsheet rows; those dates are excluded from broker-flow pattern counts.",
        ])
        for item in empty_items:
            dates = ", ".join(item.get("empty_raw_dates") or [])
            lines.append(f"- {item['symbol']}: {dates}")

    peer_summary = summary.get("current_window_peer_summary") or []
    if peer_summary:
        lines.extend([
            "",
            "## Current Common Peer Window",
            "",
            "This table uses only dates where all configured hydro symbols have both price and broker-flow data.",
            "",
            "| Symbol | Window | Days | Return | Raw qty | Rows | Avg top3 B/S | Max rows | Latest labels |",
            "|---|---|---:|---:|---:|---:|---:|---:|---|",
        ])
        for item in peer_summary:
            lines.append(
                f"| {item['symbol']} | {item['window_start']} to {item['window_end']} | "
                f"{item['days']} | {fmt_md(item['window_return_pct'])}% | "
                f"{item['total_raw_qty']} | {item['total_raw_rows']} | "
                f"{fmt_md(item['avg_top3_buyer_pct'])}/{fmt_md(item['avg_top3_seller_pct'])} | "
                f"{item['max_raw_rows']} on {item['max_raw_rows_date']} | "
                f"{item['latest_labels']} |"
            )

    lines.extend([
        "",
        "## Pattern Backtest Snapshot",
        "",
        "Forward returns are computed from the daily Sharesansar close. Positive rate is a decimal, so `0.55` means 55%.",
        "",
        "| Pattern | Count | Symbols | UPPER count | "
        + " | ".join(f"{h}d mean / hit" for h in horizons)
        + " |",
        "|---|---:|---:|---:|" + "---:|" * len(horizons),
    ])
    for item in summary["pattern_summary"]:
        metric_parts = []
        for horizon in horizons:
            mean_return = item.get(f"fwd_{horizon}d_mean_return_pct")
            hit_rate = item.get(f"fwd_{horizon}d_positive_rate")
            metric_parts.append(f"{fmt_md(mean_return)} / {fmt_md(hit_rate)}")
        lines.append(
            f"| {item['pattern']} | {item['count']} | {item['symbol_count']} | {item['upper_count']} | "
            + " | ".join(metric_parts)
            + " |"
        )

    latest_upper = summary.get("latest_upper")
    if latest_upper:
        active_flags = [
            key for key in [
                "high_volume_up",
                "high_volume_down",
                "buyer_concentrated",
                "seller_concentrated",
                "supply_pressure",
                "absorption_attempt",
                "failed_rally_candidate",
                "two_sided_churn",
                "distribution_like",
                "accumulation_like",
            ]
            if latest_upper.get(key) == 1
        ]
        lines.extend([
            "",
            "## Latest UPPER Row",
            "",
            f"- Date: `{latest_upper['date']}`",
            f"- Close: `{latest_upper['close']}`",
            f"- Return: `{latest_upper['return_pct']}`%",
            f"- Volume ratio 20d: `{latest_upper['volume_ratio_20d']}`",
            f"- Broker rows: `{latest_upper['raw_rows']}`",
            f"- Top buyers: `{latest_upper['top_net_buyers']}`",
            f"- Top sellers: `{latest_upper['top_net_sellers']}`",
            f"- Active labels: `{', '.join(active_flags) if active_flags else 'none'}`",
        ])

    lines.extend([
        "",
        "## Read This Carefully",
        "",
        "- This is a first-pass pattern lab, not a trading signal.",
        "- Current-window peer coverage is now aligned for all configured hydros.",
        "- Long-history peer coverage is still uneven: UPPER/API/AKPL are stronger than AHPC/BHCL/RADHI/RHPL.",
        "- The next useful upgrade is longer historical backfill for the weak-coverage peers before trusting long-window hit rates.",
    ])
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_float(value: Any, digits: int = 4) -> Any:
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        return round(float(value), digits)
    return value


def fmt_md(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
