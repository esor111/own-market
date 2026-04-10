"""
Build an LLM-ready manual package for one symbol by combining the existing
analysis pipeline, truth-layer data, and a few browser-only context pages.

Usage:
    python manual_llm_package.py JBBL 1W
"""
import asyncio
import json
import os
import sys
import warnings
from datetime import datetime

from analyze_stock import StockAnalysisAutomation
from browser_edge_features import capture_browser_edge_features
from config import get_run_directories
from forward_context_enrichment import (
    build_market_breadth_lines,
    build_nrb_macro_lines,
    build_sharesansar_event_lines,
    format_manual_context_block,
    load_live_nrb_macro_snapshot,
    load_manual_context_overlay,
    load_merolagani_market_breadth,
    load_sharesansar_company_event_timing,
)
from memory_store import build_memory_store
from replay_family_guidance import resolve_latest_family_guidance
from similar_setup_retrieval import retrieve_similar_setups


warnings.filterwarnings(
    "ignore",
    message=".*Unverified HTTPS request is being made to host 'www.nepalstock.com'.*",
)
warnings.filterwarnings(
    "ignore",
    message=".*SSL certificate verification has been disabled.*",
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def average(values):
    values = [float(value) for value in values if value is not None]
    return round(sum(values) / len(values), 2) if values else None


def pct_change(current, previous):
    if current in (None, 0) or previous in (None, 0):
        return None
    return round(((float(current) / float(previous)) - 1) * 100, 2)


def classify_change_trend(change_pct):
    if change_pct is None:
        return "unknown"
    if change_pct >= 2:
        return "up"
    if change_pct > 0:
        return "slightly_up"
    if change_pct <= -2:
        return "down"
    if change_pct < 0:
        return "slightly_down"
    return "flat"


def relative_strength_label(stock_change, benchmark_change):
    if stock_change is None or benchmark_change is None:
        return "unknown"
    if stock_change > benchmark_change + 1:
        return "stronger"
    if stock_change < benchmark_change - 1:
        return "weaker"
    return "equal"


def alignment_label(monthly_trend, weekly_trend, daily_trend):
    values = [monthly_trend, weekly_trend, daily_trend]
    up_count = sum(1 for value in values if value in {"uptrend", "up", "slightly_up"})
    down_count = sum(1 for value in values if value in {"downtrend", "down", "slightly_down"})
    if up_count == 3:
        return "fully_aligned"
    if up_count >= 2 and down_count == 0:
        return "mostly_aligned"
    if down_count >= 2 and up_count == 0:
        return "conflicted"
    return "mixed"


def infer_trade_quality(action, rr, qc_status):
    if qc_status != "pass":
        return "low-quality"
    if action == "buy" and rr is not None and rr >= 2:
        return "valid"
    if action == "watch_only" and rr is not None and rr >= 1.2:
        return "early"
    if rr is not None and rr < 1:
        return "low-quality"
    return "extended"


def build_truth_metrics(truth_bundle):
    history_rows = (((truth_bundle.get("history") or {}).get("history") or {}).get("content") or [])
    latest = history_rows[0] if history_rows else {}

    def pick(index, field):
        if index < len(history_rows):
            return history_rows[index].get(field)
        return None

    traded_values_5 = [row.get("totalTradedValue") for row in history_rows[:5]]
    traded_values_20 = [row.get("totalTradedValue") for row in history_rows[:20]]
    trades_5 = [row.get("totalTrades") for row in history_rows[:5]]
    trades_20 = [row.get("totalTrades") for row in history_rows[:20]]
    highs_20 = [row.get("highPrice") for row in history_rows[:20] if row.get("highPrice") is not None]
    lows_20 = [row.get("lowPrice") for row in history_rows[:20] if row.get("lowPrice") is not None]
    highs_60 = [row.get("highPrice") for row in history_rows[:60] if row.get("highPrice") is not None]
    lows_60 = [row.get("lowPrice") for row in history_rows[:60] if row.get("lowPrice") is not None]

    return {
        "latest_date": latest.get("businessDate"),
        "latest_close": latest.get("closePrice"),
        "return_1d_pct": pct_change(latest.get("closePrice"), latest.get("previousDayClosePrice")),
        "return_5d_pct": pct_change(pick(0, "closePrice"), pick(4, "closePrice")),
        "return_20d_pct": pct_change(pick(0, "closePrice"), pick(19, "closePrice")),
        "return_60d_pct": pct_change(pick(0, "closePrice"), pick(59, "closePrice")),
        "avg_value_5d": average(traded_values_5),
        "avg_value_20d": average(traded_values_20),
        "avg_trades_5d": average(trades_5),
        "avg_trades_20d": average(trades_20),
        "highest_high_20d": max(highs_20) if highs_20 else None,
        "lowest_low_20d": min(lows_20) if lows_20 else None,
        "highest_high_60d": max(highs_60) if highs_60 else None,
        "lowest_low_60d": min(lows_60) if lows_60 else None,
    }


def parse_floorsheet_row(row_text):
    parts = str(row_text).split()
    if len(parts) < 6:
        return {"raw": row_text}
    return {
        "broker": parts[0],
        "qty": parts[1],
        "matching": parts[2],
        "share_pct": f"{parts[3]} {parts[4]}" if len(parts) >= 5 else "",
        "amount": " ".join(parts[5:-2]) if len(parts) > 7 else "",
        "avg_price": " ".join(parts[-2:]) if len(parts) >= 2 else "",
        "raw": row_text,
    }


def build_markdown_package(symbol, timeframe, run_date, package):
    def numeric_or_zero(value):
        try:
            if value in (None, ""):
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def value_or_unknown(value):
        if value in (None, "", [], {}):
            return "unknown"
        return value

    market_browser = package["browser_market"]
    sector_browser = package["browser_sector"]
    stock_browser = package["browser_stock"]
    truth_metrics = package["truth_metrics"]
    today_row = package["truth_bundle"].get("ticker", {}).get("today_price_row") or {}
    event_data = package["event"]
    decision = package["decision"]
    qc = package["qc"]
    floorsheet = package["floorsheet"]
    broker_holdings = package["broker_holdings"]
    broker_holding_changes = package["broker_holding_changes"]
    broker_edge_summary = package.get("broker_edge_summary") or {}
    session = package["session"]
    trader_volume = package["trader_volume_sentiment"]
    similar_setups = package.get("similar_setups") or {}
    similar_summary = similar_setups.get("human_summary") or {}
    family_guidance = package.get("family_guidance") or {}
    symbol_family_guidance = family_guidance.get("symbol_guidance") or {}
    sector_family_guidance = family_guidance.get("sector_guidance") or {}
    nrb_macro_snapshot = package.get("nrb_macro_snapshot") or {}
    market_breadth = package.get("market_breadth_snapshot") or {}
    sharesansar_event_timing = package.get("sharesansar_event_timing") or {}
    manual_context = package.get("manual_context") or {}

    market_condition = "trending_up" if classify_change_trend(market_browser.get("1M", {}).get("change_pct")) in {"up", "slightly_up"} else "unclear"
    sector_rs_market = relative_strength_label(
        sector_browser.get("1W", {}).get("change_pct"),
        market_browser.get("1W", {}).get("change_pct"),
    )
    stock_rs_market_1w = relative_strength_label(
        stock_browser.get("1W", {}).get("change_pct"),
        market_browser.get("1W", {}).get("change_pct"),
    )
    stock_rs_sector_1w = relative_strength_label(
        stock_browser.get("1W", {}).get("change_pct"),
        sector_browser.get("1W", {}).get("change_pct"),
    )
    stock_rs_market_1d = relative_strength_label(
        stock_browser.get("1D", {}).get("change_pct"),
        market_browser.get("1D", {}).get("change_pct"),
    )
    stock_rs_sector_1d = relative_strength_label(
        stock_browser.get("1D", {}).get("change_pct"),
        sector_browser.get("1D", {}).get("change_pct"),
    )

    monthly_trend = package["timeframes"].get("1M", {}).get("stock", {}).get("trend_label") or classify_change_trend(stock_browser.get("1M", {}).get("change_pct"))
    weekly_trend = package["timeframes"].get("1W", {}).get("stock", {}).get("trend_label") or classify_change_trend(stock_browser.get("1W", {}).get("change_pct"))
    daily_trend = package["timeframes"].get("1D", {}).get("stock", {}).get("trend_label") or classify_change_trend(stock_browser.get("1D", {}).get("change_pct"))
    alignment = alignment_label(monthly_trend, weekly_trend, daily_trend)
    entry_zone = decision.get("entry_zone") or []
    entry_zone_text = f"{entry_zone[0]}-{entry_zone[-1]}" if entry_zone else "unknown"
    targets = ", ".join(str(target) for target in decision.get("targets", [])) or "unknown"
    floor_buyers = floorsheet.get("buyer_side", {}).get("rows", [])
    floor_sellers = floorsheet.get("seller_side", {}).get("rows", [])
    weekly_brokers = broker_holdings.get("weekly", {})
    monthly_brokers = broker_holdings.get("monthly", {})
    weekly_top_buyer_net_qty = numeric_or_zero(weekly_brokers.get("top_buyer_net_qty"))
    weekly_top_seller_net_qty = numeric_or_zero(weekly_brokers.get("top_seller_net_qty"))
    liquidity_quality = (
        "strong" if (today_row.get("totalTradedValue") or 0) >= 100_000_000 and (today_row.get("totalTrades") or 0) >= 500
        else "acceptable" if (today_row.get("totalTradedValue") or 0) >= 25_000_000 and (today_row.get("totalTrades") or 0) >= 150
        else "weak"
    )

    lines = [
        f"SYMBOL: {symbol}",
        f"DATE: {run_date}",
        f"PRIMARY_TIMEFRAME: {timeframe}",
        "HORIZON: swing / position",
        "",
        "Facts first:",
        f"- Company: {value_or_unknown(package['company_name'])}",
        f"- Sector: {value_or_unknown(package['sector_name'])}",
        f"- Market session now: {'open' if session.get('market_open_now') else 'closed'}",
        f"- Next tradable session: {value_or_unknown(session.get('next_trade_session'))}",
        f"- Browser 1D OHLC: O {value_or_unknown(stock_browser.get('1D', {}).get('open'))} / H {value_or_unknown(stock_browser.get('1D', {}).get('high'))} / L {value_or_unknown(stock_browser.get('1D', {}).get('low'))} / C {value_or_unknown(stock_browser.get('1D', {}).get('close'))} / {value_or_unknown(stock_browser.get('1D', {}).get('change_pct'))}%",
        f"- Browser 1W OHLC: O {value_or_unknown(stock_browser.get('1W', {}).get('open'))} / H {value_or_unknown(stock_browser.get('1W', {}).get('high'))} / L {value_or_unknown(stock_browser.get('1W', {}).get('low'))} / C {value_or_unknown(stock_browser.get('1W', {}).get('close'))} / {value_or_unknown(stock_browser.get('1W', {}).get('change_pct'))}%",
        f"- Browser 1M OHLC: O {value_or_unknown(stock_browser.get('1M', {}).get('open'))} / H {value_or_unknown(stock_browser.get('1M', {}).get('high'))} / L {value_or_unknown(stock_browser.get('1M', {}).get('low'))} / C {value_or_unknown(stock_browser.get('1M', {}).get('close'))} / {value_or_unknown(stock_browser.get('1M', {}).get('change_pct'))}%",
        f"- Truth-source daily row: O {value_or_unknown(today_row.get('openPrice'))} / H {value_or_unknown(today_row.get('highPrice'))} / L {value_or_unknown(today_row.get('lowPrice'))} / C {value_or_unknown(today_row.get('closePrice'))} / traded value {value_or_unknown(today_row.get('totalTradedValue'))} / trades {value_or_unknown(today_row.get('totalTrades'))}",
        "",
        "1. Market Regime",
        f"- NEPSE 1D change: {value_or_unknown(market_browser.get('1D', {}).get('change_pct'))}%",
        f"- NEPSE 1W trend: {classify_change_trend(market_browser.get('1W', {}).get('change_pct'))}, {value_or_unknown(market_browser.get('1W', {}).get('change_pct'))}%",
        f"- NEPSE 1M trend: {classify_change_trend(market_browser.get('1M', {}).get('change_pct'))}, {value_or_unknown(market_browser.get('1M', {}).get('change_pct'))}%",
        f"- Market condition: {market_condition}",
        "",
        "2. Sector Regime",
        f"- Sector: {value_or_unknown(package['sector_name'])}",
        f"- Sector 1D change: {value_or_unknown(sector_browser.get('1D', {}).get('change_pct'))}%",
        f"- Sector 1W trend: {classify_change_trend(sector_browser.get('1W', {}).get('change_pct'))}, {value_or_unknown(sector_browser.get('1W', {}).get('change_pct'))}%",
        f"- Sector 1M trend: {classify_change_trend(sector_browser.get('1M', {}).get('change_pct'))}, {value_or_unknown(sector_browser.get('1M', {}).get('change_pct'))}%",
        f"- Sector relative strength vs market: {sector_rs_market}",
        "",
        "3. Multi-Timeframe Structure",
        f"- 1M trend: {value_or_unknown(monthly_trend)}",
        f"- 1M structure: {value_or_unknown(package['timeframes'].get('1M', {}).get('stock', {}).get('structure_label'))}",
        f"- 1W trend: {value_or_unknown(weekly_trend)}",
        f"- 1W structure: {value_or_unknown(package['timeframes'].get('1W', {}).get('stock', {}).get('structure_label'))}",
        f"- 1D trend: {value_or_unknown(daily_trend)}",
        f"- 1D trigger/setup: {value_or_unknown(decision.get('setup_type'))}",
        f"- Alignment: {alignment}",
        "",
        "4. Current Technical Plan",
        f"- Current price: {value_or_unknown(decision.get('current_price') or today_row.get('closePrice') or stock_browser.get('1W', {}).get('close'))}",
        f"- Key support zone: {value_or_unknown(package['timeframes'].get('1W', {}).get('stock', {}).get('support_zones'))}",
        f"- Key resistance zone: {value_or_unknown(package['timeframes'].get('1W', {}).get('stock', {}).get('resistance_zones'))}",
        f"- Breakout level: {value_or_unknown(package['timeframes'].get('1W', {}).get('stock', {}).get('breakout_level'))}",
        f"- Invalidation level: {value_or_unknown(decision.get('invalidation_level') or package['timeframes'].get('1W', {}).get('stock', {}).get('invalidation_level'))}",
        f"- Entry zone: {entry_zone_text}",
        f"- Stop loss: {value_or_unknown(decision.get('stop_loss'))}",
        f"- Targets: {targets}",
        f"- Risk/reward: {value_or_unknown(decision.get('risk_reward_ratio'))}",
        "",
        "5. Relative Strength",
        f"- Stock vs NEPSE on 1W: {stock_rs_market_1w}",
        f"- Stock vs sector on 1W: {stock_rs_sector_1w}",
        f"- Stock vs NEPSE on 1D: {stock_rs_market_1d}",
        f"- Stock vs sector on 1D: {stock_rs_sector_1d}",
        f"- Leader or laggard: {'leader' if stock_rs_sector_1w == 'stronger' else 'laggard' if stock_rs_sector_1w == 'weaker' else 'unknown'}",
        "",
        "6. Liquidity / Tradability",
        f"- Daily traded value: {value_or_unknown(today_row.get('totalTradedValue'))}",
        f"- Average traded value: {value_or_unknown(truth_metrics.get('avg_value_20d'))}",
        f"- Total trades: {value_or_unknown(today_row.get('totalTrades'))}",
        f"- Liquidity quality: {liquidity_quality}",
        "- Spread/slippage concern: unknown",
        "",
        "7. Corporate Action / Event State",
        f"- Rights issue: {event_data.get('event_type') == 'rights_issue'}",
        f"- Bonus: {event_data.get('event_type') in {'bonus_share', 'bonus_share_listing'}}",
        f"- Dividend: {event_data.get('event_type') == 'dividend_notice'}",
        f"- Book closure: {event_data.get('event_type') == 'book_closure'}",
        f"- AGM: {event_data.get('event_type') == 'agm_notice'}",
        f"- Listing notice: {event_data.get('event_type') == 'listing_notice'}",
        f"- Other official notice: {value_or_unknown(event_data.get('event_type'))}",
        f"- Event status: {value_or_unknown(event_data.get('relevance_now'))}",
        f"- Is event likely to distort technicals?: {'yes' if event_data.get('relevance_now') == 'active_window' else 'no'}",
        "",
        "8. Broker / Floorsheet Context",
        f"- Total turnover from portal floorsheet summary: {value_or_unknown(floorsheet.get('parsed', {}).get('total_turnover'))}",
        f"- Total traded quantity: {value_or_unknown(floorsheet.get('parsed', {}).get('total_traded_quantity'))}",
        f"- Total transactions: {value_or_unknown(floorsheet.get('parsed', {}).get('total_transaction'))}",
        f"- Trading at intraday higher price range: {value_or_unknown(floorsheet.get('parsed', {}).get('higher_range_pct'))}%",
        f"- Trading at intraday lower price range: {value_or_unknown(floorsheet.get('parsed', {}).get('lower_range_pct'))}%",
        f"- Top buyer brokers visible: {value_or_unknown(floor_buyers)}",
        f"- Top seller brokers visible: {value_or_unknown(floor_sellers)}",
        f"- Buyer concentration (top 3 visible): {value_or_unknown(floorsheet.get('buyer_side', {}).get('top3_share_pct_total'))}%",
        f"- Seller concentration (top 3 visible): {value_or_unknown(floorsheet.get('seller_side', {}).get('top3_share_pct_total'))}%",
        f"- Last 15-minute trades summary: {value_or_unknown(floorsheet.get('last_15_minutes'))}",
        f"- Weekly broker holdings: {value_or_unknown(weekly_brokers)}",
        f"- Monthly broker holdings: {value_or_unknown(monthly_brokers)}",
        f"- Broker holding changes: {value_or_unknown(broker_holding_changes)}",
        f"- Trader volume sentiment row: {value_or_unknown(trader_volume.get('symbol_row'))}",
        f"- Buying concentrated or broad: {'broad' if (floorsheet.get('buyer_side', {}).get('visible_broker_count') or 0) >= 4 else 'concentrated'}",
        f"- Selling concentrated or broad: {'broad' if (floorsheet.get('seller_side', {}).get('visible_broker_count') or 0) >= 4 else 'concentrated'}",
        f"- Signs of accumulation: {'mild' if (floorsheet.get('parsed', {}).get('higher_range_pct') or 0) >= 60 or weekly_top_buyer_net_qty > abs(weekly_top_seller_net_qty) or broker_holding_changes.get('net_change_signal') == 'accumulation' else 'unknown'}",
        f"- Signs of distribution: {'mild' if abs(weekly_top_seller_net_qty) > weekly_top_buyer_net_qty or broker_holding_changes.get('net_change_signal') == 'distribution' else 'unknown'}",
        "- Floorsheet confidence: medium-high",
        "",
        "9. Compact Broker Edge Summary",
        f"- Headline: {value_or_unknown(broker_edge_summary.get('headline'))}",
        f"- Closing flow: {value_or_unknown(broker_edge_summary.get('closing_flow'))}",
        f"- Concentration signal: {value_or_unknown(broker_edge_summary.get('concentration_signal'))}",
        f"- Weekly holdings signal: {value_or_unknown(broker_edge_summary.get('weekly_holdings_signal'))}",
        f"- Monthly holdings signal: {value_or_unknown(broker_edge_summary.get('monthly_holdings_signal'))}",
        f"- Holding-change signal: {value_or_unknown(broker_edge_summary.get('holding_change_signal'))}",
        "",
        "10. Session / Execution Reality",
        f"- Session window: {value_or_unknown(session.get('session_window'))}",
        f"- Market open now: {value_or_unknown(session.get('market_open_now'))}",
        f"- Trading day today: {value_or_unknown(session.get('is_trading_day'))}",
        f"- Session risk flags: {value_or_unknown(session.get('session_risk_flags'))}",
        f"- Realistic execution note: {'next session planning required' if not session.get('market_open_now') else 'can act during active session'}",
        "",
        "11. High-Level Fundamentals",
        "- EPS trend: unknown",
        "- Book value trend: unknown",
        "- Recent quarterly result direction: unknown",
        "- Dilution/capital risk: unknown",
        "- Major quality red flag: unknown",
        "",
        "12. Similar Past Setup Context",
        f"- Summary: {value_or_unknown(similar_summary.get('headline'))}",
        "",
        "13. Replay Family Guidance",
        f"- Source replay: {value_or_unknown(family_guidance.get('source_replay_id'))}",
        f"- Use as: {value_or_unknown(family_guidance.get('use_as'))}",
        f"- Do not use as hard rule: {value_or_unknown(family_guidance.get('do_not_use_as_hard_rule'))}",
        f"- Symbol guidance: {value_or_unknown(symbol_family_guidance.get('guidance_label'))}",
        f"- Symbol sample confidence: {value_or_unknown(symbol_family_guidance.get('sample_confidence'))}",
        f"- Symbol note: {value_or_unknown(symbol_family_guidance.get('advisory_note'))}",
        f"- Sector guidance: {value_or_unknown(sector_family_guidance.get('guidance_label'))}",
        f"- Sector sample confidence: {value_or_unknown(sector_family_guidance.get('sample_confidence'))}",
        f"- Sector note: {value_or_unknown(sector_family_guidance.get('advisory_note'))}",
        "",
        "14. Main Uncertainties",
        f"- Biggest uncertainty 1: {qc.get('findings', ['unknown'])[0] if qc.get('findings') else 'unknown'}",
        f"- Biggest uncertainty 2: {'current price near immediate resistance' if package['timeframes'].get('1W', {}).get('stock', {}).get('breakout_level') not in (None, '') else 'unknown'}",
        "- Biggest uncertainty 3: fundamentals not included in this pass",
        "",
        "Facts vs inference:",
        "- Directly extracted facts: browser chart states, truth-source daily row/history, official-event match result, floorsheet summary and visible broker rows",
        "- Inference: trend labels, alignment label, support/resistance interpretation, entry/stop/targets framing",
        "",
        "Recommended task for another LLM:",
        "Based on the above data, give:",
        "1. final action: buy / watch_only / avoid",
        "2. confidence out of 100",
        "3. strongest reason for the decision",
        "4. strongest risk against the decision",
        "5. whether the setup is early, valid, extended, or low-quality",
        "6. whether the trade plan is practical in the real market",
        "7. what must happen next to upgrade confidence",
        "",
        "System summary:",
        f"- Current system decision: {value_or_unknown(decision.get('action'))}",
        f"- Current system confidence: {value_or_unknown(decision.get('confidence'))}",
        f"- Current setup quality: {infer_trade_quality(decision.get('action'), decision.get('risk_reward_ratio'), qc.get('status'))}",
    ]
    nrb_macro_lines = build_nrb_macro_lines(nrb_macro_snapshot)
    if nrb_macro_lines:
        insert_at = lines.index("2. Sector Regime")
        lines[insert_at:insert_at] = ["1.5 NRB Macro Snapshot", *nrb_macro_lines, ""]
    market_breadth_lines = build_market_breadth_lines(market_breadth)
    if market_breadth_lines:
        insert_at = lines.index("2. Sector Regime")
        lines[insert_at:insert_at] = ["1.75 Market Breadth / Participation", *market_breadth_lines, ""]
    sharesansar_event_lines = build_sharesansar_event_lines(sharesansar_event_timing)
    if sharesansar_event_lines:
        insert_at = lines.index("8. Broker / Floorsheet Context")
        lines[insert_at:insert_at] = ["7.5 ShareSansar Event Timing Snapshot", *sharesansar_event_lines, ""]
    for point in broker_edge_summary.get("summary_points", []):
        insert_at = lines.index("10. Session / Execution Reality")
        lines.insert(insert_at, f"- {point}")
    for point in similar_summary.get("key_points", []):
        insert_at = lines.index("14. Main Uncertainties")
        lines.insert(insert_at, f"- {point}")
    manual_context_block = format_manual_context_block(manual_context)
    if manual_context_block:
        lines.extend(["", manual_context_block])
    return "\n".join(lines) + "\n"


async def main():
    if len(sys.argv) < 3:
        print("Usage: python manual_llm_package.py SYMBOL TIMEFRAME [RUN_DATE]")
        sys.exit(1)

    symbol = sys.argv[1].upper()
    timeframe = sys.argv[2].upper()
    run_date = sys.argv[3] if len(sys.argv) >= 4 else datetime.now().strftime("%Y-%m-%d")
    automation = StockAnalysisAutomation(symbol, timeframe, run_date)

    try:
        await automation.browser.start()
        await automation.capture_market_context()
        await automation.analyze_symbol()
        await automation.capture_sector_evidence()
        await automation.capture_truth_layer()
        await automation.capture_event_context()
        await automation.generate_analysis()
        await automation.create_normalized_records()

        company_name = (
            (((automation.data.get("truth") or {}).get("ticker") or {}).get("ticker_info") or {}).get("companyName")
            or automation.data.get("stock", {}).get("series_title")
            or symbol
        )
        sector_name = (
            (((automation.data.get("truth") or {}).get("ticker") or {}).get("ticker_info") or {})
            .get("security", {})
            .get("companyId", {})
            .get("sectorMaster", {})
            .get("sectorDescription")
            or automation.data.get("sector", {}).get("name")
            or "UNKNOWN"
        )
        browser_edge = await capture_browser_edge_features(automation.browser, symbol, sector_name)
        nrb_macro_snapshot = load_live_nrb_macro_snapshot(run_date)
        market_breadth_snapshot = load_merolagani_market_breadth()
        sharesansar_event_timing = load_sharesansar_company_event_timing(symbol)
        manual_context = load_manual_context_overlay(symbol, run_date, timeframe)

        truth_metrics = build_truth_metrics(automation.data.get("truth") or {})
        package = {
            "symbol": symbol,
            "timeframe": timeframe,
            "run_date": run_date,
            "company_name": company_name,
            "sector_name": sector_name,
            "session": browser_edge["session"],
            "browser_market": browser_edge["browser_market"],
            "browser_sector": browser_edge["browser_sector"],
            "browser_stock": browser_edge["browser_stock"],
            "truth_bundle": automation.data.get("truth") or {},
            "truth_metrics": truth_metrics,
            "event": automation.data.get("event") or {},
            "decision": automation.data.get("decision") or {},
            "qc": automation.data.get("qc") or {},
            "timeframes": automation.data.get("timeframes") or {},
            "floorsheet": browser_edge["floorsheet"],
            "broker_holdings": browser_edge["broker_holdings"],
            "broker_holding_changes": browser_edge["broker_holding_changes"],
            "trader_volume_sentiment": browser_edge["trader_volume_sentiment"],
            "broker_edge_summary": browser_edge["broker_edge_summary"],
            "nrb_macro_snapshot": nrb_macro_snapshot,
            "market_breadth_snapshot": market_breadth_snapshot,
            "sharesansar_event_timing": sharesansar_event_timing,
            "manual_context": manual_context,
        }

        try:
            build_memory_store()
            package["similar_setups"] = retrieve_similar_setups(symbol, run_date, timeframe, top_n=5)
        except Exception as exc:
            package["similar_setups"] = {
                "human_summary": {
                    "headline": f"Similar setup retrieval unavailable: {exc}",
                    "key_points": [],
                }
            }

        package["family_guidance"] = resolve_latest_family_guidance(symbol, sector_name)

        run_dirs = get_run_directories(symbol, run_date)
        json_path = os.path.join(run_dirs["raw_tables"], f"{run_date}__{symbol}__{timeframe}__manual_package.json")
        md_path = os.path.join(run_dirs["base"], f"{run_date}__{symbol}__{timeframe}__manual_package.md")
        save_json(json_path, package)
        with open(md_path, "w", encoding="utf-8") as handle:
            handle.write(build_markdown_package(symbol, timeframe, run_date, package))

        print(f"✓ Created: {json_path}")
        print(f"✓ Created: {md_path}")
    finally:
        try:
            await automation.browser.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
