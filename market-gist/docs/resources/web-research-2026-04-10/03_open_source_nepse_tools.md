# Thread 3: Open-Source NEPSE Tools and Datasets

## Question
What open-source code, datasets, and tools already exist for NEPSE? Are we reinventing wheels?

## Method
WebSearch across GitHub, PyPI, Kaggle, Hugging Face, and Nepal-focused dev communities. Reviewed READMEs and project descriptions for ~40 projects.

## TL;DR

**Overall ecosystem maturity: moderate, fragmented, hobby-grade.**

- **Data access:** Two solid Python wrappers exist (`nepse_scraper`, `NepseUnofficialApi`). We should use these instead of writing our own.
- **Datasets:** Kaggle has NEPSE OHLC and one floorsheet archive. No structured corporate-action database exists.
- **Analytics/quant:** Very weak — LSTM toy projects, pivot tables, no rigorous backtesting frameworks with outcome validation.
- **MCP/AI integration:** Surprisingly present — three MCP servers exist.
- **Commercial:** One legitimate licensed API (SmartWealthPro MDP).

**Critical finding:** Our work has no equivalent in the ecosystem. Direct quote from the research agent:

> "Your `market-gist/automation` pipeline appears to be **more rigorous than anything public in NEPSE open-source right now**. You're not reinventing wheels on data access, but your core methodological contribution has no equivalent in the ecosystem."

---

## Tier A — Actively Maintained, Worth Using

### polymorphisma/nepse_scraper (MIT, Python, on PyPI)
- **The de-facto standard Python client for NEPSE API**
- Dynamic endpoint registration, smart retries, type-hinted client
- Covers broker lookup, sectors, trading data, indices, floorsheet
- **Recommendation:** Use this instead of writing our own NEPSE HTTP client
- URL: https://github.com/polymorphisma/nepse_scraper
- PyPI: https://pypi.org/project/nepse-scraper/

### surajrimal07/NepseAPI-Unofficial (educational/non-commercial only)
- Wraps `basic-bgnr/NepseUnofficialApi`
- Adds REST, WebSocket, and **FastMCP MCP server with 20+ tools**
- 10-min in-memory caching
- License: forbids commercial / production trading use
- Worth studying since we're building Claude-driven analysis
- URL: https://github.com/surajrimal07/NepseAPI-Unofficial

### basic-bgnr/NepseUnofficialApi (Python)
- Original reverse-engineered nepalstock.com wrapper
- Most other unofficial APIs depend on this
- Handles the dummy-id auth bypass
- URL: https://github.com/basic-bgnr/NepseUnofficialApi

---

## The One Project Worth Studying — `nepse-quant-terminal`

### nlethetech/nepse-quant-terminal
**This is the closest project to what we're building.**

Features (from their README):
- Paper portfolio, paper order book, NAV log, trade history
- Broker-assisted **live and shadow-live trading** through TMS execution intents (`tms_audit.py`)
- Textual TUI dashboard
- Live trader with signal generation and exits
- **MCP server exposing tools:** `get_market_snapshot`, `get_portfolio_snapshot`, `get_signal_candidates`, `get_risk_status`, `semantic_story_search`, `unified_osint_search`, `submit_paper_order`, TMS intent ops
- Built-in agents: local Gemma 4 MLX analyst as default, Claude analyst as alternative
- NepalOSINT integration for news/story search

**What they have that we don't:**
- TUI dashboard for live use
- MCP tool surface (we don't expose our work via MCP yet)
- News/story OSINT integration
- Integrated paper trading flow

**What we have that they don't:**
- Outcome evaluation loop (`evaluate_outcome.py`, `reevaluate_pending_outcomes.py`)
- Forward shadow scoring with calibration (`score_persistence_shadow_reports.py`)
- Frozen-champion experiment lab discipline
- Multi-day broker persistence as a primary signal
- Documented learnings file (LEARNINGS.md, 11 entries)

**Note on terminology overlap:** Their "persistence" is *audit log persistence*, not *broker flow persistence analysis*. Our conceptual persistence (multi-day dominant broker engagement) still appears to be unoccupied open-source territory.

**Recommendation:** Read their code carefully. We could contribute our outcome-evaluation loop; we could absorb their TUI and MCP patterns.

URL: https://github.com/nlethetech/nepse-quant-terminal

---

## Floorsheet Analysis — Closest Prior Work to Ours

All lightweight, none with outcome validation:

| Project | What it does |
|---|---|
| pratyushmishra19/Nepse_floorsheet_analysis | Identifies brokers doing the most transactions below 20 units to flag possible manipulation. Includes `broker_list.csv` and `Broker_list_scrape.py`. |
| saharshtapi/Nepse-FloorSheet-Analysis | Floorsheet analysis exercises |
| madhuko/nepse_analytics | Insights from floorsheet analysis (learning project) |
| mrsudox/Nepse_FloorSheet_PivotTable | Pivot-table UI over floorsheet |
| efexos/floorsheet | Live/historic floorsheet viewer, updates every 15s |

**Verdict:** None of these do multi-day broker persistence scoring, none evaluate outcomes, none calibrate. Our work is additive.

URLs:
- https://github.com/pratyushmishra19/Nepse_floorsheet_analysis
- https://github.com/saharshtapi/Nepse-FloorSheet-Analysis
- https://github.com/madhuko/nepse_analytics
- https://github.com/mrsudox/Nepse_FloorSheet_PivotTable
- https://github.com/efexos/floorsheet

---

## Datasets Worth Downloading

### Kaggle
- **shivaharisubedi/nepse-floorsheet** — NEPSE daily floorsheet transactions. **Most interesting for our broker-persistence work.** URL: https://www.kaggle.com/datasets/shivaharisubedi/nepse-floorsheet
- **sagyamthapa/nepali-stock-market-form-2012-to-2020-till-march** — Daily OHLC per company, 2012-2020. URL: https://www.kaggle.com/datasets/sagyamthapa/nepali-stock-market-form-2012-to-2020-till-march
- **qramkrishna/nepal-stock-exchange-data** — NEPSE data up to 2019
- **dimanjung/nepse-index-historical-data** — NEPSE index history
- **dinkarregmi/nepse-dataset**
- **sarojrana/nepse-data**

### Academic / research-linked
- **tejshahi/StockPricePrediction-NEPSE-** — publishes raw news, raw stock, and final CSVs from LSTM-based prediction paper. URL: https://github.com/tejshahi/StockPricePrediction-NEPSE-
- Paper: "Predicting NEPSE index price using deep learning models" (Sitaula et al., 2022, ScienceDirect)
- Paper: "Predicting the Direction of NEPSE Index Movement with News Headlines" (MDPI Econometrics 2024)

### Other open portals
- **omitnomis.github.io/ShareSansarScraper/** — downloadable historical archive (Excel/CSV)
- **Open Data Nepal** (opendatanepal.com) — macro indicators, no NEPSE floorsheet

### Hugging Face
**No confirmed NEPSE-specific dataset on HF as of search.** We could publish ours and likely be the first.

---

## Commercial / Licensed Platforms

### SmartWealthPro MDP — **Only NEPSE-Licensed Commercial API**
- The only legitimate commercial route
- Real-time + historical, REST, 99.9% SLA claim
- Pricing not public — requires contact
- URLs:
  - https://data.smartwealthpro.com/
  - https://data.smartwealthpro.com/documentation/

### Nepalytix
- Live NEPSE analytics, AI stock insights, portfolio tracking
- Advertises "Open data for developers" but actual API terms are gated
- Run by Cognify System Pvt. Ltd.
- URL: https://nepalytix.com/

### NepseAlpha
- Charting, floorsheet analysis, broker holdings, investment calendar
- No public API documentation; data extracted via reverse engineering
- URL: https://nepsealpha.com/

### ShareSansar
- Corporate action tables, indices history, floorsheet
- "SS Pro" paid desktop product with "NEPSE Confidence Meter"
- URL: https://www.sharesansar.com/

### Others
- **MeroLagani** — datewise floorsheet, indices
- **ShareHub Nepal** — advanced screener, broker dashboard
- **Chukul** — Android app, "algo & AI-based analytics"
- **Share Alpha** — "AI and Algo Base" Windows app
- **Smart Wealth Pro** — Play Store app, fed by MDP

---

## MCP Servers (Relevant Because We're Running Claude-Driven)

| Project | License | Notes |
|---|---|---|
| surajrimal07/NepseAPI-Unofficial | Educational only | 20+ tools, FastMCP. Most comprehensive. |
| razaanstha/nepse-mcp-server | MIT, Node | Wraps ShareBazaar API. Tools: `getTrendingStocks`, `getChartDataByStock`, `getMarketRangeData`, `getTechnicalIndicatorData`. |
| nlethetech/nepse-quant-terminal MCP | (project license) | Built-in MCP for paper trading tools |

URLs:
- https://github.com/surajrimal07/NepseAPI-Unofficial
- https://github.com/razaanstha/nepse-mcp-server
- GitHub topic: https://github.com/topics/nepse-mcp-servers

---

## ML / Prediction Projects (Read for What NOT to Do)

These are the LSTM-on-OHLC efforts that almost certainly have no real predictive edge (per L-011 + the L-002 calibration finding):

- **tejshahi/StockPricePrediction-NEPSE-** — LSTM with news + stock features
- **pudasainishushant/NEPSE-prediction** — LSTM. Classic naive setup.
- **Anup-Dhakal/NEPSE-stock-Prediction-ML-Project**
- **q-viper/NEPSE-Data-Analysis** — 2000-2018 data
- Medium: "Advanced Stock Forecasting with LSTM and Attention" by Bishaljoshi

**Read these to understand the common failure modes:** train/test leakage, no outcome evaluation, no calibration, no walk-forward validation.

---

## What's Missing in the Open Source Ecosystem (Our White Space)

The agent identified four gaps where nothing comparable exists:

1. **Structured open corporate-action database** for NEPSE — all data exists on ShareSansar / MeroLagani / NepseAlpha as HTML tables; nobody has published a clean normalized CSV/JSON open dataset. **We have one.**

2. **Nepal economic indicator dataset tied to NEPSE movements** — macro exists on Open Data Nepal / NSO / World Bank but nobody has joined it to NEPSE series in open source.

3. **Active open-source broker persistence / flow-validation framework with outcome evaluation and calibration** — does not appear to exist. **This is our whitespace.**

4. **Multi-day broker persistence scoring with frozen policy + forward evidence collection** — closest comparable (`nepse-quant-terminal`) has trading paper UI but no calibration discipline or learnings tracking.

---

## Recommendations

### Should we use existing tools?

**Yes, for data access:**
- Use `polymorphisma/nepse_scraper` instead of maintaining our own NEPSE HTTP client
- Fall back to `basic-bgnr/NepseUnofficialApi` if needed
- Stop writing custom Selenium/BS4 scrapers — five already exist and go stale quarterly

**Yes, for historical bulk data:**
- Download `shivaharisubedi/nepse-floorsheet` from Kaggle for floorsheet backfill
- Download `sagyamthapa/nepali-stock-market-form-2012-to-2020-till-march` for OHLC backfill
- Download `omitnomis.github.io/ShareSansarScraper/` archive

**No, for persistence/outcome/calibration logic:**
- This is our white space. Keep building.

### Should we contribute?

- **`polymorphisma/nepse_scraper`:** contribute endpoint additions or bug fixes; it's the most dependable foundation
- **`nlethetech/nepse-quant-terminal`:** consider contributing our outcome-evaluation discipline; absorb their TUI/MCP patterns
- **`surajrimal07/NepseAPI-Unofficial`:** study caching patterns for our own use

### Should we publish?

- Our experiment lab structure + LEARNINGS.md discipline could be valuable as a public reference for NEPSE researchers
- Our broker persistence framework with calibration would be the first of its kind in NEPSE open source
- VPIN applied to NEPSE floorsheet would be a real academic contribution (mentioned in thread 1)

---

## Master Source List — Notable GitHub Projects

### Data access
- https://github.com/polymorphisma/nepse_scraper
- https://github.com/basic-bgnr/NepseUnofficialApi
- https://github.com/surajrimal07/NepseAPI-Unofficial
- https://github.com/Aabishkar2/NepseAPI
- https://github.com/Aabishkar2/nepse-data
- https://github.com/CaffeineDuck/nepse-api
- https://github.com/pyFrappe/nepse
- https://github.com/Sabin-Subedi/nepse-scraper
- https://github.com/AjanShrestha/nepse-scraper
- https://github.com/AashisMhj/nepse-api
- https://github.com/bishaludash/NEPSE-Api
- https://github.com/biv-neupane7/Nepse-API
- https://github.com/Prabesh01/nepalstock-api
- https://github.com/manishmodi/Nepal-Stock-Data-Api
- https://github.com/ghimiresunil/Nepse-Web-Scraper
- https://github.com/BkrmDahal/nepse
- https://github.com/Nabinda/Nepse
- https://github.com/sudeep611/nepserate
- https://github.com/BikeshSuwal/nepseData

### Floorsheet scrapers
- https://github.com/suyogdahal/nepse-data
- https://github.com/sbmagar13/sharesansar_datascrape
- https://github.com/fuunshi/ShareSansarDataScrape
- https://github.com/aakash-shakya/nepse-live-floorsheet-scraper
- https://github.com/rajanprasad460/NEPSE_EXTRACTOR
- https://github.com/Sagyam/web-scrapers
- https://github.com/OmitNomis/ShareSansarScraper
- https://github.com/sureshshrestha/dailyStockPrice

### Analytics
- https://github.com/nlethetech/nepse-quant-terminal
- https://github.com/pratyushmishra19/Nepse_floorsheet_analysis
- https://github.com/saharshtapi/Nepse-FloorSheet-Analysis
- https://github.com/madhuko/nepse_analytics
- https://github.com/mrsudox/Nepse_FloorSheet_PivotTable
- https://github.com/efexos/floorsheet

### Datasets
- https://www.kaggle.com/datasets/shivaharisubedi/nepse-floorsheet
- https://www.kaggle.com/datasets/sagyamthapa/nepali-stock-market-form-2012-to-2020-till-march
- https://www.kaggle.com/datasets/qramkrishna/nepal-stock-exchange-data
- https://www.kaggle.com/datasets/dinkarregmi/nepse-dataset
- https://www.kaggle.com/datasets/sarojrana/nepse-data
- https://www.kaggle.com/datasets/dimanjung/nepse-index-historical-data
- https://omitnomis.github.io/ShareSansarScraper/

### Commercial
- https://data.smartwealthpro.com/
- https://nepalytix.com/
- https://nepsealpha.com/
- https://www.sharesansar.com/
- https://merolagani.com/
- https://sharehubnepal.com/

### MCP Servers
- https://github.com/topics/nepse-mcp-servers
- https://github.com/razaanstha/nepse-mcp-server
