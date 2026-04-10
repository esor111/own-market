"""
Main automation script for stock analysis
Usage: python analyze_stock.py SMHL 1W
"""
import asyncio
import sys
import os
import json
import statistics
from datetime import datetime

from browser_actions import BrowserAutomation
from data_extractor import DataExtractor
from analyzer import StockAnalyzer
from file_generator import FileGenerator
from structure_signals import StructureSignalEngine
from quality_gate import AnalysisQualityGate
from event_sources import OfficialEventExtractor
from data_sources import get_truth_source
from truth_comparison import build_truth_comparison
from config import (
    get_session_id, get_file_prefix,
    get_run_directories,
    INDICATORS,
    SECTOR_MAP_FILE,
    DEFAULT_TRUTH_SOURCE,
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
        self.session_id = get_session_id(self.symbol, self.timeframe, self.run_date)
        self.file_prefix = get_file_prefix(self.symbol, self.run_date)
        self.run_dirs = get_run_directories(self.symbol, self.run_date)
        
        self.browser = BrowserAutomation()
        self.extractor = DataExtractor()
        self.analyzer = StockAnalyzer()
        self.structure = StructureSignalEngine()
        self.quality_gate = AnalysisQualityGate()
        self.event_extractor = OfficialEventExtractor()
        self.file_gen = FileGenerator(self.session_id, self.run_date, self.run_dirs)
        self.sector_map = self._load_sector_map()
        self.truth_source_name = DEFAULT_TRUTH_SOURCE
        
        self.data = {
            "market": {},
            "sector": {},
            "stock": {},
            "indicators": {},
            "volume": {},
            "relative_strength": {},
            "event": {},
            "truth": {},
            "truth_comparison": {},
            "evidence_files": [],
            "timeframe_evidence": {},
            "timeframes": {},
            "qc": {}
        }

    def _load_sector_map(self):
        """Load symbol-to-sector mapping from a maintained JSON file."""
        try:
            with open(SECTOR_MAP_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return {str(symbol).upper(): sector for symbol, sector in raw.items()}
        except FileNotFoundError:
            print(f"  Warning: sector map file not found at {SECTOR_MAP_FILE}")
            return {}
        except Exception as exc:
            print(f"  Warning: could not load sector map: {exc}")
            return {}

    def _record_evidence(self, filepath):
        """Store run-relative evidence references for later traceability."""
        relative = os.path.relpath(filepath, self.run_dirs["base"]).replace("\\", "/")
        if relative not in self.data["evidence_files"]:
            self.data["evidence_files"].append(relative)
        return relative

    def _record_timeframe_evidence(self, timeframe, filepath):
        """Store evidence references for a specific timeframe."""
        relative = self._record_evidence(filepath)
        if timeframe:
            bucket = self.data["timeframe_evidence"].setdefault(timeframe, [])
            if relative not in bucket:
                bucket.append(relative)
        return relative

    def _save_raw_json(self, filename, payload, timeframe=None):
        """Persist raw extracted payloads inside the current run folder."""
        filepath = os.path.join(self.run_dirs["raw_tables"], filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        if timeframe:
            self._record_timeframe_evidence(timeframe, filepath)
        else:
            self._record_evidence(filepath)
        return filepath

    def _get_context_timeframes(self):
        """Return the primary timeframe plus one supporting higher/lower context timeframe."""
        ordered = [self.timeframe]
        if self.timeframe == "1W":
            ordered.extend(["1D", "1M"])
        elif self.timeframe == "1D":
            ordered.extend(["1W", "1M"])
        elif self.timeframe == "1M":
            ordered.append("1W")

        unique = []
        seen = set()
        for timeframe in ordered:
            if timeframe not in seen:
                seen.add(timeframe)
                unique.append(timeframe)
        return unique

    def _infer_bar_timeframe(self, bars):
        """Infer the actual timeframe from recent bar spacing."""
        close_times = sorted(
            bar.get("close_time_ms")
            for bar in bars
            if bar.get("close_time_ms") is not None
        )
        if len(close_times) < 3:
            return "unknown"

        gaps_hours = []
        for previous, current in zip(close_times, close_times[1:]):
            gap_ms = current - previous
            if gap_ms > 0:
                gaps_hours.append(gap_ms / 3_600_000)

        if not gaps_hours:
            return "unknown"

        median_gap_hours = statistics.median(gaps_hours)
        if median_gap_hours >= 500:
            return "1M"
        if median_gap_hours >= 96:
            return "1W"
        if median_gap_hours >= 12:
            return "1D"
        return "intraday"

    async def _capture_stock_timeframe(self, timeframe, configure_indicators=False):
        """Capture chart, bars, indicators, and screenshots for one stock timeframe."""
        await self.browser.set_timeframe(timeframe)
        await asyncio.sleep(2)

        snapshot_path = os.path.join(
            self.run_dirs["raw_snapshots"],
            f"{self.file_prefix}__{timeframe}__pre_indicators_snapshot.txt"
        )
        snapshot = await self.browser.get_page_snapshot()
        if snapshot:
            os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(snapshot)
            self._record_timeframe_evidence(timeframe, snapshot_path)

        if configure_indicators:
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
                await self.browser.close_indicators_dialog()
                await asyncio.sleep(2)

        current_symbol = await self.browser.get_current_symbol_code()
        if current_symbol and current_symbol.upper() != self.symbol:
            print(f"  Warning: expected symbol {self.symbol}, found {current_symbol}. Reloading once...")
            await self.browser.search_and_load_symbol(self.symbol)
            await asyncio.sleep(2)
            await self.browser.set_timeframe(timeframe)
            await asyncio.sleep(2)

        print(f"  Extracting chart data for {timeframe}...")
        chart_data = await self.browser.extract_chart_data()
        recent_bars_payload = await self.browser.extract_recent_bars()
        chart_data["recent_bars"] = recent_bars_payload.get("bars", [])
        chart_data["recent_bar_count"] = recent_bars_payload.get("extracted_bars", 0)
        chart_data["total_bar_count"] = recent_bars_payload.get("total_bars", 0)

        inferred_timeframe = self._infer_bar_timeframe(chart_data["recent_bars"])
        chart_data["inferred_timeframe"] = inferred_timeframe
        if inferred_timeframe != "unknown" and inferred_timeframe != timeframe:
            raise ValueError(
                f"timeframe_mismatch:{timeframe}:extracted_{inferred_timeframe}"
            )

        self._save_raw_json(
            f"{self.file_prefix}__{timeframe}__stock_extract.json",
            {"extraction_type": "stock_chart", "symbol": self.symbol, "timeframe": timeframe, "data": chart_data},
            timeframe=timeframe
        )
        self._save_raw_json(
            f"{self.file_prefix}__{timeframe}__bar_extract.json",
            {
                "extraction_type": "recent_bars",
                "symbol": self.symbol,
                "timeframe": timeframe,
                "data": recent_bars_payload
            },
            timeframe=timeframe
        )

        print(f"  Extracting indicator values for {timeframe}...")
        indicator_data = await self.browser.extract_indicator_values()
        self._save_raw_json(
            f"{self.file_prefix}__{timeframe}__indicator_extract.json",
            {"extraction_type": "indicator_values", "symbol": self.symbol, "timeframe": timeframe, "data": indicator_data},
            timeframe=timeframe
        )

        clean_path = os.path.join(self.run_dirs["raw_screenshots"], f"{self.file_prefix}__{timeframe}__clean_v2.png")
        await self.browser.take_screenshot(clean_path)
        self._record_timeframe_evidence(timeframe, clean_path)

        annotated_path = os.path.join(self.run_dirs["raw_screenshots"], f"{self.file_prefix}__{timeframe}__annotated_v2.png")
        await self.browser.take_screenshot(annotated_path)
        self._record_timeframe_evidence(timeframe, annotated_path)

        volume_profile = self.structure.derive_volume_profile(chart_data)
        self.data["timeframes"][timeframe] = {
            "stock": chart_data,
            "indicators": indicator_data,
            "volume": volume_profile
        }

        if timeframe == self.timeframe:
            self.data["stock"] = chart_data
            self.data["indicators"] = indicator_data
            self.data["volume"] = volume_profile

        print(f"✓ Captured {self.symbol} {timeframe}")

    def _derive_timeframe_context(self, timeframe):
        """Enrich a timeframe payload with derived structure fields."""
        payload = self.data["timeframes"].get(timeframe)
        if not payload:
            return

        stock_data = payload.get("stock", {})
        indicator_data = payload.get("indicators", {})
        price = stock_data.get("close")
        ema_20 = indicator_data.get("ema_20")
        ma_50 = indicator_data.get("ma_50")
        rsi = indicator_data.get("rsi")
        macd_histogram = indicator_data.get("histogram")

        if None in {price, ema_20, ma_50, rsi}:
            stock_data.setdefault("trend_label", "unknown")
            stock_data.setdefault("structure_label", "insufficient_structure")
            stock_data.setdefault("structure_confidence", "low")
            return

        trend_label = self.analyzer.classify_trend(price, ema_20, ma_50)
        price_levels = self.structure.derive_price_levels(price, stock_data, indicator_data)
        volume_profile = payload.get("volume") or self.structure.derive_volume_profile(stock_data)
        payload["volume"] = volume_profile

        if rsi >= 60 and (macd_histogram or 0) >= 0:
            momentum_label = "bullish_momentum"
        elif rsi < 40:
            momentum_label = "weak_or_reversal_watch"
        else:
            momentum_label = "neutral_momentum"

        indicator_data.update({
            "price_above_ema_20": price > ema_20,
            "price_above_ma_50": price > ma_50,
            "momentum_label": momentum_label
        })

        stock_data.update({
            "trend_label": trend_label,
            "structure_label": price_levels.get("structure_label"),
            "swing_highs": price_levels.get("resistance_levels", []),
            "swing_lows": price_levels.get("support_levels", []),
            "support_zones": self.structure.levels_to_zones(price_levels.get("support_levels", [])),
            "resistance_zones": self.structure.levels_to_zones(price_levels.get("resistance_levels", [])),
            "breakout_level": price_levels.get("breakout_level"),
            "breakdown_level": price_levels.get("breakdown_level"),
            "invalidation_level": price_levels.get("invalidation_level"),
            "local_range_high": price_levels.get("local_range_high"),
            "local_range_low": price_levels.get("local_range_low"),
            "range_width_pct": price_levels.get("range_width_pct"),
            "location_label": (
                "near_support"
                if price_levels.get("nearest_support") and price_levels.get("nearest_resistance")
                and abs(price - price_levels["nearest_support"]) <= abs(price_levels["nearest_resistance"] - price)
                else "near_resistance"
            ),
            "structure_confidence": price_levels.get("structure_confidence"),
            "structure_confidence_reasons": price_levels.get("confidence_reasons", []),
            "confidence_source": "extracted_plus_derived"
        })

    def _build_model_input_payload(self):
        """Build the high-value model-input package for a stronger reasoning model."""
        for timeframe in self.data.get("timeframes", {}):
            self._derive_timeframe_context(timeframe)

        timeframe_summary = {}
        for timeframe, payload in self.data.get("timeframes", {}).items():
            stock_data = payload.get("stock", {})
            indicator_data = payload.get("indicators", {})
            volume_data = payload.get("volume", {})
            timeframe_summary[timeframe] = {
                "close": stock_data.get("close"),
                "trend_label": stock_data.get("trend_label"),
                "structure_label": stock_data.get("structure_label"),
                "support_zones": stock_data.get("support_zones", []),
                "resistance_zones": stock_data.get("resistance_zones", []),
                "breakout_level": stock_data.get("breakout_level"),
                "invalidation_level": stock_data.get("invalidation_level"),
                "ema_20": indicator_data.get("ema_20"),
                "ma_50": indicator_data.get("ma_50"),
                "rsi": indicator_data.get("rsi"),
                "macd_histogram": indicator_data.get("histogram"),
                "volume_participation": volume_data.get("participation_label"),
                "structure_confidence": stock_data.get("structure_confidence")
            }

        monthly = timeframe_summary.get("1M", {})
        weekly = timeframe_summary.get("1W", {})
        daily = timeframe_summary.get("1D", {})
        weekly_trend = weekly.get("trend_label")
        daily_trend = daily.get("trend_label")
        monthly_trend = monthly.get("trend_label")
        if monthly_trend == "uptrend" and weekly_trend == "uptrend" and daily_trend == "uptrend":
            alignment = "fully_aligned_bullish"
            structure_agreement = "monthly_weekly_daily_supportive"
        elif weekly_trend == "uptrend" and daily_trend == "uptrend":
            alignment = "aligned_bullish"
            structure_agreement = "weekly_and_daily_supportive"
        elif monthly_trend == "downtrend" and weekly_trend == "downtrend":
            alignment = "aligned_bearish"
            structure_agreement = "monthly_and_weekly_weak"
        elif weekly_trend == "downtrend" and daily_trend == "downtrend":
            alignment = "aligned_bearish"
            structure_agreement = "weekly_and_daily_weak"
        elif monthly_trend and weekly_trend and daily_trend:
            alignment = "mixed"
            structure_agreement = "multi_timeframe_conflict"
        elif weekly_trend and daily_trend:
            alignment = "mixed"
            structure_agreement = "timeframe_conflict"
        else:
            alignment = "higher_tf_conflict"
            structure_agreement = "insufficient_timeframe_data"

        decision = self.data.get("decision", {})
        if decision.get("action") in {"buy", "strong_buy"}:
            trigger_readiness = "confirmed_actionable"
        elif decision.get("setup_type") == "breakout_watch":
            trigger_readiness = "near_breakout_but_not_confirmed"
        elif decision.get("action") == "watch_only":
            trigger_readiness = "watch_but_not_confirmed"
        else:
            trigger_readiness = "not_ready"

        entry_zone = decision.get("entry_zone") or []
        stop_loss = decision.get("stop_loss")
        if entry_zone and stop_loss is not None:
            entry_reference = entry_zone[0]
            risk_pct = abs(entry_reference - stop_loss) / entry_reference if entry_reference else 0
            invalidation_quality = "clear" if risk_pct >= 0.03 else "acceptable"
        else:
            invalidation_quality = "weak"

        uncertainties = []
        if self.data.get("event", {}).get("event_found") is False:
            uncertainties.append("official_event_layer_found_no_recent_match")
        if self.data.get("stock", {}).get("structure_confidence") == "low":
            uncertainties.append("primary_structure_confidence_low")
        if self.data.get("qc", {}).get("status") != "pass":
            uncertainties.append("qc_gate_not_pass")
        truth_close_diff = self.data.get("truth_comparison", {}).get("api_vs_browser_daily", {}).get("close_diff")
        if truth_close_diff is None:
            uncertainties.append("truth_comparison_unavailable")
        elif abs(truth_close_diff) > 0.5:
            uncertainties.append("api_browser_daily_close_mismatch")
        uncertainties.append("usable_calibration_samples_still_low")

        timeframe_alignment = self.data.get("timeframe_alignment", {})
        if timeframe_alignment.get("status") == "conflicted":
            uncertainties.append("multi_timeframe_alignment_conflicted")

        return {
            "primary_horizon": "swing",
            "market": {
                "symbol": "NEPSE",
                "timeframe": "1D",
                "close": self.data["market"].get("close"),
                "change_pct": self.data["market"].get("change_pct"),
                "trend_label": self.data["market"].get("trend_label"),
                "market_phase": self.data["market"].get("market_phase"),
                "structure_confidence": "medium"
            },
            "sector": {
                "name": self.data["sector"].get("name"),
                "timeframe": "1D",
                "close": self.data["sector"].get("close"),
                "change_pct": self.data["sector"].get("change_pct"),
                "trend_label": self.data["sector"].get("trend_label"),
                "relative_strength_vs_market": self.data["relative_strength"].get("rs_vs_sector_label"),
                "structure_confidence": "medium" if self.data["sector"].get("name") != "UNKNOWN" else "low"
            },
            "timeframes": timeframe_summary,
            "derived_alignment": {
                "higher_timeframe_alignment": alignment,
                "structure_agreement": structure_agreement,
                "alignment_gate_status": timeframe_alignment.get("status"),
                "alignment_gate_score": timeframe_alignment.get("score"),
                "alignment_gate_findings": timeframe_alignment.get("findings", []),
                "trigger_readiness": trigger_readiness,
                "invalidation_quality": invalidation_quality,
                "trade_quality": "good_but_needs_confirmation" if decision.get("action") in {"buy", "watch_only"} else "not_actionable"
            },
            "event_context": {
                "has_active_event": self.data["event"].get("event_found") and self.data["event"].get("relevance_now") == "active_window",
                "event_type": self.data["event"].get("event_type"),
                "event_date": self.data["event"].get("event_date"),
                "event_sentiment": self.data["event"].get("sentiment"),
                "event_status": self.data["event"].get("relevance_now"),
                "impact_window_days": self.data["event"].get("impact_window_days"),
                "event_confidence": "high" if self.data["event"].get("event_found") else "medium",
                "details": self.data["event"].get("details", {})
            },
            "quality_flags": {
                "market_data_quality": "high" if self.data["market"].get("close") is not None else "low",
                "sector_data_quality": "high" if self.data["sector"].get("name") != "UNKNOWN" else "low",
                "stock_structure_quality": self.data["stock"].get("structure_confidence", "low"),
                "indicator_quality": "high" if self.data["indicators"].get("rsi") is not None and self.data["indicators"].get("ema_20") is not None else "low",
                "event_data_quality": (
                    "high" if str(self.data["event"].get("source", "")).startswith("nepse_")
                    else "medium" if self.data["event"].get("source") == "sebon_prospectus"
                    else "low"
                ),
                "truth_data_quality": "high" if self.data.get("truth") else "low",
                "truth_alignment_quality": (
                    "aligned"
                    if truth_close_diff is not None and abs(truth_close_diff) <= 0.5
                    else "mismatch" if truth_close_diff is not None else "unknown"
                ),
                "outcome_history_quality": "low"
            },
            "uncertainties": uncertainties,
            "decision_inputs": {
                "setup_type": decision.get("setup_type"),
                "score": decision.get("score"),
                "confidence": decision.get("confidence"),
                "action": decision.get("action"),
                "watchlist_tier": decision.get("watchlist_tier"),
                "watchlist_priority": decision.get("watchlist_priority"),
                "watchlist_score": decision.get("watchlist_score"),
                "entry_zone": decision.get("entry_zone", []),
                "stop_loss": decision.get("stop_loss"),
                "targets": decision.get("targets", []),
                "risk_reward_ratio": decision.get("risk_reward_ratio"),
                "qc_status": self.data.get("qc", {}).get("status"),
                "qc_findings": self.data.get("qc", {}).get("findings", [])
            }
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
            
            # Step 4: Capture external truth layer
            await self.capture_truth_layer()

            # Step 5: Capture official event context
            await self.capture_event_context()

            # Step 6: Generate analysis and decision
            await self.generate_analysis()
            
            # Step 7: Create all normalized records
            await self.create_normalized_records()
            
            print(f"\n{'='*60}")
            print(f"✓ Analysis completed successfully!")
            print(f"{'='*60}\n")
            return True
            
        except Exception as e:
            print(f"\n✗ Error during analysis: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.browser.close()

    
    async def capture_market_context(self):
        """Capture NEPSE market context"""
        print("\n[1/7] Capturing market context...")

        # Navigate to NEPSE index (loads on 1D by default)
        await self.browser.search_and_load_symbol("NEPSE")
        await asyncio.sleep(2)

        # Take market screenshot
        screenshot_path = os.path.join(self.run_dirs["raw_screenshots"], f"{self.file_prefix}__NEPSE__1D__market_context.png")
        await self.browser.take_screenshot(screenshot_path)
        self._record_evidence(screenshot_path)

        # Get snapshot
        snapshot = await self.browser.get_page_snapshot()
        if snapshot:
            snapshot_path = os.path.join(self.run_dirs["raw_snapshots"], f"{self.file_prefix}__NEPSE__1D__snapshot.txt")
            os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(snapshot)
            self._record_evidence(snapshot_path)

        # Extract real market data from chart
        market_ohlc = await self.browser.extract_chart_data()
        self._save_raw_json(
            f"{self.file_prefix}__NEPSE__1D__market_extract.json",
            {"extraction_type": "market_chart", "data": market_ohlc}
        )
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
        print(f"\n[2/7] Analyzing {self.symbol}...")
        
        # Search and load symbol
        await self.browser.search_and_load_symbol(self.symbol)
        await asyncio.sleep(2)
        
        context_timeframes = self._get_context_timeframes()
        for index, timeframe in enumerate(context_timeframes):
            await self._capture_stock_timeframe(timeframe, configure_indicators=(index == 0))

        print(f"✓ {self.symbol} analysis completed")
        print(f"  Primary ({self.timeframe}) Data: {self.data['stock']}")
        print(f"  Primary ({self.timeframe}) Indicators: {self.data['indicators']}")

    
    async def capture_sector_evidence(self):
        """Capture sector chart evidence"""
        print("\n[3/7] Capturing sector evidence...")
        
        sector_symbol = self.sector_map.get(self.symbol)
        if not sector_symbol:
            self.data["sector"] = {
                "name": "UNKNOWN",
                "change_pct": None,
                "trend_label": "unknown",
                "notes": f"sector_mapping_missing_for_symbol:{self.symbol}"
            }
            print(f"  Sector mapping missing for {self.symbol}; recording explicit skip")
            return
        
        # Load sector chart
        await self.browser.search_and_load_symbol(sector_symbol)
        await asyncio.sleep(2)

        # Extract real sector OHLCV data
        sector_ohlc = await self.browser.extract_chart_data()
        self._save_raw_json(
            f"{self.file_prefix}__{sector_symbol}__sector_extract.json",
            {"extraction_type": "sector_chart", "sector_symbol": sector_symbol, "data": sector_ohlc}
        )
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
        self._record_evidence(screenshot_path)

        # Get sector snapshot
        snapshot = await self.browser.get_page_snapshot()
        if snapshot:
            snapshot_path = os.path.join(self.run_dirs["raw_snapshots"], f"{self.file_prefix}__{sector_symbol}__sector_snapshot.txt")
            os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(snapshot)
            self._record_evidence(snapshot_path)

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

    async def capture_event_context(self):
        """Capture official event context from SEBON plus NEPSE truth-feed notices."""
        print("\n[5/7] Capturing official event context...")

        company_name = (
            self.data.get("stock", {}).get("series_title")
            or self.symbol
        )

        try:
            event_data = self.event_extractor.find_recent_official_event(
                self.symbol,
                company_name,
                self.run_date,
                truth_bundle=self.data.get("truth", {})
            )
        except Exception as exc:
            event_data = {
                "event_found": False,
                "source": "sebon_prospectus",
                "event_date": "",
                "event_type": "event_lookup_failed",
                "sentiment": "neutral",
                "impact_window_days": 0,
                "relevance_now": "inactive",
                "confidence_source": "manual_note",
                "details": {
                    "company_name": company_name,
                    "symbol": self.symbol,
                    "error": str(exc)
                },
                "source_refs": []
            }

        self.data["event"] = event_data
        self._save_raw_json(
            f"{self.file_prefix}__event_extract.json",
            {
                "extraction_type": "official_event_context",
                "symbol": self.symbol,
                "data": event_data
            }
        )
        print(
            f"  Event: {event_data.get('event_type')} "
            f"({event_data.get('relevance_now')})"
        )
        print("✓ Official event context captured")

    async def capture_truth_layer(self):
        """Capture external raw-data truth and compare it with browser evidence."""
        print("\n[4/7] Capturing external truth layer...")

        try:
            truth_source = get_truth_source(self.truth_source_name, verify_ssl=False)
            truth_bundle = truth_source.build_truth_bundle(self.symbol)
            comparison = build_truth_comparison(
                self.symbol,
                self.run_date,
                self.timeframe,
                truth_bundle,
                {
                    "daily_stock": self.data.get("timeframes", {}).get("1D", {}).get("stock", {}),
                    "primary_stock": self.data.get("stock", {}),
                    "daily_indicator": self.data.get("timeframes", {}).get("1D", {}).get("indicators", {}),
                    "market": self.data.get("market", {}),
                    "sector": self.data.get("sector", {}),
                }
            )

            self.data["truth"] = truth_bundle
            self.data["truth_comparison"] = comparison

            self._save_raw_json(
                f"{self.file_prefix}__api_truth_bundle.json",
                {
                    "extraction_type": "external_truth_bundle",
                    "truth_source": self.truth_source_name,
                    "symbol": self.symbol,
                    "data": truth_bundle
                }
            )
            self._save_raw_json(
                f"{self.file_prefix}__{self.timeframe}__api_truth_comparison.json",
                {
                    "extraction_type": "external_truth_comparison",
                    "truth_source": self.truth_source_name,
                    "symbol": self.symbol,
                    "timeframe": self.timeframe,
                    "data": comparison
                }
            )

            close_diff = comparison.get("api_vs_browser_daily", {}).get("close_diff")
            if close_diff is None:
                print("  Truth comparison captured, but no direct daily close comparison was available.")
            else:
                print(f"  Truth comparison daily close diff: {close_diff}")
            print("✓ External truth layer captured")
        except Exception as exc:
            self.data["truth"] = {
                "truth_source": self.truth_source_name,
                "status": "failed",
                "error": str(exc)
            }
            self.data["truth_comparison"] = {}
            self._save_raw_json(
                f"{self.file_prefix}__{self.timeframe}__api_truth_comparison.json",
                {
                    "extraction_type": "external_truth_comparison",
                    "truth_source": self.truth_source_name,
                    "symbol": self.symbol,
                    "timeframe": self.timeframe,
                    "error": str(exc)
                }
            )
            print(f"  Truth layer unavailable: {exc}")

    
    async def generate_analysis(self):
        """Generate scores and decision"""
        print("\n[6/7] Generating analysis...")

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
        price_levels = self.structure.derive_price_levels(price, self.data["stock"], self.data["indicators"])
        nearest_support = price_levels["nearest_support"]
        nearest_resistance = price_levels["nearest_resistance"]
        structure_confidence = price_levels.get("structure_confidence", "medium")
        structure_label = price_levels.get("structure_label", "insufficient_structure")

        volume_profile = self.structure.derive_volume_profile(self.data["stock"])
        self.data["volume"] = volume_profile
        volume_score = self.analyzer.calculate_volume_score(volume_profile["volume_vs_average"])

        location_score = self.analyzer.calculate_location_score(
            price,
            nearest_support,
            nearest_resistance
        )
        structure_score = self.analyzer.calculate_structure_quality_score(
            trend_label,
            structure_label=structure_label,
            structure_confidence=structure_confidence
        )

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
            "event_quality": 7 if self.data["event"].get("event_found") and self.data["event"].get("relevance_now") == "active_window" else 5,
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
        setup_type = self.analyzer.determine_setup_type(
            trend_label,
            price,
            ema_20,
            rsi,
            structure_label=structure_label
        )

        self._derive_timeframe_context("1M")
        self._derive_timeframe_context("1W")
        self._derive_timeframe_context("1D")
        timeframe_alignment = self.analyzer.evaluate_timeframe_alignment(
            (self.data.get("timeframes", {}).get("1M") or {}).get("stock", {}),
            (self.data.get("timeframes", {}).get("1W") or {}).get("stock", {}),
            (self.data.get("timeframes", {}).get("1D") or {}).get("stock", {}),
            setup_type
        )
        self.data["timeframe_alignment"] = timeframe_alignment

        if setup_type == "continuation":
            entry_zone = self.analyzer.select_continuation_entry(
                price,
                nearest_support,
                ema_20,
                ma_50,
                price_levels["invalidation_level"]
            )
            stop_loss = price_levels["invalidation_level"]
        elif setup_type in {"reversal_watch", "breakout_watch"}:
            breakout_level = price_levels["breakout_level"]
            entry_zone = [
                breakout_level,
                self.structure.round_price(breakout_level * 1.01)
            ]
            stop_loss = price_levels["invalidation_level"]
        else:
            entry_zone = []
            stop_loss = None

        targets = []
        risk_reward_ratio = None
        if entry_zone and stop_loss is not None:
            targets = [
                self.structure.round_price(target)
                for target in self.analyzer.filter_viable_targets(
                    entry_zone[0],
                    stop_loss,
                    price_levels["resistance_levels"]
                )
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

        if timeframe_alignment["status"] == "conflicted" and action in {"watch_only", "buy", "strong_buy"}:
            action = "avoid"
            entry_zone = []
            stop_loss = None
            targets = []
            risk_reward_ratio = None

        self.data["stock"].update({
            "trend_label": trend_label,
            "structure_label": structure_label,
            "swing_highs": price_levels["resistance_levels"],
            "swing_lows": price_levels["support_levels"],
            "support_zones": self.structure.levels_to_zones(price_levels["support_levels"]),
            "resistance_zones": self.structure.levels_to_zones(price_levels["resistance_levels"]),
            "breakout_level": price_levels["breakout_level"],
            "breakdown_level": price_levels["breakdown_level"],
            "invalidation_level": stop_loss,
            "local_range_high": price_levels.get("local_range_high"),
            "local_range_low": price_levels.get("local_range_low"),
            "range_width_pct": price_levels.get("range_width_pct"),
            "structure_confidence": structure_confidence,
            "structure_confidence_reasons": price_levels.get("confidence_reasons", []),
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
        if timeframe_alignment["status"] == "conflicted":
            self.data["scores"]["notes"] = (
                (self.data["scores"]["notes"] + "; " if self.data["scores"]["notes"] else "")
                + f"timeframe_alignment:{','.join(timeframe_alignment['findings']) or 'conflicted'}"
            )
        if structure_confidence == "low":
            if action in {"buy", "strong_buy"}:
                action = "watch_only"
            self.data["scores"]["notes"] = (
                (self.data["scores"]["notes"] + "; " if self.data["scores"]["notes"] else "")
                + "structure_confidence_low"
            )
        decision_payload = {
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
                f"Event: {self.data['event'].get('event_type')} ({self.data['event'].get('relevance_now')})",
                f"Derived support/resistance: {nearest_support} / {nearest_resistance}",
                f"Structure: {structure_label} ({structure_confidence})",
                f"Timeframe alignment: {timeframe_alignment['status']} ({', '.join(timeframe_alignment['findings']) if timeframe_alignment['findings'] else 'supportive'})",
                f"Local range: {price_levels.get('local_range_low')} -> {price_levels.get('local_range_high')}",
                f"Setup: {setup_type}, Score: {score_summary['percent']}/100, Confidence: {confidence}%",
                f"Action: {action.upper()}"
            ]
        }
        truth_close_diff = self.data.get("truth_comparison", {}).get("api_vs_browser_daily", {}).get("close_diff")
        if truth_close_diff is not None:
            decision_payload["why"].append(
                f"Truth daily close diff: {truth_close_diff}"
            )
        qc_result = self.quality_gate.evaluate(
            decision_payload,
            self.data["stock"],
            self.data.get("truth_comparison", {}),
            self.data.get("truth", {}),
            self.data.get("event", {})
        )
        self.data["qc"] = qc_result
        self._save_raw_json(
            f"{self.file_prefix}__{self.timeframe}__decision_qc.json",
            {
                "extraction_type": "decision_qc",
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "data": qc_result
            }
        )
        if qc_result["status"] != "pass":
            qc_notes = ", ".join(qc_result["findings"]) or "qc_failed"
            self.data["scores"]["notes"] = (
                (self.data["scores"]["notes"] + "; " if self.data["scores"]["notes"] else "")
                + f"qc_gate:{qc_notes}"
            )
            decision_payload = qc_result["decision"]
            decision_payload["why"] = decision_payload.get("why", []) + [f"QC gate: {qc_notes}"]
            if "truth_daily_close_mismatch_major" in qc_result["findings"]:
                decision_payload["why"].append(
                    "External truth layer disagreed materially with browser daily data, so the setup was downgraded for reliability."
                )
            active_event_findings = [
                finding for finding in qc_result["findings"]
                if finding.startswith("active_event_window:")
            ]
            if active_event_findings:
                decision_payload["why"].append(
                    "An active corporate-action window makes the technical setup less trustworthy right now."
                )
            if "liquidity_below_minimum" in qc_result["findings"]:
                decision_payload["why"].append(
                    "Truth-layer liquidity was too weak for a reliable actionable setup."
                )
            if "liquidity_unconfirmed" in qc_result["findings"]:
                decision_payload["why"].append(
                    "Truth-layer liquidity could not be confirmed, so the setup was downgraded conservatively."
                )
        else:
            rank_result = self.analyzer.rank_watchlist_candidate(
                decision_payload.get("action"),
                decision_payload.get("setup_type"),
                score_summary["percent"],
                decision_payload.get("confidence") or 0,
                decision_payload.get("risk_reward_ratio"),
                structure_confidence,
                self.data["stock"].get("location_label")
            )
            decision_payload["watchlist_tier"] = rank_result["watchlist_tier"]
            decision_payload["watchlist_priority"] = rank_result["watchlist_priority"]
            decision_payload["watchlist_score"] = rank_result["watchlist_score"]

            if rank_result["action"] != decision_payload.get("action"):
                decision_payload["action"] = rank_result["action"]
                decision_payload["entry_zone"] = []
                decision_payload["stop_loss"] = None
                decision_payload["invalidation_level"] = None
                decision_payload["targets"] = []
                decision_payload["risk_reward_ratio"] = None

            if rank_result["notes"]:
                note_text = ", ".join(rank_result["notes"])
                self.data["scores"]["notes"] = (
                    (self.data["scores"]["notes"] + "; " if self.data["scores"]["notes"] else "")
                    + f"watchlist_gate:{note_text}"
                )
                decision_payload["why"].append(f"Watchlist gate: {note_text}")

        self.data["decision"] = decision_payload
        
        print(
            f"✓ Analysis complete: {self.data['decision']['action'].upper()} "
            f"(Score: {score_summary['percent']}/100, Confidence: {confidence}%)"
        )

    
    async def create_normalized_records(self):
        """Create all normalized JSON records"""
        print("\n[7/7] Creating normalized records...")

        for timeframe in self.data.get("timeframes", {}):
            self._derive_timeframe_context(timeframe)
        
        # Session record
        self.file_gen.generate_session_record(
            self.symbol,
            self.timeframe,
            stages_completed=[
                "market_context_capture", "symbol_chart_load",
                "timeframe_selection", "indicator_setup",
                "clean_chart_capture",
                "sector_evidence_capture" if self.data["sector"].get("name") != "UNKNOWN" else "sector_mapping_check",
                "official_event_capture",
                "external_truth_capture",
                "decision_qc"
            ],
            stages_skipped=(
                ["broker_flow_capture"]
                + (["sector_evidence_capture"] if self.data["sector"].get("name") == "UNKNOWN" else [])
            ),
            notes=(
                "Automated analysis run"
                + (
                    f"; truth_source={self.truth_source_name}"
                    if self.data.get("truth")
                    else ""
                )
                + (
                    f"; qc_gate={','.join(self.data.get('qc', {}).get('findings', []))}"
                    if self.data.get("qc", {}).get("findings")
                    else ""
                )
            )
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
        for timeframe, timeframe_payload in self.data.get("timeframes", {}).items():
            timeframe_evidence = self.data["timeframe_evidence"].get(timeframe, self.data["evidence_files"])

            self.file_gen.generate_stock_chart_record(
                self.symbol,
                timeframe,
                timeframe_payload.get("stock", {}),
                timeframe_evidence
            )

            self.file_gen.generate_indicator_record(
                self.symbol,
                timeframe,
                timeframe_payload.get("indicators", {}),
                timeframe_evidence
            )

            self.file_gen.generate_volume_record(
                self.symbol,
                timeframe,
                timeframe_payload.get("volume", {}),
                timeframe_evidence
            )
        
        # Relative strength record
        self.file_gen.generate_relative_strength_record(
            self.symbol,
            self.data.get("relative_strength", {"benchmark_sector": self.data["sector"]["name"]}),
            self.data["evidence_files"]
        )

        # Model-input record
        self.file_gen.generate_model_input_record(
            self.symbol,
            self.timeframe,
            self._build_model_input_payload(),
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
            self.timeframe,
            self.data["decision"],
            self.data["evidence_files"]
        )
        
        # Event record
        self.file_gen.generate_event_record(
            self.symbol,
            self.data.get("event", {}),
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
