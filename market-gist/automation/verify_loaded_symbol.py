import asyncio
import json
from browser_actions import BrowserAutomation


async def main():
    browser = BrowserAutomation()
    try:
        await browser.start()
        await browser.search_and_load_symbol("SMHL")
        await asyncio.sleep(2)
        await browser.set_timeframe("1W")
        await asyncio.sleep(2)

        symbol_info = await browser.frame.evaluate(
            """
() => {
  const seriesItem = document.querySelector('[data-name="legend-series-item"]');
  const title = seriesItem?.querySelector('.title-l31H9iuA')?.textContent?.trim() || '';
  const desc = seriesItem?.querySelector('[data-name="legend-source-description"]')?.textContent?.trim() || '';
  const text = seriesItem?.textContent?.trim() || '';
  return { title, desc, text };
}
            """
        )
        chart_data = await browser.extract_chart_data()
        print(json.dumps({"symbol_info": symbol_info, "chart_data": chart_data}, indent=2))
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
