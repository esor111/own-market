"""Manual verification of live chart contexts before relying on the main pipeline."""
import asyncio
import json
from browser_actions import BrowserAutomation


async def dump_context(browser, symbol, timeframe=None, with_indicators=False):
    print(f"\n=== VERIFY {symbol}{' ' + timeframe if timeframe else ''} ===")
    loaded = await browser.search_and_load_symbol(symbol)
    print(f"loaded={loaded}")
    await asyncio.sleep(2)

    if timeframe:
        timeframe_ok = await browser.set_timeframe(timeframe)
        print(f"timeframe_ok={timeframe_ok}")
        await asyncio.sleep(2)

    chart_data = await browser.extract_chart_data()
    print(f"chart_data={chart_data}")

    result = {
        "symbol": symbol,
        "timeframe": timeframe,
        "loaded": loaded,
        "chart_data": chart_data,
    }

    if with_indicators:
        already = await browser.has_expected_indicators()
        print(f"indicators_already_present={already}")
        indicator_data = await browser.extract_indicator_values()
        print(f"indicator_data={indicator_data}")
        result["indicators_already_present"] = already
        result["indicator_data"] = indicator_data

    return result


async def main():
    browser = BrowserAutomation()
    try:
        await browser.start()
        results = []
        results.append(await dump_context(browser, "NEPSE"))
        results.append(await dump_context(browser, "HYDROPOWER"))
        results.append(await dump_context(browser, "SMHL", "1W", with_indicators=True))

        with open("manual_verify_output.json", "w", encoding="utf-8") as file:
            json.dump(results, file, indent=2)
        print("Wrote manual_verify_output.json")
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
