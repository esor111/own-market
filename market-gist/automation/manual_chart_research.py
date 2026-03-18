"""Manual capability audit for NEPSE Alpha TradingView chart.

This script connects to the live Chrome debug session, performs manual-like
UI interactions, and records what worked, what failed, and what data can be extracted.
"""
import asyncio
import json
import os
from datetime import datetime

from playwright.async_api import async_playwright

CDP_URL = "http://localhost:9222"
CHART_URL = "https://nepsealpha.com/nepse-chart"
OUT_DIR = os.path.join("..", "data", "raw", "tables")
SHOT_DIR = os.path.join("..", "data", "raw", "screenshots", "manual_research")


def now_stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def get_tv_frame(page):
    for _ in range(30):
        await asyncio.sleep(1)
        for f in page.frames:
            if "tradingview" in f.name.lower() and f != page.main_frame:
                return f
    return None


async def safe_click(locator, timeout=5000):
    try:
        await locator.first.click(timeout=timeout)
        return True
    except Exception:
        return False


async def gather_toolbar_candidates(frame):
    return await frame.evaluate(
        """
() => {
  const read = (nodes) => Array.from(nodes).map(n => {
    const label = n.getAttribute('aria-label') || n.getAttribute('title') || n.textContent || '';
    return label.trim();
  }).filter(Boolean);

  const buttons = read(document.querySelectorAll('button[aria-label], button[title]'));
  const tools = read(document.querySelectorAll('[aria-label][role="button"], [title][role="button"]'));

  const uniq = (arr) => [...new Set(arr)].slice(0, 400);
  return {
    buttons: uniq(buttons),
    tools: uniq(tools)
  };
}
        """
    )


async def chart_series_text(frame):
    return await frame.evaluate(
        """
() => {
  const seriesItem = document.querySelector('[data-name="legend-series-item"]');
  return (seriesItem?.textContent || '').trim();
}
        """
    )


async def extract_ohlc_from_series(frame):
    import re

    text = await chart_series_text(frame)
    pattern = r"O\s*([\d,\.]+).*?H\s*([\d,\.]+).*?L\s*([\d,\.]+).*?C\s*([\d,\.]+)"
    match = re.search(pattern, text or "")
    data = {}
    if match:
        data["open"] = float(match.group(1).replace(",", ""))
        data["high"] = float(match.group(2).replace(",", ""))
        data["low"] = float(match.group(3).replace(",", ""))
        # close can be duplicated in text; parse first valid float token
        close_token = match.group(4).replace(",", "")
        close_num = re.findall(r"-?\d+(?:\.\d{1,2})?", close_token)
        if close_num:
            data["close"] = float(close_num[0])

    ch = re.search(r"[−\-]([\d,\.]+)\s*\([−\-]([\d,\.]+)%\)", text or "")
    if ch:
        data["change"] = -float(ch.group(1).replace(",", ""))
        data["change_pct"] = -float(ch.group(2).replace(",", ""))

    return data, text


async def add_indicator(frame, name, search):
    result = {"indicator": name, "ok": False, "error": None}
    try:
        opened = await safe_click(frame.get_by_role("button", name="Indicators & Strategies"), timeout=6000)
        if not opened:
            raise RuntimeError("cannot open indicators dialog")

        box = frame.get_by_role("textbox", name="Search")
        await box.first.click(timeout=6000)
        await box.press("Control+a")
        await box.type(search, delay=40)
        await asyncio.sleep(1.0)

        clicked = await safe_click(frame.get_by_text(name, exact=True), timeout=6000)
        if not clicked:
            # fallback to contains text
            clicked = await safe_click(frame.get_by_text(name), timeout=6000)
        if not clicked:
            raise RuntimeError("indicator option not clickable")

        await asyncio.sleep(1.0)
        result["ok"] = True
    except Exception as exc:
        result["error"] = str(exc)
    finally:
        await safe_click(frame.get_by_role("button", name="Close menu"), timeout=2000)
    return result


async def try_drawing_tool(frame, page, label_options):
    """Try selecting a drawing tool and draw one segment on chart canvas."""
    outcome = {
        "selected_tool": None,
        "select_ok": False,
        "draw_ok": False,
        "error": None,
    }

    try:
        # Attempt direct tool selection by aria label or title.
        tool_chosen = None
        for label in label_options:
            by_role = frame.get_by_role("button", name=label)
            if await by_role.count() > 0:
                await by_role.first.click(timeout=3000)
                tool_chosen = label
                break
            by_title = frame.locator(f'[title="{label}"]')
            if await by_title.count() > 0:
                await by_title.first.click(timeout=3000)
                tool_chosen = label
                break

        if not tool_chosen:
            # Try opening a generic drawing toolbar/menu.
            await safe_click(frame.get_by_role("button", name="Drawings"), timeout=2000)
            await safe_click(frame.get_by_role("button", name="Brushes"), timeout=2000)
            # Retry tool lookup
            for label in label_options:
                by_role = frame.get_by_role("button", name=label)
                if await by_role.count() > 0:
                    await by_role.first.click(timeout=3000)
                    tool_chosen = label
                    break

        if not tool_chosen:
            raise RuntimeError("drawing tool not found")

        outcome["selected_tool"] = tool_chosen
        outcome["select_ok"] = True

        # Draw on first visible canvas in iframe by dragging.
        canvas = frame.locator("canvas").first
        box = await canvas.bounding_box()
        if not box:
            raise RuntimeError("chart canvas not found")

        x1 = box["x"] + box["width"] * 0.35
        y1 = box["y"] + box["height"] * 0.35
        x2 = box["x"] + box["width"] * 0.60
        y2 = box["y"] + box["height"] * 0.55

        await page.mouse.move(x1, y1)
        await page.mouse.down()
        await page.mouse.move(x2, y2)
        await page.mouse.up()
        await asyncio.sleep(1.0)
        outcome["draw_ok"] = True
    except Exception as exc:
        outcome["error"] = str(exc)

    return outcome


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(SHOT_DIR, exist_ok=True)

    stamp = now_stamp()
    out_path = os.path.join(OUT_DIR, f"{stamp}__manual_chart_research.json")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        if "nepsealpha.com" not in (page.url or ""):
            await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=45000)

        frame = await get_tv_frame(page)
        if not frame:
            raise RuntimeError("TradingView iframe not found")

        report = {
            "timestamp": datetime.now().isoformat(),
            "url": page.url,
            "frame_name": frame.name,
            "capabilities": {},
            "valuable_data": {},
            "artifacts": [],
            "notes": [],
        }

        # Baseline screenshot
        shot = os.path.join(SHOT_DIR, f"{stamp}__baseline.png")
        await page.screenshot(path=shot, full_page=True)
        report["artifacts"].append(shot)

        # 1) Symbol + timeframe interactions
        steps = []
        sym_open = await safe_click(frame.get_by_role("button", name="Symbol Search"), timeout=7000)
        steps.append({"action": "open_symbol_search", "ok": sym_open})
        if sym_open:
            try:
                box = frame.get_by_role("textbox", name="Search")
                await box.first.click(timeout=6000)
                await box.press("Control+a")
                await box.type("SMHL", delay=50)
                await asyncio.sleep(1.0)
                picked = await safe_click(frame.get_by_text("SMHL", exact=True), timeout=5000)
                if not picked:
                    await box.press("Enter")
                    picked = True
                steps.append({"action": "load_symbol_SMHL", "ok": picked})
            except Exception as exc:
                steps.append({"action": "load_symbol_SMHL", "ok": False, "error": str(exc)})

        tf_ok = False
        for t in ["1 week", "W", "1W"]:
            btn = frame.get_by_role("button", name=t)
            if await btn.count() > 0:
                tf_ok = await safe_click(btn, timeout=3000)
                if tf_ok:
                    break
        if not tf_ok:
            tf_ok = await safe_click(frame.get_by_text("W", exact=True), timeout=3000)
        steps.append({"action": "set_timeframe_1W", "ok": tf_ok})

        shot = os.path.join(SHOT_DIR, f"{stamp}__smhl_1w.png")
        await page.screenshot(path=shot, full_page=True)
        report["artifacts"].append(shot)

        report["capabilities"]["symbol_timeframe"] = steps

        # 2) Indicator interactions
        indicator_results = []
        indicator_results.append(await add_indicator(frame, "MACD", "macd"))
        indicator_results.append(await add_indicator(frame, "Relative Strength Index", "rsi"))
        report["capabilities"]["indicators"] = indicator_results

        shot = os.path.join(SHOT_DIR, f"{stamp}__with_indicators.png")
        await page.screenshot(path=shot, full_page=True)
        report["artifacts"].append(shot)

        # 3) Drawing interactions
        draw_result = await try_drawing_tool(
            frame,
            page,
            [
                "Trend Line",
                "Horizontal Line",
                "Ray",
                "Rectangle",
                "Brush",
                "Text",
            ],
        )
        report["capabilities"]["drawing"] = draw_result

        shot = os.path.join(SHOT_DIR, f"{stamp}__after_draw_attempt.png")
        await page.screenshot(path=shot, full_page=True)
        report["artifacts"].append(shot)

        # 4) What high-value data can be extracted directly
        ohlc, series_text = await extract_ohlc_from_series(frame)
        indicator_values = await frame.evaluate(
            """
() => {
  const nodes = Array.from(document.querySelectorAll('[data-name="legend-source-item"]'));
  return nodes.map((node) => {
    const titleNode = node.querySelector('[data-name="legend-source-title"] .title-l31H9iuA') ||
                      node.querySelector('[data-name="legend-source-title"]');
    const title = (titleNode?.textContent || '').trim();
    const desc = (node.querySelector('[data-name="legend-source-description"]')?.textContent || '').trim();
    const values = Array.from(node.querySelectorAll('.valueValue-l31H9iuA'))
      .map(v => (v.textContent || '').trim())
      .filter(Boolean);
    return { title, desc, values };
  });
}
            """
        )

        report["valuable_data"] = {
            "series_text": series_text,
            "ohlc_change": ohlc,
            "indicator_legend_items": indicator_values,
        }

        toolbar = await gather_toolbar_candidates(frame)
        report["capabilities"]["visible_toolbar_labels"] = toolbar

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"Wrote research report: {out_path}")
        print(f"Screenshots saved to: {SHOT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
