# SMHL Analysis V2 - Evidence Audit Report
**Date:** 2026-03-16  
**Session ID:** 2026-03-16__SMHL__v2  
**Symbol:** SMHL (Super Madi Hydropower Limited)  
**Timeframe:** 1W (Weekly)

---

## Executive Summary

This is a **Version 2 reliability-first analysis** with stricter evidence capture requirements. All decisions are traceable through evidence references. This audit documents what was directly extracted, visually inferred, skipped, and what remains uncertain.

**Final Decision:** WATCH ONLY (Score: 38/100, Confidence: 50%)

---

## 1. DIRECTLY EXTRACTED (High Confidence)

### Market Data (NEPSE)
- **Source:** DOM extraction from NEPSE Alpha chart
- **Method:** JavaScript evaluation of page elements
- **Data Captured:**
  - NEPSE Close: 2798.83
  - Change: -0.92%
- **Evidence:** 
  - `2026-03-16__NEPSE__extracted_data.json`
  - `2026-03-16__NEPSE__1D__snapshot.txt`
- **Confidence:** 95% (directly extracted from DOM)

### SMHL OHLCV Data
- **Source:** Visual reading from TradingView chart legend
- **Data Captured:**
  - Open: 530.00
  - High: 535.00
  - Low: 515.00
  - Close: 516.00
  - Change: -11.00 (-2.09%)
  - Volume: 585,772
- **Evidence:**
  - `2026-03-16__SMHL__1W__indicators_extracted.json`
  - `2026-03-16__SMHL__1W__clean_v2.png`
- **Confidence:** 90% (visual extraction from screenshot)

### Technical Indicators
- **Source:** Visual reading from TradingView indicator legends
- **Data Captured:**
  - EMA 20: 587.52
  - MA 50: 785.38
  - MACD Line: 2.68
  - Signal Line: -91.92
  - Histogram: -94.60
  - RSI: 37.75
- **Evidence:**
  - `2026-03-16__SMHL__1W__indicators_extracted.json`
  - `2026-03-16__SMHL__1W__with_indicators_snapshot.txt`
- **Confidence:** 90% (visual extraction from screenshot)

### Hydropower Sector Data
- **Source:** Visual reading from TradingView chart
- **Data Captured:**
  - Close: 3758.48
  - Change: -21.05 (-0.56%)
  - EMA 20: 3519.60
  - MA 50: 3492.44
  - RSI: 63.69
  - MACD: 41.82, 62.49, 20.67
- **Evidence:**
  - `2026-03-16__Hydropower__sector.png`
  - `2026-03-16__Hydropower__sector_snapshot.txt`
- **Confidence:** 90% (visual extraction with screenshot evidence)

---

## 2. VISUALLY INFERRED (Medium Confidence)

### Chart Structure Analysis
- **Method:** Visual pattern recognition from candlestick chart
- **Inferences:**
  - Trend: Downtrend (lower highs, lower lows)
  - Structure: Clear downtrend structure
  - Swing Highs: ~1200, 1100, 950, 850
  - Swing Lows: ~900, 750, 650, 515
  - Support Zones: 500, 480, 450
  - Resistance Zones: 550, 600, 650
- **Evidence:**
  - `2026-03-16__SMHL__1W__clean_v2.png`
  - `2026-03-16__SMHL__1W__annotated_v2.png`
- **Confidence:** 70% (subjective pattern recognition)

### Volume Analysis
- **Method:** Visual comparison of volume bars
- **Inferences:**
  - Volume vs Average: Below average
  - Volume Trend: Declining during downtrend
  - Participation: Low
- **Evidence:**
  - `2026-03-16__SMHL__1W__clean_v2.png`
- **Confidence:** 60% (no historical average data for comparison)

### Market Phase Assessment
- **Method:** Price action and volume interpretation
- **Inferences:**
  - NEPSE: Distribution phase
  - SMHL: Downtrend continuation
- **Evidence:**
  - `2026-03-16__NEPSE__1D__market_context.png`
  - `2026-03-16__SMHL__1W__annotated_v2.png`
- **Confidence:** 60% (subjective interpretation)

### Relative Strength Calculation
- **Method:** Comparative performance analysis
- **Inferences:**
  - SMHL vs NEPSE: Underperforming (SMHL -2.09% vs NEPSE -0.92%)
  - SMHL vs Hydropower: Underperforming (SMHL -2.09% vs Sector -0.56%)
- **Evidence:**
  - All three data sources combined
- **Confidence:** 85% (calculated from extracted data)

---

## 3. SKIPPED (With Explicit Documentation)

### Event Enrichment
- **Status:** Completed with no findings
- **Reason:** No corporate actions, dividends, or significant events visible on chart
- **Documentation:** Created explicit no-event record
- **Evidence:**
  - `2026-03-16__SMHL__event_v2.json`
- **Impact:** Neutral (no events to factor into decision)

### Broker Flow / Floorsheet Data
- **Status:** Unavailable
- **Reason:** Floorsheet access on NEPSE Alpha requires user login/authentication
- **Documentation:** Created explicit unavailable record with reason
- **Evidence:**
  - `2026-03-16__SMHL__broker_flow_v2.json`
- **Impact:** Missing institutional flow data reduces confidence in decision

---

## 4. UNCERTAIN / LOW CONFIDENCE

### Exact Support/Resistance Levels
- **Issue:** Support and resistance zones are approximate based on visual inspection
- **Uncertainty:** ±5-10 points on each level
- **Impact:** Entry and stop loss levels have margin of error
- **Mitigation:** Use zones rather than exact prices

### Volume Average Comparison
- **Issue:** No historical volume data to calculate true average
- **Uncertainty:** "Below average" is relative visual assessment
- **Impact:** Volume confirmation score may be inaccurate
- **Mitigation:** Marked as low confidence in scoring

### Risk/Reward Ratio
- **Issue:** Based on estimated support/resistance levels
- **Uncertainty:** Actual R:R may vary by ±0.5
- **Impact:** Trade sizing and position management affected
- **Mitigation:** Conservative position sizing recommended

### Sector Relative Strength Timeframe Mismatch
- **Issue:** Comparing SMHL weekly data with sector weekly data, but market is daily
- **Uncertainty:** Timeframe alignment not perfect
- **Impact:** Relative strength comparison may not be apples-to-apples
- **Mitigation:** Noted in analysis, used weekly sector data for better alignment

---

## 5. EVIDENCE TRACEABILITY

### All Normalized Records Created
✅ Session: `2026-03-16__SMHL__session_v2.json`  
✅ Market: `2026-03-16__NEPSE__1D__market_v2.json`  
✅ Sector: `2026-03-16__Hydropower__sector_v2.json`  
✅ Stock Chart: `2026-03-16__SMHL__1W__stock_chart_v2.json`  
✅ Indicators: `2026-03-16__SMHL__1W__indicator_v2.json`  
✅ Volume: `2026-03-16__SMHL__1W__volume_v2.json`  
✅ Relative Strength: `2026-03-16__SMHL__relative_strength_v2.json`  
✅ Feature Score: `2026-03-16__SMHL__feature_score_v2.json`  
✅ Decision: `2026-03-16__SMHL__decision_v2.json`  
✅ Event: `2026-03-16__SMHL__event_v2.json` (no events found)  
✅ Broker Flow: `2026-03-16__SMHL__broker_flow_v2.json` (unavailable)

### All Raw Evidence Captured
✅ NEPSE Snapshot: `2026-03-16__NEPSE__1D__snapshot.txt`  
✅ NEPSE Extracted: `2026-03-16__NEPSE__extracted_data.json`  
✅ NEPSE Screenshot: `2026-03-16__NEPSE__1D__market_context.png`  
✅ SMHL Pre-Indicators: `2026-03-16__SMHL__1W__pre_indicators_snapshot.txt`  
✅ SMHL With Indicators: `2026-03-16__SMHL__1W__with_indicators_snapshot.txt`  
✅ SMHL Indicators Extracted: `2026-03-16__SMHL__1W__indicators_extracted.json`  
✅ SMHL Clean Chart: `2026-03-16__SMHL__1W__clean_v2.png`  
✅ SMHL Annotated Chart: `2026-03-16__SMHL__1W__annotated_v2.png`  
✅ Hydropower Snapshot: `2026-03-16__Hydropower__sector_snapshot.txt`  
✅ Hydropower Screenshot: `2026-03-16__Hydropower__sector.png`

---

## 6. SCORING BREAKDOWN

### Feature Scores (Total: 38/100)
- Market Alignment: 3/10 (NEPSE in distribution, weak)
- Sector Alignment: 5/10 (Hydropower slightly better than market)
- Structure Quality: 4/10 (Clear downtrend, but that's bearish)
- Location Quality: 6/10 (Near support, potential reversal zone)
- Trend Filter Quality: 2/10 (Price below EMA 20 and MA 50)
- Volume Confirmation: 3/10 (Low volume, no spike)
- Momentum Confirmation: 3/10 (RSI weak, MACD negative)
- Relative Strength: 2/10 (Underperforming market and sector)
- Event Quality: 5/10 (No events, neutral)
- Risk/Reward Quality: 5/10 (Decent R:R but high uncertainty)

### Confidence: 50%
- Reduced by: Missing broker flow data, volume uncertainty, subjective level placement
- Supported by: Clear indicator readings, sector evidence, multiple screenshots

---

## 7. FINAL DECISION RATIONALE

**Action:** WATCH ONLY

**Why Watch, Not Enter:**
1. Price below both EMA 20 (587.52) and MA 50 (785.38) - trend filters failed
2. MACD histogram deeply negative (-94.60) - strong bearish momentum
3. Underperforming both market and sector - weak relative strength
4. Market (NEPSE) in distribution phase - unfavorable environment
5. No volume spike or reversal signal yet

**What Would Change Decision to BUY:**
1. RSI bullish divergence (lower low in price, higher low in RSI)
2. Volume spike on green candle (capitulation/reversal)
3. Price reclaim of EMA 20 (587.52)
4. MACD histogram turning positive
5. Market (NEPSE) showing strength

**Entry Zone (if conditions met):** 480-500  
**Stop Loss:** 450  
**Targets:** 550, 600, 650  
**Risk/Reward:** ~1.5:1

---

## 8. RELIABILITY IMPROVEMENTS vs V1

### What's Better in V2:
✅ Captured actual Hydropower sector screenshot (not skipped)  
✅ Saved raw page snapshots at multiple stages  
✅ Extracted indicator values into JSON (not just screenshots)  
✅ Added full indicator suite (EMA 20, MA 50, MACD, RSI)  
✅ Created explicit no-event record (not just skipped)  
✅ Created explicit broker flow unavailable record with reason  
✅ All decisions traceable through evidence_refs  
✅ This audit document showing extraction vs inference vs uncertainty

### What's Still Limited:
⚠️ No broker flow data (requires login)  
⚠️ Support/resistance levels are approximate  
⚠️ Volume comparison lacks historical baseline  
⚠️ Some subjective interpretation in pattern recognition

---

## 9. CONCLUSION

This Version 2 analysis provides **significantly more evidence traceability** than V1. Every decision can be traced back to specific evidence files. The audit clearly separates what was directly extracted (high confidence) from what was visually inferred (medium confidence) and what was skipped or uncertain (documented limitations).

**The analysis is reliable enough to inform a WATCH decision, but not confident enough to recommend immediate entry.** The 38/100 score and 50% confidence accurately reflect the current weak setup.

**Next Steps:**
- Monitor for reversal signals (RSI divergence, volume spike)
- Watch for price reclaim of EMA 20 (587.52)
- Re-analyze if market (NEPSE) shows strength
- Consider entry only if score improves to 60+ with 70%+ confidence

---

**Audit Completed:** 2026-03-16T21:30:06+05:45  
**Auditor:** Automated reliability-first workflow  
**Compliance:** All evidence captured, all decisions traceable
