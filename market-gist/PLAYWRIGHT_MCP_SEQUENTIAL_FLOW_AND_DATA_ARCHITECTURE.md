# Playwright MCP Sequential Flow and Data Architecture

**Date:** March 16, 2026  
**Project:** NEPSE technical-analysis automation using Playwright MCP  
**Purpose:** Define the exact automation flow, rich-data structure, and missing layers required for prediction-quality analysis

---

## 1. What This Document Solves

The main idea of this project is not just "analyze charts."

The main idea is:

- use the Playwright MCP server as the primary automation engine
- interact with NEPSE Alpha sequentially and consistently
- collect rich evidence from charts and related pages
- normalize that evidence into structured data
- convert that data into setup scoring and prediction
- avoid missing steps, re-checking, and manual rework

So this document answers three questions:

1. What is the exact automation flow?
2. How should the data be structured?
3. What are we still missing if the goal is prediction, not just observation?

---

## 2. First Principle

Playwright MCP is the **execution layer**.

The decision system is the **analysis layer**.

That means:

- Playwright MCP should collect evidence in the same order every time
- our scoring and prediction logic should run on structured data, not memory
- screenshots alone are not enough
- notes alone are not enough
- raw data without context is also not enough

We need all three:

- visual evidence
- structured extracted data
- interpreted features

---

## 3. The Correct End-to-End Flow

The workflow should be divided into nine stages:

1. Session setup
2. Market context capture
3. Candidate discovery
4. Stock chart preparation
5. Chart evidence extraction
6. Context enrichment
7. Data normalization
8. Feature scoring and prediction
9. Final reporting and archive

This order matters because each later step depends on the earlier one.

---

## 4. Sequential Playwright MCP Flow

Below is the recommended sequential order for the MCP server.

### Stage 1: Session Setup

Goal:
- start a clean repeatable browser session
- make sure the chart page is ready for extraction

Playwright MCP actions:
- `browser_navigate`
- `browser_snapshot`
- `browser_wait_for`
- `browser_click`

What to do:
1. Open NEPSE Alpha chart page
2. Wait until TradingView chart area is loaded
3. Capture a structural snapshot of the page
4. Confirm visible controls:
   - symbol search
   - timeframe buttons
   - indicators button
   - drawings toolbar
   - volume area
   - chart modes if relevant
5. Store page-state metadata

Data to save:
- source URL
- timestamp
- page title
- tool availability flags
- chart-loaded boolean

---

### Stage 2: Market Context Capture

Goal:
- capture the overall environment before analyzing any single stock

Pages to inspect:
- NEPSE index chart
- sector chart
- technical screener
- technical signals page if useful

Playwright MCP actions:
- `browser_click`
- `browser_type`
- `browser_snapshot`
- `browser_take_screenshot`
- `browser_evaluate`

What to collect:
- NEPSE index price and change
- major market structure
- key support and resistance
- trend condition
- sector condition
- top market-level momentum clues

Data to save:
- market trend label
- market structure points
- sector rankings if available
- market screenshots
- raw page snapshots

Why this matters:
- stock setups without market context create false signals

---

### Stage 3: Candidate Discovery

Goal:
- avoid random stock selection
- create a filtered candidate list before deep chart work

Sources:
- technical screener
- technical signals
- watchlist
- known symbols from user input

Playwright MCP actions:
- `browser_navigate`
- `browser_click`
- `browser_fill_form`
- `browser_snapshot`
- `browser_evaluate`

What to do:
1. Open screener
2. Apply high-value filters
3. Extract the candidate table
4. Rank candidates
5. Choose which stocks go to deep analysis

Example filters:
- price above `200 MA` or reclaiming it
- `MACD` bullish or turning up
- `RSI` healthy but not exhausted
- volume expansion
- near breakout or support zone

Data to save:
- candidate symbol
- screener metrics
- filter values
- candidate rank
- reason for selection

Output of this stage:
- a structured candidate queue

---

### Stage 4: Stock Chart Preparation

Goal:
- put every stock chart into the same clean analytical state

Playwright MCP actions:
- `browser_click`
- `browser_type`
- `browser_wait_for`
- `browser_snapshot`
- `browser_take_screenshot`

What to do in exact order:
1. Search and select stock symbol
2. Confirm selected symbol
3. Open higher timeframe first
   - monthly
   - weekly
   - daily
4. Turn on required indicators
   - volume
   - `20 EMA`
   - `50 MA`
   - optional `200 MA`
   - `RSI` or `MACD`
5. Confirm chart mode and price adjustment setting
6. Confirm autoscale or scale mode
7. Capture clean screenshots for each timeframe before drawing

Important rule:
- always capture the clean chart before adding lines

Data to save:
- selected symbol
- timeframe
- active indicators
- adjustment mode
- clean screenshots

---

### Stage 5: Chart Evidence Extraction

Goal:
- collect the actual rich chart evidence needed for prediction

This is the heart of the system.

Playwright MCP actions:
- `browser_snapshot`
- `browser_evaluate`
- `browser_click`
- `browser_take_screenshot`
- `browser_hover`

What to extract from each timeframe:

#### A. Raw chart state
- OHLC of visible latest candle if accessible
- latest close
- percent move
- visible volume
- timeframe

#### B. Structure data
- latest swing highs
- latest swing lows
- breakout zone
- breakdown zone
- range boundaries
- trend label

#### C. Trend filter data
- `20 EMA` value
- `50 MA` value
- optional `200 MA` value
- price above/below each average
- slope direction if inferable

#### D. Momentum data
- `RSI` value
- `MACD` line
- signal line
- histogram
- divergence notes if visible or derived

#### E. Participation data
- current volume vs recent average
- breakout volume behavior
- pullback volume behavior

#### F. Zone and line evidence
- support zones
- resistance zones
- manually drawn trendlines
- breakout box
- invalidation line

#### G. Visual proof
- clean screenshot
- annotated screenshot
- close-up screenshot if needed

Important rule:
- use `browser_evaluate` or page text extraction whenever possible
- only rely on screenshot interpretation when direct extraction is not available

---

### Stage 6: Context Enrichment

Goal:
- make the chart data rich enough to support actual prediction

Chart data alone is not enough.

Additional sources to gather:
- company announcements
- rights share / bonus share / AGM / book closure
- sector news
- broker or floorsheet behavior
- relative strength vs NEPSE
- relative strength vs sector
- recent unusual price-volume events

This stage may use Playwright MCP on:
- announcement pages
- technical signals pages
- floorsheet chart pages
- broker-related views if exposed in the UI

Data to save:
- event date
- event type
- event sentiment
- event relevance window
- broker flow clues
- relative strength snapshot

---

### Stage 7: Data Normalization

Goal:
- convert messy evidence into predictable structured records

We should not jump directly from screenshots to a final thesis.

We need layered data.

#### Layer 1: Raw capture
- raw page snapshot text
- screenshots
- extracted tables
- DOM text

#### Layer 2: Normalized records
- market record
- sector record
- stock chart record
- technical indicator record
- event record
- broker-flow record

#### Layer 3: Derived features
- trend score
- location score
- volume score
- momentum score
- market alignment score
- risk-reward score
- setup type

#### Layer 4: Final decision
- action
- confidence
- scenario probabilities
- entry
- stop
- targets

---

### Stage 8: Feature Scoring and Prediction

Goal:
- turn rich evidence into an action, not just a description

The scoring model should operate on normalized fields, not freeform notes.

Core scoring buckets:
- market context
- sector context
- structure quality
- trend filter quality
- volume confirmation
- momentum confirmation
- setup quality
- risk-reward quality
- event catalyst quality
- relative strength quality

Example output:
- setup type: `breakout`, `pullback`, `reversal`, `avoid`
- score: `0-100`
- confidence: `low`, `medium`, `high`
- action: `buy now`, `wait for breakout`, `watch`, `avoid`

Important rule:
- prediction should always include invalidation

Without invalidation, prediction is not useful.

---

### Stage 9: Final Reporting and Archive

Goal:
- make every run usable later

Every run should produce:
- a summary report
- a structured JSON output
- screenshots
- raw evidence references
- a decision record

This prevents re-analysis from zero.

---

## 5. Rich Data: What It Actually Means

"Rich data" does **not** mean collecting everything possible.

"Rich data" means collecting the smallest set of data that captures:

- price behavior
- trend state
- momentum state
- volume participation
- market and sector context
- catalyst context
- risk structure
- evidence quality

For this project, rich data should include these ten categories:

1. Market state
2. Sector state
3. Stock structure
4. Indicator values
5. Volume behavior
6. Relative strength
7. Event and catalyst data
8. Floorsheet or broker behavior
9. Risk-reward and invalidation
10. Visual evidence references

If any of these are missing, prediction quality drops.

---

## 6. Recommended Data Structure

We need a layered folder structure so evidence is not mixed with conclusions.

Recommended structure:

```text
market-gist/
  data/
    raw/
      sessions/
      screenshots/
      page_snapshots/
      extracted_tables/
    normalized/
      market/
      sectors/
      stocks/
      events/
      broker_flow/
    features/
      setup_scores/
      prediction_inputs/
    outputs/
      summaries/
      trade_setups/
      reports/
  docs/
    workflows/
    schemas/
    playbooks/
```

---

## 7. Recommended Record Types

These are the main data objects we should maintain.

### A. Session Record

```json
{
  "session_id": "2026-03-16T17-45-00-smhl",
  "run_started_at": "2026-03-16T17:45:00+05:45",
  "source": "nepsealpha",
  "symbol": "SMHL",
  "status": "completed"
}
```

### B. Market Record

```json
{
  "session_id": "2026-03-16T17-45-00-smhl",
  "index_symbol": "NEPSE",
  "timeframe": "1D",
  "close": 2824.90,
  "change_pct": 0.16,
  "trend_label": "neutral_to_bullish",
  "support_levels": [2800, 2750],
  "resistance_levels": [2900, 3000],
  "evidence_refs": ["raw/screenshots/nepse-daily-clean.png"]
}
```

### C. Stock Chart Record

```json
{
  "session_id": "2026-03-16T17-45-00-smhl",
  "symbol": "SMHL",
  "timeframe": "1W",
  "close": 525.00,
  "volume": 316929,
  "trend_label": "base_forming",
  "swing_highs": [641.40, 742.90],
  "swing_lows": [477.50, 504.30],
  "support_zones": [[500, 515]],
  "resistance_zones": [[531, 545], [641, 650]],
  "breakout_level": 531.10,
  "invalidation_level": 477.50,
  "evidence_refs": [
    "raw/screenshots/smhl-weekly-clean.png",
    "raw/screenshots/smhl-weekly-annotated.png"
  ]
}
```

### D. Indicator Record

```json
{
  "session_id": "2026-03-16T17-45-00-smhl",
  "symbol": "SMHL",
  "timeframe": "1W",
  "ema_20": 495.12,
  "ma_50": null,
  "ma_200": null,
  "rsi": 38.44,
  "macd_line": 3.25,
  "signal_line": -91.20,
  "histogram": -94.46,
  "price_above_ema_20": true,
  "momentum_label": "bullish_reversal_forming"
}
```

### E. Event Record

```json
{
  "symbol": "SMHL",
  "event_date": "2026-01-04",
  "event_type": "bonus_and_rights_announcement",
  "sentiment": "positive",
  "impact_window_days": 90,
  "details": {
    "bonus_share_pct": 20,
    "rights_share_pct": 100
  }
}
```

### F. Final Setup Record

```json
{
  "session_id": "2026-03-16T17-45-00-smhl",
  "symbol": "SMHL",
  "setup_type": "breakout_watch",
  "score": 78,
  "confidence": 0.82,
  "action": "wait_for_breakout_above_535",
  "entry_zone": [535, 550],
  "stop_loss": 500,
  "targets": [641, 742, 850],
  "risk_reward_ratio": 4.7,
  "invalidation_reason": "weekly_support_break_below_500",
  "why": [
    "oversold RSI",
    "positive corporate action",
    "weekly base forming",
    "market not broken"
  ]
}
```

---

## 8. The Minimum Rich-Data Pipeline

If we want to keep this practical, the minimum useful pipeline is:

1. Capture NEPSE market context
2. Capture sector context
3. Pull candidates from screener
4. Prepare chart with fixed indicators
5. Save clean screenshots for monthly, weekly, daily
6. Extract latest price, volume, `20 EMA`, `50 MA`, `RSI`, `MACD`
7. Mark support, resistance, breakout, invalidation
8. Gather event and catalyst data
9. Add relative strength and broker/floorsheet context when important
10. Normalize everything into JSON
11. Score the setup
12. Output final action

This is enough to start.

---

## 9. What You Are Missing Right Now

This is the important part.

The current project has strong notes and strong screenshots, but for real prediction these missing pieces matter:

### 1. A fixed sequential MCP runbook

Right now the project idea is clear, but the automation order is not yet fully frozen.

Without that, every run risks inconsistency.

### 2. A normalized data layer

Right now much of the knowledge is in markdown reports.

That is useful for humans, but weak for automation, backtesting, and reuse.

### 3. Historical storage

Prediction improves when we compare today's setup to past setups.

That means we need historical records of:
- charts
- indicator states
- events
- scores
- later outcomes

### 4. Outcome labeling

This is one of the biggest missing pieces.

If we want prediction quality, every setup later needs a result label such as:
- worked
- failed
- partial success
- hit stop first
- hit target first

Without outcome labels, we can produce analysis but not true learning.

### 5. Relative strength layer

A stock chart by itself is incomplete.

We also need:
- stock vs NEPSE
- stock vs sector
- sector vs market

This is one of the highest-value missing features.

### 6. Event timing windows

Not just event text.

We need to know:
- what event happened
- when it happened
- how long its effect should matter
- whether price already absorbed it

### 7. Evidence quality flags

Every extracted field should eventually have a confidence level:
- direct page extraction
- inferred from screenshot
- manually estimated

This prevents false confidence.

### 8. Broker and floorsheet logic

You already know this may matter in NEPSE.

But it needs a rule:
- when do we check it?
- what counts as accumulation?
- what counts as suspicious distribution?

Without rules, this becomes noise.

### 9. Setup library

Prediction gets much stronger if we maintain a library of:
- successful breakouts
- failed breakouts
- healthy pullbacks
- fake reversals

This becomes the pattern memory of the system.

### 10. Backtesting and calibration

This is the final missing layer.

The system should eventually answer:
- when we scored a setup `78`, what historically happened?
- what score range actually worked best?
- which features matter most in NEPSE?

Without calibration, scores can look precise but still be weak.

---

## 10. Best Structure for Decision Intelligence

To make the system strong, think in five layers:

### Layer 1: Evidence
- screenshots
- page snapshots
- extracted values

### Layer 2: State
- market state
- sector state
- stock state
- event state

### Layer 3: Features
- trend
- location
- momentum
- volume
- relative strength
- catalyst

### Layer 4: Decision
- setup type
- score
- action
- invalidation

### Layer 5: Outcome
- future result after `1 day`, `1 week`, `1 month`, `3 months`

This is the full intelligence loop.

---

## 11. Recommended Operating Rule

Every Playwright MCP run should produce three outputs:

1. Human-readable summary
2. Machine-readable structured data
3. Evidence pack

If one of these is missing, the run is incomplete.

---

## 12. Suggested Next Build Order

The best next sequence for building the system is:

1. Freeze the sequential MCP runbook
2. Freeze the normalized JSON schema
3. Create standard folder structure for raw, normalized, features, outputs
4. Build the market-context capture stage
5. Build the candidate discovery stage
6. Build the per-stock chart preparation stage
7. Build the extraction and normalization stage
8. Build the scorecard logic
9. Build the outcome tracking layer
10. Backtest and calibrate scores

---

## 13. One-Sentence System Definition

We are building a Playwright-MCP-driven NEPSE intelligence pipeline that sequentially captures chart, market, sector, event, and participation evidence, converts it into structured features, and outputs a scored actionable setup with traceable proof.
