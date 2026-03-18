# Exact Required Work

**Date:** March 18, 2026  
**Purpose:** Define only the minimum required work based on the current system behavior  
**Rule:** No extra features. No speculative scope. Only the work that is necessary to make the current system more reliable, organized, and extendable.

---

## 1. What This Document Is

This is not a broad roadmap.

This is the **required-only list** based on what the current automation actually does today.

It is based on:

- current run outputs
- current extraction behavior
- current scoring behavior
- current storage behavior
- current structural weaknesses observed in generated files

---

## 2. What Is Working Already

These parts are already working enough to keep:

- browser connection and chart loading
- symbol loading
- timeframe switching
- extraction of visible OHLC values
- extraction of `EMA 20`, `MA 50`, `RSI`, `MACD`
- market capture
- sector capture
- symbol/date-based folder writing
- JSON file generation
- incomplete-data handling

These should **not** be rewritten right now unless a specific bug appears.

---

## 3. Exact Required Work

These are the things that must be done next.

### 1. Save raw extraction artifacts as first-class files

**Problem:**
The current automation extracts chart data and indicator values in memory, but does not consistently store those raw extracted values as dedicated raw JSON files for every run.

**Why this is required:**
If the final decision is questioned later, we need the raw extraction output, not just screenshots and normalized records.

**Required result:**
For each run, save raw extracted JSON for:

- market chart extraction
- stock chart extraction
- indicator extraction
- sector chart extraction

---

### 2. Make evidence references fully traceable

**Problem:**
Current `evidence_refs` mostly store bare filenames, not stable run-relative paths.

**Why this is required:**
Bare filenames are weak. Reliable systems need explicit references that point to the exact file location inside the symbol/date run folder.

**Required result:**
All `evidence_refs` should use run-relative paths like:

```text
raw/screenshots/2026-03-18__SMHL__1W__clean_v2.png
normalized/stocks/2026-03-18__SMHL__1W__stock_chart_v2.json
```

---

### 3. Separate structure-signal logic into its own module

**Problem:**
Support/resistance and setup derivation currently live inside `analyze_stock.py`, mixed together with browser orchestration.

**Why this is required:**
This makes the system harder to reason about, harder to test, and harder to extend safely.

**Required result:**
Move structure-related logic into a separate module, for example:

- `structure_signals.py`

That module should own:

- trend classification
- support/resistance derivation
- breakout level
- invalidation level
- target generation
- location labeling

---

### 4. Replace one-candle level logic with real structure logic

**Problem:**
Current levels are too dependent on the latest candle and moving averages.

Example symptom:
- entry zone equals current price
- nearest resistance only a few points above price
- targets are too close to be meaningful

**Why this is required:**
This is the main reason the current trade plan is not yet reliable.

**Required result:**
Levels must be derived from more than just:

- latest `open`
- latest `high`
- latest `low`
- latest `close`
- `EMA 20`
- `MA 50`

At minimum, the structure logic must use:

- recent visible swing highs
- recent visible swing lows
- local range boundaries
- trend break level

If those cannot be extracted directly, the system should mark structure confidence as low instead of pretending the levels are strong.

---

### 5. Add a quality gate for invalid trade plans

**Problem:**
The system currently produces trade plans even when:

- entry zone is too narrow
- nearest target is too close
- risk/reward is poor
- structure confidence is weak

**Why this is required:**
A system should refuse weak plans instead of formatting them nicely.

**Required result:**
Before final decision output, reject or downgrade plans when:

- `entry_zone` collapses to a trivial value
- `risk_reward_ratio < 1`
- support/resistance confidence is weak
- structure is not well-defined

This should force:

- `watch_only`
- `avoid`
- or `incomplete_structure`

instead of a misleading precise setup.

---

### 6. Replace hard-coded sector mapping with a maintained lookup

**Problem:**
Sector detection is currently hard-coded only for a tiny set of symbols.

**Why this is required:**
This makes the system non-general and unreliable for any new symbol.

**Required result:**
Move sector lookup into a maintained data file, for example:

- `sector_map.json`

This file should be used by the automation instead of hard-coded inline symbol checks.

---

### 7. Add a post-run QC pass for the generated setup

**Problem:**
The script can finish successfully even when the final trade plan is structurally weak.

**Why this is required:**
Runtime success is not the same as analysis quality.

**Required result:**
Add a simple QC rule set that checks:

- required fields exist
- evidence files exist
- score is internally consistent
- decision is consistent with derived structure
- entry/stop/targets are not trivial or self-contradictory

This does not need to be a second full system.
It can be a small validation pass.

---

## 4. Not Required Yet

These are **not** required for the next step and should not be done now.

- all drawing tools
- annotation tools
- pattern libraries
- geometric shapes
- XABCD tools
- Gann tools
- Elliott-like tools
- OCR
- broker/floorsheet automation
- full event/news engine
- machine learning
- backtesting framework
- dashboard
- notifications

These can come later.
They are not the minimum required work right now.

---

## 5. First Work Order

If we do only what is required, the build order should be:

1. Save raw extraction JSON
2. Fix evidence references
3. Extract structure logic into its own module
4. Improve level derivation so it is not one-candle-based
5. Add invalid-plan QC gate
6. Replace sector hard-coding with a lookup file

This is the smallest serious sequence.

---

## 6. Exact Current Limitation

The current system is good at:

- getting visible chart data
- storing runs
- producing structured output

The current system is **not yet reliable** at:

- producing meaningful structure levels
- producing high-confidence entry/stop/target plans

So the exact required next work is:

**make structure-derived levels trustworthy before adding more features**

That is the real bottleneck.
