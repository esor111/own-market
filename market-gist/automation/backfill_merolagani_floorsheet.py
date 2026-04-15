"""
Backfill historical broker-flow data from Merolagani's datewise floorsheet.

This script is intentionally separate from the live Romeo/Juliet prediction lane.
It:
- pulls historical raw floorsheet rows by symbol/date from Merolagani
- stores a raw daily payload under broker_flow_ledger/raw_merolagani/<SYMBOL>/<DATE>.json
- writes a canonical broker ledger file when one does not already exist
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List

from playwright.sync_api import sync_playwright

from artifact_io import save_json_atomic
from broker_flow_market_calendar import classify_empty_day_reason, get_market_day_context
from broker_flow_ledger_utils import BROKER_LEDGER_ROOT, build_broker_flow_ledger, build_ledger_output_path, write_json
from browser_edge_features import build_broker_edge_summary
from nepse_trading_calendar import is_trading_weekday


FLOORSHEET_URL = "https://merolagani.com/Floorsheet.aspx"
TABLE_SELECTOR = "table.table.table-bordered.table-striped.table-hover.sortable"
PAGER_SELECTOR = "#ctl00_ContentPlaceHolder1_PagerControl1_litRecords"
SEARCH_BUTTON_SELECTOR = "#ctl00_ContentPlaceHolder1_lbtnSearchFloorsheet"
SYMBOL_INPUT_SELECTOR = "input[name='ctl00$ContentPlaceHolder1$ASCompanyFilter$txtAutoSuggest']"
DATE_INPUT_SELECTOR = "input[name='ctl00$ContentPlaceHolder1$txtFloorsheetDateFilter']"
NAVIGATION_TIMEOUT_MS = 180000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill historical Merolagani broker floorsheet data.")
    parser.add_argument("--symbol", action="append", dest="symbols", required=True, help="Symbol(s) to backfill, repeatable")
    parser.add_argument("--start-date", required=True, help="Inclusive start date in YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="Inclusive end date in YYYY-MM-DD")
    parser.add_argument("--timeframe", default="1D", help="Ledger timeframe label, default 1D")
    parser.add_argument("--headed", action="store_true", help="Run Chrome headed instead of headless")
    parser.add_argument("--force", action="store_true", help="Overwrite existing raw/ledger outputs")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional page cap for testing")
    return parser.parse_args()


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def to_merolagani_date(value: date) -> str:
    return value.strftime("%m/%d/%Y")


def iter_trading_dates(start_date: date, end_date: date) -> Iterable[date]:
    current = start_date
    while current <= end_date:
        if is_trading_weekday(current):
            yield current
        current += timedelta(days=1)


def raw_output_path(symbol: str, run_date: str) -> Path:
    return Path(BROKER_LEDGER_ROOT) / "raw_merolagani" / symbol.upper() / f"{run_date}.json"


def parse_pager_text(text: str) -> Dict[str, int | str | None]:
    cleaned = " ".join(str(text or "").split())
    match = re.search(r"Showing\s+(\d+)\s*-\s*(\d+)\s+of\s+(\d+)\s+records\.\s*\[Total pages:\s*(\d+)\]", cleaned)
    if not match:
        return {
            "pager_text": cleaned,
            "from_record": None,
            "to_record": None,
            "total_records": None,
            "total_pages": 0,
        }
    return {
        "pager_text": cleaned,
        "from_record": int(match.group(1)),
        "to_record": int(match.group(2)),
        "total_records": int(match.group(3)),
        "total_pages": int(match.group(4)),
    }


def parse_float(value: str) -> float | None:
    cleaned = str(value or "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_int(value: str) -> int | None:
    cleaned = re.sub(r"[^\d-]", "", str(value or ""))
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def extract_table_rows(page) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    row_cells = page.locator(f"{TABLE_SELECTOR} tr").evaluate_all(
        """(tableRows) => tableRows.map((row) =>
            Array.from(row.querySelectorAll('th,td')).map((cell) => (cell.innerText || '').trim())
        )"""
    )
    for cells in row_cells:
        normalized = [str(cell or "").strip() for cell in cells]
        if len(normalized) < 8 or normalized[0] == "#":
            continue
        row_number, contract_no, symbol, buyer, seller, qty_text, rate_text, amount_text = normalized[:8]
        quantity = parse_int(qty_text)
        rate = parse_float(rate_text)
        amount = parse_float(amount_text)
        rows.append(
            {
                "row_number": parse_int(row_number),
                "contract_no": contract_no,
                "symbol": symbol,
                "buyer_broker": buyer,
                "seller_broker": seller,
                "quantity": quantity,
                "rate": rate,
                "amount": amount,
                "quantity_text": qty_text,
                "rate_text": rate_text,
                "amount_text": amount_text,
            }
        )
    return rows


def wait_for_expected_table_rows(page, pager: Dict[str, int | str | None], timeout_ms: int = 45000) -> None:
    expected_rows = None
    from_record = pager.get("from_record")
    to_record = pager.get("to_record")
    total_records = pager.get("total_records")
    if isinstance(from_record, int) and isinstance(to_record, int):
        expected_rows = max(to_record - from_record + 1, 0)
    elif isinstance(total_records, int) and total_records > 0:
        expected_rows = min(total_records, 500)

    if not expected_rows:
        return

    page.wait_for_function(
        """([selector, minimumRows]) => {
            return document.querySelectorAll(selector).length >= minimumRows;
        }""",
        arg=[f"{TABLE_SELECTOR} tr", expected_rows + 1],
        timeout=timeout_ms,
    )


def search_symbol_date(page, symbol: str, run_date: str) -> Dict[str, int | str | None]:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            page.goto(FLOORSHEET_URL, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
            page.wait_for_selector(SYMBOL_INPUT_SELECTOR, state="visible", timeout=NAVIGATION_TIMEOUT_MS)
            page.wait_for_selector(DATE_INPUT_SELECTOR, state="visible", timeout=NAVIGATION_TIMEOUT_MS)
            page.wait_for_selector(SEARCH_BUTTON_SELECTOR, state="visible", timeout=NAVIGATION_TIMEOUT_MS)
            page.locator(SYMBOL_INPUT_SELECTOR).fill(symbol, timeout=NAVIGATION_TIMEOUT_MS)
            page.locator(DATE_INPUT_SELECTOR).fill(to_merolagani_date(parse_iso_date(run_date)), timeout=NAVIGATION_TIMEOUT_MS)
            page.locator(SEARCH_BUTTON_SELECTOR).click(timeout=NAVIGATION_TIMEOUT_MS)
            page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT_MS)
            pager_text = page.locator(PAGER_SELECTOR).inner_text() if page.locator(PAGER_SELECTOR).count() else ""
            pager = parse_pager_text(pager_text)
            wait_for_expected_table_rows(page, pager)
            return pager
        except Exception as exc:
            last_error = exc
            page.wait_for_timeout(1500)

    if last_error is not None:
        raise last_error

    return parse_pager_text("")


def go_to_next_page(page) -> Dict[str, int | str | None]:
    pager_locator = page.locator(PAGER_SELECTOR)
    current_pager_text = pager_locator.inner_text() if pager_locator.count() else ""
    if page.evaluate("""() => document.querySelectorAll("a[title='Next Page']").length""") == 0:
        return parse_pager_text(current_pager_text)

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            clicked = page.evaluate(
                """() => {
                    const el = document.querySelector("a[title='Next Page']");
                    if (!el) return false;
                    el.click();
                    return true;
                }"""
            )
            if not clicked:
                page.wait_for_timeout(1000)
                continue
        except Exception as exc:
            last_error = exc
            page.wait_for_timeout(1000)
            continue

        try:
            page.wait_for_function(
                """([selector, previousText]) => {
                    const el = document.querySelector(selector);
                    if (!el) return false;
                    return (el.innerText || '').trim() !== (previousText || '').trim();
                }""",
                arg=[PAGER_SELECTOR, current_pager_text],
                timeout=45000,
            )
        except Exception as wait_exc:
            last_error = wait_exc
            page.wait_for_timeout(1500)
            continue

        page.wait_for_timeout(500)
        pager_text = pager_locator.inner_text() if pager_locator.count() else ""
        pager = parse_pager_text(pager_text)
        wait_for_expected_table_rows(page, pager)
        return pager

    if last_error is not None:
        raise last_error

    pager_text = pager_locator.inner_text() if pager_locator.count() else ""
    return parse_pager_text(pager_text)


def summarize_broker_side(rows: List[Dict[str, object]], broker_key: str) -> Dict[str, object]:
    broker_stats: Dict[str, Dict[str, float | int]] = {}
    total_quantity = 0
    for row in rows:
        broker = str(row.get(broker_key) or "")
        quantity = int(row.get("quantity") or 0)
        amount = float(row.get("amount") or 0.0)
        if not broker:
            continue
        stat = broker_stats.setdefault(broker, {"qty": 0, "amount": 0.0, "matching": 0})
        stat["qty"] += quantity
        stat["amount"] += amount
        stat["matching"] += 1
        total_quantity += quantity

    sorted_stats = sorted(
        broker_stats.items(),
        key=lambda item: (item[1]["qty"], item[1]["amount"]),
        reverse=True,
    )

    parsed_rows = []
    for broker, stat in sorted_stats[:10]:
        qty = int(stat["qty"])
        amount = float(stat["amount"])
        matching = int(stat["matching"])
        share_pct = round((qty / total_quantity) * 100, 2) if total_quantity else None
        avg_price = round(amount / qty, 2) if qty else None
        parsed_rows.append(
            {
                "broker": broker,
                "qty": str(qty),
                "matching": str(matching),
                "share_pct_text": f"{share_pct} %" if share_pct is not None else "",
                "share_pct": share_pct,
                "amount": f"NPR {amount:,.2f}" if amount else "",
                "avg_price": f"NPR {avg_price:.2f}" if avg_price is not None else "",
                "raw": f"{broker} {qty} {matching} {share_pct if share_pct is not None else ''} % NPR {amount:,.2f} NPR {avg_price:.2f}" if avg_price is not None else broker,
            }
        )

    top_share = parsed_rows[0]["share_pct"] if parsed_rows else None
    top3_total = round(sum(row["share_pct"] or 0 for row in parsed_rows[:3]), 2) if parsed_rows else None
    return {
        "rows": parsed_rows,
        "top_broker": parsed_rows[0]["broker"] if parsed_rows else None,
        "top_share_pct": top_share,
        "top3_share_pct_total": top3_total,
        "visible_broker_count": len(broker_stats),
    }


def build_historical_package(symbol: str, run_date: str, timeframe: str, rows: List[Dict[str, object]], raw_path: Path, total_pages: int | None, total_records: int | None) -> Dict[str, object]:
    total_turnover = round(sum(float(row.get("amount") or 0.0) for row in rows), 2)
    total_quantity = sum(int(row.get("quantity") or 0) for row in rows)
    total_transactions = len(rows)

    floorsheet = {
        "symbol": symbol,
        "summary_text": {
            "source": "merolagani_historical_browser",
            "raw_path": str(raw_path),
            "page_count": total_pages,
            "total_records": total_records,
        },
        "parsed": {
            "total_turnover": total_turnover,
            "total_traded_quantity": total_quantity,
            "total_transaction": total_transactions,
            "higher_range_pct": None,
            "lower_range_pct": None,
        },
        "buyer_side": summarize_broker_side(rows, "buyer_broker"),
        "seller_side": summarize_broker_side(rows, "seller_broker"),
        "last_15_minutes": {},
        "available": bool(rows),
    }
    broker_edge_summary = build_broker_edge_summary(floorsheet, {}, {}, {})
    package = {
        "symbol": symbol,
        "run_date": run_date,
        "timeframe": timeframe,
        "floorsheet": floorsheet,
        "broker_holdings": {},
        "broker_holding_changes": {},
        "broker_edge_summary": broker_edge_summary,
        "trader_volume_sentiment": {},
        "_source_path": str(raw_path),
    }
    return package


def backfill_symbol_date(page, symbol: str, run_date: str, timeframe: str, force: bool, max_pages: int | None = None) -> Dict[str, object]:
    market_day_context = get_market_day_context(run_date)
    pager = search_symbol_date(page, symbol, run_date)
    total_pages = int(pager.get("total_pages") or 0)
    total_records = int(pager.get("total_records") or 0) if pager.get("total_records") is not None else None

    rows: List[Dict[str, object]] = []
    if total_pages >= 1:
        rows.extend(extract_table_rows(page))
        last_page = total_pages if max_pages is None else min(total_pages, max_pages)
        for _ in range(2, last_page + 1):
            go_to_next_page(page)
            rows.extend(extract_table_rows(page))

    raw_payload = {
        "schema_version": "1.0",
        "source": {
            "kind": "merolagani_floorsheet_browser",
            "url": FLOORSHEET_URL,
            "symbol": symbol,
            "run_date": run_date,
            "scraped_at": datetime.now().isoformat(),
        },
        "market_day_context": market_day_context,
        "pager": pager,
        "row_count_collected": len(rows),
        "rows": rows,
    }
    raw_path = raw_output_path(symbol, run_date)
    if force or not raw_path.exists():
        save_json_atomic(str(raw_path), raw_payload)

    ledger_path = Path(build_ledger_output_path(symbol, run_date))
    ledger_written = False
    ledger_skipped_reason = None
    if ledger_path.exists() and not force:
        ledger_skipped_reason = "existing_ledger_present"
    elif rows:
        package = build_historical_package(symbol, run_date, timeframe, rows, raw_path, total_pages, total_records)
        ledger = build_broker_flow_ledger(package)
        ledger["source"] = {
            "kind": "historical_merolagani_raw",
            "raw_floorsheet_path": str(raw_path),
            "manual_package_path": None,
        }
        ledger["market_day_context"] = market_day_context
        ledger["quality_flags"]["historical_backfill"] = True
        ledger["quality_flags"]["backfill_ready"] = True
        ledger["notes"].append("Historical backfill from Merolagani raw floorsheet browser capture.")
        ledger_written = write_json(str(ledger_path), ledger, overwrite=force)
        if not ledger_written:
            ledger_skipped_reason = "write_skipped"
    else:
        ledger_skipped_reason = classify_empty_day_reason(market_day_context)

    return {
        "symbol": symbol,
        "run_date": run_date,
        "raw_path": str(raw_path),
        "ledger_path": str(ledger_path),
        "market_day_context": market_day_context,
        "total_pages": total_pages,
        "total_records": total_records,
        "row_count_collected": len(rows),
        "ledger_written": ledger_written,
        "ledger_skipped_reason": ledger_skipped_reason,
    }


def main() -> int:
    args = parse_args()
    start_date = parse_iso_date(args.start_date)
    end_date = parse_iso_date(args.end_date)
    symbols = [symbol.upper().strip() for symbol in args.symbols if symbol.strip()]
    if start_date > end_date:
        raise SystemExit("start-date must be <= end-date")

    results: List[Dict[str, object]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=not args.headed)
        page = browser.new_page()
        try:
            for symbol in symbols:
                for current_date in iter_trading_dates(start_date, end_date):
                    run_date = current_date.strftime("%Y-%m-%d")
                    print(f"[RUN] {symbol} {run_date}")
                    result = backfill_symbol_date(
                        page=page,
                        symbol=symbol,
                        run_date=run_date,
                        timeframe=args.timeframe.upper(),
                        force=args.force,
                        max_pages=args.max_pages,
                    )
                    results.append(result)
                    print(json.dumps(result, indent=2))
        finally:
            browser.close()

    summary = {
        "symbols": symbols,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "results": len(results),
        "raw_written": sum(1 for item in results if Path(item["raw_path"]).exists()),
        "ledgers_written": sum(1 for item in results if item["ledger_written"]),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
