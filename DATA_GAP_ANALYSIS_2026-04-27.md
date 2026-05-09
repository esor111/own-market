# Data Gap Analysis — 2026-04-27

## Current Data Inventory

| Symbol | Price History | Broker-Flow Days | Broker-Flow Coverage | Intraday Tape |
|--------|---------------|------------------|---------------------|---------------|
| UPPER | 1,012 days | 328 (32%) | 2023-06-11 to 2026-04-24 | 23 days ✅ |
| AKPL | 1,012 days | 388 (38%) | 2023-09-07 to 2026-04-24 | 0 days |
| API | 1,012 days | 377 (37%) | Similar to AKPL | 0 days |
| AHPC | 1,012 days | **467 (46%)** ✅ | **2023-01-01 to 2026-04-24** | 0 days |
| RADHI | 1,012 days | **376 (37%)** ✅ | **2023-01-01 to 2026-04-24** | 0 days |
| RHPL | 1,012 days | **~400 (40%)** ⏳ | **2023-01-01 to 2026-04-24** (in progress) | 0 days |
| BHCL | 1,012 days | 69 (7%) | Recent only | 0 days |

## Gap 1: Broker-Flow Backfill ✅ MOSTLY RESOLVED

### Status
- **AHPC**: ✅ Complete (467 files, 2023-2026)
- **RADHI**: ✅ Complete (376 files, 2023-2026)
- **RHPL**: ⏳ In progress (83 files so far, target ~400)

### Impact
Before backfill, AHPC/RADHI/RHPL avoid/buy signals were based on only **69 days** (Jan-Apr 2026). This is too thin to distinguish real patterns from recent coincidences.

After backfill, these symbols have **~400 trading days** of broker-flow history, comparable to UPPER/AKPL/API.

### What This Unlocks
- **Trust the avoid signals** for AHPC, RADHI, RHPL
- **Cross-symbol pattern validation** across 3-year history
- **Regime-aware analysis** (can see how patterns behaved in different market conditions)

## Gap 2: Intraday Tape Data ⚠️ CRITICAL

### Current State
- **UPPER**: 23 days of minute/hourly volume ✅
- **All others**: 0 days

### Why This Matters
Intraday tape data answers:
- Did volume spike in the last 30 minutes?
- Did the stock close strong or weak inside the day's range?
- Was there absorption (large volume, small price move) or panic (large volume, large price move)?
- Did the stock fade after opening strong?

These are the **most diagnostic clues** for accumulation vs. distribution.

### What's Missing
Without intraday data, we're blind to:
- **Panic vs. absorption distinction** — A -3% day with volume spike could be panic selling OR smart money absorbing supply. We can't tell without intraday structure.
- **Close strength** — Did the stock recover from lows or close at lows? This changes the interpretation completely.
- **Volume timing** — Was volume front-loaded (morning panic) or back-loaded (afternoon accumulation)?

### Minimum Viable Solution
**30 trading days** of daily scrapes for each symbol to start building intraday patterns. Ideally 60-90 days.

### Data Source
ShareSansar provides intraday data via their chart endpoints. We already have a scraper for UPPER (`scrape_sharesansar_intraday.py` or similar).

### Next Steps
1. Identify the existing intraday scraper script
2. Extend it to cover AKPL, API, AHPC, RADHI, RHPL, BHCL
3. Run daily scrapes going forward
4. Optionally backfill recent 30-60 days if ShareSansar provides historical intraday data

## Gap 3: Daily Refresh Discipline ⚠️ PROCESS GAP

### Current State
The system is **frozen at April 24, 2026**. Every day after market close, we need to refresh:
- Price data (daily OHLCV)
- Broker-flow data (daily floorsheet)
- Intraday tape data (minute/hourly volume)

### Why This Matters
Without daily refresh:
- The watchlist becomes stale
- Avoid signals can't update
- New accumulation/distribution patterns are missed
- The system becomes a **frozen research artifact** instead of a **live decision tool**

### What's Needed
A daily refresh workflow that runs after market close (typically 3:00 PM Nepal time):

1. **Price refresh**: Scrape latest daily OHLCV from ShareSansar
2. **Broker-flow refresh**: Scrape latest floorsheet from Merolagani
3. **Intraday tape refresh**: Scrape minute/hourly data from ShareSansar
4. **Psychology engine update**: Recompute avoid/buy signals with new data

### Existing Infrastructure
The scripts already exist:
- `scrape_sharesansar_daily.py` (or similar) for price data
- `scrape_merolagani_floorsheet.py` for broker-flow
- `scrape_sharesansar_intraday.py` for tape data

What's missing is the **daily discipline** to run them.

### Automation Options
1. **Manual**: Run scripts manually each evening after market close
2. **Scheduled task**: Windows Task Scheduler or cron job
3. **GitHub Actions**: Cloud-based scheduled workflow
4. **Hybrid**: Manual trigger with automated data collection

## Priority Ranking

### 1. RHPL Backfill Completion (⏳ In Progress)
**Impact**: High  
**Effort**: Low (already running)  
**Timeline**: 1-2 hours

### 2. Intraday Tape Collection (⚠️ Critical)
**Impact**: Very High (unlocks panic vs. absorption distinction)  
**Effort**: Medium (extend existing scraper, run daily)  
**Timeline**: 1-2 days to set up, then daily maintenance

### 3. Daily Refresh Discipline (⚠️ Critical)
**Impact**: Very High (keeps system live)  
**Effort**: Low (scripts exist, need process)  
**Timeline**: Immediate (can start today)

## Recommended Next Steps

1. **Wait for RHPL backfill to complete** (~1-2 hours)
2. **Set up intraday tape scraper** for all 7 symbols
3. **Establish daily refresh workflow** (manual or automated)
4. **Run first full refresh** to bring system current to April 27, 2026
5. **Document the refresh process** so it's repeatable

## Success Metrics

After closing all gaps:
- ✅ All 7 symbols have 3+ years of broker-flow data
- ✅ All 7 symbols have 30+ days of intraday tape data
- ✅ System is current within 24 hours of market close
- ✅ Daily refresh process is documented and running
- ✅ Avoid/buy signals are trustworthy and actionable
