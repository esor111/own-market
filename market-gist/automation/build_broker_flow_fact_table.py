"""
Build a broker-flow fact table from raw Merolagani floorsheet JSON files.

This is a manual research data product. It does not touch the daily shadow
pipeline and does not create trading signals.

Input:
    market-gist/broker_flow_ledger/raw_merolagani/<SYMBOL>/<YYYY-MM-DD>.json

Outputs:
    market-gist/data/validation/broker_flow_fact_table/broker_flow_fact_table.csv
    market-gist/data/validation/broker_flow_fact_table/broker_flow_coverage_by_symbol.csv
    market-gist/data/validation/broker_flow_fact_table/broker_flow_fact_table_summary.json
    market-gist/data/validation/broker_flow_fact_table/broker_flow_fact_table_summary.md

Each fact-table row is one (date, symbol, broker_id) aggregate:
    buy_qty, sell_qty, buy_amount, sell_amount, net_qty, net_amount, etc.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
RAW_ROOT = REPO_ROOT / "broker_flow_ledger" / "raw_merolagani"
OUTPUT_DIR = REPO_ROOT / "data" / "validation" / "broker_flow_fact_table"


FACT_TABLE_CSV = OUTPUT_DIR / "broker_flow_fact_table.csv"
COVERAGE_CSV = OUTPUT_DIR / "broker_flow_coverage_by_symbol.csv"
SUMMARY_JSON = OUTPUT_DIR / "broker_flow_fact_table_summary.json"
SUMMARY_MD = OUTPUT_DIR / "broker_flow_fact_table_summary.md"


@dataclass
class BrokerAgg:
    buy_qty: int = 0
    sell_qty: int = 0
    buy_amount: float = 0.0
    sell_amount: float = 0.0
    buy_trade_count: int = 0
    sell_trade_count: int = 0
    buy_contracts: set[str] = field(default_factory=set)
    sell_contracts: set[str] = field(default_factory=set)


@dataclass
class SymbolCoverage:
    raw_files: int = 0
    bad_files: int = 0
    files_with_rows: int = 0
    files_without_rows: int = 0
    trade_rows: int = 0
    first_date: str | None = None
    last_date: str | None = None
    unique_brokers: set[str] = field(default_factory=set)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--symbol",
        action="append",
        dest="symbols",
        help="Restrict to one or more symbols. Repeatable.",
    )
    parser.add_argument("--start-date", help="Inclusive YYYY-MM-DD lower bound.")
    parser.add_argument("--end-date", help="Inclusive YYYY-MM-DD upper bound.")
    parser.add_argument(
        "--raw-root",
        default=str(RAW_ROOT),
        help="Override raw Merolagani root directory.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Override output directory.",
    )
    return parser.parse_args()


def as_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).replace(",", "").strip()
    if not text:
        return 0
    return int(float(text))


def as_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("NPR", "").strip()
    if not text:
        return 0.0
    return float(text)


def normalize_broker(value: Any) -> str:
    return str(value or "").strip()


def normalize_symbol(value: Any) -> str:
    return str(value or "").upper().strip()


def include_date(date_text: str, start_date: str | None, end_date: str | None) -> bool:
    if start_date and date_text < start_date:
        return False
    if end_date and date_text > end_date:
        return False
    return True


def iter_raw_files(raw_root: Path, symbols: list[str] | None, start_date: str | None, end_date: str | None):
    if not raw_root.exists():
        raise FileNotFoundError(f"Raw Merolagani root not found: {raw_root}")

    wanted = {normalize_symbol(s) for s in symbols} if symbols else None
    for sym_dir in sorted(p for p in raw_root.iterdir() if p.is_dir()):
        symbol = normalize_symbol(sym_dir.name)
        if wanted is not None and symbol not in wanted:
            continue
        for path in sorted(sym_dir.glob("*.json")):
            date_text = path.stem
            if include_date(date_text, start_date, end_date):
                yield symbol, date_text, path


def update_date_bounds(cov: SymbolCoverage, date_text: str) -> None:
    if cov.first_date is None or date_text < cov.first_date:
        cov.first_date = date_text
    if cov.last_date is None or date_text > cov.last_date:
        cov.last_date = date_text


def add_side(
    agg: BrokerAgg,
    side: str,
    qty: int,
    amount: float,
    contract_no: str,
) -> None:
    if side == "buy":
        agg.buy_qty += qty
        agg.buy_amount += amount
        agg.buy_trade_count += 1
        if contract_no:
            agg.buy_contracts.add(contract_no)
    elif side == "sell":
        agg.sell_qty += qty
        agg.sell_amount += amount
        agg.sell_trade_count += 1
        if contract_no:
            agg.sell_contracts.add(contract_no)


def build_fact_table(
    raw_root: Path,
    symbols: list[str] | None,
    start_date: str | None,
    end_date: str | None,
) -> tuple[list[dict], list[dict], dict]:
    broker_day: dict[tuple[str, str, str], BrokerAgg] = defaultdict(BrokerAgg)
    day_totals: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {"qty": 0, "amount": 0.0, "trades": 0}
    )
    coverage: dict[str, SymbolCoverage] = defaultdict(SymbolCoverage)
    bad_files: list[dict[str, str]] = []

    for symbol_from_dir, date_text, path in iter_raw_files(raw_root, symbols, start_date, end_date):
        cov = coverage[symbol_from_dir]
        cov.raw_files += 1
        update_date_bounds(cov, date_text)

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            cov.bad_files += 1
            bad_files.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})
            continue

        rows = payload.get("rows") or []
        if not isinstance(rows, list):
            rows = []

        if rows:
            cov.files_with_rows += 1
        else:
            cov.files_without_rows += 1

        for row in rows:
            if not isinstance(row, dict):
                continue
            symbol = normalize_symbol(row.get("symbol")) or symbol_from_dir
            buyer = normalize_broker(row.get("buyer_broker"))
            seller = normalize_broker(row.get("seller_broker"))
            qty = as_int(row.get("quantity"))
            amount = as_float(row.get("amount"))
            contract_no = str(row.get("contract_no") or "").strip()

            if qty <= 0 and amount <= 0:
                continue

            day_key = (date_text, symbol)
            day_totals[day_key]["qty"] += qty
            day_totals[day_key]["amount"] += amount
            day_totals[day_key]["trades"] += 1
            cov.trade_rows += 1

            if buyer:
                cov.unique_brokers.add(buyer)
                add_side(broker_day[(date_text, symbol, buyer)], "buy", qty, amount, contract_no)
            if seller:
                cov.unique_brokers.add(seller)
                add_side(broker_day[(date_text, symbol, seller)], "sell", qty, amount, contract_no)

    fact_rows: list[dict] = []
    all_brokers: set[str] = set()
    for (date_text, symbol, broker_id), agg in sorted(broker_day.items()):
        totals = day_totals[(date_text, symbol)]
        gross_qty = agg.buy_qty + agg.sell_qty
        gross_amount = agg.buy_amount + agg.sell_amount
        net_qty = agg.buy_qty - agg.sell_qty
        net_amount = agg.buy_amount - agg.sell_amount
        buy_avg_price = agg.buy_amount / agg.buy_qty if agg.buy_qty else None
        sell_avg_price = agg.sell_amount / agg.sell_qty if agg.sell_qty else None
        day_qty = totals["qty"]
        day_amount = totals["amount"]
        all_brokers.add(broker_id)

        fact_rows.append({
            "date": date_text,
            "symbol": symbol,
            "broker_id": broker_id,
            "buy_qty": agg.buy_qty,
            "sell_qty": agg.sell_qty,
            "buy_amount": round(agg.buy_amount, 2),
            "sell_amount": round(agg.sell_amount, 2),
            "buy_trade_count": agg.buy_trade_count,
            "sell_trade_count": agg.sell_trade_count,
            "buy_contract_count": len(agg.buy_contracts),
            "sell_contract_count": len(agg.sell_contracts),
            "net_qty": net_qty,
            "net_amount": round(net_amount, 2),
            "gross_qty": gross_qty,
            "gross_amount": round(gross_amount, 2),
            "avg_buy_price": round(buy_avg_price, 4) if buy_avg_price is not None else "",
            "avg_sell_price": round(sell_avg_price, 4) if sell_avg_price is not None else "",
            "buy_share_of_day_qty": round(agg.buy_qty / day_qty, 6) if day_qty else 0,
            "sell_share_of_day_qty": round(agg.sell_qty / day_qty, 6) if day_qty else 0,
            "buy_share_of_day_amount": round(agg.buy_amount / day_amount, 6) if day_amount else 0,
            "sell_share_of_day_amount": round(agg.sell_amount / day_amount, 6) if day_amount else 0,
            "day_total_qty": int(day_qty),
            "day_total_amount": round(day_amount, 2),
            "day_total_trades": int(totals["trades"]),
            "is_net_buyer": net_qty > 0,
            "is_net_seller": net_qty < 0,
        })

    coverage_rows: list[dict] = []
    for symbol, cov in sorted(coverage.items()):
        coverage_rows.append({
            "symbol": symbol,
            "raw_files": cov.raw_files,
            "bad_files": cov.bad_files,
            "files_with_rows": cov.files_with_rows,
            "files_without_rows": cov.files_without_rows,
            "trade_rows": cov.trade_rows,
            "first_date": cov.first_date or "",
            "last_date": cov.last_date or "",
            "unique_brokers": len(cov.unique_brokers),
        })

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "raw_root": str(raw_root),
        "symbol_filter": symbols or "ALL",
        "start_date": start_date,
        "end_date": end_date,
        "raw_files": sum(row["raw_files"] for row in coverage_rows),
        "bad_files": sum(row["bad_files"] for row in coverage_rows),
        "files_with_rows": sum(row["files_with_rows"] for row in coverage_rows),
        "files_without_rows": sum(row["files_without_rows"] for row in coverage_rows),
        "trade_rows": sum(row["trade_rows"] for row in coverage_rows),
        "fact_rows": len(fact_rows),
        "symbol_count": len(coverage_rows),
        "symbols_with_trade_rows": sum(1 for row in coverage_rows if row["trade_rows"] > 0),
        "unique_brokers": len(all_brokers),
        "bad_file_examples": bad_files[:10],
    }

    return fact_rows, coverage_rows, summary


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_summary_md(summary: dict, coverage_rows: list[dict]) -> str:
    lines = [
        "# Broker Flow Fact Table Summary",
        "",
        "> Generated from raw Merolagani floorsheet JSON. Research data product only; not a trading signal.",
        "",
        "## Totals",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- Raw files scanned: `{summary['raw_files']}`",
        f"- Bad files: `{summary['bad_files']}`",
        f"- Files with trade rows: `{summary['files_with_rows']}`",
        f"- Files without trade rows: `{summary['files_without_rows']}`",
        f"- Raw trade rows: `{summary['trade_rows']}`",
        f"- Fact rows: `{summary['fact_rows']}`",
        f"- Symbols with coverage: `{summary['symbol_count']}`",
        f"- Symbols with trade rows: `{summary['symbols_with_trade_rows']}`",
        f"- Unique broker IDs: `{summary['unique_brokers']}`",
        "",
        "## Coverage By Symbol",
        "",
        "| Symbol | Raw files | Trade rows | First | Last | Unique brokers | Empty files |",
        "|---|---:|---:|---|---|---:|---:|",
    ]
    for row in sorted(coverage_rows, key=lambda r: (-r["trade_rows"], r["symbol"])):
        lines.append(
            f"| {row['symbol']} | {row['raw_files']} | {row['trade_rows']} | "
            f"{row['first_date']} | {row['last_date']} | {row['unique_brokers']} | "
            f"{row['files_without_rows']} |"
        )
    lines.extend([
        "",
        "## Output Files",
        "",
        f"- Fact table: `{FACT_TABLE_CSV}`",
        f"- Coverage CSV: `{COVERAGE_CSV}`",
        f"- Summary JSON: `{SUMMARY_JSON}`",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    raw_root = Path(args.raw_root).resolve()
    output_dir = Path(args.output_dir).resolve()

    global FACT_TABLE_CSV, COVERAGE_CSV, SUMMARY_JSON, SUMMARY_MD
    FACT_TABLE_CSV = output_dir / "broker_flow_fact_table.csv"
    COVERAGE_CSV = output_dir / "broker_flow_coverage_by_symbol.csv"
    SUMMARY_JSON = output_dir / "broker_flow_fact_table_summary.json"
    SUMMARY_MD = output_dir / "broker_flow_fact_table_summary.md"

    fact_rows, coverage_rows, summary = build_fact_table(
        raw_root=raw_root,
        symbols=args.symbols,
        start_date=args.start_date,
        end_date=args.end_date,
    )

    fact_fieldnames = [
        "date", "symbol", "broker_id",
        "buy_qty", "sell_qty", "buy_amount", "sell_amount",
        "buy_trade_count", "sell_trade_count",
        "buy_contract_count", "sell_contract_count",
        "net_qty", "net_amount", "gross_qty", "gross_amount",
        "avg_buy_price", "avg_sell_price",
        "buy_share_of_day_qty", "sell_share_of_day_qty",
        "buy_share_of_day_amount", "sell_share_of_day_amount",
        "day_total_qty", "day_total_amount", "day_total_trades",
        "is_net_buyer", "is_net_seller",
    ]
    coverage_fieldnames = [
        "symbol", "raw_files", "bad_files", "files_with_rows",
        "files_without_rows", "trade_rows", "first_date", "last_date",
        "unique_brokers",
    ]

    write_csv(FACT_TABLE_CSV, fact_rows, fact_fieldnames)
    write_csv(COVERAGE_CSV, coverage_rows, coverage_fieldnames)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text(format_summary_md(summary, coverage_rows), encoding="utf-8")

    print(f"Wrote {FACT_TABLE_CSV} ({len(fact_rows)} rows)")
    print(f"Wrote {COVERAGE_CSV} ({len(coverage_rows)} rows)")
    print(f"Wrote {SUMMARY_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print()
    print(f"Raw trade rows: {summary['trade_rows']}")
    print(f"Unique broker IDs: {summary['unique_brokers']}")
    print(f"Symbols with trade rows: {summary['symbols_with_trade_rows']}/{summary['symbol_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
