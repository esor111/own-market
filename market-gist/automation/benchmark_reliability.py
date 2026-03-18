"""Run repeated extraction cycles and report reliability metrics."""
import asyncio
import json
from datetime import datetime

from browser_actions import BrowserAutomation
from config import INDICATORS


async def one_cycle(browser, symbol="SMHL", timeframe="1W"):
    result = {
        "symbol": symbol,
        "timeframe": timeframe,
        "loaded_symbol": None,
        "chart_data": {},
        "indicator_data": {},
        "ok": False,
        "issues": [],
    }

    ok = await browser.search_and_load_symbol(symbol)
    if not ok:
        result["issues"].append("symbol_load_failed")
        return result

    tf_ok = await browser.set_timeframe(timeframe)
    if not tf_ok:
        result["issues"].append("timeframe_set_failed")
        return result

    current_symbol = await browser.get_current_symbol_code()
    result["loaded_symbol"] = current_symbol
    if current_symbol and current_symbol.upper() != symbol.upper():
        result["issues"].append(f"symbol_mismatch:{current_symbol}")

    if not await browser.has_expected_indicators():
        for _, indicator_config in INDICATORS.items():
            added = await browser.add_indicator(indicator_config["name"], indicator_config.get("search"))
            if not added:
                result["issues"].append(f"indicator_add_failed:{indicator_config['name']}")
        await browser.close_indicators_dialog()

    chart_data = await browser.extract_chart_data()
    indicator_data = await browser.extract_indicator_values()

    result["chart_data"] = chart_data
    result["indicator_data"] = indicator_data

    required_chart = ["open", "high", "low", "close", "change_pct"]
    required_ind = ["ema_20", "ma_50", "rsi", "macd_line", "signal_line", "histogram"]

    for key in required_chart:
        if key not in chart_data:
            result["issues"].append(f"missing_chart:{key}")

    for key in required_ind:
        if key not in indicator_data:
            result["issues"].append(f"missing_indicator:{key}")

    # Sanity: OHLC ordering must hold for a valid candle
    if all(k in chart_data for k in ["open", "high", "low", "close"]):
        high = chart_data["high"]
        low = chart_data["low"]
        if not (high >= max(chart_data["open"], chart_data["close"]) and low <= min(chart_data["open"], chart_data["close"])):
            result["issues"].append("ohlc_consistency_failed")

    result["ok"] = len(result["issues"]) == 0
    return result


async def main(iterations=5):
    browser = BrowserAutomation()
    report = {
        "timestamp": datetime.now().isoformat(),
        "iterations": iterations,
        "results": [],
        "summary": {},
    }

    try:
        await browser.start()
        for i in range(iterations):
            print(f"\n--- Cycle {i+1}/{iterations} ---")
            cycle = await one_cycle(browser)
            report["results"].append(cycle)
            print(f"cycle_ok={cycle['ok']} issues={cycle['issues']}")
            await asyncio.sleep(1)
    finally:
        await browser.close()

    ok_count = sum(1 for r in report["results"] if r["ok"])
    report["summary"] = {
        "ok_count": ok_count,
        "fail_count": iterations - ok_count,
        "pass_rate_pct": round((ok_count / iterations) * 100, 2),
    }

    out_file = "benchmark_reliability_output.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\nBenchmark complete")
    print(json.dumps(report["summary"], indent=2))
    print(f"Wrote {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
