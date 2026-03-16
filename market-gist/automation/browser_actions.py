"""
Browser automation actions using Playwright
"""
import asyncio
import json
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
from config import NEPSE_ALPHA_URL, BROWSER_TIMEOUT, SLOW_MO, HEADLESS


class BrowserAutomation:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.frame = None
        
    async def start(self):
        """Start browser and navigate to NEPSE Alpha"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO
        )
        self.page = await self.browser.new_page()
        await self.page.goto(NEPSE_ALPHA_URL, wait_until="networkidle", timeout=BROWSER_TIMEOUT)
        
        # Wait for TradingView iframe to load
        await asyncio.sleep(2)
        
        # Get the TradingView iframe
        frames = self.page.frames
        for frame in frames:
            if "tradingview" in frame.name.lower():
                self.frame = frame
                break
        
        if not self.frame:
            raise Exception("TradingView iframe not found")
        
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
            # Click symbol search button
            await self.frame.get_by_role("button", name="Symbol Search").click()
            await asyncio.sleep(1)
            
            # Type symbol in search box
            search_box = self.frame.get_by_role("textbox", name="Search")
            await search_box.fill(symbol)
            await asyncio.sleep(1)
            
            # Click on the first result (should be exact match)
            # Wait for search results to appear
            await asyncio.sleep(1)
            
            # Press Enter or click the first result
            await search_box.press("Enter")
            await asyncio.sleep(2)
            
            print(f"✓ Loaded symbol: {symbol}")
            return True
        except Exception as e:
            print(f"✗ Error loading symbol {symbol}: {e}")
            return False
    
    async def set_timeframe(self, timeframe):
        """Set chart timeframe (1D, 1W, etc.)"""
        try:
            # Map timeframe to button text
            timeframe_map = {
                "1D": "1 day",
                "1W": "1 week",
                "1M": "1 month"
            }
            
            button_name = timeframe_map.get(timeframe, timeframe)
            await self.frame.get_by_role("button", name=button_name).click()
            await asyncio.sleep(2)
            
            print(f"✓ Set timeframe: {timeframe}")
            return True
        except Exception as e:
            print(f"✗ Error setting timeframe: {e}")
            return False
    
    async def add_indicator(self, indicator_name, search_term=None):
        """Add an indicator to the chart"""
        try:
            # Open indicators dialog
            await self.frame.get_by_role("button", name="Indicators & Strategies").click()
            await asyncio.sleep(1)
            
            # Search for indicator
            search_box = self.frame.get_by_role("textbox", name="Search")
            await search_box.fill(search_term or indicator_name)
            await asyncio.sleep(1)
            
            # Click on the indicator (exact match)
            await self.frame.get_by_text(indicator_name, exact=True).click()
            await asyncio.sleep(1)
            
            print(f"✓ Added indicator: {indicator_name}")
            return True
        except Exception as e:
            print(f"✗ Error adding indicator {indicator_name}: {e}")
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
    
    async def extract_chart_data(self):
        """Extract OHLCV and indicator data from chart"""
        try:
            # Get all text content from the chart legend area
            data = {}
            
            # Try to extract OHLCV data
            try:
                ohlcv_elements = await self.frame.locator('[class*="valueItem"]').all_text_contents()
                # Parse OHLCV from text like "O530.00", "H535.00", etc.
                for text in ohlcv_elements:
                    if text.startswith("O"):
                        data["open"] = float(text[1:].replace(",", ""))
                    elif text.startswith("H"):
                        data["high"] = float(text[1:].replace(",", ""))
                    elif text.startswith("L"):
                        data["low"] = float(text[1:].replace(",", ""))
                    elif text.startswith("C"):
                        data["close"] = float(text[1:].replace(",", ""))
            except:
                pass
            
            print(f"✓ Extracted chart data: {data}")
            return data
        except Exception as e:
            print(f"✗ Error extracting chart data: {e}")
            return {}
    
    async def extract_indicator_values(self):
        """Extract indicator values from chart legend"""
        try:
            indicators = {}
            
            # This is a simplified version - in practice, you'd need to parse
            # the specific legend elements for each indicator
            # For now, we'll return empty dict and rely on visual extraction
            
            return indicators
        except Exception as e:
            print(f"✗ Error extracting indicators: {e}")
            return {}
