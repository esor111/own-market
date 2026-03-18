"""
Probe script: discover which symbol string loads the NEPSE index
and HYDROPOWER sector index on nepsealpha.com TradingView chart.

Run: python probe_index_symbols.py
Chrome must be running with --remote-debugging-port=9222
"""
import asyncio
import re
from playwright.async_api import async_playwright

CDP_URL = "http://localhost:9222"
CANDIDATES = {
    "NEPSE_index": ["NEPSE", "NEPSEIDX", "NEPSE200", "NEPSE50", "NEPSE:NEPSE", "NSE"],
    "HYDROPOWER_sector": ["HYDROPOWER", "HYDRO", "NEPSE:HYDROPOWER", "HYDROELECTRICITY"],
}


async def get_frame(page):
    for _ in range(20):
        await asyncio.sleep(1)
        for f in page.frames:
            if "tradingview" in f.name.lower() and f != page.main_frame:
                return f
    return None


async def try_symbol(frame, symbol):
    """Load symbol, wait, then return the chart title text and OHLCV snippet."""
    try:
        await frame.get_by_role("button", name="Symbol Search").click()
        await asyncio.sleep(1)
        search_box = frame.get_by_role("textbox", name="Search")
        await search_box.click()
        await search_box.press("Control+a")
        for c in symbol:
            await search_box.type(c, delay=60)
        await asyncio.sleep(1.5)

        # Try clicking exact match first
        try:
            await frame.get_by_text(symbol, exact=True).first.click()
        except Exception:
            await search_box.press("Enter")
        await asyncio.sleep(3)

        # Read what loaded
        body_text = await frame.text_content("body")

        # Grab the first 400 chars around OHLC pattern for a quick sanity check
        ohlc_match = re.search(r"O[\s]?([\d,\.]+).{0,60}H[\s]?([\d,\.]+).{0,60}L[\s]?([\d,\.]+).{0,60}C[\s]?([\d,\.]+)", body_text)
        ohlc_snippet = ohlc_match.group(0)[:80] if ohlc_match else "(no OHLC found)"

        # Try to read the chart symbol title from known selectors
        title_text = ""
        for sel in [
            ".chart-symbol-name",
            "[data-name='legend-series-item'] .title-l31H9iuA",
            ".js-symbol-short",
        ]:
            try:
                el = frame.locator(sel).first
                if await el.count() > 0:
                    title_text = (await el.text_content() or "").strip()
                    if title_text:
                        break
            except Exception:
                pass

        # Also check legend titles to see what's shown
        legend_titles = await frame.evaluate(
            """
() => {
  const nodes = Array.from(document.querySelectorAll('[data-name="legend-source-item"]'));
  return nodes.map(n => {
    const t = n.querySelector('[data-name="legend-source-title"] .title-l31H9iuA') ||
               n.querySelector('[data-name="legend-source-title"]');
    return (t?.textContent || '').trim();
  }).filter(Boolean);
}
            """
        )

        # Get header bar symbol — TradingView puts loaded symbol in button with title attr
        symbol_in_chart = ""
        try:
            symbol_in_chart = await frame.evaluate(
                "document.querySelector('[data-name=\"legend-series-item\"]')?.querySelector('.title-l31H9iuA')?.textContent?.trim() || ''"
            )
        except Exception:
            pass

        return {
            "searched": symbol,
            "chart_symbol": symbol_in_chart or title_text,
            "ohlc_snippet": ohlc_snippet,
            "legend_titles": legend_titles,
        }

    except Exception as e:
        return {"searched": symbol, "error": str(e)}


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"Connected. Current URL: {page.url}")

        frame = await get_frame(page)
        if not frame:
            print("ERROR: TradingView iframe not found. Make sure nepsealpha.com chart is open.")
            return

        print(f"Using frame: {frame.name}\n")

        for group, symbols in CANDIDATES.items():
            print(f"=== {group} ===")
            for sym in symbols:
                result = probe = await try_symbol(frame, sym)
                if "error" in result:
                    print(f"  [{sym}] ERROR: {result['error']}")
                else:
                    print(f"  [{sym}]")
                    print(f"    chart_symbol : {result['chart_symbol']}")
                    print(f"    ohlc_snippet : {result['ohlc_snippet']}")
                    print(f"    legend_titles: {result['legend_titles']}")
                print()

        print("Probe complete.")


asyncio.run(main())
