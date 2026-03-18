# Revalidated Integration Recommendation

## Purpose

This note revalidates the current architecture, external tooling options, and the exact next integration order for the NEPSE analysis system.

It corrects earlier recommendations where needed.

## What Is Confirmed

### 1. The current system is a real chart-evidence pipeline

The local codebase already has:

- Playwright chart automation
- timeframe validation
- raw extraction JSON
- screenshots and snapshots
- structure scoring
- QC gating
- outcome tracking
- calibration summaries
- model-input package generation

This means the project is no longer "just notes." It is a working evidence-to-decision pipeline.

### 2. The current dataset is still small

Local counts on 2026-03-18:

- `9` symbol/date run folders
- `9` decision files
- `8` outcome files
- `42` screenshots
- `68` raw extraction JSON tables
- `2` model-input package files
- `0` usable calibration samples

So the system can organize and reason over data, but it still cannot honestly claim measured predictive accuracy yet.

### 3. Playwright should stay, but not as the whole system

Playwright is still the right tool for:

- NepseAlpha chart access
- symbol/timeframe switching
- screenshots
- TradingView-only chart state
- drawing tools
- portal-specific UI data

It is not the best long-term source for all raw market data.

## What Needed Correction

### 1. "Use NepseAPI-Unofficial first" was too loose

After rechecking primary sources, this is not the best first integration for the current Python pipeline.

What is confirmed about `surajrimal07/NepseAPI`:

- it is a NEPSE toolkit with REST, WebSocket, and MCP server surfaces
- it advertises more than 20 MCP tools
- it is GPL-3.0 licensed
- the README says it is for educational and non-commercial use
- it is built on top of `basic-bgnr/NepseUnofficialApi`

This makes it interesting if you want:

- another MCP surface
- a standalone NEPSE data server
- agent-to-server access

But it is not the cleanest first dependency inside the current local Python pipeline.

### 2. The lower-level NepseUnofficialApi is feature-rich, but legally less clear

What is confirmed about `basic-bgnr/NepseUnofficialApi`:

- it has broad NEPSE coverage
- it includes company details, price volume history, floor sheet, supply/demand, news, and live/index data
- it is a lower-level Python client

What is not clearly confirmed from the repo page/README:

- an explicit license

That makes it a weaker first recommendation than a permissively licensed alternative.

### 3. The best first raw-data integration is `nepse_scraper`

What is confirmed about `polymorphisma/nepse_scraper`:

- MIT license
- published on PyPI
- supports market status, live data, historical price-volume, floor sheet, company details, dividends/right shares, and disclosures
- offers a high-level `NepseScraper` client plus low-level/custom endpoint access

For this codebase, that is the best first external integration candidate.

Reason:

- Python-native
- direct fit with the current scripts
- permissive license
- better match for raw data ingestion than spinning up a second server layer first

### 4. OpenBB is useful later, not first

What is confirmed from OpenBB docs:

- OpenBB supports custom provider extensions
- OpenBB has an MCP interface

What I did not find:

- a native NEPSE provider in OpenBB docs

So OpenBB is best treated as a later integration if you want to expose your own NEPSE data layer to multiple agents or tools.

It is not the best first way to get NEPSE data into this project.

### 5. Backtesting frameworks are later-stage additions

What is confirmed:

- `vectorbt` is strong for large-scale quantitative research, but its open-source licensing is more restrictive than standard permissive OSS
- `backtesting.py` is easier to use, but AGPL-3.0

These are useful later for walk-forward and strategy testing.

They are not the first thing to integrate while the raw data layer and record layout still need tightening.

## Critical Local Weakness Found During Revalidation

Top-level decision/session/model-input filenames are not timeframe-scoped.

Examples:

- [file_generator.py](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/automation/file_generator.py#L44)
- [file_generator.py](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/automation/file_generator.py#L229)
- [file_generator.py](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/automation/file_generator.py#L295)

This means:

- a `1M` run can overwrite the same-day `1W` decision for the same symbol
- a later run can silently replace the model-input package
- validation summaries can become stale or internally mixed if reruns happen after the summary is created

This is the most important local reliability fix before deeper external integration.

## Exact Recommendation Order

### Step 1. Fix timeframe-safe top-level records

Make these records timeframe-scoped:

- session
- decision
- model_input

This should happen before more serious integration work.

### Step 2. Add `nepse_scraper` as the raw market-data adapter

Use it for:

- symbol metadata
- historical OHLCV
- floor sheet
- market status
- corporate actions/disclosures where supported

Do not replace Playwright with it.

Use it to reduce browser dependence for data that does not need the chart UI.

### Step 3. Keep Playwright only for chart-specific evidence

Use Playwright for:

- NepseAlpha/TradingView evidence capture
- exact visible chart state
- screenshots
- special portal-only views
- drawing-based annotations if needed

### Step 4. Add a TradingView-aligned indicator calculation layer

Once raw OHLCV is available outside the browser, compute indicators from raw bars and compare them against chart-extracted values.

This is the right place to reduce entropy further.

### Step 5. Only later add a server/provider layer

If you eventually want multi-agent access, then either:

- expose your own NEPSE provider through OpenBB, or
- add a server layer like NepseAPI-Unofficial

That is useful later, not first.

### Step 6. Only after that add backtesting/walk-forward tooling

At that point, the raw data and record model will be stable enough for:

- walk-forward validation
- score calibration
- strategy comparison

## What Not To Do Next

- Do not replace Playwright entirely.
- Do not add OpenBB first expecting native NEPSE support.
- Do not integrate AgenticTrading first.
- Do not treat current calibration as real predictive accuracy.
- Do not keep building more chart-only logic while raw data and timeframe-safe record identity are still incomplete.

## Final Recommendation

The exact smartest next move is:

1. fix timeframe-safe decision/session/model-input records
2. integrate `nepse_scraper` as the first external data layer
3. keep Playwright for chart-only and portal-only evidence
4. delay OpenBB/server/backtesting integrations until after the raw-data layer is stable

That is the lowest-waste path from the current system to a stronger, lower-entropy prediction workflow.
