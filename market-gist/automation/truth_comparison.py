"""Reusable comparison logic between browser evidence and external truth data."""
from datetime import datetime


def normalize_sector_token(value):
    """Normalize sector names for loose matching."""
    if not value:
        return ""
    token = str(value).strip().upper()
    return "".join(char for char in token if char.isalnum())


def build_truth_comparison(symbol, run_date, timeframe, truth_bundle, browser_snapshot):
    """Build a comparison record from browser-side and provider-side evidence."""
    symbol = symbol.upper()

    browser_daily = browser_snapshot.get("daily_stock") or {}
    browser_primary = browser_snapshot.get("primary_stock") or {}
    browser_daily_indicator = browser_snapshot.get("daily_indicator") or {}
    browser_market = browser_snapshot.get("market") or {}
    browser_sector = browser_snapshot.get("sector") or {}

    ticker_row = truth_bundle.get("ticker", {}).get("today_price_row") or {}
    ticker_info = truth_bundle.get("ticker", {}).get("ticker_info") or {}
    history = truth_bundle.get("history", {}).get("history") or {}
    history_rows = history.get("content", []) if isinstance(history, dict) else []
    latest_history_row = history_rows[0] if history_rows else {}
    sector_summary = truth_bundle.get("market", {}).get("sectorwise_summary") or []

    sector_match = None
    browser_sector_name = browser_sector.get("sector_name") or browser_sector.get("name")
    browser_sector_token = normalize_sector_token(browser_sector_name)
    if browser_sector_token:
        for row in sector_summary:
            sector_name = row.get("sectorName")
            if normalize_sector_token(sector_name) == browser_sector_token:
                sector_match = row
                break

    api_close = ticker_row.get("closePrice")
    browser_close = browser_daily.get("close")
    close_diff = None
    if api_close is not None and browser_close is not None:
        close_diff = round(api_close - browser_close, 4)

    return {
        "symbol": symbol,
        "run_date": run_date,
        "timeframe": timeframe,
        "api_business_date": ticker_row.get("businessDate") or latest_history_row.get("businessDate"),
        "browser_files_found": {
            "daily_stock": bool(browser_daily),
            "primary_stock": bool(browser_primary),
            "daily_indicator": bool(browser_daily_indicator),
            "market": bool(browser_market),
            "sector": bool(browser_sector),
        },
        "api_vs_browser_daily": {
            "api_close": api_close,
            "browser_close": browser_close,
            "close_diff": close_diff,
            "api_open": ticker_row.get("openPrice"),
            "browser_open": browser_daily.get("open"),
            "api_high": ticker_row.get("highPrice"),
            "browser_high": browser_daily.get("high"),
            "api_low": ticker_row.get("lowPrice"),
            "browser_low": browser_daily.get("low"),
            "api_volume": ticker_row.get("totalTradedQuantity"),
            "browser_volume": browser_daily.get("volume"),
        },
        "api_ticker_truth": {
            "security_name": ticker_info.get("security", {}).get("securityName"),
            "sector_description": (
                ticker_info.get("security", {})
                .get("companyId", {})
                .get("sectorMaster", {})
                .get("sectorDescription")
            ),
            "fifty_two_week_high": (
                ticker_row.get("fiftyTwoWeekHigh")
                or ticker_info.get("securityDailyTradeDto", {}).get("fiftyTwoWeekHigh")
            ),
            "fifty_two_week_low": (
                ticker_row.get("fiftyTwoWeekLow")
                or ticker_info.get("securityDailyTradeDto", {}).get("fiftyTwoWeekLow")
            ),
            "market_capitalization": ticker_info.get("marketCapitalization"),
        },
        "api_market_truth": {
            "market_open": truth_bundle.get("market", {}).get("market_open"),
            "market_summary_rows": len(truth_bundle.get("market", {}).get("market_summary") or []),
            "sector_summary_rows": len(sector_summary),
        },
        "api_sector_match": {
            "browser_sector_name": browser_sector_name,
            "matched_sector_row": sector_match,
        },
        "api_history_truth": {
            "history_total_elements": history.get("totalElements") if isinstance(history, dict) else None,
            "latest_history_row": latest_history_row,
        },
        "captured_at": datetime.now().isoformat(),
    }
