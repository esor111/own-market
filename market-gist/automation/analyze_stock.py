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
    get_run_directories,
    INDICATORS
)

for stream_name in ("stdout", "stderr"):
    stream = getattr(sys, stream_name, None)
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


class StockAnalysisAutomation:
    def __init__(self, symbol, timeframe="1W", run_date=None):
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        self.run_date = run_date or datetime.now().strftime("%Y-%m-%d")
        self.session_id = get_session_id(self.symbol, self.run_date)
        self.file_prefix = get_file_prefix(self.symbol, self.run_date)
        self.run_dirs = get_run_directories(self.symbol, self.run_date)
        
        self.browser = BrowserAutomation()
        self.extractor = DataExtractor()
        self.analyzer = StockAnalyzer()
        self.file_gen = FileGenerator(self.session_id, self.run_date, self.run_dirs)
        
        self.data = {
            "market": {},
            "sector": {},
            "stock": {},
            "indicators": {},
            "volume": {},
            "relative_strength": {},
            "evidence_files": []
        }

    @staticmethod
    def _round_price(value):
        """Round numeric values for stable output."""
        if value is None:
            return None
        return round(float(value), 2)

    def _sorted_levels(self, levels, reverse=False):
        """Return unique rounded levels in sorted order."""
        cleaned = []
        seen = set()
        for level in levels:
            if level is None:
                continue
            rounded = self._round_price(level)
            if rounded is None or rounded <= 0:
                continue
            key = f"{rounded:.2f}"
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(rounded)
        return sorted(cleaned, reverse=reverse)

    def _levels_to_zones(self, levels):
        """Convert levels into narrow support/resistance zones."""
        zones = []
        for level in levels[:3]:
            width = max(level * 0.01, 1)
            zones.append([
                self._round_price(level - width),
                self._round_price(level + width)
            ])
        return zones

    def _derive_price_levels(self, price, chart_data, indicator_data):
        """Derive support, resistance, breakout, and invalidation from chart state."""
        low = chart_data.get("low")
        high = chart_data.get("high")
        open_price = chart_data.get("open")
        ema_20 = indicator_data.get("ema_20")
        ma_50 = indicator_data.get("ma_50")

        support_candidates = list(chart_data.get("swing_lows", []))
        resistance_candidates = list(chart_data.get("swing_highs", []))

        if low is not None:
            support_candidates.append(low)
        if open_price is not None:
            support_candidates.append(min(open_price, price))
            resistance_candidates.append(max(open_price, price))
        if high is not None:
            resistance_candidates.append(high)
        if ema_20 is not None:
            if ema_20 <= price:
                support_candidates.append(ema_20)
            else:
                resistance_candidates.append(ema_20)
        if ma_50 is not None:
            if ma_50 <= price:
                support_candidates.append(ma_50)
            else:
                resistance_candidates.append(ma_50)

        if not support_candidates:
            support_candidates.append(price * 0.97)
        if not resistance_candidates:
            resistance_candidates.append(price * 1.03)

        support_levels = self._sorted_levels(
            [level for level in support_candidates if level <= price * 1.02],
            reverse=True
        )
        resistance_levels = self._sorted_levels(
            [level for level in resistance_candidates if level >= price * 0.98]
        )

        nearest_support = next((level for level in support_levels if level <= price), support_levels[0])
        nearest_resistance = next((level for level in resistance_levels if level >= price), resistance_levels[0])

        deeper_supports = [level for level in support_levels if level < nearest_support]
        if deeper_supports:
            invalidation = deeper_supports[0]
        elif low is not None and low < nearest_support:
            invalidation = low
        else:
            invalidation = nearest_support * 0.97

        return {
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "nearest_support": self._round_price(nearest_support),
            "nearest_resistance": self._round_price(nearest_resistance),
            "breakout_level": self._round_price(nearest_resistance),
            "breakdown_level": self._round_price(nearest_support),
            "invalidation_level": self._round_price(invalidation)
        }

    def _derive_volume_profile(self, chart_data):
        """Build a conservative volume profile from extracted chart data."""
        current_volume = chart_data.get("volume")
        if current_volume is None:
            return {
                "current_volume": None,
                "volume_vs_average": "unknown",
                "breakout_volume_signal": "unknown",
                "pullback_volume_signal": "unknown",
                "participation_label": "volume_unconfirmed",
                "notes": "Volume not extracted from chart."
            }

        return {
            "current_volume": current_volume,
            "volume_vs_average": "available",
            "breakout_volume_signal": "not_triggered",
            "pullback_volume_signal": "unknown",
            "participation_label": "volume_available",
            "notes": "Current candle volume extracted, but no historical average is available yet."
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

        # Navigate to NEPSE index (loads on 1D by default)
        await self.browser.search_and_load_symbol("NEPSE")
        await asyncio.sleep(2)

        # Take market screenshot
        screenshot_path = os.path.join(self.run_dirs["raw_screenshots"], f"{self.file_prefix}__NEPSE__1D__market_context.png")
        await self.browser.take_screenshot(screenshot_path)
        self.data["evidence_files"].append(os.path.basename(screenshot_path))

        # Get snapshot
        snapshot = await self.browser.get_page_snapshot()
        if snapshot:
            snapshot_path = os.path.join(self.run_dirs["raw_snapshots"], f"{self.file_prefix}__NEPSE__1D__snapshot.txt")
            os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(snapshot)
            self.data["evidence_files"].append(os.path.basename(snapshot_path))

        # Extract real market data from chart
        market_ohlc = await self.browser.extract_chart_data()
        change_pct = market_ohlc.get("change_pct", 0)
        if change_pct > 0.5:
            trend_label = "up"
        elif change_pct < -0.5:
            trend_label = "down"
        else:
            trend_label = "flat"

        self.data["market"] = {
            "close": market_ohlc.get("close", 0),
            "change_pct": change_pct,
            "trend_label": trend_label,
            "market_phase": "unknown"
        }
        print(f"  Market: close={self.data['market']['close']}, change_pct={change_pct}%, trend={trend_label}")
        print("\u2713 Market context captured")

    
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
        snapshot_path = os.path.join(self.run_dirs["raw_snapshots"], f"{self.file_prefix}__{self.timeframe}__pre_indicators_snapshot.txt")
        snapshot = await self.browser.get_page_snapshot()
        if snapshot:
            os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(snapshot)
            self.data["evidence_files"].append(os.path.basename(snapshot_path))
        
        # Add indicators only if not already present on the chart
        if await self.browser.has_expected_indicators():
            print("  Indicators already on chart — skipping add step")
        else:
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

        # Symbol sanity check: avoid silent drift before extracting final values.
        current_symbol = await self.browser.get_current_symbol_code()
        if current_symbol and current_symbol.upper() != self.symbol:
            print(f"  Warning: expected symbol {self.symbol}, found {current_symbol}. Reloading once...")
            await self.browser.search_and_load_symbol(self.symbol)
            await asyncio.sleep(2)
            await self.browser.set_timeframe(self.timeframe)
            await asyncio.sleep(2)
        
        # Extract chart data BEFORE screenshots
        print("  Extracting chart data...")
        chart_data = await self.browser.extract_chart_data()
        self.data["stock"] = chart_data
        
        # Extract indicator values
        print("  Extracting indicator values...")
        indicator_data = await self.browser.extract_indicator_values()
        self.data["indicators"] = indicator_data
        
        # Take clean chart screenshot
        screenshot_path = os.path.join(self.run_dirs["raw_screenshots"], f"{self.file_prefix}__{self.timeframe}__clean_v2.png")
        await self.browser.take_screenshot(screenshot_path)
        self.data["evidence_files"].append(os.path.basename(screenshot_path))
        
        # Take annotated screenshot (same as clean for now)
        screenshot_path = os.path.join(self.run_dirs["raw_screenshots"], f"{self.file_prefix}__{self.timeframe}__annotated_v2.png")
        await self.browser.take_screenshot(screenshot_path)
        self.data["evidence_files"].append(os.path.basename(screenshot_path))
        
        print(f"✓ {self.symbol} analysis completed")
        print(f"  Data: {self.data['stock']}")
        print(f"  Indicators: {self.data['indicators']}")

    
    async def capture_sector_evidence(self):
        """Capture sector chart evidence"""
        print("\n[3/5] Capturing sector evidence...")
        
        # Determine sector (simplified - would need lookup table)
        sector_map = {
            "SMHL": "HYDROPOWER",
            "NABIL": "BANKING"
        }
        sector_symbol = sector_map.get(self.symbol, "HYDROPOWER")
        
        # Load sector chart
        await self.browser.search_and_load_symbol(sector_symbol)
        await asyncio.sleep(2)

        # Extract real sector OHLCV data
        sector_ohlc = await self.browser.extract_chart_data()
        sector_change_pct = sector_ohlc.get("change_pct")
        if sector_change_pct is None:
            sector_trend = "unknown"
        elif sector_change_pct > 0.5:
            sector_trend = "up"
        elif sector_change_pct < -0.5:
            sector_trend = "down"
        else:
            sector_trend = "sideways"

        # Take sector screenshot
        screenshot_path = os.path.join(self.run_dirs["raw_screenshots"], f"{self.file_prefix}__{sector_symbol}__sector.png")
        await self.browser.take_screenshot(screenshot_path)
        self.data["evidence_files"].append(os.path.basename(screenshot_path))

        # Get sector snapshot
        snapshot = await self.browser.get_page_snapshot()
        if snapshot:
            snapshot_path = os.path.join(self.run_dirs["raw_snapshots"], f"{self.file_prefix}__{sector_symbol}__sector_snapshot.txt")
            os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(snapshot)
            self.data["evidence_files"].append(os.path.basename(snapshot_path))

        # Store real sector data
        self.data["sector"] = {
            "name": sector_symbol,
            "close": sector_ohlc.get("close", 0),
            "change_pct": sector_change_pct,
            "trend_label": sector_trend,
            "notes": None if sector_change_pct is not None else "sector_change_pct_not_visible_on_chart"
        }
        print(f"  Sector: close={self.data['sector']['close']}, change_pct={sector_change_pct}%, trend={sector_trend}")
        
        # Return to symbol chart
        await self.browser.search_and_load_symbol(self.symbol)
        await asyncio.sleep(2)
        
        print("✓ Sector evidence captured")

    
    async def generate_analysis(self):
        """Generate scores and decision"""
        print("\n[4/5] Generating analysis...")

        required_stock_fields = ["close", "change_pct"]
        required_indicator_fields = ["ema_20", "ma_50", "rsi"]

        missing_stock = [
            k for k in required_stock_fields
            if k not in self.data["stock"] or self.data["stock"].get(k) is None
        ]
        missing_indicators = [
            k for k in required_indicator_fields
            if k not in self.data["indicators"] or self.data["indicators"].get(k) is None
        ]

        if missing_stock or missing_indicators:
            missing_fields = missing_stock + missing_indicators
            print(f"  Warning: missing extracted fields: {missing_fields}")

            self.data["scores"] = {
                "individual": {},
                "total": 0,
                "max": 100,
                "percent": 0,
                "notes": f"incomplete_data: missing {', '.join(missing_fields)}"
            }
            self.data["decision"] = {
                "setup_type": "no_setup",
                "score": 0,
                "score_max": 100,
                "confidence": 0,
                "action": "incomplete_data",
                "entry_zone": [],
                "stop_loss": None,
                "invalidation_level": None,
                "targets": [],
                "risk_reward_ratio": None,
                "why": [
                    "Analysis skipped due to incomplete extracted chart data.",
                    f"Missing fields: {', '.join(missing_fields)}"
                ]
            }

            print("✓ Analysis skipped: incomplete extracted data")
            return
        
        # Use extracted data only. If it's missing, the run should have stopped above.
        price = self.data["stock"]["close"]
        ema_20 = self.data["indicators"]["ema_20"]
        ma_50 = self.data["indicators"]["ma_50"]
        rsi = self.data["indicators"]["rsi"]
        macd_histogram = self.data["indicators"].get("histogram", 0)
        stock_change_pct = self.data["stock"]["change_pct"]
        
        print(f"  Using: Price={price}, EMA20={ema_20}, MA50={ma_50}, RSI={rsi}")
        
        has_sector_change = self.data["sector"].get("change_pct") is not None

        if has_sector_change:
            sector_alignment_score = self.analyzer.calculate_sector_alignment_score(
                self.data["sector"]["change_pct"],
                self.data["market"]["change_pct"]
            )
            relative_strength_score = self.analyzer.calculate_relative_strength_score(
                stock_change_pct,
                self.data["market"]["change_pct"],
                self.data["sector"]["change_pct"]
            )
        else:
            # Do not invent a neutral sector reading when the chart does not expose it.
            sector_alignment_score = 0
            relative_strength_score = 6 if stock_change_pct > self.data["market"]["change_pct"] else 2

        trend_label = self.analyzer.classify_trend(price, ema_20, ma_50)
        price_levels = self._derive_price_levels(price, self.data["stock"], self.data["indicators"])
        nearest_support = price_levels["nearest_support"]
        nearest_resistance = price_levels["nearest_resistance"]

        volume_profile = self._derive_volume_profile(self.data["stock"])
        self.data["volume"] = volume_profile
        volume_score = self.analyzer.calculate_volume_score(volume_profile["volume_vs_average"])

        location_score = self.analyzer.calculate_location_score(
            price,
            nearest_support,
            nearest_resistance
        )
        structure_score = self.analyzer.calculate_structure_quality_score(trend_label)

        market_label = "underperforming" if stock_change_pct < self.data["market"]["change_pct"] else "outperforming"
        if has_sector_change:
            sector_label = "underperforming" if stock_change_pct < self.data["sector"]["change_pct"] else "outperforming"
        else:
            sector_label = "unknown"

        self.data["relative_strength"] = {
            "benchmark_sector": self.data["sector"]["name"],
            "rs_vs_market_label": market_label,
            "rs_vs_sector_label": sector_label,
            "rs_notes": (
                f"{self.symbol} move {stock_change_pct}% vs NEPSE {self.data['market']['change_pct']}%"
                if has_sector_change
                else f"{self.symbol} move {stock_change_pct}% vs NEPSE {self.data['market']['change_pct']}%; sector comparison unavailable"
            )
        }

        # Calculate scores
        scores = {
            "market_alignment": self.analyzer.calculate_market_alignment_score(
                self.data["market"]["change_pct"]
            ),
            "sector_alignment": sector_alignment_score,
            "trend_filter_quality": self.analyzer.calculate_trend_filter_score(
                price, ema_20, ma_50
            ),
            "momentum_confirmation": self.analyzer.calculate_momentum_score(
                rsi, macd_histogram
            ),
            "relative_strength": relative_strength_score,
            "structure_quality": structure_score,
            "location_quality": location_score,
            "volume_confirmation": volume_score,
            "event_quality": 5,
            "risk_reward_quality": 0
        }

        score_summary = self.analyzer.calculate_total_score(scores)
        
        # Determine action
        confidence = self.analyzer.calculate_confidence(
            score_summary["percent"],
            {
                "has_sector_data": has_sector_change,
                "has_volume_data": volume_profile["current_volume"] is not None,
                "has_all_indicators": bool(self.data["indicators"]),
                "has_broker_flow": False
            }
        )

        action = self.analyzer.determine_action(score_summary["percent"], confidence)
        setup_type = self.analyzer.determine_setup_type(trend_label, price, ema_20, rsi)

        if setup_type == "continuation":
            entry_zone = [
                self._round_price(min(price, nearest_support)),
                self._round_price(max(price, nearest_support))
            ]
            stop_loss = price_levels["invalidation_level"]
        elif setup_type in {"reversal_watch", "breakout_watch"}:
            breakout_level = price_levels["breakout_level"]
            entry_zone = [
                breakout_level,
                self._round_price(breakout_level * 1.02)
            ]
            stop_loss = price_levels["invalidation_level"]
        else:
            entry_zone = []
            stop_loss = None

        targets = []
        risk_reward_ratio = None
        if entry_zone and stop_loss is not None:
            targets = [
                self._round_price(target)
                for target in self.analyzer.calculate_targets(entry_zone[0], price_levels["resistance_levels"])
            ]
            if targets:
                risk_reward_ratio = self.analyzer.calculate_risk_reward(entry_zone[0], stop_loss, targets[0])

        if risk_reward_ratio is not None:
            if risk_reward_ratio >= 3:
                scores["risk_reward_quality"] = 8
            elif risk_reward_ratio >= 2:
                scores["risk_reward_quality"] = 6
            elif risk_reward_ratio >= 1:
                scores["risk_reward_quality"] = 4
            else:
                scores["risk_reward_quality"] = 2
            score_summary = self.analyzer.calculate_total_score(scores)
            confidence = self.analyzer.calculate_confidence(
                score_summary["percent"],
                {
                    "has_sector_data": has_sector_change,
                    "has_volume_data": volume_profile["current_volume"] is not None,
                    "has_all_indicators": bool(self.data["indicators"]),
                    "has_broker_flow": False
                }
            )
            action = self.analyzer.determine_action(score_summary["percent"], confidence)

        self.data["stock"].update({
            "trend_label": trend_label,
            "structure_label": "price_vs_moving_averages",
            "swing_highs": price_levels["resistance_levels"],
            "swing_lows": price_levels["support_levels"],
            "support_zones": self._levels_to_zones(price_levels["support_levels"]),
            "resistance_zones": self._levels_to_zones(price_levels["resistance_levels"]),
            "breakout_level": price_levels["breakout_level"],
            "breakdown_level": price_levels["breakdown_level"],
            "invalidation_level": stop_loss,
            "location_label": (
                "near_support" if nearest_support and abs(price - nearest_support) <= abs(nearest_resistance - price)
                else "near_resistance"
            ),
            "confidence_source": "extracted_plus_derived"
        })

        # Store analysis results
        self.data["scores"] = {
            "individual": scores,
            **score_summary,
            "notes": None if has_sector_change else "sector_change_pct_missing; sector alignment scored conservatively"
        }
        self.data["decision"] = {
            "setup_type": setup_type,
            "score": score_summary["total"],
            "score_max": score_summary["max"],
            "confidence": confidence,
            "action": action,
            "entry_zone": entry_zone,
            "stop_loss": stop_loss,
            "invalidation_level": stop_loss,
            "targets": targets,
            "risk_reward_ratio": risk_reward_ratio,
            "why": [
                f"Price: {price}, EMA20: {ema_20}, MA50: {ma_50}",
                f"RSI: {rsi}, MACD Histogram: {macd_histogram}",
                "Sector change% unavailable; sector scoring was reduced" if not has_sector_change else f"Sector change%: {self.data['sector']['change_pct']}",
                f"Derived support/resistance: {nearest_support} / {nearest_resistance}",
                f"Setup: {setup_type}, Score: {score_summary['percent']}/100, Confidence: {confidence}%",
                f"Action: {action.upper()}"
            ]
        }
        
        print(f"✓ Analysis complete: {action.upper()} (Score: {score_summary['percent']}/100, Confidence: {confidence}%)")

    
    async def create_normalized_records(self):
        """Create all normalized JSON records"""
        print("\n[5/5] Creating normalized records...")
        
        # Session record
        self.file_gen.generate_session_record(
            self.symbol,
            stages_completed=[
                "market_context_capture", "symbol_chart_load",
                "timeframe_selection", "indicator_setup",
                "clean_chart_capture", "sector_evidence_capture"
            ],
            stages_skipped=["event_enrichment", "broker_flow_capture"],
            notes="Automated analysis run"
        )
        
        # Market record
        self.file_gen.generate_market_record(
            self.data["market"],
            self.data["evidence_files"]
        )
        
        # Sector record
        self.file_gen.generate_sector_record(
            self.data["sector"]["name"],
            self.data["sector"],
            self.data["evidence_files"]
        )
        
        # Stock chart record
        self.file_gen.generate_stock_chart_record(
            self.symbol,
            self.timeframe,
            self.data["stock"],
            self.data["evidence_files"]
        )
        
        # Indicator record
        self.file_gen.generate_indicator_record(
            self.symbol,
            self.timeframe,
            self.data.get("indicators", {}),
            self.data["evidence_files"]
        )
        
        # Volume record
        self.file_gen.generate_volume_record(
            self.symbol,
            self.timeframe,
            self.data.get("volume", {}),
            self.data["evidence_files"]
        )
        
        # Relative strength record
        self.file_gen.generate_relative_strength_record(
            self.symbol,
            self.data.get("relative_strength", {"benchmark_sector": self.data["sector"]["name"]}),
            self.data["evidence_files"]
        )
        
        # Feature score record
        self.file_gen.generate_feature_score_record(
            self.symbol,
            self.data["scores"],
            self.data["evidence_files"]
        )
        
        # Decision record
        self.file_gen.generate_decision_record(
            self.symbol,
            self.data["decision"],
            self.data["evidence_files"]
        )
        
        # Event record (no events)
        self.file_gen.generate_event_record(
            self.symbol,
            False,
            self.data["evidence_files"]
        )
        
        # Broker flow record (unavailable)
        self.file_gen.generate_broker_flow_record(
            self.symbol,
            False,
            self.data["evidence_files"]
        )
        
        print("✓ All normalized records created")


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_stock.py SYMBOL [TIMEFRAME]")
        print("Example: python analyze_stock.py SMHL 1W")
        sys.exit(1)
    
    symbol = sys.argv[1]
    timeframe = sys.argv[2] if len(sys.argv) > 2 else "1W"
    
    automation = StockAnalysisAutomation(symbol, timeframe)
    await automation.run()


if __name__ == "__main__":
    asyncio.run(main())
