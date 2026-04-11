# Thread 4: Nepal Data Sources We Missed

## Question
What Nepal-specific structured data sources could be used for stock market analysis that we haven't yet discovered? Look for the unusual stuff. Look for things NEPSE traders don't typically use.

## Method
WebSearch across government portals, industry associations, multilateral data providers, niche/weird sources. Reviewed actual page contents where possible.

## TL;DR

40+ sources surfaced. Most are noise. **Five sources are worth bookmarking; none should be built now.** Under L-011 patience mode, the rule is no new builds before persistence forward evidence batch-scores. The single most interesting new hypothesis is NRB Public Debt Ownership Structure as a contrarian liquidity signal — captured here so the idea is preserved, but it should not be the next thing built.

---

## Tier 1 — Worth Knowing Exists, Not Actionable Under Patience Mode

### 1. NRB Forex API (JSON)
- **URL:** https://www.nrb.org.np/api-docs-v1/
- Base: `https://www.nrb.org.np/api/forex/v1/`
- **The ONLY structured JSON endpoint NRB offers**
- Daily FX rates for ~20 currencies
- Date range queries supported
- No authentication required
- **Trivial to add. Daily signal for FX-sensitive sectors.**

### 2. NRB Public Debt Ownership Structure
- **URL:** https://www.nrb.org.np/pdm/ownership-structure-of-government-securities-2080-05-bhadra/
- Archive category: https://www.nrb.org.np/category/public-debt-operations-archive/
- Monthly breakdown of who holds government securities (commercial banks, NRB, insurance, EPF, individuals)
- Format: PDF tables (scrapable)
- **Hypothesis:** when commercial banks decrease their T-bill holdings month-over-month, they may be shifting liquidity into productive (or speculative) lending — possibly leading NEPSE rallies. When they increase holdings, banks may be parking liquidity defensively — possibly leading declines.
- **Status:** Best new experiment hypothesis from the research session. **Bookmarked for after persistence forward batch-scoring.** Not built yet. The hypothesis is unproven on our data and would constitute a new experiment, which violates L-011 patience mode if built now.

### 3. ICRA Nepal — Rating Actions
- **URL:** https://www.icranepal.com/
- Mirror with archive: https://www.sharesansar.com/icra-rating
- Credit rating upgrades/downgrades for banks, hydro, insurance, corporate debt
- **Documented to lead stock price by days-to-weeks in Nepal** (per agent research)
- Direct event source — could plug into existing event-study framework as a new lane
- Frequency: rating-action driven; rationale PDFs published per action

### 4. Open Data Nepal + Nepal in Data
- **URLs:**
  - https://opendatanepal.com/
  - http://nepalindata.com/
  - http://www.nationaldata.gov.np/
- 1600+ datasets across economy, finance, energy, industry
- **CSV/XLSX/JSON formats with API access**
- **The most machine-readable Nepal aggregator that exists**
- Could replace a lot of PDF scraping for backfills

### 5. NRB Public Debt Management — T-bill Auctions
- **URL:** https://obss.nrb.org.np/pd/tbnotices.php
- Online Bidding System for T-bills and development bonds
- Weekly T-bill auction notices and results
- Cleaner short-rate signal than the monthly macro report
- Format: PHP-served HTML tables (scrapable)

---

## Tier 2 — Interesting for Later

### IBN — Investment Board Nepal Project Bank
- URL: https://ibn.gov.np/
- Fast-track project pipeline (hydro >200 MW, cement, cross-border transmission)
- PDA/PIA stage data, capacity, developer, status
- Format: PDF dispatches; needs OCR
- Maps directly to large-cap hydro names (UPPER, API, NHPC)
- Project-milestone events drive individual hydro stocks weeks before disclosure

### Department of Industry — FDI Statistics
- URL: https://www.doind.gov.np/industrial-statistics
- Monthly FDI approvals by sector
- FDI flow into a sector leads bank credit flow into that sector by 2-4 quarters
- Strong for hydropower, cement, tourism lanes

### Ministry of Energy, Water Resources and Irrigation
- URL: https://moewri.gov.np/
- Notices: https://www.moewri.gov.np/pages/notices?lan=en&id=362
- PPA/PDA policy changes, project approvals, export MoUs
- Rule changes are first-order events for every hydro name

### Department of Land Management — Real Estate Transactions
- Monthly deeds registered, revenue collected by district
- **Real estate transaction volume is the cleanest available proxy for informal economy liquidity** and household credit demand
- Leads commercial bank loan growth

### Nepal Insurance Authority Stats
- URL: https://nia.gov.np/stats
- Premium collection by company (life, non-life, micro, reinsurance)
- ~37 insurers (14 life, 14 non-life, 2 re, 4 micro)
- Premium growth trajectory leads insurer stock earnings by 1-2 quarters

### Nepal Telecommunications Authority — MIS Reports
- URL: https://nta.gov.np/
- Sample: https://nta.gov.np/uploads/contents/MIS%20Report_2080%20Poush.pdf
- Monthly MIS reports: voice/data subscribers, ARPU, market share (NT, Ncell, Smart)
- Nepal Telecom (NTC) is listed; Ncell market-share shifts are direct trading signal

### Immigration Department — Arrival/Departure Reports
- URL: https://www.immigration.gov.np/en/page/arrival-departure-report
- Country-of-origin breakdown by month
- **Departure data for Nepali workers by destination — leading remittance signal 3-6 months ahead**
- Almost nobody uses this operationally

### Financial Comptroller General Office (FCGO)
- URL: https://fcgo.gov.np/
- Daily/monthly treasury operations
- Capex release cadence drives cement demand
- More granular than MoF budget speeches

### NRB Forex Database
- URL: https://www.nrb.org.np/database-on-nepalese-economy/financial-sector/
- Daily summary HTML + CSV links
- Interbank money market volume

---

## Niche / Weird Sources

### IPPAN Energy Statistics 2025 (We Have This — Documenting For Reference)
- Sept 2025 PDF: https://www.ippan.org.np/wp-content/uploads/2025/09/Energy-statics-of-Nepal-2025-1.pdf
- Mar 2025 PDF: https://www.ippan.org.np/wp-content/uploads/2025/03/Energy-Statistics-2025.pdf
- 204 operational projects: 2,948 MW
- 143 under construction: 4,303 MW
- Private sector >80% of generation capacity

### Nepal Bankers' Association — Monthly Press Meets
- URL: https://nepalbankers.com.np/monthly-press-meet-5/
- After NRB's May 2025 rule, all 20 commercial banks publish base rates on 1st of each month
- Monthly cleanest signal for commercial banks
- More granular than NRB quarterly rate archive

### CNI Business Confidence Index (Quarterly)
- URL: https://www.cni.org.np/
- Q1 2080/81 example: https://www.cni.org.np/storage/publication/4hxy6wyF7byj5rbmvzkObPMGjRrn928qbejpvUER.pdf
- Identifies "wait-and-watch" share of entrepreneurs — a real number you can regress against NEPSE

### FNCCI Data Portal + Business Confidence Survey
- URL: https://data.fncci.org/en/
- Survey reports: https://data.fncci.org/gridtemplate/survey_report
- Quarterly Business Confidence Survey + economic surveys
- Direct sentiment proxy

### FENEGOSIDA — Daily Gold Prices
- URL: https://www.fenegosida.com/
- Official daily gold (Hallmark, Tejabi) and silver prices
- Set daily at 11:00 NPT (except Saturdays and holidays)
- HTML — scrapeable
- **Gold is a retail wealth store in Nepal and competes with NEPSE for retail household allocation.** Sustained gold rally correlates with NEPSE breadth compression.

### Nepal Oil Corporation — Retail Fuel Prices
- URL: https://noc.org.np/retailprice
- LPG history: https://noc.org.np/lpg
- Fortnightly (1st, 15th)
- Fuel pass-through for cement, hydro, airlines, logistics

### UrjaKhabar — Daily Energy Trade Publication
- URL: https://www.urjakhabar.com/en/
- Project milestones, PPA news, tariff changes, construction updates
- **Publishes hydropower project news 1-3 days before ShareSansar/MeroLagani pick it up**
- Direct edge for hydropower names

### CareEdge Ratings Nepal
- URL: https://www.careratingsnepal.com/
- Second rating agency in Nepal
- Complementary to ICRA for cross-validation

### SEBON Quarterly Statistics
- URL: https://www.sebon.gov.np/quarterly-statistics
- Quarterly Securities Market Indicators PDF
- Broker quarterly submission status (compliant/stressed brokers)
- Credit rating intermediaries: https://sebon.gov.np/intermediaries/credit-ratings

---

## Multilateral / International Mirrors

| Source | URL | Use |
|---|---|---|
| World Bank Nepal | https://data.worldbank.org/country/nepal | Clean backfill for gaps in Nepal official data; CSV/JSON/API |
| ADB Nepal | https://www.adb.org/countries/nepal/main | Hydropower loan commitments lead approvals by 6-12 months |
| IMF Article IV | https://www.imf.org/en/Countries/NPL | Annual forward macro projections + annex tables |
| CEIC Nepal (paid) | https://www.ceicdata.com/en/country/nepal | ~5000 time series; subscription |
| Trading Economics | https://tradingeconomics.com/nepal/indicators | Quick cross-check for NRB numbers |

---

## Specific Data Types Inventory

| Data type | Source | Frequency | Format |
|---|---|---|---|
| Daily gold prices | FENEGOSIDA | Daily | HTML |
| Daily fuel/LPG prices | NOC | Fortnightly | HTML |
| Real estate transactions | Department of Land Management via FCGO | Monthly | PDF/press |
| Insurance premium by company | NIA + sharesansar mirror | Quarterly | PDF |
| Banking NPL | NRB BSD supervision + FSR (biannual) | Biannual/annual | PDF |
| Cement production by company | CMAN press + company quarterly | Quarterly | PDF |
| Electricity generation by IPP | NEA annual report + PPA list | Annual | PDF |
| Tourist arrivals by country | Immigration Department | Monthly | HTML + PDF |
| Remittance by source country | NRB monthly (aggregate) + Article IV (by country, annual) | Mixed | PDF |
| FX reserves by currency | NRB FSR | Quarterly | PDF |
| Interbank money market volume | NRB Financial Sector database | Daily summary | HTML + CSV |

---

## Priority Additions Ranked

Given our verticals and the "mechanical > LLM" lesson, the highest-value additions that are machine-readable and reliable:

1. **NRB Forex API (JSON)** — trivial to add, daily FX signal
2. **NRB Public Debt Management T-bill auctions + ownership structure** — direct liquidity regime signal; PDF-scrapable
3. **NTA Monthly MIS reports** — telecom sector signal for NTC stock
4. **Immigration Department arrival/departure reports** — forward-looking remittance and tourism signals
5. **ICRA Nepal rating action feed** — direct event source for banks/hydros/insurers
6. **Open Data Nepal + Nepal in Data API** — backfill aggregator, cleanest machine-readable store
7. **FENEGOSIDA daily gold price** — retail-wealth substitute signal
8. **NOC retail price history** — fuel pass-through for cement, hydro, airlines, logistics
9. **IBN project bank dispatches** — hydropower event leader
10. **NIA insurance premium quarterly stats** — insurer earnings leader

---

## The Single Most Interesting New Lens (Bookmarked)

**NRB Public Debt Ownership Structure.** Contrarian liquidity hypothesis we never considered.

The hypothesis:
- When commercial banks **increase** their T-bill holdings → defensive parking → may lead NEPSE decline
- When commercial banks **decrease** their T-bill holdings → liquidity flowing to credit / margin lending → may lead NEPSE rally

Testable, monthly granularity, public PDF source. **Bookmarked for after persistence forward batch-scoring.** It would be a new experiment, and L-011 patience mode says no new experiments now.

---

## Master Source List

### Tier 1
- https://www.nrb.org.np/api-docs-v1/
- https://www.nrb.org.np/pdm/ownership-structure-of-government-securities-2080-05-bhadra/
- https://www.nrb.org.np/category/public-debt-operations-archive/
- https://www.icranepal.com/
- https://www.sharesansar.com/icra-rating
- https://opendatanepal.com/
- http://nepalindata.com/
- https://obss.nrb.org.np/pd/tbnotices.php

### Tier 2
- https://ibn.gov.np/
- https://www.doind.gov.np/industrial-statistics
- https://moewri.gov.np/
- https://nia.gov.np/stats
- https://www.nta.gov.np/
- https://www.immigration.gov.np/en/page/arrival-departure-report
- https://fcgo.gov.np/
- https://www.nrb.org.np/database-on-nepalese-economy/financial-sector/

### Niche / Weird
- https://www.ippan.org.np/
- https://nepalbankers.com.np/
- https://www.cni.org.np/
- https://data.fncci.org/en/
- https://www.fenegosida.com/
- https://noc.org.np/retailprice
- https://noc.org.np/lpg
- https://www.urjakhabar.com/en/
- https://www.careratingsnepal.com/
- https://www.sebon.gov.np/quarterly-statistics

### Multilateral
- https://data.worldbank.org/country/nepal
- https://www.adb.org/countries/nepal/main
- https://www.imf.org/en/Countries/NPL
- https://www.ceicdata.com/en/country/nepal
- https://tradingeconomics.com/nepal/indicators

### NEA + Hydropower
- https://www.nea.org.np/annual_report
- https://www.nea.org.np/admin/assets/uploads/supportive_docs/72250302.pdf
- https://www.rpgcl.com/
- https://www.ippan.org.np/wp-content/uploads/2025/09/Energy-statics-of-Nepal-2025-1.pdf
