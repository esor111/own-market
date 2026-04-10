# System Architecture And Safe Feedback Plan

## Why This Document Exists

This project is now big enough that we should stop thinking of it as "just scripts."

We need a clean system that is:

- safe
- extendable
- easy to inspect
- easy to recover if a run stops halfway
- easy to compare across days
- easy to improve without breaking the core

This document defines that shape.


## Main Goal

The system should do this reliably:

1. collect data
2. save it safely
3. make a decision
4. track what happened later
5. compare prediction vs reality
6. let AI critique the result
7. help us improve filters and thresholds

This is the real smart loop.

It is not "fully autonomous self-reinforcement."

It is:

- structured evidence
- structured decisions
- structured outcomes
- structured critique
- careful human-approved improvement


## Core Architecture

The clean architecture should stay split into **five layers**.

### 1. Truth Layer

Purpose:

- provide raw market truth and historical truth

Current sources:

- `nepse_scraper`
- `sharesansar_local`

Rules:

- truth providers stay behind our adapter layer
- outside repos are never merged into the core logic
- each provider is optional
- providers can disagree, and disagreement should be recorded

Good fit for this layer:

- OHLCV
- historical daily data
- market summary
- sector summary
- company metadata
- official notices if available

Not a good fit:

- portal-only browser surfaces


### 2. Browser Edge Layer

Purpose:

- capture data that only the browser portal exposes well

Current examples:

- floorsheet summary
- last 15-minute trades
- broker holdings
- broker holding changes
- trader volume sentiment
- session context around market close

Rules:

- browser-edge logic stays separate from the core batch pipeline
- it is optional and slower
- it is mainly for richer LLM packages and special research


### 3. Core Decision Layer

Purpose:

- turn raw data into disciplined decisions

Current responsibilities:

- multi-timeframe structure
- market/sector alignment
- event checks
- liquidity checks
- risk/reward checks
- QC filtering
- watchlist ranking
- trade plan generation

Rules:

- keep this layer lean
- do not inject random external repo logic here
- only promote inputs that clearly improve decisions


### 4. Memory And Feedback Layer

Purpose:

- remember the past and compare it to the present

This is the most important next architectural layer.

Responsibilities:

- store past setup snapshots
- store realized outcomes
- store calibration summaries
- retrieve similar old cases
- compare current setup to past setup families

This is what moves us from:

- "good current analysis"

to:

- "current analysis with memory"


### 5. LLM Reasoning Layer

Purpose:

- synthesize the clean structured package
- explain the strongest edge
- explain the biggest risk
- critique wins and losses
- propose improvements

Rules:

- the LLM never invents missing facts
- the LLM never silently overwrites the rule system
- the LLM critiques and recommends
- humans decide what to adopt


## Storage Principles

Every run should be safely inspectable even if it stops halfway.

That means:

### A. Never overwrite different contexts

We already fixed this partly with timeframe-safe names.

Keep this principle:

- date
- symbol
- timeframe
- run label
- artifact type

should appear in filenames whenever needed


### B. Separate raw from normalized from derived

Keep three clear zones:

- `raw/`
  direct captures, tables, snapshots, screenshots, provider bundles
- `normalized/`
  cleaned symbol/date records
- `features/`
  scored or model-ready packages


### C. Every major run should produce a traceable summary

For each run type we should always have:

- dated history file
- stable `latest__...` pointer

This is already working for validation artifacts and should remain the standard.


### D. Partial failure should still save useful work

If a run stops halfway:

- raw evidence already captured should remain
- completed symbol outputs should remain
- run summary should show `run_error` clearly
- stale files should never be silently reused as new success

This rule is important and already partly implemented.


## Run Lifecycle

The clean Nepal-market flow should be:

### 1. Pre-market review

Look at:

- previous shortlist
- pending follow-ups
- known event risk

This is a human review step, not a heavy run step.


### 2. Near market close capture

Best capture window:

- around `2:45 PM-3:15 PM`

Why:

- that is when end-of-day structure and closing-session order flow are most meaningful


### 3. After-market decision run

Standard run order:

1. `light_scan.py`
2. `deep_dive_shortlist.py`
3. optional `manual_llm_package.py`


### 4. Outcome follow-up

Later, evaluate what happened after the decision.

This should stay as independent as possible from live browser availability.

The current truth-first follow-up path is the right direction.


### 5. Feedback review

After enough outcomes accumulate:

- compare score vs outcome
- compare LLM view vs outcome
- inspect false positives
- inspect false negatives


## Safe Feedback Loop

The safe loop should be:

1. decision created
2. decision stored
3. outcome stored
4. comparison generated
5. LLM critique generated
6. recommendation generated
7. human approves any change
8. next run uses the improved rule or summary

This avoids dangerous self-editing.


## What The LLM Should Compare

For each finished case, the LLM should eventually compare:

- rule-engine decision
- LLM decision
- actual outcome
- key reasons for mismatch

The LLM output should answer:

- what feature was most useful?
- what feature was misleading?
- was the loss caused by event risk, liquidity, bad timing, weak sector, or weak RR?
- what warning or filter should exist next time?


## Minimal Smart Improvement System

We do **not** need a giant autonomous system.

We need a small smart loop:

### Inputs

- core decision package
- browser-edge summary
- truth history
- actual outcome

### Process

- compare case vs similar past cases
- let the LLM critique the decision
- store suggested changes

### Output

- recommendation list
- threshold-change candidates
- new warning candidates
- summary-field improvement ideas

This is enough to learn well without becoming chaotic.


## Most Important Missing Architecture Piece

The biggest missing piece now is:

## Historical Memory

What it should do:

- build a reusable store of historical daily setup features
- attach later outcomes
- let us retrieve similar old cases for a current stock

Why this matters:

- without memory, the LLM only sees the current moment
- with memory, it sees pattern families

This is the highest-value next layer.


## Recommended New Internal Modules

These are the next clean modules to add.

### 1. `memory_store.py`

Purpose:

- save compact historical setup snapshots

Should store:

- symbol
- date
- timeframe context
- structure state
- trend state
- event state
- liquidity state
- decision/action
- targets/stops
- later outcome label


### 2. `similar_setup_retrieval.py`

Purpose:

- given a new setup, find similar old setups

Output should be small and readable:

- number of similar cases
- win/loss distribution
- common failure reason
- sector-level similarity


### 3. `llm_case_critique.py`

Purpose:

- critique a finished case after outcome resolution

Should answer:

- what was right
- what was wrong
- what should change


### 4. `improvement_log.py`

Purpose:

- store suggested adjustments without directly editing code logic

This becomes the safe bridge between:

- data
- critique
- future engineering changes


## File And Artifact Strategy

To keep the system safe and extendable, use these rules:

### Decision artifacts

- one file per symbol/date/timeframe
- no silent overwrites

### Outcome artifacts

- one file per symbol/date/timeframe
- status should clearly show:
  - pending
  - resolved
  - not_applicable
  - missing

### Critique artifacts

- separate from decisions
- separate from outcomes
- clearly versioned

### Improvement proposals

- do not mix with raw outputs
- keep in a separate folder like:
  - `data/validation/improvement_proposals/`


## What "Reliable" Means Here

Reliable does not mean:

- the market prediction is perfect

Reliable means:

- data is traceable
- runs are recoverable
- outputs are inspectable
- decisions are consistent
- outcomes are recorded
- critique is structured
- improvements are reviewable


## Best Next Implementation Order

This is the safest order from here:

1. build `memory_store.py`
2. build `similar_setup_retrieval.py`
3. add compact broker/floorsheet summary fields for the LLM package
4. build `llm_case_critique.py`
5. build `improvement_log.py`

This order is smart because:

- it adds memory before adding more reasoning
- it keeps the architecture modular
- it improves learning without bloating the core run path


## Human-Friendly Design Rule

Everything should stay readable for future sessions.

That means:

- short stable filenames
- clearly separated layers
- summaries before raw detail
- latest pointers for convenience
- dated history for traceability

The system should feel understandable, not magical.


## Final Principle

Do not build more than the feedback loop can teach us.

The architecture should grow only when it helps one of these:

- safer data
- better decisions
- better outcome tracking
- better comparison
- better learning

That is how we keep the project smart, safe, and extendable.
