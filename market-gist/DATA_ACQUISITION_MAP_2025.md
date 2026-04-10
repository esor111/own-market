# Data Acquisition Map For 2025 Replay

## Purpose

This note answers one question:

- where exactly do we get each missing 2025 replay data layer?

The goal is to avoid random scraping and avoid building the wrong adapter first.


## Core Rule

For 2025 replay:

- use the local CSV archive for historical per-symbol daily data
- derive as much as possible from that archive first
- only add new sources where the archive truly cannot provide the missing layer
- use Playwright for source discovery and early extraction only when direct adapter paths are not yet stable


## Data Map

### 1. Per-Symbol Daily History

Status:

- already available

What it covers:

- open
- high
- low
- close
- VWAP
- volume
- turnover
- trades
- 52-week high/low
- 120-day / 180-day averages

Source:

- local Sharesansar archive: `sharesansar_datascrape/data`

Current adapter:

- [sharesansar_csv_source.py](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/automation/data_sources/sharesansar_csv_source.py)

Acquisition method:

- script only
- no Playwright needed


### 2. Market Benchmark History

Status:

- source confirmed
- adapter not built yet

What we need:

- historical NEPSE Index values by replay date
- ideally 1D daily benchmark series for 2025

Confirmed source:

- official NEPSE charts page: `https://www.nepalstock.com/charts`

What discovery found:

- official `Index` chart exists
- page network requests hit NEPSE API-style endpoints such as:
  - `/api/nots/nepse-index`
  - `/api/nots/graph/index/...`

Best acquisition method:

1. first build a small discovery extractor using Playwright or browser-network inspection
2. then try to replace it with a direct HTTP adapter if session/certificate handling becomes stable

Why not start with raw HTTP immediately:

- direct local request probes hit certificate / connection handling issues
- browser requests are clearly succeeding

So the smart first move is:

- Playwright-assisted source hardening
- then direct adapter if possible


### 3. Sector / Sub-Index History

Status:

- source confirmed
- adapter not built yet

What we need:

- Banking SubIndex history
- Development Bank Index history
- HydroPower Index history
- Finance Index history
- and other relevant sector indices

Confirmed source:

- official NEPSE charts page `Sub Index` tab

What discovery found:

- visible sub-index choices on official site:
  - Banking SubIndex
  - Development Bank Index
  - HydroPower Index
  - Finance Index
  - Mutual Fund
  - and others
- page calls official graph endpoints behind the UI

Best acquisition method:

- same as market benchmark history
- build one benchmark/sub-index adapter layer together


### 4. Corporate Action Timeline

Status:

- source confirmed
- enriched extraction now exists
- now useful for the current replay basket

What we need:

- rights issue state
- right-share pipeline / approval state
- prospectus state
- bonus listing / listing notices
- book closure
- AGM notices
- important corporate disclosures

Confirmed sources:

- official NEPSE corporate disclosures page:
  - `https://www.nepalstock.com/corporatedisclosures`
- official NEPSE notices/disclosures feeds discovered from homepage network activity
- official SEBON pages:
  - `https://www.sebon.gov.np/prospectus`
  - `https://www.sebon.gov.np/right-share-approved`
  - `https://www.sebon.gov.np/right-share-pipeline`

Current code starting point:

- [event_sources.py](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/automation/event_sources.py)
- [corporate_action_pdf_extractors.py](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/automation/corporate_action_pdf_extractors.py)
- [corporate_action_timeline.py](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/automation/corporate_action_timeline.py)
- [nepse_company_news_archive.py](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/automation/nepse_company_news_archive.py)

What is now confirmed:

- the SEBON right-share index page was too generic by itself
- but the linked official PDF contains company-level rows
- those rows can be parsed and matched against the NEPSE security directory
- the official NEPSE corporate-disclosures page loads from:
  - `https://www.nepalstock.com/api/nots/news/media/company-news`
- that endpoint returns full-year symbol-tagged 2025 disclosures and directly covers the replay basket

Current honest limitation:

- event dates are still mostly publication-date-based
- this layer still needs replay measurement before any rule change

Best acquisition method:

- direct HTTP from the official NEPSE company-news archive first
- direct HTTP/table parsing for SEBON pages as secondary enrichment
- enrich generic SEBON summary rows from the linked official PDFs
- direct HTTP or browser-assisted extraction for NEPSE disclosures/notices depending endpoint stability
- Playwright fallback only where direct access is unreliable


### 5. Trading Calendar / Holidays

Status:

- source confirmed
- adapter not built yet

Why we need it:

- to explain unverified weekday gaps like `2025-03-25`
- to build a true Nepal trading calendar for replay

Confirmed source:

- official NEPSE holiday listing page:
  - `https://www.nepalstock.com/holiday-listing`

Best acquisition method:

- direct page parsing first
- Playwright only if the page requires dynamic rendering


### 6. Liquidity / Execution Features

Status:

- no new source required for first version

What we need:

- turnover persistence
- trade-count persistence
- volume persistence
- gap frequency
- zero-return / low-move frequency
- ATR-like volatility proxy
- Thursday-close / weekend-gap tag

Where it comes from:

- derive directly from the 2025 daily CSV archive

Best acquisition method:

- feature engineering script only
- no browser source needed


### 7. Breadth / Sentiment Proxies

Status:

- mostly derivable already

What we need:

- advancers vs decliners
- sector breadth
- new highs / new lows
- turnover concentration
- symbol participation ratio

Where it comes from:

- derive from the full daily cross-section in the CSV archive
- sector breadth requires replay sector grouping

Possible official supplement:

- NEPSE market summary endpoints may add useful current-style counts, but replay can start by deriving breadth from the archive itself

Best acquisition method:

- derive first
- source official supplements only if they add something not reproducible from CSV


### 8. Browser-Only Order Flow Features

Status:

- useful later
- not replay backbone for 2025

What it includes:

- last 15-minute trades
- broker holdings
- broker holding changes
- detailed floorsheet behavior

Best acquisition method:

- Playwright/browser layer

Important:

- do not block 2025 replay progress on this layer
- this is for later enrichment, not the first historical backbone


## Recommended Build Order

### Build Now

1. benchmark/sub-index source hardening
2. holiday/trading-calendar adapter
3. expanded event timeline adapter
4. liquidity and breadth feature derivation from CSV


### Build Later

1. browser-only order-flow history if reconstructable
2. deeper sentiment / macro / policy tags


## Short Bottom Line

For 2025, we do **not** need a new source for everything.

We already have enough to derive:

- symbol-local history
- liquidity persistence
- execution proxies
- breadth

The true missing external sources are:

- market benchmark history
- sector/sub-index history
- holiday calendar
- expanded corporate action timeline

And the best first acquisition method is:

- script the CSV-derived layers directly
- use Playwright to harden and confirm official benchmark/event sources
- then replace browser discovery with clean adapters where possible
