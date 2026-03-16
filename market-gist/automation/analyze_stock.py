"""
Main automation script for stock analysis
Usage: python analyze_stock.py SMHL 1W
"""
import asyncio
import sys
import os
from datetime import datetime

from browser_actions import BrowserAutomation
from data_extractor import DataExtractor
from analyzer import StockAnalyzer
from file_generator import FileGenerator
from config import (
    get_session_id, get_file_prefix,
    RAW_SCREENSHOTS_DIR, RAW_SNAPSHOTS_DIR, RAW_TABLES_DIR,
    INDICATORS
)


class StockAnalysisAutomation:
    def __init__(self, symbol, timeframe="1W", run_date=None):
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        self.run_date = run_date or datetime.now().strftime("%Y-%m-%d")
        self.session_id = get_session_id(self.symbol, self.run_date)
        self.file_prefix = get_file_prefix(self.symbol, self.run_date)
        
        self.browser = BrowserAutomation()
        self.extractor = DataExtractor()
        self.analyzer = StockAnalyzer()
        self.file_gen = FileGenerator(self.session_id, self.run_date)
        
        self.data = {
            "market": {},
            "sector": {},
            "stock": {},
            "indicators": {},
            "volume": {},
            "evidence_files": []
        }

    
    async def run(self):
        """Main execution flow"""
        try:
            print(f"\n{'='*60}")
            print(f"Starting analysis for {self.symbol} ({self.timeframe})")
            print(f"Session ID: {self.session_id}")
            print(f"{'='*60}\n")
            
            # Start browser
            await self.browser.start()
            
            # Step 1: Capture market context
            await self.capture_market_context()
            
            # Step 2: Load and analyze symbol
            await self.analyze_symbol()
            
            # Step 3: Capture sector evidence
            await self.capture_sector_evidence()
            
            # Step 4: Generate analysis and decision
            await self.generate_analysis()
            
            # Step 5: Create all normalized records
            await self.create_normalized_records()
            
            print(f"\n{'='*60}")
            print(f"✓ Analysis completed successfully!")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n✗ Error during analysis: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.browser.close()

    
    async def capture_market_context(self):
        """Capture NEPSE market context"""
        print("\n[1/5] Capturing market context...")
        
        # Take market screenshot
        screenshot_path = os.path.join(RAW_SCREENSHOTS_DIR, f"{self.file_prefix}__NEPSE__1D__market_context.png")
        await self.browser.take_screenshot(screenshot_path)
        self.data["evidence_files"].append(os.path.basename(screenshot_path))
        
        # Get snapshot
        snapshot = await self.browser.get_page_snapshot()
        if snapshot:
            snapshot_path = os.path.join(RAW_SNAPSHOTS_DIR, f"{self.file_prefix}__NEPSE__1D__snapshot.txt")
            os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(snapshot)
            self.data["evidence_files"].append(os.path.basename(snapshot_path))
        
        # Extract market data (simplified - would need actual extraction logic)
        self.data["market"] = {
            "close": 2798.83,  # Placeholder - needs actual extraction
            "change_pct": -0.92,
            "trend_label": "down",
            "market_phase": "distribution"
        }
        
        print("✓ Market context captured")

    
    async def analyze_symbol(self):
        """Load symbol and capture data"""
        print(f"\n[2/5] Analyzing {self.symbol}...")
        
        # Search and load symbol
        await self.browser.search_and_load_symbol(self.symbol)
        await asyncio.sleep(2)
        
        # Set timeframe
        await self.browser.set_timeframe(self.timeframe)
        await asyncio.sleep(2)
        
        # Take pre-indicators snapshot
        snapshot_path = os.path.join(RAW_SNAPSHOTS_DIR, f"{self.file_prefix}__{self.timeframe}__pre_indicators_snapshot.txt")
        snapshot = await self.browser.get_page_snapshot()
        if snapshot:
            os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(snapshot)
            self.data["evidence_files"].append(os.path.basename(snapshot_path))
        
        # Add indicators
        print("  Adding indicators...")
        for indicator_key, indicator_config in INDICATORS.items():
            await self.browser.add_indicator(
                indicator_config["name"],
                indicator_config.get("search")
            )
            await asyncio.sleep(1)
        
        # Close indicators dialog
        await self.browser.close_indicators_dialog()
        await asyncio.sleep(2)
        
        # Take clean chart screenshot
        screenshot_path = os.path.join(RAW_SCREENSHOTS_DIR, f"{self.file_prefix}__{self.timeframe}__clean_v2.png")
        await self.browser.take_screenshot(screenshot_path)
        self.data["evidence_files"].append(os.path.basename(screenshot_path))
        
        # Take annotated screenshot (same as clean for now)
        screenshot_path = os.path.join(RAW_SCREENSHOTS_DIR, f"{self.file_prefix}__{self.timeframe}__annotated_v2.png")
        await self.browser.take_screenshot(screenshot_path)
        self.data["evidence_files"].append(os.path.basename(screenshot_path))
        
        # Extract chart data
        chart_data = await self.browser.extract_chart_data()
        self.data["stock"] = chart_data
        
        print(f"✓ {self.symbol} analysis completed")
