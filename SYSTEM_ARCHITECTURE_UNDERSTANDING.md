# System Architecture — Complete Understanding

## Overview

This is a **sophisticated, multi-layered NEPSE trading research system** with:
- **Automated data collection** (broker flow, price, events)
- **Multi-agent reasoning** (Romeo, Juliet, Grok)
- **Forward validation** (shadow reports, scoring, calibration)
- **Historical replay** (walk-forward testing on 2025 data)
- **Entry research** (execution-aware buy-side analysis)
- **Monitoring stack** (hostile/buy-side pattern tracking)

## System Layers

### Layer 1: Data Collection

**Price Data**:
- Source: ShareSansar CSV archive (`sharesansar_datascrape/data/`)
- Coverage: 1,570 daily files (2021-2026)
- Format: Daily OHLCV per symbol

**Broker-Flow Data**:
- Source: Merolagani floorsheet (via `backfill_merolagani_floorsheet.py`)
- Storage: `market-gist/broker_flow_ledger/{SYMBOL}/{DATE}.json`
- Current coverage:
  - AHPC: 754 files (2023-2026) ✅
  - RADHI: 376 files (2023-2026) ✅
  - RHPL: 754 files (2023-2026) ✅
  - NABIL, EBL, SANIMA: Active shadow symbols
  - AKPL, UPPER, API: Research symbols

**Intraday Tape Data**:
- Source: nepsealpha.com TradingView charts (via `scripts/refresh_nepse_symbol.js`)
- Storage: `{symbol}_volume_1min.csv`, `{symbol}_volume_hourly.csv`, `{symbol}_volume_daily.csv`
- Current coverage:
  - UPPER: 23 days ✅
  - BHL: ~30 days ✅
  - Others: 0 days ❌

**Corporate Actions**:
- Source: ShareSansar, SEBON PDFs, NEPSE company news
- Scripts: `backfill_corporate_actions_2025.py`, `corporate_action_timeline.py`
- Storage: `data/validation/historical_context_backfills/`

**Macro Context**:
- Source: NRB (Nepal Rastra Bank)
- Scripts: `backfill_nrb_macro_context.py`, `nrb_current_macro_discovery.py`
- Data: Interbank rates, policy events

### Layer 2: Signal Generation

**Broker Persistence Shadow** (Main Live Signal):
- Script: `daily_persistence_shadow_report.py`
- Logic: Top-weighted broker selling persistence over 7+ days
- Output: `data/validation/persistence_shadow_reports/{DATE}__persistence_shadow_report_v1.json`
- Current status: 72.7% success rate on 11 resolved cases (N<25, not yet significant)

**Dividend Annotation** (Research-Only):
- Logic: Bank dividend declaration → drift 2-10 days
- Status: 76% negative hit rate (p=0.0002) but annotation-only, not verdict-changing

**Hostile Window Caution** (Validated):
- Logic: Fiscal year-end and post-results windows → avoid borderline setups
- Status: Validated in replay, promoted to champion

**Fragile Sector Caution** (Validated):
- Logic: Certain sector families → demote borderline watch_only to avoid
- Status: Validated in replay, promoted to champion

### Layer 3: Forward Validation

**Shadow Batch Scoring**:
- Script: `score_persistence_shadow_reports.py`
- Logic: Score saved shadow reports against forward price returns
- Output: `data/validation/persistence_shadow_reviews/latest__shadow_batch_scorecard_v1.json`
- Metrics: 10-day success rate, 5-day negative hit rate, mean return, binomial test

**Outcome Tracking**:
- Script: `evaluate_outcome.py`, `reevaluate_pending_outcomes.py`
- Logic: Track forward outcomes for all decisions
- Storage: Per-symbol outcome records

### Layer 4: Historical Replay

**Walk-Forward Replay**:
- Script: `walk_forward_replay.py`
- Logic: Point-in-time replay on 2025 historical data
- Storage: `data/replays/{REPLAY_ID}/`
- Purpose: Test signals on out-of-sample historical data

**Replay Context Backfills**:
- Scripts: `backfill_replay_context.py`, `backfill_replay_derived_context.py`
- Logic: Build replay-safe context (benchmarks, breadth, sector summaries)
- Storage: `data/validation/historical_context_backfills/`

**Replay Diagnostics**:
- Scripts: `replay_market_breadth_diagnostics.py`, `replay_sector_context_diagnostics.py`, etc.
- Logic: Measure which context layers explain replay outcomes
- Output: Diagnostic reports per replay window

**Replay Calibration**:
- Script: `replay_calibration_report.py`, `replay_confidence_remap.py`
- Logic: Build action-aware confidence calibration from replay
- Output: Calibrated confidence bundles

### Layer 5: Monitoring Stack

**Hostile Window Monitor**:
- Script: `aggregate_hostile_window_monitor.py`
- Logic: Track hostile fiscal/results windows where champion still triggers
- Output: Warning/watch baseline for future hostile windows

**Buy-Side Pattern Monitor**:
- Script: `aggregate_buy_side_pattern_monitor.py`
- Logic: Rank repeated realistic winner slices and failure slices
- Output: Candidate-positive slices and warning slices

**Watchlist Derivation**:
- Scripts: `derive_hostile_watchlist.py`, `derive_buy_side_watchlist.py`
- Logic: Convert monitors into reusable watchlist baselines
- Output: Stable/worsening/missing/emergent slice tracking

**Monitoring Cycle**:
- Script: `run_monitoring_cycle.py`
- Logic: Check freshness, run monitors, derive watchlists, build decision gate
- Output: `monitoring_cycle_packet.py`, `monitoring_executive_status.py`

### Layer 6: Entry Research

**Entry Dataset**:
- Script: `build_entry_research_dataset.py`
- Logic: Build execution-aware Entry Research v1 dataset from actionable replay
- Features: Concentration tracking, canonical executable labels

**Entry Baselines**:
- Scripts: `entry_baseline_ranking_study.py`, `entry_relative_feature_study.py`, etc.
- Logic: Test simple ranking baselines on execution-aware entry dataset
- Purpose: Find low-complexity entry candidate families

**Next-Open Entry Lane**:
- Script: `run_entry_next_open_cycle.py`
- Logic: Safe next-open entry lane cycle with freshness gates
- Output: `entry_next_open_decision_gate.py`, `entry_next_open_executive_status.py`

### Layer 7: System Program

**System-Level Cycle**:
- Script: `run_system_program_cycle.py`
- Logic: Run both frozen risk engine (monitoring) and guarded entry lane
- Modes: `--summary-only`, `--force-monitoring`, `--force-entry`, `--force-all`

**Reliability Scorecard**:
- Script: `system_reliability_readiness_scorecard.py`
- Logic: Measure which trust/readiness thresholds are passed
- Output: What blocks higher-trust prediction and buy-side prediction

## Daily Workflow

### Current Daily Routine (Persistence Shadow)

**Step 1: Scrape Broker Flow**
```bash
python run_daily_scrape.py --date 2026-04-27
```
- Reads `scrape_symbol_list.json` for symbol tiers
- Calls `backfill_merolagani_floorsheet.py` for pending symbols
- Writes ledger files to `broker_flow_ledger/{SYMBOL}/{DATE}.json`

**Step 2: Generate Shadow Report**
```bash
python run_persistence_shadow_daily.py --date 2026-04-27
```
- Checks broker flow ledger coverage
- Runs `daily_persistence_shadow_report.py`
- Runs `score_persistence_shadow_reports.py` to refresh outcomes
- Writes shadow report to `data/validation/persistence_shadow_reports/`

### Missing Daily Routines

**Price Data Refresh** ❌
- No automated daily price scraper found
- ShareSansar CSV archive is manually updated
- Need: Daily scraper to add latest OHLCV to archive

**Intraday Tape Refresh** ❌
- Scraper exists (`scripts/refresh_nepse_symbol.js`)
- Not integrated into daily workflow
- Need: Run for all 7 symbols after market close

**Psychology Engine Update** ❌
- No script found that recomputes avoid/buy signals with new data
- Need: Identify and run the signal computation script

## Key Configuration Files

**Symbol Lists**:
- `scrape_symbol_list.json` - Tiered symbol tracking (active_shadow, research, etc.)
- `symbol_lists.json` - Reusable symbol lists (@dev_fast, @replay_basket_v1, etc.)
- `COMMERCIAL_BANK_SYMBOLS.json` - Commercial bank symbols for broker flow

**Sector Mapping**:
- `sector_map.json` - Live browser sector coverage
- `replay_sector_groups.json` - Historical replay sector buckets

**Replay Configuration**:
- Replay IDs follow pattern: `YYYY-MM-DD_to_YYYY-MM-DD__{LIST}__{LABEL}`
- Example: `2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_context_v1`

## Data Storage Structure

```
market-gist/
├── broker_flow_ledger/
│   ├── {SYMBOL}/
│   │   └── {DATE}.json
│   └── raw_merolagani/
│       └── {SYMBOL}/
│           └── {DATE}.json
├── data/
│   ├── raw/
│   │   ├── screenshots/
│   │   ├── snapshots/
│   │   └── tables/
│   ├── normalized/
│   │   ├── sessions/
│   │   ├── market/
│   │   ├── sectors/
│   │   ├── stocks/
│   │   ├── indicators/
│   │   ├── decisions/
│   │   └── broker_flow/
│   ├── features/
│   │   └── setup_scores/
│   ├── symbols/
│   │   └── {SYMBOL}/
│   │       └── {DATE}/
│   ├── validation/
│   │   ├── persistence_shadow_reports/
│   │   ├── persistence_shadow_reviews/
│   │   ├── historical_data_audits/
│   │   ├── historical_context_backfills/
│   │   ├── improvement_proposals/
│   │   └── learning_reviews/
│   └── replays/
│       └── {REPLAY_ID}/
│           ├── sessions/
│           └── summaries/
└── automation/
    └── [150+ Python scripts]
```

## Multi-Agent System

**Romeo** (Directional Reader):
- Role: Lead directional analysis
- Output: Buy/watch_only/avoid recommendations

**Juliet** (Caution/Veto Layer):
- Role: Challenge Romeo's recommendations
- Output: Veto or confirm with caution notes

**Grok** (Observer):
- Role: Observer on unresolved or important cases
- Usage: Optional, not in daily workflow

## Current State (2026-04-27)

**What's Working**:
- ✅ Broker-flow backfill complete for AHPC, RADHI, RHPL (3+ years)
- ✅ Daily broker-flow scraping for active symbols
- ✅ Persistence shadow report generation
- ✅ Forward outcome scoring
- ✅ Historical replay framework
- ✅ Monitoring stack

**What's Missing**:
- ❌ Daily price data refresh
- ❌ Daily intraday tape collection (scraper exists, not integrated)
- ❌ Psychology engine signal recomputation
- ❌ Intraday data for 6 symbols (AKPL, API, AHPC, RADHI, RHPL, BHCL)

**System Frozen At**: April 24, 2026

## Next Steps

### Immediate (Today)
1. Test intraday scraper: `.\test_intraday_scraper.ps1 -Symbol AKPL`
2. Scrape missing intraday data for 6 symbols
3. Identify price data refresh script
4. Identify psychology engine update script

### Short-term (This Week)
5. Integrate intraday scraper into daily workflow
6. Establish daily refresh routine (price + broker + intraday)
7. Update psychology engine with expanded broker-flow data

### Long-term (Ongoing)
8. Run daily workflow after market close
9. Monitor N=25 gate for persistence shadow (late April/early May)
10. Continue replay validation and monitoring

## Bottom Line

This is a **production-grade research system** with:
- Sophisticated data collection and validation
- Multi-layer signal generation and testing
- Forward and historical validation
- Monitoring and entry research lanes

The infrastructure is **90% complete**. What's missing is:
- Daily integration of existing tools
- Process discipline to run daily workflows
- Signal recomputation with expanded data

The hard engineering work is done. Now it's about **operational discipline**.
