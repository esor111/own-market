"""
Browser automation actions using Playwright
"""
import asyncio
import json
import random
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
from config import NEPSE_ALPHA_URL, BROWSER_TIMEOUT, SLOW_MO, HEADLESS


def random_delay(min_ms=500, max_ms=2000):
    """Add random human-like delay"""
    return asyncio.sleep(random.uniform(min_ms/1000, max_ms/1000))


class BrowserAutomation:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.frame = None
        
    async def start(self):
        """Start browser and navigate to NEPSE Alpha"""
        self.playwright = await async_playwright().start()
        
        # Try to connect to existing Chrome instance first
        try:
            print("  Attempting to connect to existing Chrome browser...")
            self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9222")
            
            # Get existing page or create new one
            if self.browser.contexts:
                context = self.browser.contexts[0]
                if context.pages:
                    self.page = context.pages[0]
                else:
                    self.page = await context.new_page()
            else:
                context = await self.browser.new_context()
                self.page = await context.new_page()
            
            print("✓ Connected to existing Chrome browser")
            
        except Exception as e:
            print(f"  Could not connect to existing browser: {e}")
            print("  Please run start_chrome.bat first!")
            raise e
        
        # Navigate to NEPSE Alpha if not already there
        current_url = self.page.url
        if "nepsealpha.com" not in current_url:
            print("  Navigating to NEPSE Alpha...")
            await self.page.goto(NEPSE_ALPHA_URL, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)
        else:
            print(f"  Already on NEPSE Alpha: {current_url}")
        
        # Wait for TradingView iframe to load
        print("  Waiting for TradingView chart to load...")
        
        # Wait up to 30 seconds for iframe to appear
        for i in range(30):
            await asyncio.sleep(1)
            frames = self.page.frames
            
            # Look for iframe by name pattern (tradingview_xxxxx)
            for frame in frames:
                frame_name = frame.name.lower()
                
                # TradingView iframes have names like "tradingview_7a045"
                if "tradingview" in frame_name and frame != self.page.main_frame:
                    self.frame = frame
                    print(f"✓ Found TradingView iframe: {frame.name}")
                    break
            
            if self.frame:
                break
            
            if i % 5 == 0 and i > 0:
                print(f"  Still waiting... ({i} seconds)")
        
        if not self.frame:
            print(f"\n  Available frames:")
            for idx, f in enumerate(self.page.frames):
                print(f"    Frame {idx}: name='{f.name}', url='{f.url}'")
            print("\n  TROUBLESHOOTING:")
            print("  1. Make sure you're on https://nepsealpha.com/nepse-chart")
            print("  2. Wait for the chart to fully load")
            print("  3. You should see a TradingView chart on the page")
            raise Exception("TradingView iframe not found - chart may not have loaded yet")
        
        print("✓ Browser started and NEPSE Alpha loaded")
        
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("✓ Browser closed")
    
    async def search_and_load_symbol(self, symbol):
        """Search for and load a symbol"""
        try:
            await random_delay(800, 1500)
            
            # Click symbol search button
            await self.frame.get_by_role("button", name="Symbol Search").click()
            await random_delay(1000, 1500)
            
            # Clear and type symbol in search box
            search_box = self.frame.get_by_role("textbox", name="Search")
            await search_box.click()
            await random_delay(300, 600)
            
            # Clear existing text using Ctrl+A and then type
            await search_box.press("Control+a")
            await random_delay(200, 400)
            
            # Type new symbol character by character
            for char in symbol:
                await search_box.type(char, delay=random.randint(50, 150))
            
            await random_delay(800, 1200)
            
            # Click on exact symbol if visible, otherwise fall back to Enter.
            try:
                await self.frame.get_by_text(symbol, exact=True).first.click(timeout=5000)
                await random_delay(2000, 3000)
            except Exception:
                # Fallback: press Enter (e.g. indices whose display name differs from symbol)
                await search_box.press("Enter")
                await random_delay(2000, 3000)
            
            print(f"✓ Loaded symbol: {symbol}")
            return True
        except Exception as e:
            print(f"✗ Error loading symbol {symbol}: {e}")
            return False
    
    async def set_timeframe(self, timeframe):
        """Set chart timeframe (1D, 1W, etc.)"""
        try:
            await random_delay(500, 1000)

            timeframe_candidates = {
                "1D": ["1 day", "D", "1D"],
                "1W": ["1 week", "W", "1W"],
                "1M": ["1 month", "M", "1M"]
            }

            candidates = timeframe_candidates.get(timeframe, [timeframe])
            clicked = False

            for candidate in candidates:
                try:
                    locator = self.frame.get_by_role("button", name=candidate).first
                    if await locator.count() > 0:
                        await locator.click()
                        clicked = True
                        break
                except:
                    pass

            # Last-resort fallback to text match when role-based selectors do not resolve.
            if not clicked:
                for candidate in candidates:
                    try:
                        locator = self.frame.get_by_text(candidate, exact=True).first
                        if await locator.count() > 0:
                            await locator.click()
                            clicked = True
                            break
                    except:
                        pass

            if not clicked:
                raise Exception(f"Timeframe control not found for: {timeframe}")
            
            await random_delay(1500, 2500)
            
            print(f"✓ Set timeframe: {timeframe}")
            return True
        except Exception as e:
            print(f"✗ Error setting timeframe: {e}")
            return False
    
    async def add_indicator(self, indicator_name, search_term=None):
        """Add an indicator to the chart"""
        try:
            await random_delay(600, 1200)

            # Ensure indicators dialog is open and search box is reachable.
            search_box = self.frame.get_by_role("textbox", name="Search")
            if await search_box.count() == 0:
                indicators_button = self.frame.get_by_role("button", name="Indicators & Strategies")
                await indicators_button.click(force=True)
                await random_delay(1000, 1500)

            # Retry once if search box does not appear due transient UI state.
            if await search_box.count() == 0:
                indicators_button = self.frame.get_by_role("button", name="Indicators & Strategies")
                await indicators_button.click(force=True)
                await random_delay(1000, 1500)

            if await search_box.count() == 0:
                raise Exception("Indicator search box not available")

            await search_box.first.click(timeout=5000)
            await random_delay(200, 400)
            
            # Clear and type search term
            await search_box.press("Control+a")
            await random_delay(100, 200)
            
            search_text = search_term or indicator_name
            for char in search_text:
                await search_box.type(char, delay=random.randint(50, 120))
            
            await random_delay(800, 1200)
            
            # Click on first exact match in strict mode to avoid duplicate-label ambiguity.
            await self.frame.get_by_text(indicator_name, exact=True).first.click()
            await random_delay(1000, 1500)
            
            print(f"✓ Added indicator: {indicator_name}")
            return True
        except Exception as e:
            print(f"✗ Error adding indicator {indicator_name}: {e}")
            return False
    
    async def has_expected_indicators(self):
        """Return True if EMA, MA, RSI and MACD legend items are already on the chart."""
        try:
            titles = await self.frame.evaluate(
                """
() => {
  const nodes = Array.from(document.querySelectorAll('[data-name="legend-source-item"]'));
  return nodes.map(node => {
    const t = node.querySelector('[data-name="legend-source-title"] .title-l31H9iuA') ||
               node.querySelector('[data-name="legend-source-title"]');
    return (t?.textContent || '').trim().toUpperCase();
  });
}
                """
            )
            required = {"EMA", "MA", "RSI", "MACD"}
            found = set(titles)
            return required.issubset(found)
        except Exception:
            return False

    async def close_indicators_dialog(self):
        """Close the indicators dialog"""
        try:
            await self.frame.get_by_role("button", name="Close menu").click()
            await asyncio.sleep(1)
            print("✓ Closed indicators dialog")
            return True
        except Exception as e:
            print(f"✗ Error closing indicators dialog: {e}")
            return False
    
    async def take_screenshot(self, filepath):
        """Take a screenshot of the page"""
        try:
            await self.page.screenshot(path=filepath, type="png")
            print(f"✓ Screenshot saved: {filepath}")
            return True
        except Exception as e:
            print(f"✗ Error taking screenshot: {e}")
            return False
    
    async def get_page_snapshot(self):
        """Get accessibility snapshot of the page"""
        try:
            # Get the iframe content
            snapshot = await self.frame.content()
            return snapshot
        except Exception as e:
            print(f"✗ Error getting snapshot: {e}")
            return None

    async def get_current_symbol_code(self):
        """Return currently selected symbol code shown in toolbar, if available."""
        try:
            symbol_code = await self.frame.evaluate(
                """
() => {
  const byId = document.querySelector('#header-toolbar-symbol-search .js-button-text');
  if (byId && byId.textContent) {
    return byId.textContent.trim();
  }

  const nodes = Array.from(document.querySelectorAll('[aria-label="Symbol Search"] .js-button-text'));
  const visible = nodes.find((n) => n && n.offsetParent !== null && (n.textContent || '').trim());
  return visible ? visible.textContent.trim() : '';
}
                """
            )
            return (symbol_code or "").strip()
        except Exception:
            return ""
    
    async def extract_chart_data(self):
        """Extract OHLCV and indicator data from chart"""
        try:
            # Wait a bit for data to load
            await asyncio.sleep(2)

            # Prefer visible active series legend text so hidden/stale nodes do not pollute parsing.
            series_payload = await self.frame.evaluate(
                """
() => {
    const nodes = Array.from(document.querySelectorAll('[data-name="legend-series-item"]'));
    const visibleNodes = nodes.filter((node) => {
        if (!node) return false;
        const style = window.getComputedStyle(node);
        return node.offsetParent !== null && style.visibility !== 'hidden' && style.display !== 'none';
    });

    const pick = (visibleNodes.length > 0 ? visibleNodes[visibleNodes.length - 1] : nodes[nodes.length - 1]);
    const text = (pick?.textContent || '').trim();
    const title = (pick?.querySelector('[data-name="legend-source-title"] .title-l31H9iuA')?.textContent || '').trim();
    return { text, title };
}
                """
            )

            series_text = (series_payload or {}).get("text", "")
            series_title = (series_payload or {}).get("title", "")

            # Fall back to the whole page body if the legend series text is unavailable.
            page_text = series_text or await self.frame.text_content("body")
            
            data = {}
            
            # Extract OHLCV using robust token patterns.
            import re

            def parse_first_numeric(raw_value):
                """Parse first well-formed number from a possibly concatenated token."""
                if not raw_value:
                    return None
                cleaned = raw_value.replace(",", "").replace('"', '').replace('−', '-').strip()
                candidates = re.findall(r"-?\d+(?:\.\d{1,2})?", cleaned)
                if not candidates:
                    return None
                return float(candidates[0])

            # Prefer grouped OHLC parsing since TradingView often concatenates tokens.
            ohlc_pattern = r"O\s*([\d,\.]+).*?H\s*([\d,\.]+).*?L\s*([\d,\.]+).*?C\s*([\d,\.]+)"
            ohlc_match = re.search(ohlc_pattern, page_text)
            if ohlc_match:
                o_val = parse_first_numeric(ohlc_match.group(1))
                h_val = parse_first_numeric(ohlc_match.group(2))
                l_val = parse_first_numeric(ohlc_match.group(3))
                c_val = parse_first_numeric(ohlc_match.group(4))

                if o_val is not None:
                    data["open"] = o_val
                if h_val is not None:
                    data["high"] = h_val
                if l_val is not None:
                    data["low"] = l_val
                if c_val is not None:
                    data["close"] = c_val
            else:
                field_patterns = {
                    "open": r"\bO\s*([^\s]+)",
                    "high": r"\bH\s*([^\s]+)",
                    "low": r"\bL\s*([^\s]+)",
                    "close": r"\bC\s*([^\s]+)"
                }

                for field, pattern in field_patterns.items():
                    match = re.search(pattern, page_text)
                    if match:
                        value = parse_first_numeric(match.group(1))
                        if value is not None:
                            data[field] = value
            
            # Extract volume
            volume_pattern = r'Volume\s*([\d,\.]+)([KMB])'
            match = re.search(volume_pattern, page_text)
            if match:
                value = float(match.group(1).replace(",", ""))
                unit = match.group(2)
                multipliers = {"K": 1000, "M": 1000000, "B": 1000000000}
                data["volume"] = int(value * multipliers.get(unit, 1))
            
            # Extract change percentage
            change_pattern = r'[−\-]([\d,\.]+)\s*\([−\-]([\d,\.]+)%\)'
            match = re.search(change_pattern, page_text)
            if match:
                data["change"] = -float(match.group(1).replace(",", ""))
                data["change_pct"] = -float(match.group(2).replace(",", ""))

            # Derive change fields when the chart legend omits them but OHLC is available.
            if "change" not in data and data.get("open") is not None and data.get("close") is not None:
                derived_change = round(data["close"] - data["open"], 2)
                data["change"] = derived_change

            if "change_pct" not in data and data.get("open") not in (None, 0) and data.get("close") is not None:
                derived_change_pct = round(((data["close"] - data["open"]) / data["open"]) * 100, 2)
                data["change_pct"] = derived_change_pct

            if series_title:
                data["series_title"] = series_title
            
            print(f"✓ Extracted chart data: {data}")
            return data
        except Exception as e:
            print(f"✗ Error extracting chart data: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    async def extract_indicator_values(self):
        """Extract indicator values from chart legend"""
        try:
            await asyncio.sleep(1)

            indicators = {}

            legend_items = await self.frame.evaluate(
                """
() => {
  const nodes = Array.from(document.querySelectorAll('[data-name="legend-source-item"]'));
  return nodes.map((node) => {
    const title = node.querySelector('[data-name="legend-source-title"] .title-l31H9iuA')?.textContent?.trim() ||
                  node.querySelector('[data-name="legend-source-title"]')?.textContent?.trim() || '';
    const desc = node.querySelector('[data-name="legend-source-description"]')?.textContent?.trim() || '';
    const values = Array.from(node.querySelectorAll('.valueValue-l31H9iuA'))
      .map(v => (v.textContent || '').trim())
      .filter(Boolean);
    return { title, desc, values };
  });
}
                """
            )

            def to_float(raw):
                if raw is None:
                    return None
                value = str(raw).replace(",", "").replace("−", "-").strip()
                if value in {"", "∅", "na", "n/a"}:
                    return None
                try:
                    return float(value)
                except ValueError:
                    return None

            ema_candidates = []
            ma_candidates = []

            for item in legend_items:
                title = (item.get("title") or "").upper()
                desc = (item.get("desc") or "")
                values = item.get("values") or []

                if title == "EMA":
                    period_match = __import__("re").search(r"(\d+)", desc)
                    period = int(period_match.group(1)) if period_match else None
                    val = to_float(values[0] if values else None)
                    if val is not None:
                        ema_candidates.append((period, val))

                elif title == "MA":
                    period_match = __import__("re").search(r"(\d+)", desc)
                    period = int(period_match.group(1)) if period_match else None
                    val = to_float(values[0] if values else None)
                    if val is not None:
                        ma_candidates.append((period, val))

                elif title == "RSI":
                    rsi_val = to_float(values[0] if values else None)
                    if rsi_val is not None:
                        indicators["rsi"] = rsi_val

                elif title == "MACD":
                    if len(values) >= 3:
                        macd_line = to_float(values[0])
                        signal_line = to_float(values[1])
                        histogram = to_float(values[2])
                        if macd_line is not None:
                            indicators["macd_line"] = macd_line
                        if signal_line is not None:
                            indicators["signal_line"] = signal_line
                        if histogram is not None:
                            indicators["histogram"] = histogram

            # Prefer configured periods if present; otherwise use first available candidate.
            for period, val in ema_candidates:
                if period == 20:
                    indicators["ema_20"] = val
                    break
            if "ema_20" not in indicators and ema_candidates:
                indicators["ema_20"] = ema_candidates[0][1]

            for period, val in ma_candidates:
                if period == 50:
                    indicators["ma_50"] = val
                    break
            if "ma_50" not in indicators and ma_candidates:
                indicators["ma_50"] = ma_candidates[0][1]
            
            print(f"✓ Extracted indicators: {indicators}")
            return indicators
        except Exception as e:
            print(f"✗ Error extracting indicators: {e}")
            import traceback
            traceback.print_exc()
            return {}
