# Historical 2025 Backfill Plan

## Purpose

This note defines the safest way to prepare 2025 data for replay and later learning.

The main decision is:

- use the local CSV archive as the historical price/trade backbone
- use browser discovery only to locate missing official data sources
- then build separate adapters for those missing sources


## What The Current CSV Archive Does

The local Sharesansar archive stores one daily snapshot per file:

- path: `sharesansar_datascrape/data`
- filename pattern: `MM_DD_YYYY.csv`

The adapter that reads it is:

- [sharesansar_csv_source.py](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/automation/data_sources/sharesansar_csv_source.py)

That adapter currently:

- scans files by date
- loads rows per day
- finds one symbol row on a given date
- normalizes fields such as:
  - open
  - high
  - low
  - close
  - vwap
  - volume
  - turnover
  - total trades
  - 52-week high/low
  - 120-day / 180-day averages

So for historical replay, the system is **already script-based**, not browser-based.


## 2025 Audit Result

We added:

- [historical_csv_audit.py](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/automation/historical_csv_audit.py)

Audit outputs:

- [2025 audit json](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/data/validation/historical_data_audits/2025__sharesansar_local__archive_audit_v1.json)
- [latest 2025 audit json](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/data/validation/historical_data_audits/latest__2025__sharesansar_local__archive_audit_v1.json)
- [2025 audit markdown](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/data/validation/historical_data_audits/2025__sharesansar_local__archive_audit_v1.md)

Current result:

- total CSV files: `364`
- weekday files: `260`
- weekend files: `104`
- schema issue files: `0`
- duplicate symbol files: `0`
- blank symbol files: `0`
- replay basket gap files: `0`
- archive confidence: `high`

Important note:

- one weekday gap remains: `2025-03-25`
- this should be treated as an **unverified gap**, not automatically a missing trading day, until checked against a holiday calendar


## Best Data Strategy

### 1. Use Scripts For Historical CSV Data

This should be the main replay backbone for 2025.

Why:

- point-in-time
- local
- fast
- reproducible
- already integrated

This means:

- do **not** use Playwright to re-scrape 2025 daily OHLCV/turnover/trade data


### 2. Use Playwright For Discovery, Not Backbone

Playwright is still useful, but for a different job:

- inspect where benchmark / sector / event data lives
- confirm whether the page hides an API endpoint
- decide whether to build a browser extractor or a direct adapter

So the rule is:

- browser first for discovery
- adapter second for durable ingestion


## Source Discovery Findings

### Official NEPSE benchmark and sector source

Using Playwright on `https://www.nepalstock.com/charts`, we confirmed:

- there is an `Index` tab
- there is a `Sub Index` tab
- the site exposes official sub-index choices like:
  - Banking SubIndex
  - Development Bank Index
  - HydroPower Index
  - Finance Index
  - Mutual Fund
  - and others

More importantly, the page network requests revealed API-style endpoints behind the UI, including:

- `/api/nots/nepse-index`
- `/api/nots/market-summary/`
- `/api/nots/graph/index/58`
- `/api/nots/graph/index/65`

This is the key architectural result:

- benchmark and sector history should probably become a **normal adapter**
- not a Playwright-only historical pipeline


### Official event source

We also confirmed official event surfaces already exist and are suitable for adapter-style extraction:

- NEPSE homepage disclosures and exchange messages
- SEBON right-share approved / pipeline pages
- SEBON prospectus pages

The current project already has:

- [event_sources.py](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/automation/event_sources.py)

So event data is not a greenfield problem.
It is an extension problem.


## Best Next Implementation Order

### Step 1

Keep using the CSV adapter for 2025 historical replay.


### Step 2

Build a new adapter layer for:

- official NEPSE benchmark / sub-index history

This is the highest-value next data layer.


### Step 3

Extend the event layer so replay can use:

- right-share state
- approved / pipeline state
- listing / notice context
- book closure / AGM / disclosure state where available


### Step 4

Only after those adapters exist:

- rerun historical replay with stronger market/sector/event context


## What Not To Do

Do not:

- rebuild 2025 daily replay data through Playwright
- merge browser scraping into the historical backbone
- keep replaying on weak symbol-local data once the benchmark layer is available


## Short Bottom Line

For 2025:

- historical CSV script ingestion is already the right backbone
- Playwright should only help discover missing benchmark and event sources
- the next real adapter to build is **official benchmark / sub-index history**

