"""
Simple test to connect to Chrome and check page status
"""
import asyncio
from playwright.async_api import async_playwright


NEPSE_CHART_URL = "https://nepsealpha.com/nepse-chart"


async def test_connection():
    print("Testing connection to Chrome...")
    
    playwright = await async_playwright().start()
    
    try:
        # Connect to existing Chrome
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        print("✓ Connected to Chrome")
        
        # Get or create page
        if browser.contexts:
            context = browser.contexts[0]
            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()

            print(f"✓ Active page: {page.url}")

            if "nepsealpha.com/nepse-chart" not in page.url:
                print(f"  Navigating to {NEPSE_CHART_URL}...")
                await page.goto(NEPSE_CHART_URL, wait_until="domcontentloaded", timeout=45000)
                print(f"✓ Navigated: {page.url}")

            # Wait a bit
            await asyncio.sleep(3)

            # Check frames
            print(f"\nTotal frames: {len(page.frames)}")
            for i, frame in enumerate(page.frames):
                print(f"  Frame {i}:")
                print(f"    Name: {frame.name}")
                print(f"    URL: {frame.url}")

            tv_frames = [
                f for f in page.frames
                if "tradingview" in (f.name or "").lower() and f != page.main_frame
            ]
            if tv_frames:
                print(f"\n✓ TradingView iframe ready: {tv_frames[0].name}")
            else:
                print("\n✗ TradingView iframe not found")

            # Try to get page title
            title = await page.title()
            print(f"\nPage title: {title}")

            # Check if TradingView elements exist
            print("\nLooking for TradingView elements...")
            try:
                # Wait for iframe with tradingview in the name
                await page.wait_for_selector('iframe', timeout=5000)
                iframes = await page.query_selector_all('iframe')
                print(f"Found {len(iframes)} iframes")

                for i, iframe in enumerate(iframes):
                    src = await iframe.get_attribute('src')
                    name = await iframe.get_attribute('name')
                    print(f"  iframe {i}: name='{name}', src='{src}'")

            except Exception as e:
                print(f"Error checking iframes: {e}")
        else:
            print("✗ No contexts found")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await playwright.stop()
        print("\n✓ Test complete")


if __name__ == "__main__":
    asyncio.run(test_connection())
