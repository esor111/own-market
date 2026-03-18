import asyncio
import re
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        frame = None
        for f in page.frames:
            if "tradingview" in (f.name or "").lower() and f != page.main_frame:
                frame = f
                break

        if frame is None:
            print("TradingView iframe not found")
            return

        print(f"Frame: name={frame.name} url={frame.url}")

        body_text = await frame.text_content("body") or ""
        body_text = re.sub(r"\s+", " ", body_text)

        ohlc_match = re.search(r"O\s*([\d,.]+).*?H\s*([\d,.]+).*?L\s*([\d,.]+).*?C\s*([\d,.]+)", body_text)
        if ohlc_match:
            print("OHLC text match:", ohlc_match.group(0)[:180])
            print("OHLC parsed tokens:", ohlc_match.groups())
        else:
            print("OHLC text match: not found")

        indicator_items = await frame.evaluate(
            """
() => {
  const nodes = Array.from(document.querySelectorAll('[data-name="legend-source-item"]'));
  return nodes.map((node) => {
    const title = node.querySelector('[data-name="legend-source-title"] .title-l31H9iuA')?.textContent?.trim() ||
                  node.querySelector('[data-name="legend-source-title"]')?.textContent?.trim() ||
                  '';
    const desc = node.querySelector('[data-name="legend-source-description"]')?.textContent?.trim() || '';
    const values = Array.from(node.querySelectorAll('.valueValue-l31H9iuA'))
      .map(v => (v.textContent || '').trim())
      .filter(Boolean);
    return { title, desc, values };
  });
}
            """
        )

        print("Legend items:")
        for item in indicator_items:
            print(item)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
