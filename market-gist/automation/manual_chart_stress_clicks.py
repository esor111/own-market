"""Stress-click key TradingView controls and record what works."""
import asyncio
import json
import os
from datetime import datetime

from playwright.async_api import async_playwright

CDP_URL = "http://localhost:9222"
CHART_URL = "https://nepsealpha.com/nepse-chart"
OUT_DIR = os.path.join("..", "data", "raw", "tables")


async def get_tv_frame(page):
    for _ in range(30):
        await asyncio.sleep(1)
        for f in page.frames:
            if "tradingview" in f.name.lower() and f != page.main_frame:
                return f
    return None


async def click_by_name(frame, name, timeout=4000):
    try:
        btn = frame.get_by_role("button", name=name)
        if await btn.count() == 0:
            return {"control": name, "ok": False, "reason": "not_found"}
        target = btn.first
        await target.scroll_into_view_if_needed(timeout=timeout)
        try:
            await target.click(timeout=timeout)
        except Exception:
            # Some toolbars require force click due overlays/transitions.
            await target.click(timeout=timeout, force=True)
        await asyncio.sleep(0.4)
        return {"control": name, "ok": True}
    except Exception as exc:
        return {"control": name, "ok": False, "reason": str(exc)}


async def reset_ui_state(frame):
    """Best-effort reset between actions so one menu does not block other controls."""
    try:
        await frame.keyboard.press("Escape")
        await asyncio.sleep(0.2)
        await frame.keyboard.press("Escape")
    except Exception:
        pass

    for close_name in ["Close menu", "Close"]:
        try:
            close_btn = frame.get_by_role("button", name=close_name)
            if await close_btn.count() > 0:
                await close_btn.first.click(timeout=700, force=True)
        except Exception:
            pass


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(OUT_DIR, f"{stamp}__manual_chart_stress_clicks.json")

    controls = [
        "Symbol Search",
        "Compare or Add Symbol",
        "Candles",
        "Indicators & Strategies",
        "Indicator Templates",
        "Chart settings",
        "Take a snapshot",
        "Chart Modes",
        "Cross",
        "Trend Line",
        "Fib Retracement",
        "Brush",
        "Text",
        "Measure",
        "Zoom In",
        "Magnet Mode snaps drawings placed near price bars to the closest OHLC value",
        "Stay in Drawing Mode",
        "Lock All Drawing Tools",
        "Hide all drawings",
        "Show Object Tree",
        "Toggle Percentage",
        "Toggle Log Scale",
        "Toggle Auto Scale",
        "Go to",
        "Timezone",
    ]

    results = {
        "timestamp": datetime.now().isoformat(),
        "url": None,
        "frame_name": None,
        "click_results": [],
        "counts": {"ok": 0, "failed": 0},
    }

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        if "nepsealpha.com" not in (page.url or ""):
            await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=45000)

        results["url"] = page.url
        frame = await get_tv_frame(page)
        if not frame:
            raise RuntimeError("TradingView iframe not found")
        results["frame_name"] = frame.name

        for name in controls:
            await reset_ui_state(frame)
            r = await click_by_name(frame, name)
            results["click_results"].append(r)
            if r.get("ok"):
                results["counts"]["ok"] += 1
            else:
                results["counts"]["failed"] += 1

        await reset_ui_state(frame)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Wrote: {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
