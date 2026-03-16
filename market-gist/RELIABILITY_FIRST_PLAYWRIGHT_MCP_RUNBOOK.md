# Reliability-First Playwright MCP Runbook

**Date:** March 16, 2026  
**Purpose:** Define the exact sequential run order for reliable Playwright MCP analysis  
**Primary Goal:** Collect repeatable evidence without missing steps, skipping context, or mixing interpretation with raw capture

---

## 1. Non-Negotiable Rule

This system is for reliability first.

That means:

- do the same stages in the same order every run
- capture evidence before interpretation
- never skip market context
- never jump to prediction without invalidation
- never trust memory over stored data
- never trust a screenshot alone if a field can be extracted directly

If the run does not create:

1. evidence
2. structured data
3. final decision

then the run is incomplete.

---

## 2. Reliability Principles

### Principle 1: Same sequence every time
- no random clicking
- no ad hoc order
- no starting with a stock before market context

### Principle 2: Clean chart before annotated chart
- always save the clean chart first
- only then add lines, zones, or tools

### Principle 3: Higher timeframe before lower timeframe
- monthly or weekly for context
- daily for setup
- lower timeframe only for entry refinement

### Principle 4: Direct extraction before visual inference
- use page text or DOM extraction first
- use screenshots as supporting proof
- use manual inference only when unavoidable

### Principle 5: Prediction must be falsifiable
- every setup must include invalidation
- every prediction must include a stop or failure level

---

## 3. Standard Run Stages

Every full run should follow this fixed order:

1. Open session
2. Validate page and tools
3. Capture market context
4. Capture sector context
5. Pull or confirm candidate list
6. Open one stock
7. Prepare clean chart
8. Capture higher-timeframe evidence
9. Capture setup-timeframe evidence
10. Capture lower-timeframe evidence if needed
11. Add annotations
12. Enrich with events, relative strength, and broker context
13. Normalize data
14. Score setup
15. Write decision
16. Save evidence pack

No stage should be skipped without explicit reason stored in the run record.

---

## 4. Exact MCP Tool Order

This is the recommended operational sequence when using Playwright MCP.

### Session Start
1. `browser_navigate`
2. `browser_wait_for`
3. `browser_snapshot`
4. `browser_take_screenshot`

### Page Interaction
1. `browser_click`
2. `browser_type` or `browser_fill_form`
3. `browser_wait_for`
4. `browser_snapshot`

### Data Extraction
1. `browser_evaluate`
2. `browser_snapshot`
3. `browser_take_screenshot`

### Verification
1. `browser_snapshot`
2. `browser_take_screenshot`
3. optional `browser_network_requests` if page behavior is unclear

Important:
- after every meaningful page change, take a new structural snapshot
- after every analytical stage, save a screenshot

---

## 5. Stage-by-Stage Runbook

### Stage 1: Open Session

Goal:
- create a traceable session

Required output:
- session id
- run timestamp
- source page
- first full-page screenshot

Checklist:
- open NEPSE Alpha page
- confirm chart loads
- store base metadata
- confirm the relevant tools exist

Stop if:
- chart does not load
- controls are missing
- symbol search is not usable

---

### Stage 2: Validate Tool Availability

Goal:
- ensure the chart environment supports the intended workflow

Confirm:
- symbol search
- timeframe controls
- indicators
- drawing toolbar
- volume panel
- scale or adjustment controls if needed

Save:
- page snapshot
- tool availability flags

Why:
- do not continue with partial environment assumptions

---

### Stage 3: Capture Market Context

Goal:
- capture the condition of the full market before any stock call

Minimum required data:
- NEPSE index price
- daily change
- market trend label
- nearest support and resistance
- market screenshot

Checklist:
- open NEPSE chart
- save clean chart
- identify structure
- store support and resistance
- store trend label

Do not continue to stock prediction without this stage.

---

### Stage 4: Capture Sector Context

Goal:
- avoid treating stock strength in isolation

Minimum required data:
- sector name
- sector trend
- sector relative strength note
- sector screenshot

Checklist:
- open relevant sector chart or sector view
- store clean evidence
- record sector trend

Skip only if sector data is unavailable, and record the skip reason.

---

### Stage 5: Candidate Discovery

Goal:
- create a filtered list of stocks worth deeper analysis

Minimum required data:
- candidate symbol
- why selected
- screener values or signals used

Checklist:
- open screener or signals page
- apply fixed high-value filters
- extract result rows
- rank candidates

Never analyze random stocks when a discovery stage exists.

---

### Stage 6: Open and Confirm Stock Symbol

Goal:
- ensure the correct symbol is selected before collecting evidence

Checklist:
- search symbol
- confirm symbol text
- save initial stock chart screenshot

Store:
- symbol
- company name if visible
- base chart screenshot

---

### Stage 7: Prepare the Clean Chart

Goal:
- put the chart into a standardized evidence-ready state

Required chart setup:
- candlesticks
- volume on
- `20 EMA`
- `50 MA`
- optional `200 MA`
- `RSI` or `MACD`

Checklist:
- confirm timeframe controls
- add indicators
- confirm chart style
- confirm scale and adjustment mode
- save clean chart before annotation

This stage is mandatory.

---

### Stage 8: Capture Higher-Timeframe Evidence

Goal:
- determine trend and major structure

Primary timeframes:
- monthly
- weekly

Capture:
- close
- visible trend
- major swings
- major zones
- higher-timeframe screenshot

Use:
- monthly or weekly for regime and major structure only

---

### Stage 9: Capture Setup-Timeframe Evidence

Goal:
- capture the actual trade setup

Primary timeframe:
- daily by default
- weekly if swing setup is longer-term

Minimum required fields:
- latest close
- volume
- support zone
- resistance zone
- breakout level
- invalidation level
- `20 EMA`
- `50 MA`
- `RSI` or `MACD`

Save:
- clean screenshot
- extracted values
- chart-state snapshot

---

### Stage 10: Capture Lower-Timeframe Evidence

Goal:
- refine entry, not define the entire thesis

Use only after higher and setup timeframes are clear.

Suitable for:
- entry timing
- retest confirmation
- intraday invalidation refinement

Do not let lower timeframe override higher-timeframe context.

---

### Stage 11: Annotate the Chart

Goal:
- create visual proof of the analytical thesis

Allowed annotations:
- support zones
- resistance zones
- trendlines
- breakout box
- invalidation line
- target zones

Checklist:
- save clean chart first
- add only necessary lines
- save annotated chart after drawing

Rule:
- annotated chart is proof, not primary data

---

### Stage 12: Enrich Context

Goal:
- make the setup prediction-worthy, not just technically attractive

Capture when relevant:
- rights share
- bonus share
- AGM
- book closure
- sector news
- unusual broker flow
- floorsheet clues
- relative strength vs NEPSE
- relative strength vs sector

Do not add context randomly.
Only add context that can change setup quality, timing, or risk.

---

### Stage 13: Normalize Data

Goal:
- convert evidence into machine-usable records

Create normalized records for:
- session
- market
- sector
- candidate
- stock chart
- indicators
- events
- relative strength
- broker flow
- final setup

No freeform summary should replace this stage.

---

### Stage 14: Score Setup

Goal:
- turn evidence into an objective decision

Minimum scoring buckets:
- market alignment
- sector alignment
- structure quality
- location quality
- trend filter quality
- volume confirmation
- momentum confirmation
- event quality
- risk-reward quality

Every score must be linked to stored evidence.

---

### Stage 15: Write Decision

Goal:
- produce a clear action

Every decision must include:
- setup type
- score
- confidence
- action
- entry zone
- stop loss
- invalidation
- targets
- why

If any of these are missing, the decision is incomplete.

---

### Stage 16: Save Evidence Pack

Goal:
- make future review possible without rerunning the whole analysis

Every completed stock run should store:
- raw screenshots
- raw snapshots
- normalized JSON
- feature scores
- final summary

This is what prevents repeated re-analysis.

---

## 6. Required Fields by Reliability Level

### Mandatory
- session id
- symbol
- timestamp
- market trend
- sector trend or sector skip reason
- timeframe
- latest close
- support
- resistance
- invalidation
- at least one momentum reading
- volume context
- final score
- final action

### Strongly Recommended
- `20 EMA`
- `50 MA`
- breakout level
- target levels
- relative strength
- event catalyst fields

### Optional
- broker flow
- floorsheet analysis
- `200 MA`
- advanced custom indicators

Optional fields must never block the run.

---

## 7. Failure and Retry Rules

### Retry if
- chart fails to load
- symbol search fails
- indicator does not render
- extracted value conflicts with visible state

### Abort if
- symbol cannot be confirmed
- market context cannot be captured
- screenshots cannot be saved
- the chart is visually inconsistent and cannot be validated

### Mark partial if
- market and stock data are captured, but enrichment sources are unavailable

Never silently continue after a failed extraction.

---

## 8. What Makes a Run Reliable

A run is reliable when:

- the same symbol processed twice produces near-identical structured records
- screenshots and JSON point to the same state
- every decision has evidence
- every prediction has invalidation
- skipped stages are explicitly recorded
- later outcome can be attached to the same setup

---

## 9. Reliability Checklist Before Finalizing a Prediction

Before final output, confirm:

1. Market context captured
2. Sector context captured or properly skipped
3. Clean chart saved
4. Annotated chart saved
5. Required indicator values stored
6. Support and resistance stored
7. Invalidation stored
8. Volume context stored
9. Setup type assigned
10. Score assigned
11. Action assigned
12. Evidence refs attached

Only then is the prediction ready.

---

## 10. One-Sentence Rule

Reliability comes from fixed sequence, stored evidence, normalized data, and explicit invalidation, not from more tools or more opinions.
