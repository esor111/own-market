# Project Vision and Requirements

**Date:** March 16, 2026  
**Workspace:** `own-market`  
**Focus:** Build a repeatable NEPSE technical-analysis workflow with high-value decision support

---

## 1. What We Actually Want

We want a professional stock-analysis system for the Nepal stock market that helps us make better trading and investing decisions without re-thinking the whole chart from zero every time.

This system should:

- reduce noise
- reduce repeated corrections and re-analysis
- make chart reading consistent
- improve trade quality
- define clear invalidation
- turn chart analysis into a repeatable workflow

The goal is **not** to use every possible chart tool.

The goal is to use only the highest-value tools in a structured order so that each tool answers one specific question and the final decision becomes clearer, faster, and more reliable.

---

## 2. Core Problem

Right now, technical analysis can become messy because:

- too many tools create confusion
- the same chart gets re-checked again and again
- interpretation changes too much from one review to another
- indicators can duplicate each other
- trade decisions are sometimes not tied to a clear scoring or invalidation model

Because of that, analysis becomes slower, noisier, and less trustworthy.

---

## 3. Final Outcome We Want

We want a system that can take a NEPSE stock and produce a clean, structured decision like this:

1. What is the market context?
2. What is the sector context?
3. What is the stock trend?
4. Where are the key support and resistance zones?
5. Is volume confirming the move?
6. Is momentum confirming the move?
7. Is the setup a breakout, pullback, reversal, or avoid?
8. What is the exact entry, stop loss, and target?
9. What score does this setup get?
10. What is the final action: buy, wait, avoid, reduce, or review later?

This should be repeatable across many stocks, not just one stock like `SMHL`.

---

## 4. The Real Product

The real product is not a single stock report.

The real product is a **decision framework**:

`market -> sector -> stock structure -> zones -> trend filter -> volume -> momentum -> setup type -> risk -> score -> action`

This framework should later become:

- a daily checklist
- a scorecard
- a setup library
- a repeatable documentation format
- an automated or semi-automated Playwright workflow

---

## 5. High-Value Technical Edge We Want

We do not want indicator overload.

We want the small set of technical tools that gives most of the value:

- candlestick chart
- volume
- support and resistance zones
- trendlines
- `20 EMA`
- `50 MA`
- optional `200 MA` for broader trend
- one momentum tool: `RSI` or `MACD`
- multi-timeframe confirmation
- risk-reward and invalidation logic

Each tool must have one job:

- market structure -> direction
- support/resistance -> location
- moving averages -> trend filter
- volume -> confirmation
- RSI or MACD -> momentum confirmation
- lower timeframe -> entry timing
- stop/target -> risk structure

If a tool does not clearly improve decision quality, it should not be part of the default workflow.

---

## 6. Questions the System Must Answer Every Time

Every analysis must answer these seven questions:

1. What is the trend?
2. Where is price located right now?
3. Is volume supporting the move?
4. Is momentum strong or weak?
5. Is the overall market helping or hurting?
6. What exactly is the trade setup?
7. Where are we wrong if the setup fails?

If these are not answered clearly, the chart is not ready for a decision.

---

## 7. Default Workflow We Want

The workflow should always happen in this order:

1. Check overall NEPSE market condition
2. Check sector condition
3. Open stock on higher timeframe
4. Mark major support and resistance zones
5. Identify market structure
6. Add `20 EMA` and `50 MA`
7. Check volume behavior
8. Check `RSI` or `MACD`
9. Move to lower timeframe for entry refinement
10. Define entry, stop loss, invalidation, and target
11. Score the setup
12. Decide action

This order matters because it reduces back-and-forth thinking.

---

## 8. Types of Setups the System Should Recognize

To stay focused, the workflow should mainly classify setups into:

### Breakout
- price approaches major resistance
- volume expands on breakout
- momentum confirms
- market context is not weak

### Pullback
- strong uptrend already exists
- price pulls back into support or moving average zone
- pullback volume is weaker than breakout volume
- bullish reaction appears

### Reversal
- prior decline is strong
- base forms near support
- repeated support holds
- bullish divergence or momentum shift appears
- breakout from base confirms

### Avoid
- price is in the middle of nowhere
- support and resistance are unclear
- market context is poor
- volume is not confirming
- stop is too large or reward too small

---

## 9. Scoring System We Want

We want a simple score so decisions become more objective.

Example scoring categories:

- Trend
- Location
- Volume
- Momentum
- Market context
- Risk-reward quality

Each category can be scored from `0` to `2`, producing a total score out of `12`.

Example interpretation:

- `10-12` = strong setup
- `8-9` = tradable but needs discipline
- `6-7` = weak or watchlist only
- `0-5` = avoid

The exact scoring model can be refined later, but the core idea is fixed:
**do not rely on feeling alone.**

---

## 10. Role of Playwright in This Project

Playwright is important, but it is not the strategy itself.

Playwright should help us:

- open NEPSE Alpha charts quickly
- switch stocks and timeframes
- add indicators consistently
- draw lines and zones precisely
- capture screenshots
- extract visible chart context
- make the workflow repeatable

So Playwright is the **execution and automation layer**, while the technical workflow is the **decision layer**.

---

## 11. NEPSE-Specific Edge We Want

Because this project is for Nepal's market, the workflow should consider:

- overall NEPSE index condition
- sector condition
- broker and floorsheet behavior when useful
- price action around lower-liquidity names
- local corporate actions such as rights shares, bonus shares, book closure, and AGM events

This means the system should not depend only on generic chart logic. It should also fit the reality of NEPSE.

---

## 12. What We Do Not Want

We do not want:

- random indicator stacking
- constant setting changes
- overcomplicated charts
- too many drawn lines
- unclear trade logic
- analysis without invalidation
- repeating the same thinking manually every time
- fake confidence from too much information

Complexity is not the target.
Clarity and repeatability are the target.

---

## 13. Success Criteria

This project is successful if:

- the workflow can be reused on any NEPSE stock
- the same stock analyzed twice gives similar conclusions
- chart review becomes faster
- low-quality setups get filtered out earlier
- entry, stop, and target become clearer
- screenshots and notes follow a repeatable structure
- Playwright can support the workflow with minimal manual correction

The real measure of improvement is not "perfect prediction."

The real measure is:

- fewer bad trades
- better trade selection
- cleaner invalidation
- more consistent execution

---

## 14. Immediate Deliverables We Should Build Next

After this vision doc, the next practical deliverables should be:

1. A one-page master workflow
2. A chart-marking checklist
3. A setup scorecard template
4. A standard analysis output format
5. A setup library with screenshots
6. A Playwright execution workflow for chart preparation

---

## 15. One-Sentence Project Definition

We are building a repeatable NEPSE chart-decision system that combines market context, structure, trend, volume, momentum, and risk into a clear scored action so that technical analysis becomes faster, cleaner, and more reliable.
