"""
Run a lightweight truth-source scan to shortlist symbols before full browser deep-dives.
Usage:
    python light_scan.py 1W @controlled_expansion_v1
    python light_scan.py 1D SMHL EBL
"""
import json
import os
import sys
import warnings
from datetime import datetime, timedelta

from config import (
    DEFAULT_TRUTH_SOURCE,
    VALIDATION_DIR,
    build_run_label,
    get_latest_validation_filename,
    get_run_directories,
    get_validation_filename,
    resolve_symbols,
)
from data_sources import get_truth_source
from event_sources import OfficialEventExtractor

warnings.filterwarnings(
    "ignore",
    message=".*Unverified HTTPS request is being made to host 'www.nepalstock.com'.*",
)
warnings.filterwarnings(
    "ignore",
    message=".*SSL certificate verification has been disabled.*",
)


def parse_market_turnover(market_summary):
    """Extract total market turnover from provider market summary rows."""
    for row in market_summary or []:
        detail = str(row.get("detail") or "").lower()
        if "total turnover" in detail:
            try:
                return float(row.get("value") or 0)
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def normalize_history_rows(history_payload):
    """Flatten provider history into ascending business-date rows."""
    content = ((history_payload or {}).get("history") or {}).get("content") or []
    rows = []
    for item in content:
        close_price = item.get("closePrice")
        last_traded = item.get("lastTradedPrice")
        close_value = close_price if close_price not in (None, 0, 0.0) else last_traded
        if close_value in (None, 0, 0.0):
            continue
        rows.append({
            "businessDate": item.get("businessDate"),
            "openPrice": item.get("openPrice"),
            "highPrice": item.get("highPrice"),
            "lowPrice": item.get("lowPrice"),
            "closePrice": close_value,
            "totalTradedValue": item.get("totalTradedValue") or 0,
            "totalTrades": item.get("totalTrades") or 0,
        })
    rows.sort(key=lambda row: row.get("businessDate") or "")
    return rows


def average(values):
    """Return arithmetic mean or None for empty values."""
    filtered = [float(value) for value in values if value is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)


def get_scan_profile(timeframe):
    """Choose rolling windows based on the intended deep-dive horizon."""
    timeframe = str(timeframe).upper()
    if timeframe == "1D":
        return {"short_window": 10, "long_window": 20, "breakout_window": 20, "history_days": 90}
    if timeframe == "1M":
        return {"short_window": 50, "long_window": 120, "breakout_window": 180, "history_days": 420}
    return {"short_window": 20, "long_window": 50, "breakout_window": 60, "history_days": 220}


class LightScanEngine:
    """Truth-only shortlist scan for faster development and batch screening."""

    def __init__(self, timeframe, run_date, truth_source_name=DEFAULT_TRUTH_SOURCE):
        self.timeframe = str(timeframe).upper()
        self.run_date = run_date
        self.truth_source_name = truth_source_name
        self.truth_source = get_truth_source(truth_source_name, verify_ssl=False)
        self.event_extractor = OfficialEventExtractor()
        self.profile = get_scan_profile(self.timeframe)
        self.shared_market = self.truth_source.get_market_snapshot()
        self.shared_notices = self.truth_source.get_notices() if hasattr(self.truth_source, "get_notices") else {"notices": []}
        self.shared_disclosures = (
            self.truth_source.get_company_disclosures()
            if hasattr(self.truth_source, "get_company_disclosures")
            else {"disclosures": []}
        )
        self.market_turnover = parse_market_turnover(self.shared_market.get("market_summary"))

    def _build_truth_bundle(self, symbol):
        """Fetch the minimum truth data required for a quick screen."""
        history_days = self.profile["history_days"]
        end_date = self.run_date
        start_date = (datetime.strptime(self.run_date, "%Y-%m-%d") - timedelta(days=history_days)).strftime("%Y-%m-%d")
        history = self.truth_source.get_ticker_history(symbol, start_date, end_date)
        ticker = self.truth_source.get_ticker_snapshot(symbol)
        return {
            "provider": self.truth_source_name,
            "symbol": str(symbol).upper(),
            "market": self.shared_market,
            "ticker": ticker,
            "history": history,
            "disclosures": self.shared_disclosures,
            "notices": self.shared_notices,
            "captured_for_horizon": self.timeframe,
            "captured_at": datetime.now().isoformat(),
            "range": {"start_date": start_date, "end_date": end_date, "history_days": history_days},
        }

    def _sector_turnover_share(self, sector_name):
        sector_rows = (self.shared_market or {}).get("sectorwise_summary") or []
        if not sector_name or not self.market_turnover:
            return 0.0

        normalized_target = sector_name.lower().replace("_", " ").replace("power", "power")
        for row in sector_rows:
            source_name = str(row.get("sectorName") or "").lower()
            if source_name == normalized_target:
                return round(float(row.get("turnOverValues") or 0) / self.market_turnover, 4)
        return 0.0

    def _classify_liquidity(self, traded_value, total_trades):
        if traded_value >= 100_000_000 and total_trades >= 500:
            return "strong"
        if traded_value >= 25_000_000 and total_trades >= 150:
            return "acceptable"
        return "weak"

    def _score_symbol(self, truth_bundle):
        ticker = truth_bundle.get("ticker") or {}
        ticker_row = ticker.get("today_price_row") or {}
        ticker_info = ticker.get("ticker_info") or {}
        daily_trade = ticker_info.get("securityDailyTradeDto") or {}
        history_rows = normalize_history_rows(truth_bundle.get("history"))

        latest_close = (
            ticker_row.get("closePrice")
            or ticker_row.get("lastUpdatedPrice")
            or daily_trade.get("closePrice")
            or daily_trade.get("lastTradedPrice")
        )
        previous_close = ticker_row.get("previousDayClosePrice") or daily_trade.get("previousClose")
        traded_value = ticker_row.get("totalTradedValue") or 0
        total_trades = ticker_row.get("totalTrades") or daily_trade.get("totalTrades") or 0
        security_name = (
            ticker_row.get("securityName")
            or (((ticker_info.get("security") or {}).get("securityName")))
            or str(truth_bundle.get("symbol"))
        )
        sector_name = (
            ((((ticker_info.get("security") or {}).get("companyId") or {}).get("sectorMaster") or {}).get("sectorDescription"))
            or "Unknown"
        )

        closes = [row["closePrice"] for row in history_rows]
        highs = [row.get("highPrice") for row in history_rows if row.get("highPrice") is not None]
        short_window = self.profile["short_window"]
        long_window = self.profile["long_window"]
        breakout_window = self.profile["breakout_window"]

        sma_short = average(closes[-short_window:]) if len(closes) >= short_window else None
        sma_long = average(closes[-long_window:]) if len(closes) >= long_window else None
        prior_close_for_momentum = closes[-(short_window + 1)] if len(closes) > short_window else None
        momentum_pct = None
        if latest_close and prior_close_for_momentum:
            momentum_pct = round(((latest_close / prior_close_for_momentum) - 1) * 100, 2)

        breakout_high = max(highs[-breakout_window:]) if len(highs) >= breakout_window else (max(highs) if highs else None)
        distance_to_breakout_pct = None
        if latest_close and breakout_high:
            distance_to_breakout_pct = round(((breakout_high - latest_close) / latest_close) * 100, 2)

        liquidity_label = self._classify_liquidity(traded_value, total_trades)
        sector_turnover_share = self._sector_turnover_share(sector_name)
        daily_change_pct = None
        if latest_close and previous_close:
            daily_change_pct = round(((latest_close / previous_close) - 1) * 100, 2)

        event_record = self.event_extractor.find_recent_official_event(
            truth_bundle["symbol"],
            security_name,
            self.run_date,
            truth_bundle=truth_bundle,
        )
        event_type = event_record.get("event_type")
        active_event = event_record.get("event_found") and event_record.get("relevance_now") == "active_window"
        risky_event = event_type in {"rights_issue", "book_closure", "prospectus_offer", "debenture_offer"}

        score = 0
        reasons = []

        if latest_close and sma_short and latest_close > sma_short:
            score += 2
            reasons.append("price_above_short_average")
        if sma_short and sma_long and sma_short > sma_long:
            score += 2
            reasons.append("short_average_above_long_average")
        if momentum_pct is not None:
            if momentum_pct >= 5:
                score += 2
                reasons.append("strong_short_term_momentum")
            elif momentum_pct > 0:
                score += 1
                reasons.append("positive_short_term_momentum")
            else:
                reasons.append("weak_short_term_momentum")
        if distance_to_breakout_pct is not None:
            if 0 <= distance_to_breakout_pct <= 3:
                score += 2
                reasons.append("near_breakout_zone")
            elif 0 <= distance_to_breakout_pct <= 8:
                score += 1
                reasons.append("within_breakout_range")
        if liquidity_label == "strong":
            score += 2
            reasons.append("strong_liquidity")
        elif liquidity_label == "acceptable":
            score += 1
            reasons.append("acceptable_liquidity")
        else:
            reasons.append("weak_liquidity")
        if sector_turnover_share >= 0.10:
            score += 1
            reasons.append("active_sector_turnover")
        if active_event and risky_event:
            score -= 3
            reasons.append(f"active_risky_event:{event_type}")

        score = max(0, min(10, score))
        score_percent = score * 10

        if active_event and risky_event:
            action = "skip"
            next_step = "wait_for_event_window_to_clear"
        elif (
            latest_close
            and sma_short
            and sma_long
            and latest_close > sma_short
            and sma_short > sma_long
            and momentum_pct is not None
            and momentum_pct >= 5
            and distance_to_breakout_pct is not None
            and 0 <= distance_to_breakout_pct <= 8
            and liquidity_label in {"strong", "acceptable"}
            and not active_event
        ):
            action = "shortlist"
            next_step = "full_browser_deep_dive"
        elif liquidity_label == "weak":
            action = "skip"
            next_step = "skip_for_now"
        elif score >= 5:
            action = "review"
            next_step = "optional_browser_deep_dive"
        else:
            action = "skip"
            next_step = "skip_for_now"

        if active_event and not risky_event and action == "shortlist":
            action = "review"
            next_step = "optional_browser_deep_dive"
            reasons.append(f"active_context_event:{event_type}")
        if distance_to_breakout_pct is not None and distance_to_breakout_pct < 0 and action == "shortlist":
            action = "review"
            next_step = "optional_browser_deep_dive"
            reasons.append("already_extended_beyond_breakout_zone")

        return {
            "symbol": truth_bundle["symbol"],
            "action": action,
            "next_step": next_step,
            "score": score_percent,
            "liquidity_label": liquidity_label,
            "daily_change_pct": daily_change_pct,
            "latest_close": latest_close,
            "previous_close": previous_close,
            "sma_short": round(sma_short, 2) if sma_short is not None else None,
            "sma_long": round(sma_long, 2) if sma_long is not None else None,
            "momentum_pct": momentum_pct,
            "distance_to_breakout_pct": distance_to_breakout_pct,
            "sector_name": sector_name,
            "sector_turnover_share": sector_turnover_share,
            "traded_value": traded_value,
            "total_trades": total_trades,
            "event_type": event_type,
            "event_relevance": event_record.get("relevance_now"),
            "truth_source": self.truth_source_name,
            "scan_basis": "truth_daily_history",
            "reasons": reasons,
        }, truth_bundle

    def scan_symbol(self, symbol):
        """Scan one symbol and persist its light truth bundle."""
        truth_bundle = self._build_truth_bundle(symbol)
        result, persisted_bundle = self._score_symbol(truth_bundle)
        run_dirs = get_run_directories(symbol, self.run_date)
        output_path = os.path.join(
            run_dirs["raw_tables"],
            f"{self.run_date}__{str(symbol).upper()}__light_truth_bundle.json"
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump({
                "extraction_type": "light_truth_bundle",
                "truth_source": self.truth_source_name,
                "symbol": str(symbol).upper(),
                "data": persisted_bundle,
            }, handle, indent=2)
        result["light_truth_bundle"] = os.path.relpath(output_path, run_dirs["base"]).replace("\\", "/")
        return result


def main():
    if len(sys.argv) < 3:
        print("Usage: python light_scan.py TIMEFRAME SYMBOL_OR_LIST [SYMBOL_OR_LIST ...]")
        sys.exit(1)

    timeframe = sys.argv[1]
    raw_symbol_args = sys.argv[2:]
    try:
        symbols = resolve_symbols(raw_symbol_args)
    except ValueError as exc:
        print(str(exc))
        sys.exit(1)

    run_date = datetime.now().strftime("%Y-%m-%d")
    run_label = build_run_label(raw_symbol_args, symbols)
    engine = LightScanEngine(timeframe, run_date)
    results = [engine.scan_symbol(symbol) for symbol in symbols]
    results.sort(key=lambda item: ({"shortlist": 0, "review": 1, "skip": 2}.get(item["action"], 9), -item["score"], item["symbol"]))

    summary = {
        "run_date": run_date,
        "timeframe": str(timeframe).upper(),
        "run_label": run_label,
        "scan_mode": "truth_only_light_scan",
        "truth_source": engine.truth_source_name,
        "symbols": symbols,
        "results": results,
        "shortlist": [item["symbol"] for item in results if item["action"] == "shortlist"],
        "review_list": [item["symbol"] for item in results if item["action"] == "review"],
        "skip_list": [item["symbol"] for item in results if item["action"] == "skip"],
        "counts": {
            "shortlist": sum(1 for item in results if item["action"] == "shortlist"),
            "review": sum(1 for item in results if item["action"] == "review"),
            "skip": sum(1 for item in results if item["action"] == "skip"),
        },
    }

    os.makedirs(VALIDATION_DIR, exist_ok=True)
    output_path = os.path.join(
        VALIDATION_DIR,
        get_validation_filename("light_scan", timeframe, run_date, run_label)
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    latest_path = os.path.join(
        VALIDATION_DIR,
        get_latest_validation_filename("light_scan", timeframe, run_label)
    )
    with open(latest_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(f"Light scan saved: {output_path}")
    print(f"Latest light scan pointer saved: {latest_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
