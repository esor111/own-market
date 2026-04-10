# Nepal Market Operating Flow And Feedback Loop

## Purpose

This document defines the smart, simple operating flow for this project.

The goal is **not** to predict the market perfectly.

The goal is to build a system that:

- gathers clean low-entropy data
- makes a structured decision
- tracks what happened later
- learns from mistakes and wins
- improves the next decision without turning into a huge fragile codebase


## Current System Summary

The project already does these things:

- captures chart context on `1M`, `1W`, and `1D`
- checks browser chart data against an external truth source
- collects official event context
- checks liquidity and quality
- builds trade plans with entry, stop, and targets
- filters weak setups with QC
- collects browser-only edge data for LLM packages:
  - floorsheet
  - last 15-minute trades
  - broker holdings
  - broker holding changes
- builds an LLM-ready package
- stores everything per symbol and date

This means the infrastructure phase is already strong.


## Main Idea

The best version of this project is:

1. collect good data
2. make a prediction
3. wait for reality
4. compare prediction vs reality
5. learn what worked and failed
6. improve the next prediction

This is a **feedback loop**.

It is not fancy autonomous reinforcement learning.

It is a smart evidence -> decision -> outcome -> critique -> adjustment cycle.


## Nepal Market Context

This system should be designed around Nepal market reality, not U.S.-style always-open assumptions.

Working operating assumption for now:

- regular trading days: `Sunday-Thursday`
- regular trading time: about `11:00 AM-3:00 PM` Nepal time
- Friday and Saturday: market closed
- holidays override the normal schedule

This should be treated as a session-based market.

That means:

- we should not design the core system like a live scalping engine
- we should care about market close and next session timing
- Thursday close has extra importance because the next session is later
- event and weekend gap risk matter


## Best Operating Flow

### 1. Before Market Opens

Purpose:

- review the previous decision set
- know which symbols are already active
- know what still needs follow-up

Tasks:

- review yesterday's saved shortlist
- review pending outcomes
- review known event risk for today

This is a preparation step, not the main decision step.


### 2. During Market Hours

Purpose:

- optional monitoring only

Recommended approach:

- keep this light
- do not make the core system depend on constant intraday scraping
- only use intraday browser tools when testing special browser-only signals

Why:

- the strongest version of the system right now is still end-of-session, not constant live trading


### 3. Near Market Close

Important window:

- roughly `2:45 PM-3:15 PM`

Purpose:

- capture the most useful end-of-day context

This is the best time to capture:

- final chart state
- latest price structure
- last 15-minute trades
- floorsheet summary
- broker concentration / holdings signals

Why:

- these are much more useful near session close than random mid-session values


### 4. After Market Close

This is the main pipeline run.

Run order:

1. fast scan
2. shortlist deep-dive
3. optional manual LLM package for strongest names

Suggested command flow:

```powershell
python light_scan.py 1W '@expanded_reliability'
python deep_dive_shortlist.py 1W '@expanded_reliability'
```

If a symbol deserves a rich manual LLM package:

```powershell
python manual_llm_package.py JBBL 1W
```

Purpose:

- generate a clean shortlist
- do the slower browser work only on promising names
- save all records for later follow-up


### 5. Later Outcome Follow-Up

Purpose:

- turn predictions into learning data

This is the key step that makes the system smarter over time.

We evaluate:

- what the setup looked like at decision time
- what actually happened after that
- whether the prediction was useful or misleading

This is the real bridge from "analysis tool" to "learning system."


## What AI Should Do

The LLM should **not** replace the whole system.

The LLM should sit on top of the system.

Best role for the LLM:

- compare many signals at once
- explain why a setup is attractive or risky
- identify conflict between timeframes
- summarize the strongest edge and biggest risk
- compare the current setup to similar past setups
- critique mistakes after outcomes are known

The LLM should receive:

- clean structured data
- not giant raw noise dumps


## What AI Should Not Do

The LLM should not:

- invent missing market data
- silently trust weak data
- rewrite core rules automatically without review
- act like its confidence is proven if calibration is still weak

The right model is:

- LLM suggests
- human reviews
- system updates carefully


## Best Feedback Loop

This is the smartest minimal loop:

1. collect data
2. make decision
3. store decision package
4. wait for outcome
5. evaluate outcome
6. ask LLM to critique:
   - why it worked
   - why it failed
   - what signals were misleading
   - what extra warning should have existed
7. human approves useful changes
8. update thresholds, summaries, or filters

This is much safer and smarter than letting the system freely rewrite itself.


## What Needs To Be Built Next

The most important next step is:

- **historical memory**

That means:

- store more past setups
- store their outcomes
- retrieve similar old cases when a new setup appears

Why this matters:

- right now the system sees the current setup well
- next it should remember the past
- that gives the LLM real context, not just isolated current data

The new `sharesansar_local` adapter is useful here.

Its best use is:

- historical backfill
- offline research
- setup memory
- calibration support

It should remain a separate adapter, not a core dependency.


## Simple Future Architecture

The clean architecture should stay like this:

### 1. Truth Layer

- `nepse_scraper`
- `sharesansar_local`
- later other optional adapters if needed

Purpose:

- core market truth and history

### 2. Browser Edge Layer

- floorsheet
- last 15-minute trades
- broker holdings
- broker holding changes

Purpose:

- portal-only edge data

### 3. Core Decision Layer

- structure
- scoring
- QC
- liquidity
- event filtering
- trade plan

Purpose:

- turn raw data into disciplined decisions

### 4. LLM Layer

Purpose:

- synthesis
- critique
- similar-case reasoning
- final explanation

### 5. Feedback Layer

Purpose:

- compare decisions to outcomes
- identify failure patterns
- calibrate confidence


## What "Finished" Looks Like

This project is not finished just because data collection works.

This project is finished enough when:

- decisions are reliable
- outcomes are tracked consistently
- similar-case memory exists
- calibration becomes meaningful
- the LLM package is compact and decision-grade
- we can say what actually adds edge


## Practical Daily Routine

The simplest effective daily routine is:

1. after market close, run:

```powershell
python light_scan.py 1W '@expanded_reliability'
python deep_dive_shortlist.py 1W '@expanded_reliability'
```

2. for strongest candidates, optionally run:

```powershell
python manual_llm_package.py SYMBOL 1W
```

3. later, run outcome follow-up:

```powershell
python daily_followup.py YYYY-MM-DD 1W '@expanded_reliability'
```

4. review:

- latest shortlist outputs
- latest follow-up queue
- latest calibration summary


## Core Principle

Do not keep adding features just because AI tools can do more.

Only add new data or automation if it does at least one of these:

- lowers entropy
- improves decision quality
- improves outcome learning
- improves calibration
- catches a real failure mode

That is how the system stays smart without turning messy.
