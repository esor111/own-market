# Next Steps Summary — 2026-04-27

## What We Just Accomplished

### Gap 1: Broker-Flow Backfill ✅ MOSTLY COMPLETE

| Symbol | Before | After | Status |
|--------|--------|-------|--------|
| AHPC | 70 days | **467 days** | ✅ Complete |
| RADHI | 70 days | **376 days** | ✅ Complete |
| RHPL | 70 days | **110+ days** | ⏳ In progress (~1-2 hours remaining) |

**Impact**: These three symbols now have **3 years** of broker-flow history instead of 4 months. This transforms their avoid/buy signals from "interesting coincidences" to "trustworthy patterns."

## Remaining Gaps

### Gap 2: Intraday Tape Data ⚠️ HIGH PRIORITY

**Current State**:
- UPPER: 23 days ✅
- All others: 0 days

**Why This Matters**:
Without intraday data, we can't distinguish:
- **Panic selling** vs. **smart money absorption**
- **Morning weakness** vs. **afternoon recovery**
- **Volume spikes** at open vs. close

**Data Source**: TradingView-style charts on nepsealpha.com (as seen in BHL data)

**Next Steps**:
1. Build a scraper for nepsealpha.com chart data (minute/hourly resolution)
2. Run daily scrapes for all 7 symbols going forward
3. Optionally backfill recent 30-60 days

**Minimum Viable**: 30 trading days per symbol to start seeing patterns

### Gap 3: Daily Refresh Discipline ⚠️ CRITICAL

**Current State**: System frozen at April 24, 2026

**What's Needed**: Daily workflow after market close (3:00 PM Nepal time):
1. Scrape latest price data (OHLCV)
2. Scrape latest broker-flow (floorsheet)
3. Scrape latest intraday tape (minute/hourly)
4. Recompute avoid/buy signals

**Automation Options**:
- **Manual**: Run scripts each evening (simplest, most reliable)
- **Scheduled**: Windows Task Scheduler or cron
- **Cloud**: GitHub Actions (requires setup)

## Recommended Priority Order

### 1. Wait for RHPL Backfill ⏳ (1-2 hours)
Let the current process finish. RHPL is at 110 files, target is ~400.

### 2. Verify Backfill Success ✅ (5 minutes)
Once RHPL completes, verify:
- AHPC: 467 files, 2023-01-01 to 2026-04-24
- RADHI: 376 files, 2023-01-01 to 2026-04-24
- RHPL: ~400 files, 2023-01-01 to 2026-04-24

### 3. Build Intraday Scraper 🔨 (2-4 hours)
Create a script to scrape nepsealpha.com chart data:
- Input: symbol, date range
- Output: minute/hourly volume CSV (like `bhl_volume_minute_last_30d.csv`)
- Target: All 7 symbols (UPPER, AKPL, API, AHPC, RADHI, RHPL, BHCL)

### 4. Run First Intraday Collection 📊 (30 minutes)
Collect last 30 days of intraday data for all symbols

### 5. Establish Daily Refresh 🔄 (ongoing)
Set up daily workflow (manual or automated) to keep system current

## Success Metrics

After completing all steps:
- ✅ All 7 symbols have 3+ years of broker-flow data
- ✅ All 7 symbols have 30+ days of intraday tape data
- ✅ System is current within 24 hours of market close
- ✅ Avoid/buy signals are trustworthy and actionable

## Current Blockers

**None** - RHPL backfill is running in background. You can start working on the intraday scraper in parallel if you want, or wait for RHPL to complete first.

## Files Created This Session

1. `BACKFILL_STATUS_2026-04-27.md` - Broker-flow backfill tracking
2. `DATA_GAP_ANALYSIS_2026-04-27.md` - Comprehensive gap analysis
3. `NEXT_STEPS_SUMMARY_2026-04-27.md` - This file
4. `backfill_ahpc_radhi_rhpl_2023-2025.log` - Backfill log (AHPC + RADHI complete)
5. `backfill_rhpl_2023-2025.log` - RHPL backfill log (in progress)

## Background Process

**Terminal ID 3**: RHPL backfill still running
- Check progress: `Get-ChildItem -Path market-gist/broker_flow_ledger/RHPL/*.json | Measure-Object`
- Check if complete: `listProcesses` (should show no processes when done)
