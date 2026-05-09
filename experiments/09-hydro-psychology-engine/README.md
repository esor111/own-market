# Experiment 09 - Hydropower Psychology Engine

> Status: planning document / source of truth.
> Created: 2026-04-27.
> Research only. Not financial advice. Not wired to live prediction or persistence shadow.

## Context

We are building this as a separate side quest, not as a replacement for the existing
market experiments.

The existing lanes already have useful pieces:

- Experiment 07 owns hydropower broker-flow and floorsheet pattern testing.
- Experiment 08 owns hydropower volume and tape microstructure.
- Experiment 01 owns corporate actions such as dividend, AGM, book close, and right-share events.
- Experiment 02 owns lock-in expiry and hidden supply pressure context.
- Experiment 03 owns NRB, interbank, and macro liquidity event context.
- Experiment 04 owns hydropower seasonality context.
- Experiment 06 owns hydropower flood/project damage event structure.
- The daily prediction and persistence shadow lanes remain separate operational systems.

Experiment 09 should read from those lanes, join their evidence, score market psychology
states, and test whether those states had useful forward outcomes.

The central idea is simple:

> We are not trying to read volume alone. We are trying to infer a hidden market
> state from price, volume, broker flow, events, regime, and later outcomes.

## Core Question

For hydropower symbols, can we classify each symbol-date into a useful psychology
state such as accumulation, distribution, panic, absorption, failed rally, or
two-sided churn, and then prove which labels had positive or negative forward
expectancy?

The engine should answer questions like:

- Is this real accumulation or just a weak bounce?
- Is heavy down volume panic selling or controlled distribution?
- Did strong buyers absorb sellers near support?
- Are brokers showing persistent net accumulation or short-term churn?
- Did a rally fail because supply appeared at higher prices?
- Is a volume spike explained by right share, book close, lock-in, macro stress, or project news?
- After this same setup happened historically, what happened over the next 1, 3, 5, 10, and 20 trading sessions?

## Non-Goals

This experiment must not:

- modify live prediction prompts
- update persistence shadow policy
- scrape into the canonical daily pipeline
- overwrite experiment 07 or 08 outputs
- claim exact identity of "main players" vs retail traders
- claim certainty from public data

Broker numbers are evidence, not identity. A broker can contain retail flow,
large-client flow, or both. The software can infer professional-like behavior,
but it cannot know the real actor behind a broker number from public data alone.

## Current Data We Can Use

### Daily Price / OHLCV

Source:

- `sharesansar_datascrape/data/*.csv`

Useful fields:

- open, high, low, close, LTP, VWAP, volume, turnover, trades

Purpose:

- trend, range, close position, volume regime, turnover regime, forward returns

### Broker Flow / Floorsheet

Sources:

- `market-gist/broker_flow_ledger/raw_merolagani/<SYMBOL>/<YYYY-MM-DD>.json`
- `experiments/07-hydro-broker-flow/data/hydro_broker_flow_daily.csv`

Useful fields:

- buyer broker
- seller broker
- quantity
- rate
- amount
- top buyer/seller concentration
- top net buyers/sellers
- same-broker activity
- broker rows ratio
- existing 07 labels such as supply pressure, absorption attempt, distribution-like, accumulation-like

Purpose:

- who bought/sold that day, whether flow was concentrated, whether the same brokers persisted, and whether price reacted strongly or weakly to flow

### Volume / Tape

Sources:

- `experiments/08-hydro-volume-tape-lab/raw/<SYMBOL>/<symbol>_volume_1min.csv`
- `experiments/08-hydro-volume-tape-lab/raw/<SYMBOL>/<symbol>_volume_hourly.csv`
- `experiments/08-hydro-volume-tape-lab/raw/<SYMBOL>/<symbol>_volume_daily.csv`
- `experiments/08-hydro-volume-tape-lab/data/volume_daily.csv`
- `experiments/08-hydro-volume-tape-lab/data/volume_events.csv`

Current reality:

- UPPER has minute/hourly/daily volume captures.
- Peer symbols still need volume capture before all-hydro tape conclusions are strong.

Purpose:

- intraday volume timing, late-session recovery, panic candles, failed rallies, VWAP behavior, volume profile, and volume/price effort-vs-result behavior

### Corporate Actions

Sources:

- `experiments/01-corporate-action/data/events.csv`
- `experiments/01-corporate-action/results/event_returns.csv`

Purpose:

- avoid misreading event-driven volume as clean accumulation/distribution
- tag windows around book close, dividend, AGM, right-share, listing, and announcements

### Lock-In Expiry

Sources:

- `experiments/02-lockin-expiry/data/unlock_events.csv`
- `experiments/02-lockin-expiry/results/event_returns.csv`

Purpose:

- detect hidden future supply pressure
- explain distribution-like behavior near unlock windows

### Macro / Liquidity Regime

Sources:

- `experiments/03-nrb-rate-events/data/interbank_daily.csv`
- `experiments/03-nrb-rate-events/data/policy_events.csv`
- `experiments/03-nrb-rate-events/data/rate_move_events.csv`

Purpose:

- separate symbol-specific psychology from broad liquidity stress or relief

### Hydro Seasonality

Sources:

- `experiments/04-hydro-seasonality/data/monthly_returns.csv`

Purpose:

- provide month/season baseline for hydropower behavior

### Hydro Project / Damage Events

Sources:

- `experiments/06-hydro-flood-damage/data/hydro_symbol_registry.csv`
- `experiments/06-hydro-flood-damage/data/flood_damage_event_table.csv`

Purpose:

- identify project-specific news or damage windows that can distort normal psychology reads

## Missing Or Weak Data

The most important weak points are:

- all-hydro minute/hourly volume coverage
- true historical order book depth
- exact aggressor side for each trade
- exact floorsheet trade timestamps
- broker-client identity
- fully normalized quarterly fundamentals for all hydropower companies

The best workaround for exact intraday broker psychology is a future live
floorsheet diff collector:

- poll floorsheet during market hours
- record newly observed contract numbers
- assign an `observed_at` timestamp
- reconstruct approximate broker-minute flow

That would allow much better late-panic and late-absorption analysis.

## Target Output

The engine should produce three levels of output.

### 1. Master Daily Feature Table

Path:

- `experiments/09-hydro-psychology-engine/data/hydro_psychology_daily.csv`

Grain:

- one row per `symbol,date`

Core columns:

```text
symbol,date,sector,session_flag,
open,high,low,close,ltp,vwap,volume,turnover,trades,
return_1d,range_pct,close_position,
volume_ratio_20d,turnover_ratio_20d,trades_ratio_20d,
volume_spike,volume_drought,high_volume_up,high_volume_down,
failed_rally,absorption_candle,
broker_available,raw_qty,raw_amount,raw_rows,unique_brokers,
top_buyer,top_buyer_pct,top_seller,top_seller_pct,
top3_buyer_pct,top3_seller_pct,top3_gap,same_broker_pct,
broker_rows_ratio_20d,raw_qty_vs_price_volume_pct,
top_net_buyers,top_net_sellers,
supply_pressure,absorption_attempt,two_sided_churn,
distribution_like,accumulation_like,
corp_action_window,lockin_window,nrb_event_window,
seasonality_month_score,flood_damage_window,
quality_flags,
fwd_1d_return_pct,fwd_3d_return_pct,fwd_5d_return_pct,
fwd_10d_return_pct,fwd_20d_return_pct
```

### 2. Psychology State Table

Path:

- `experiments/09-hydro-psychology-engine/data/psychology_states.csv`

Grain:

- one row per `symbol,date,state`

Example columns:

```text
symbol,date,state,score,confidence,evidence_count,
positive_evidence,negative_evidence,invalidation_level,
expected_horizon,quality_flags
```

States:

- `accumulation`
- `distribution`
- `panic_selling`
- `panic_absorption`
- `failed_rally`
- `two_sided_churn`
- `markup_continuation`
- `markdown_continuation`
- `no_clear_signal`

### 3. Outcome Evaluation

Path:

- `experiments/09-hydro-psychology-engine/results/state_outcomes.csv`
- `experiments/09-hydro-psychology-engine/results/psychology_findings.md`

Questions:

- Which states had positive average forward return?
- Which states had the best hit rate?
- Which states had the worst drawdown?
- Which states only work in bullish market regime?
- Which states fail near lock-in, right-share, or book-close events?
- Which broker patterns had persistence across 3, 5, and 10 sessions?

## Psychology Scoring Design

The first version should be a transparent rule-scoring model, not a black-box model.

Each state gets a score from positive and negative evidence. The score becomes
a confidence band only after we test historical outcomes.

### Accumulation

Positive evidence:

- price flat or rising while buyer concentration improves
- top net buyers persist across multiple days
- close holds upper half of range
- pullbacks happen on lower volume
- OBV or accumulation/distribution line improves
- price reclaims VWAP or anchored VWAP

Negative evidence:

- seller concentration dominates
- rally fails near resistance
- volume spike produces no follow-through
- event window adds artificial demand or supply

### Distribution

Positive evidence:

- high volume rally closes weak
- seller concentration dominates
- top net sellers persist across multiple days
- price below VWAP after volume spike
- ADL/OBV weakens while price is flat or up
- supply event is nearby

Negative evidence:

- sellers fail to break support
- large down volume closes upper range
- next session reclaims the breakdown level

### Panic Selling

Positive evidence:

- large down day
- high volume or turnover spike
- close near low of range
- broad sector weakness
- sellers concentrated
- no late-session recovery

Negative evidence:

- price closes in upper range
- high-volume low is defended next session
- buyers are concentrated and persistent

### Panic Absorption

Positive evidence:

- high volume down move
- wide range but close recovers into upper half
- late-session volume appears near lows
- top buyers concentrated
- next session does not break panic low
- price stabilizes above VWAP/anchored VWAP

Negative evidence:

- next session breaks panic low
- sellers remain persistent
- bounce fails immediately on high volume

### Failed Rally

Positive evidence:

- intraday or daily rally closes below upper range
- high volume up day lacks follow-through
- seller concentration appears on the rally
- price rejects resistance or VWAP

Negative evidence:

- next session closes above the failed-rally high
- buyers remain persistent and sellers fade

### Two-Sided Churn

Positive evidence:

- high activity but small price change
- both buyer and seller concentration are high
- same-broker or cross-broker flow is elevated
- no clear follow-through

Negative evidence:

- breakout or breakdown follows quickly with confirmed volume

## Evidence Rules

Every generated verdict must separate:

- exact evidence: directly in source files
- derived evidence: calculated from source files
- inferred psychology: model interpretation

Example:

```text
Exact: seller broker 58 sold 120,000 shares on 2026-04-24.
Derived: seller top3 concentration was 34%.
Inferred: this looks like supply pressure, not confirmed distribution.
```

## Quality Flags

Rows should carry quality flags so we do not overtrust weak data.

Possible flags:

- `missing_broker_flow`
- `missing_intraday_volume`
- `event_window`
- `lockin_window`
- `low_liquidity`
- `holiday_uncertain`
- `partial_peer_coverage`
- `no_forward_outcome_yet`
- `inferred_aggressor_side`

## Build Phases

### Phase 0 - Document And Boundaries

Goal:

- create this source-of-truth plan
- keep experiment 09 read-only toward upstream experiments
- define output contracts before writing builders

Done when:

- this README exists
- the expected input lanes and output files are named

### Phase 1 - Master Daily Table

Goal:

- create `build_master_dataset.py`
- read experiment 07 broker-flow data
- left-join experiment 08 volume labels when available
- add event windows from experiments 01, 02, 03, 04, and 06
- write `data/hydro_psychology_daily.csv`

Done when:

- UPPER/API/AKPL/AHPC/BHCL/RADHI/RHPL produce rows
- each row has quality flags
- no upstream files are modified

### Phase 2 - Transparent Psychology Scoring

Goal:

- create `score_psychology_states.py`
- generate one or more psychology state candidates per symbol-date
- include evidence strings and invalidation levels

Done when:

- `data/psychology_states.csv` exists
- every state has a score, confidence placeholder, evidence, and quality flags

### Phase 3 - Outcome Testing

Goal:

- test each state against forward returns
- measure hit rate, average return, median return, drawdown, and sample size

Done when:

- `results/state_outcomes.csv` exists
- `results/psychology_findings.md` explains which states worked, failed, or had too little evidence

### Phase 3.1 - Walk-Forward Pattern Backtest

Goal:

- convert scored states into repeating pattern instances
- make historical predictions using only pattern history available before each signal date
- separate same-day close signals from next-session confirmation signals
- test 1, 3, 5, 10, and 20 session outcomes versus same-date hydro peers
- generate a latest completed-session forecast from the same pattern library

Done when:

- `data/pattern_instances.csv` exists
- `results/walk_forward_predictions.csv` exists
- `results/pattern_edge_report.csv` exists
- `results/walk_forward_report.md` explains what worked without lookahead
- `results/latest_forecast.csv` and `results/latest_forecast.md` exist

Reliability rule:

- `same_day_close` signals are dated on the scored day
- `next_session_confirmation` signals are dated on the confirmation day
- confirmation-mode outcomes start after the confirmation day, not before it

### Phase 3.2 - Validation Labs

Goal:

- break the psychology engine into separate validation questions
- prove which data is reliable enough
- test whether patterns repeat across periods and symbols
- isolate the failed-bearish pattern family
- simulate one simple entry/exit rule before calling any pattern tradable
- test stricter post-label confirmation rules before entry
- convert only robust patterns into long/avoid decisions

Done when:

- `results/data_quality_report.md` exists
- `results/pattern_robustness_report.md` exists
- `results/failed_bearish_report.md` exists
- `results/entry_exit_report.md` exists
- `results/confirmation_rule_report.md` exists
- `results/robust_pattern_trade_report.md` exists

The validation labs are:

1. Data quality audit: tells which symbols/periods are price-rich, broker-partial, or tape-sparse.
2. Pattern robustness: asks whether a pattern worked across time and symbols, not only in one pocket.
3. Failed bearish lab: isolates bearish reads that failed on the next session.
4. Entry/exit simulator: tests a concrete reclaim entry with a stop back below the reclaimed level.
5. Confirmation rule lab: tests whether waiting for extra proof after the failed bearish read improves results.
6. Robust pattern trade lab: tests only `robust_positive` and `robust_negative` patterns as long/avoid decisions.

### Phase 4 - Intraday Upgrade

Goal:

- parse minute/hourly volume into better features
- add VWAP, anchored VWAP, first/last-30-minute volume, late recovery, panic-low defense, and volume-profile levels

Done when:

- UPPER intraday features are computed
- all-hydro intraday refresh is ready once raw captures exist

### Phase 5 - Live Floorsheet Diff Collector

Goal:

- reconstruct approximate broker-minute flow during market hours

Done when:

- new contracts can be detected by polling
- each observed trade has an `observed_at` timestamp
- broker-minute flow can be joined to minute volume

This is a later phase, because it needs live market-hour collection.

## First Implementation Step

Start with Phase 1.

Minimum useful build:

1. Create `config.json` for the hydro universe.
2. Create `build_master_dataset.py`.
3. Read `experiments/07-hydro-broker-flow/data/hydro_broker_flow_daily.csv`.
4. Join `experiments/08-hydro-volume-tape-lab/data/volume_daily.csv` by `symbol,date`.
5. Add simple event-window flags from corporate action and lock-in tables.
6. Write `data/hydro_psychology_daily.csv`.
7. Write `results/build_summary.md`.

This gets us one clean table before we become clever.

Run with Python when available:

```powershell
python .\experiments\09-hydro-psychology-engine\build_master_dataset.py
```

If Python is unavailable in the current shell, the no-dependency Node fallback
writes the same Phase 1 outputs:

```powershell
node .\experiments\09-hydro-psychology-engine\build_master_dataset.mjs
```

Then run the first transparent scoring pass:

```powershell
node .\experiments\09-hydro-psychology-engine\score_psychology_states.mjs
```

The scoring pass also writes peer-relative outcome columns so a state is not
mistakenly rewarded just because the broader hydro peer group moved in the same
direction.

The v2 scoring pass tightens the psychology read:

- same-day scores reward broker persistence, support defense, and cleaner buyer/seller evidence
- event windows and missing broker flow reduce confidence
- next-session confirmation is stored separately, not secretly mixed into same-day scoring
- `results/state_confirmation_outcomes.csv` shows what happened after confirmed, failed, mixed, or unconfirmed states

This distinction matters because a failed bearish state can become useful bullish
information, while an unconfirmed bullish state should not be treated as clean
accumulation.

Finally build the edge report and latest watchlist:

```powershell
node .\experiments\09-hydro-psychology-engine\build_edge_report.mjs
```

Outputs:

- `results/edge_candidates.csv`
- `results/latest_watchlist.csv`
- `results/edge_candidate_report.md`

Then build the walk-forward pattern backtest and latest forecast:

```powershell
node .\experiments\09-hydro-psychology-engine\build_walk_forward_backtest.mjs
node .\experiments\09-hydro-psychology-engine\build_latest_forecast.mjs
```

Outputs:

- `data/pattern_instances.csv`
- `results/walk_forward_predictions.csv`
- `results/pattern_edge_report.csv`
- `results/walk_forward_summary.csv`
- `results/walk_forward_report.md`
- `results/latest_forecast.csv`
- `results/latest_forecast.md`

This is the first no-lookahead prediction loop:

```text
score psychology -> convert to pattern -> predict from earlier pattern history -> grade later outcome
```

Then run the validation labs:

```powershell
node .\experiments\09-hydro-psychology-engine\build_data_quality_audit.mjs
node .\experiments\09-hydro-psychology-engine\build_pattern_robustness.mjs
node .\experiments\09-hydro-psychology-engine\build_failed_bearish_lab.mjs
node .\experiments\09-hydro-psychology-engine\build_entry_exit_simulator.mjs
node .\experiments\09-hydro-psychology-engine\build_confirmation_rule_lab.mjs
node .\experiments\09-hydro-psychology-engine\build_robust_pattern_trade_lab.mjs
```

Outputs:

- `results/data_quality_by_symbol.csv`
- `results/data_quality_by_period.csv`
- `results/data_quality_report.md`
- `results/pattern_robustness.csv`
- `results/pattern_robustness_report.md`
- `results/failed_bearish_cases.csv`
- `results/failed_bearish_summary.csv`
- `results/failed_bearish_report.md`
- `results/entry_exit_trades.csv`
- `results/entry_exit_summary.csv`
- `results/entry_exit_report.md`
- `results/confirmation_rule_trades.csv`
- `results/confirmation_rule_summary.csv`
- `results/confirmation_rule_report.md`
- `results/robust_pattern_trades.csv`
- `results/robust_pattern_trade_summary.csv`
- `results/latest_robust_pattern_watchlist.csv`
- `results/robust_pattern_trade_report.md`

## One-Command Refresh

Use the guarded refresh wrapper when the market data for a session is available:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\experiments\09-hydro-psychology-engine\refresh_hydro_psychology.ps1 -Date 2026-04-27
```

Before 11:00 Nepal time on the target date, the wrapper skips live price and
broker scraping unless `-AllowPreMarket` is passed. It still rebuilds the derived
experiment outputs from existing local data.

Useful variants:

```powershell
# Rebuild derived outputs only, no live data collection.
powershell -NoProfile -ExecutionPolicy Bypass -File .\experiments\09-hydro-psychology-engine\refresh_hydro_psychology.ps1 -RebuildOnly

# Check which hydro symbols would be scraped without collecting live data.
powershell -NoProfile -ExecutionPolicy Bypass -File .\experiments\09-hydro-psychology-engine\refresh_hydro_psychology.ps1 -Date 2026-04-27 -BrokerDryRun
```

## Success Criteria

The experiment is useful only if it can say:

- what it knows
- what it infers
- what data is missing
- what would invalidate the read
- what historically happened after the same state appeared

The target is not certainty. The target is a reliable research assistant that
reduces bad trades, highlights asymmetric setups, and keeps us honest when the
evidence is weak.
