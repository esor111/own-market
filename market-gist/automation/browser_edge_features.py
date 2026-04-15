"""
Browser-only edge feature extraction for LLM-facing packages.

This layer intentionally stays separate from the core batch pipeline so we can
use slower portal-only features without making every normal analysis run heavy.
"""
import asyncio
import json
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from nepse_trading_calendar import (
    is_last_trading_day_of_week,
    is_trading_weekday,
    session_window_label,
)


NEPAL_TZ = ZoneInfo("Asia/Katmandu")
SESSION_OPEN = time(11, 0)
SESSION_CLOSE = time(15, 0)

SECTOR_INDEX_SYMBOLS = {
    "HYDROPOWER": "HYDROPOWER",
    "DEVELOPMENT BANKS": "DEVBANK",
    "COMMERCIAL BANKS": "COMMBANK",
    "FINANCE": "FINANCE",
    "HOTELS AND TOURISM": "HOTELS",
    "INVESTMENT": "INVESTMENT",
    "LIFE INSURANCE": "LIFEINSU",
    "MICROFINANCE": "MICROFINANCE",
    "MANUFACTURING AND PROCESSING": "MANUFACTURE",
    "MUTUAL FUND": "MUTUAL",
    "NON LIFE INSURANCE": "NONLIFE",
    "OTHERS": "OTHERS",
    "TRADING": "TRADING",
}


def _clean_text(value):
    return " ".join(str(value or "").split()).strip()


def _parse_float(text):
    cleaned = "".join(char for char in str(text) if char.isdigit() or char in {".", "-"})
    return float(cleaned) if cleaned else None


def _parse_int(text):
    digits = "".join(char for char in str(text) if char.isdigit())
    return int(digits) if digits else None


def parse_broker_change_cell(cell_text):
    parts = _clean_text(cell_text).split()
    if len(parts) < 2:
        return {"raw": _clean_text(cell_text)}
    qty_text = parts[1]
    multiplier = 1
    normalized = qty_text.upper().replace(",", "")
    if normalized.endswith("K"):
        multiplier = 1000
        normalized = normalized[:-1]
    qty_value = _parse_float(normalized)
    signed_qty = qty_value * multiplier if qty_value is not None else None
    return {
        "broker": parts[0],
        "qty_text": qty_text,
        "net_qty": signed_qty,
        "direction": "rise" if signed_qty is not None and signed_qty > 0 else "fall" if signed_qty is not None and signed_qty < 0 else "unknown",
        "raw": _clean_text(cell_text),
    }


def parse_broker_row(row_text):
    parts = str(row_text).split()
    if len(parts) < 6:
        return {"raw": _clean_text(row_text)}
    return {
        "broker": parts[0],
        "qty": parts[1],
        "matching": parts[2],
        "share_pct_text": f"{parts[3]} {parts[4]}" if len(parts) >= 5 else "",
        "share_pct": _parse_float(parts[3]),
        "amount": " ".join(parts[5:-2]) if len(parts) > 7 else "",
        "avg_price": " ".join(parts[-2:]) if len(parts) >= 2 else "",
        "raw": _clean_text(row_text),
    }


def _summarize_broker_side(rows):
    parsed_rows = [parse_broker_row(row) for row in rows if row]
    share_pcts = [row.get("share_pct") for row in parsed_rows if row.get("share_pct") is not None]
    brokers = [row.get("broker") for row in parsed_rows if row.get("broker")]
    return {
        "rows": parsed_rows,
        "top_broker": brokers[0] if brokers else None,
        "top_share_pct": share_pcts[0] if share_pcts else None,
        "top3_share_pct_total": round(sum(share_pcts[:3]), 2) if share_pcts else None,
        "visible_broker_count": len(set(brokers)),
    }


def _parse_trade_row(row_text):
    parts = str(row_text).split()
    if len(parts) < 10:
        return {"raw": _clean_text(row_text)}
    rate = None
    amount = None
    date_text = None
    time_text = None
    if len(parts) >= 10 and parts[4] == "NPR":
        rate = _parse_float(parts[5])
        amount = _parse_float(parts[7]) if len(parts) > 7 else None
        date_text = parts[8] if len(parts) > 8 else None
        time_text = parts[9] if len(parts) > 9 else None
    return {
        "contract_number": parts[0],
        "buyer_broker": parts[1],
        "seller_broker": parts[2],
        "quantity": _parse_int(parts[3]),
        "rate": rate,
        "amount": amount,
        "trade_date": date_text,
        "trade_time": time_text,
        "raw": _clean_text(row_text),
    }


def _summarize_last_15(rows):
    parsed_rows = [_parse_trade_row(row) for row in rows if row]
    buyers = [row.get("buyer_broker") for row in parsed_rows if row.get("buyer_broker")]
    sellers = [row.get("seller_broker") for row in parsed_rows if row.get("seller_broker")]
    amounts = [row.get("amount") for row in parsed_rows if row.get("amount") is not None]
    rates = [row.get("rate") for row in parsed_rows if row.get("rate") is not None]
    closing_strength_hint = "mixed"
    if len(rates) >= 3 and rates[0] >= max(rates[-3:]):
        closing_strength_hint = "firm"
    return {
        "rows": parsed_rows,
        "trade_count_visible": len(parsed_rows),
        "unique_buyers": len(set(buyers)),
        "unique_sellers": len(set(sellers)),
        "largest_trade_amount": max(amounts) if amounts else None,
        "latest_rate": rates[0] if rates else None,
        "earliest_visible_rate": rates[-1] if rates else None,
        "latest_trade_time": parsed_rows[0].get("trade_time") if parsed_rows else None,
        "earliest_visible_trade_time": parsed_rows[-1].get("trade_time") if parsed_rows else None,
        "closing_strength_hint": closing_strength_hint,
    }


def build_broker_edge_summary(floorsheet, broker_holdings, broker_holding_changes, trader_volume_sentiment):
    """Compress raw browser-edge broker/floorsheet data into short high-signal summaries."""
    floorsheet = floorsheet or {}
    broker_holdings = broker_holdings or {}
    broker_holding_changes = broker_holding_changes or {}
    trader_volume_sentiment = trader_volume_sentiment or {}

    parsed = floorsheet.get("parsed") or {}
    buyer_side = floorsheet.get("buyer_side") or {}
    seller_side = floorsheet.get("seller_side") or {}
    last_15 = floorsheet.get("last_15_minutes") or {}
    weekly = broker_holdings.get("weekly") or {}
    monthly = broker_holdings.get("monthly") or {}

    buyer_top3 = buyer_side.get("top3_share_pct_total")
    seller_top3 = seller_side.get("top3_share_pct_total")
    closing_hint = last_15.get("closing_strength_hint")
    weekly_signal = "balanced"
    weekly_buy = weekly.get("top_buyer_net_qty")
    weekly_sell = weekly.get("top_seller_net_qty")
    if weekly_buy is not None and weekly_sell is not None:
        if weekly_buy > abs(weekly_sell):
            weekly_signal = "weekly_accumulation_bias"
        elif abs(weekly_sell) > weekly_buy:
            weekly_signal = "weekly_distribution_bias"

    monthly_signal = "balanced"
    monthly_buy = monthly.get("top_buyer_net_qty")
    monthly_sell = monthly.get("top_seller_net_qty")
    if monthly_buy is not None and monthly_sell is not None:
        if monthly_buy > abs(monthly_sell):
            monthly_signal = "monthly_accumulation_bias"
        elif abs(monthly_sell) > monthly_buy:
            monthly_signal = "monthly_distribution_bias"

    concentration = "balanced"
    if buyer_top3 is not None and seller_top3 is not None:
        if buyer_top3 >= 60 and seller_top3 < 60:
            concentration = "buying_concentrated"
        elif seller_top3 >= 60 and buyer_top3 < 60:
            concentration = "selling_concentrated"
        elif buyer_top3 >= 60 and seller_top3 >= 60:
            concentration = "both_sides_concentrated"
        else:
            concentration = "participation_broad"

    net_change_signal = broker_holding_changes.get("net_change_signal") or "mixed"
    trade_count_visible = last_15.get("trade_count_visible")
    visible_row = trader_volume_sentiment.get("symbol_row") or []
    turnover = parsed.get("total_turnover")
    quantity = parsed.get("total_traded_quantity")

    headline_parts = []
    if closing_hint:
        headline_parts.append(f"closing_flow_{closing_hint}")
    if net_change_signal in {"accumulation", "distribution"}:
        headline_parts.append(f"holding_changes_{net_change_signal}")
    if concentration != "balanced":
        headline_parts.append(concentration)
    if weekly_signal != "balanced":
        headline_parts.append(weekly_signal)

    headline = ", ".join(headline_parts) if headline_parts else "broker_edge_mixed"

    short_points = [
        f"Last-15m closing flow: {closing_hint or 'unknown'}",
        f"Buyer top-3 concentration: {buyer_top3 if buyer_top3 is not None else 'unknown'}%",
        f"Seller top-3 concentration: {seller_top3 if seller_top3 is not None else 'unknown'}%",
        f"Weekly holdings signal: {weekly_signal}",
        f"Monthly holdings signal: {monthly_signal}",
        f"Holding-change signal: {net_change_signal}",
        f"Visible last-15m trades: {trade_count_visible if trade_count_visible is not None else 'unknown'}",
        f"Portal turnover: {turnover if turnover is not None else 'unknown'}",
        f"Portal traded quantity: {quantity if quantity is not None else 'unknown'}",
        f"Trader-volume sentiment available: {'yes' if visible_row else 'no'}",
    ]

    return {
        "headline": headline,
        "closing_flow": closing_hint,
        "concentration_signal": concentration,
        "weekly_holdings_signal": weekly_signal,
        "monthly_holdings_signal": monthly_signal,
        "holding_change_signal": net_change_signal,
        "visible_last_15_trade_count": trade_count_visible,
        "turnover": turnover,
        "traded_quantity": quantity,
        "has_trader_volume_sentiment_row": bool(visible_row),
        "summary_points": short_points,
    }


def build_market_session_context(now=None):
    local_now = now.astimezone(NEPAL_TZ) if now else datetime.now(NEPAL_TZ)
    current_time = local_now.time()
    is_trading_day = is_trading_weekday(local_now.date())
    is_open_now = is_trading_day and SESSION_OPEN <= current_time <= SESSION_CLOSE
    is_before_open = is_trading_day and current_time < SESSION_OPEN
    is_after_close = (not is_trading_day) or current_time > SESSION_CLOSE

    next_session_date = local_now.date()
    next_session_time = datetime.combine(next_session_date, SESSION_OPEN, tzinfo=NEPAL_TZ)

    if is_open_now:
        next_session_time = local_now
    else:
        if not is_trading_day or current_time > SESSION_CLOSE:
            next_session_date = next_session_date + timedelta(days=1)
        while not is_trading_weekday(next_session_date):
            next_session_date = next_session_date + timedelta(days=1)
        next_session_time = datetime.combine(next_session_date, SESSION_OPEN, tzinfo=NEPAL_TZ)

    session_risk = []
    # "Weekly close gap risk" fires on the last trading weekday near the close —
    # Thursday pre-transition, Friday post-transition.
    if is_last_trading_day_of_week(local_now.date()) and current_time >= time(14, 30):
        session_risk.append("weekly_close_gap_risk")
    if not is_trading_day:
        session_risk.append("weekend_market_closed")
    if is_after_close and next_session_time.date() != local_now.date():
        session_risk.append("next_action_delayed_to_future_session")

    return {
        "timezone": "Asia/Katmandu",
        "local_now": local_now.isoformat(),
        "market_open_now": is_open_now,
        "market_closed_now": not is_open_now,
        "is_trading_day": is_trading_day,
        "is_before_open": is_before_open,
        "is_after_close": is_after_close,
        "session_window": session_window_label(local_now.date()),
        "next_trade_session": next_session_time.isoformat(),
        "days_until_next_session": (next_session_time.date() - local_now.date()).days,
        "session_risk_flags": session_risk,
    }


async def capture_chart_state(browser, symbol, timeframe):
    await browser.search_and_load_symbol(symbol)
    await browser.set_timeframe(timeframe)
    await asyncio.sleep(1.5)
    chart = await browser.extract_chart_data()
    chart["symbol"] = symbol
    chart["timeframe"] = timeframe
    return chart


async def capture_multi_timeframe(browser, symbol, timeframes):
    results = {}
    for timeframe in timeframes:
        results[timeframe] = await capture_chart_state(browser, symbol, timeframe)
    return results


async def extract_floorsheet_context(browser, symbol):
    await browser.search_and_load_symbol(symbol)
    await browser.set_timeframe("1D")
    await asyncio.sleep(1.5)
    await browser.frame.get_by_text("Floorsheet").click(timeout=5000)
    await browser.page.get_by_role("heading", name=f"{symbol} TRADE SUMMARY AND FLOORSHEET ANALYSIS").wait_for(timeout=15000)
    summary_rows = await browser.page.locator("table").filter(has_text="Total Traded Quantity").first.locator("tr").all_text_contents()
    summary_rows = [_clean_text(row) for row in summary_rows if _clean_text(row)]
    summary_text = {}
    for row in summary_rows:
        if row.startswith("Date:"):
            summary_text["date"] = row
        elif row.startswith("LTP:"):
            summary_text["ltp"] = row
        elif row.startswith("Total Turnover:"):
            summary_text["total_turnover"] = row
        elif row.startswith("Total Traded Quantity:"):
            summary_text["total_traded_quantity"] = row
        elif row.startswith("Total Transaction:"):
            summary_text["total_transaction"] = row
        elif row.startswith("Trading at Intraday Higher Price Range:"):
            summary_text["higher_range_pct"] = row
        elif row.startswith("Trading at Intraday Lower Price Range:"):
            summary_text["lower_range_pct"] = row

    async def grid_rows():
        for _ in range(5):
            rows = await browser.page.get_by_role("grid").first.get_by_role("row").all_text_contents()
            cleaned_rows = [_clean_text(row) for row in rows[1:] if _clean_text(row)]
            data_rows = [row for row in cleaned_rows if any(char.isdigit() for char in row)]
            if len(data_rows) >= 3:
                return data_rows[:10]
            await asyncio.sleep(0.5)
        return data_rows[:10] if "data_rows" in locals() else []

    async def regular_table_rows(table_index=1):
        for _ in range(5):
            locator = browser.page.locator("table").filter(has_text="Contract Number").filter(has_text="Time").first.locator("tr")
            rows = await locator.all_text_contents()
            cleaned_rows = [_clean_text(row) for row in rows[1:] if _clean_text(row)]
            data_rows = [row for row in cleaned_rows if any(char.isdigit() for char in row)]
            if len(data_rows) >= 3:
                return data_rows[:15]
            await asyncio.sleep(0.5)
        return data_rows[:15] if "data_rows" in locals() else []

    await browser.page.locator("[href='#buyer-side']").click()
    await asyncio.sleep(0.6)
    buyer_rows = await grid_rows()

    await browser.page.locator("[href='#seller-side']").click()
    await asyncio.sleep(0.6)
    seller_rows = await grid_rows()

    await browser.page.locator("[href='#ending-floorsheet']").click()
    await asyncio.sleep(0.6)
    last_15_rows = await regular_table_rows()

    try:
        await browser.page.get_by_role("button", name="×").click(timeout=3000)
    except Exception:
        pass

    return {
        "summary_text": summary_text,
        "parsed": {
            "ltp": _parse_float(summary_text.get("ltp")),
            "total_turnover": _parse_float(summary_text.get("total_turnover")),
            "total_traded_quantity": _parse_int(summary_text.get("total_traded_quantity")),
            "total_transaction": _parse_int(summary_text.get("total_transaction")),
            "higher_range_pct": _parse_float(summary_text.get("higher_range_pct")),
            "lower_range_pct": _parse_float(summary_text.get("lower_range_pct")),
        },
        "buyer_side": _summarize_broker_side(buyer_rows),
        "seller_side": _summarize_broker_side(seller_rows),
        "last_15_minutes": _summarize_last_15(last_15_rows),
    }


async def _extract_visible_tables(page):
    return await page.evaluate(
        """
() => {
  const isVisible = (element) => {
    if (!element) return false;
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  };

  return Array.from(document.querySelectorAll('table'))
    .filter((table) => isVisible(table))
    .map((table, index) => {
      const rows = Array.from(table.querySelectorAll('tr')).map((tr) =>
        Array.from(tr.querySelectorAll('th,td'))
          .map((cell) => (cell.innerText || '').replace(/\\s+/g, ' ').trim())
          .filter(Boolean)
      ).filter((row) => row.length > 0);
      return { index, rows };
    })
    .filter((table) => table.rows.length > 1);
}
        """
    )


async def extract_broker_holdings_context(browser, symbol):
    await browser.page.goto(f"https://nepsealpha.com/broker-holding?symbol={symbol}", wait_until="domcontentloaded")
    await browser.page.get_by_text("Top Broker Holding").first.wait_for(timeout=15000)

    async def capture_period(period_name):
        combobox = browser.page.locator("#report-types")
        if await combobox.count():
            await combobox.select_option(label=period_name)
            await asyncio.sleep(1.2)
        tables = await _extract_visible_tables(browser.page)
        headings = await browser.page.evaluate(
            """
() => Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,strong'))
  .map((node) => (node.innerText || '').replace(/\\s+/g, ' ').trim())
  .filter(Boolean)
            """
        )
        def transpose_table_rows(rows):
            if len(rows) < 2:
                return []
            header_row = rows[0]
            value_row = rows[1]
            pairs = []
            for index in range(1, min(len(header_row), len(value_row))):
                broker = header_row[index]
                qty = value_row[index]
                if broker and qty:
                    pairs.append([broker, qty])
            return pairs[:10]

        top_buyers = transpose_table_rows(tables[0]["rows"]) if len(tables) >= 1 else []
        top_sellers = transpose_table_rows(tables[1]["rows"]) if len(tables) >= 2 else []
        return {
            "period": period_name.lower(),
            "heading": next((heading for heading in headings if "Top Broker Holding" in heading), None),
            "top_buyers": top_buyers,
            "top_sellers": top_sellers,
            "dominant_buyer": top_buyers[0][0] if top_buyers and top_buyers[0] else None,
            "dominant_seller": top_sellers[0][0] if top_sellers and top_sellers[0] else None,
            "top_buyer_net_qty": _parse_int(top_buyers[0][1]) if top_buyers and len(top_buyers[0]) > 1 else None,
            "top_seller_net_qty": _parse_int(top_sellers[0][1]) if top_sellers and len(top_sellers[0]) > 1 else None,
        }

    monthly = await capture_period("Monthly")
    weekly = await capture_period("Weekly")
    return {"monthly": monthly, "weekly": weekly}


async def extract_trader_volume_sentiment_context(browser, symbol):
    await browser.page.goto(f"https://nepsealpha.com/buy-sell-depth?symbol={symbol}", wait_until="domcontentloaded")
    await asyncio.sleep(1.5)
    tables = await _extract_visible_tables(browser.page)
    symbol_row = None
    headers = []
    for table in tables:
        if not table["rows"]:
            continue
        if not headers:
            headers = table["rows"][0]
        for row in table["rows"][1:]:
            if row and row[0] == symbol:
                symbol_row = row
                break
        if symbol_row:
            break
    return {
        "headers": headers,
        "symbol_row": symbol_row,
        "available": symbol_row is not None,
    }


async def extract_broker_holding_changes_context(browser, symbol):
    await browser.page.goto(f"https://nepsealpha.com/broker-holding-changes?symbol={symbol}", wait_until="domcontentloaded")
    await asyncio.sleep(1.5)
    page_size_select = browser.page.locator("select").first
    if await page_size_select.count():
        await page_size_select.select_option("100")
        await asyncio.sleep(1.5)

    row_data = await browser.page.evaluate(
        """
() => {
  const isVisible = (element) => {
    if (!element) return false;
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  };

  const tables = Array.from(document.querySelectorAll('table')).filter((table) => isVisible(table));
  for (const table of tables) {
    const rows = Array.from(table.querySelectorAll('tr')).map((tr) =>
      Array.from(tr.querySelectorAll('th,td'))
        .map((cell) => (cell.innerText || '').replace(/\\s+/g, ' ').trim())
        .filter(Boolean)
    ).filter((row) => row.length > 0);
    const header = rows[0] || [];
    const match = rows.find((row, index) => index > 0 && row[0] === SYMBOL_PLACEHOLDER);
    if (match) {
      return { header, row: match };
    }
  }
  return null;
}
        """.replace("SYMBOL_PLACEHOLDER", json.dumps(symbol))
    )

    if not row_data:
        return {"available": False, "symbol": symbol}

    raw_row = row_data.get("row") or []
    rise_cells = raw_row[1:6]
    fall_cells = raw_row[6:11]
    rises = [parse_broker_change_cell(cell) for cell in rise_cells if cell]
    falls = [parse_broker_change_cell(cell) for cell in fall_cells if cell]
    largest_rise = max((item for item in rises if item.get("net_qty") is not None), key=lambda item: item["net_qty"], default=None)
    largest_fall = min((item for item in falls if item.get("net_qty") is not None), key=lambda item: item["net_qty"], default=None)

    return {
        "available": True,
        "symbol": symbol,
        "headers": row_data.get("header") or [],
        "rises": rises,
        "falls": falls,
        "largest_rise": largest_rise,
        "largest_fall": largest_fall,
        "net_change_signal": "accumulation" if (largest_rise or {}).get("net_qty", 0) > abs((largest_fall or {}).get("net_qty", 0)) else "distribution" if largest_fall else "mixed",
    }


async def capture_browser_edge_features(browser, symbol, sector_name):
    async def safe_capture(label, coro, default_payload):
        try:
            return await coro
        except Exception as exc:
            print(f"WARNING: browser edge capture failed for {symbol} {label}: {exc}")
            fallback = dict(default_payload)
            fallback["available"] = False
            fallback["error"] = str(exc)
            return fallback

    browser_market = await capture_multi_timeframe(browser, "NEPSE", ["1D", "1W", "1M"])
    sector_index_symbol = SECTOR_INDEX_SYMBOLS.get(str(sector_name).upper())
    browser_sector = {}
    if sector_index_symbol:
        browser_sector = await capture_multi_timeframe(browser, sector_index_symbol, ["1D", "1W", "1M"])
    browser_stock = await capture_multi_timeframe(browser, symbol, ["1D", "1W", "1M"])
    floorsheet = await safe_capture(
        "floorsheet",
        extract_floorsheet_context(browser, symbol),
        {
            "symbol": symbol,
            "summary_text": {},
            "parsed": {},
            "buyer_side": {},
            "seller_side": {},
            "last_15_minutes": {},
        },
    )
    broker_holdings = await safe_capture(
        "broker_holdings",
        extract_broker_holdings_context(browser, symbol),
        {
            "symbol": symbol,
            "weekly": {},
            "monthly": {},
        },
    )
    broker_holding_changes = await safe_capture(
        "broker_holding_changes",
        extract_broker_holding_changes_context(browser, symbol),
        {
            "symbol": symbol,
            "headers": [],
            "rises": [],
            "falls": [],
            "largest_rise": None,
            "largest_fall": None,
            "net_change_signal": "mixed",
        },
    )
    trader_volume_sentiment = await safe_capture(
        "trader_volume_sentiment",
        extract_trader_volume_sentiment_context(browser, symbol),
        {
            "symbol": symbol,
            "headers": [],
            "symbol_row": None,
        },
    )
    broker_edge_summary = build_broker_edge_summary(
        floorsheet,
        broker_holdings,
        broker_holding_changes,
        trader_volume_sentiment,
    )

    return {
        "session": build_market_session_context(),
        "browser_market": browser_market,
        "browser_sector": browser_sector,
        "browser_stock": browser_stock,
        "floorsheet": floorsheet,
        "broker_holdings": broker_holdings,
        "broker_holding_changes": broker_holding_changes,
        "trader_volume_sentiment": trader_volume_sentiment,
        "broker_edge_summary": broker_edge_summary,
    }
