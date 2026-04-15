# Resources Library — NEPSE Research Lab

> **For: exploration teams and anyone joining the lab.**
> **Purpose: the curated list of every URL, paper, tool, and data source we've used.**
> **Use this INSTEAD of starting a fresh web search. If it's here, we've already vetted it.**
>
> **Important note on coordination:** The main team (Juliet + Romeo + Ishwor) is ALSO doing research,
> web searches, and agent-based exploration in parallel with you. We are not passive. If you find a
> new resource not in this file, document it in your completion report so we can add it. If you
> find contradictions between this file and current reality, flag them.

Last updated: 2026-04-10 by Juliet.

---

## 1. Nepal Regulators and Official Data

### Nepal Rastra Bank (NRB)
- **NRB Forex API (JSON):** https://www.nrb.org.np/api-docs-v1/ — the ONLY structured JSON endpoint NRB offers
- **NRB AJAX endpoint for rate series:** `https://www.nrb.org.np/wp-admin/admin-ajax.php` (POST with `action=get_rates`, `rate_type`, `rate_id`)
  - Interbank Rate Daily: `rate_id=62`, `rate_type=SHORT_TERM_RATE`
  - Repo Rate: `rate_id=63`, `rate_type=SHORT_TERM_RATE`
- **NRB Current Macroeconomic Situation:** https://www.nrb.org.np/category/current-macroeconomic-situation/
- **NRB Monthly Statistics Archive:** https://www.nrb.org.np/category/monthly-statistics/
- **NRB Quarterly Interest Rate:** https://www.nrb.org.np/category/quarterly-interest-rate/
- **NRB Economic Bulletin:** https://www.nrb.org.np/category/economic-bulletin/
- **NRB Financial Sector Database:** https://www.nrb.org.np/database-on-nepalese-economy/financial-sector/
- **NRB Public Debt Management — T-bill Notices:** https://obss.nrb.org.np/pd/tbnotices.php
- **NRB Public Debt Ownership Structure (monthly PDF):** https://www.nrb.org.np/pdm/ownership-structure-of-government-securities-2080-05-bhadra/
- **NRB Public Debt Archive:** https://www.nrb.org.np/category/public-debt-operations-archive/
- **NRB Annual Bank Supervision Report 2024:** https://www.nrb.org.np/contents/uploads/2025/03/Annual-Bank-Supervision-Report-2024-3.pdf
- **NRB Financial Stability Report 2022/23:** https://www.nrb.org.np/contents/uploads/2024/06/FSR-2022_23.pdf
- **NRB Monetary Policy FY 2025/26 PDF:** https://www.nrb.org.np/contents/uploads/2025/08/Monetary-policy-in-English-2025_26.pdf
- **NRB Investing in Shares of Commercial Banks:** https://www.nrb.org.np/red/no_14investing_in_shares_of_commercial_banks/

### SEBON (Securities Board of Nepal)
- **SEBON main site:** https://www.sebon.gov.np/
- **SEBON IPO Approved:** https://www.sebon.gov.np/ipo-approved
- **SEBON IPO Pipeline:** https://www.sebon.gov.np/ipo-pipeline
- **SEBON Quarterly Statistics:** https://www.sebon.gov.np/quarterly-statistics
- **SEBON Stock Brokers List:** https://www.sebon.gov.np/intermediaries/stock-brokers
- **SEBON Credit Rating Intermediaries:** https://sebon.gov.np/intermediaries/credit-ratings
- **SEBON Annual Reports:** https://www.sebon.gov.np/annual-report

### CDSC (CDS and Clearing Limited)
- **CDSC main:** https://cdsc.com.np/
- **CDSC Lock-in Period:** https://cdsc.com.np/lockin
- **CDSC Settlement Procedure:** https://cdsc.com.np/cmsettlementprocedure

### NEPSE
- **NEPSE official:** https://nepalstock.com/
- **NEPSE Floorsheet:** https://www.nepalstock.com/floorsheet
- **NEPSE Indices:** https://nepalstock.com/indices
- **NEPSE Events / Notifications:** https://www.nepalstock.com/events

### Other Nepal Regulatory / Government
- **Ministry of Finance:** https://www.mof.gov.np/
- **Financial Comptroller General Office (FCGO):** https://fcgo.gov.np/
- **Investment Board Nepal (IBN):** https://ibn.gov.np/
- **Department of Industry (DoI):** https://www.doind.gov.np/industrial-statistics
- **Department of Mines and Geology:** http://dmgnepal.gov.np/en
- **Ministry of Energy, Water Resources and Irrigation:** https://moewri.gov.np/
- **Office of the Company Registrar:** https://ocr.gov.np/
- **Inland Revenue Department:** https://ird.gov.np/
- **National Statistics Office:** https://nsonepal.gov.np/
- **NSO data portal:** https://data.nsonepal.gov.np/
- **Nepal Insurance Authority stats:** https://nia.gov.np/stats
- **Nepal Telecommunications Authority:** https://www.nta.gov.np/
- **Immigration Department arrival/departure:** https://www.immigration.gov.np/en/page/arrival-departure-report
- **PPMO (procurement) bolpatra:** https://bolpatra.gov.np/egp/
- **Department of Hydrology and Meteorology (DHM):** https://www.dhm.gov.np/
- **DHM Real-Time Streamflow:** https://dhm.gov.np/hydrology/realtime-stream
- **Department of Customs:** http://customs.gov.np/
- **Nepal Tourism Board trade updates:** https://trade.ntb.gov.np/

### Power and Hydropower
- **Nepal Electricity Authority (NEA):** https://www.nea.org.np/
- **NEA Annual Reports:** https://www.nea.org.np/annual_report
- **NEA PPA List PDF:** https://www.nea.org.np/admin/assets/uploads/supportive_docs/72250302.pdf
- **Rastriya Prasaran Grid Company:** https://www.rpgcl.com/

---

## 2. Nepal Practitioner Sites (Data and Analytics)

### Primary aggregators
- **ShareSansar:** https://www.sharesansar.com/
- **ShareSansar Top Brokers:** https://www.sharesansar.com/top-brokers
- **ShareSansar Proposed Dividend:** https://www.sharesansar.com/proposed-dividend
- **ShareSansar Index History:** https://www.sharesansar.com/index-history-data
- **ShareSansar Right Adjustment Calculator:** https://www.sharesansar.com/right-adjustment-price-calculator
- **ShareSansar ICRA Rating Mirror:** https://www.sharesansar.com/icra-rating
- **MeroLagani:** https://merolagani.com/
- **MeroLagani Floorsheet:** https://www.merolagani.com/Floorsheet.aspx
- **MeroLagani Indices:** https://merolagani.com/Indices.aspx
- **NepseAlpha:** https://nepsealpha.com/
- **NepseAlpha Floorsheet Analysis:** https://nepsealpha.com/floorsheet-analysis
- **NepseAlpha Floorsheet History:** https://nepsealpha.com/floorsheet-history
- **NepseAlpha Broker Holdings:** https://nepsealpha.com/broker-holding
- **NepseAlpha Broker Holding Changes:** https://nepsealpha.com/broker-holding-changes
- **NepseAlpha Seasonality:** https://nepsealpha.com/seasonality
- **NepseAlpha Investment Calendar Dividends:** https://nepsealpha.com/investment-calandar/dividend
- **NepseAlpha Promoter Lock-In Tracker:** https://nepsealpha.com/promoter-lock-in
- **NepseAlpha Hydropower Production Indicator:** https://nepsealpha.com/indicators/hydropower-production
- **ShareHub Nepal:** https://sharehubnepal.com/
- **ShareHub Broker Dashboard:** https://sharehubnepal.com/broker/dashboard
- **Chukul Top Broker Top Holding:** https://chukul.com/top-broker-top-holding
- **NEPSE Stock upcoming lock-in unlock:** https://nepsestock.com/upcoming-lock-in-unlock-in-nepal-stock-market
- **NEPSE Broker Analysis:** https://nepsebrokeranalysis.com/

### Nepal analysis blogs
- **Nepalytix:** https://nepalytix.com/
- **Nepalytix broker tracking:** https://nepalytix.com/blog/how-broker-behavior-shapes-nepse-spotting-smart-moves-before-the-crowd
- **Nepalytix floorsheet guide:** https://nepalytix.com/blog/how-to-read-nepse-floor-sheets-a-complete-guide-for-investors
- **Nepalytix circuit breakers:** https://nepalytix.com/blog/circuit-breakers-in-nepse-how-upper-and-lower-limits-protect-and-trap-traders
- **Nepalytix Dashain effect:** https://nepalytix.com/blog/dashain-tihar-effect-on-nepse-do-festivals-really-bring-a-stock-market-rally
- **Nepalytix remittance:** https://nepalytix.com/blog/how-remittance-inflows-shape-nepals-stock-market
- **NEPSE Trading (blog):** https://nepsetrading.com/
- **NEPSE Trading liquidity analysis:** https://nepsetrading.com/insights/nepal-stock-market-liquidity-analysis
- **NEPSE Trading smart money tracking:** https://nepsetrading.com/insights/nepse-floor-sheet-analysis-smart-money-tracking-method
- **NEPSE Trading intraday guide:** https://nepsetrading.com/insights/intraday-trading-in-nepal-strategy-risk-and-profit-guide
- **Investopaper:** https://www.investopaper.com/
- **Investopaper Hydropower Index 2007-2025:** https://www.investopaper.com/news/analysis-of-performance-of-hydropower-index-compared-to-nepse-index-2007-2025/
- **Investopaper Performance by Days of Week:** https://www.investopaper.com/news/performance-of-nepse-index-by-days-of-the-week/

### Commercial / licensed
- **SmartWealthPro MDP (only NEPSE-licensed commercial API):** https://data.smartwealthpro.com/
- **SmartWealthPro MDP Docs:** https://data.smartwealthpro.com/documentation/

### Other Nepal sources
- **UrjaKhabar (energy trade news):** https://www.urjakhabar.com/en/
- **Nepal Economic Forum:** https://nepaleconomicforum.org/
- **Bajarko Chirfar (English):** https://eng.bajarkochirfar.com/
- **Fiscal Nepal:** https://www.fiscalnepal.com/
- **Ratopati:** https://english.ratopati.com/
- **Farsight Nepal:** https://farsightnepal.com/
- **New Business Age:** https://www.newbusinessage.com/
- **Khabarhub:** https://english.khabarhub.com/
- **Nepali Times:** https://nepalitimes.com/
- **Nepal News:** https://english.nepalnews.com/

### Industry associations
- **IPPAN (Independent Power Producers Association):** https://www.ippan.org.np/
- **IPPAN Energy Statistics 2025 (Sept):** https://www.ippan.org.np/wp-content/uploads/2025/09/Energy-statics-of-Nepal-2025-1.pdf
- **IPPAN Energy Statistics 2025 (Mar):** https://www.ippan.org.np/wp-content/uploads/2025/03/Energy-Statistics-2025.pdf
- **Nepal Bankers' Association:** https://nepalbankers.com.np/
- **Development Bankers Association:** https://www.dban.com.np/
- **Nepal Microfinance Bankers' Association:** https://nmba.org.np/
- **FNCCI:** https://data.fncci.org/en/
- **CNI:** https://www.cni.org.np/
- **FENEGOSIDA daily gold/silver:** https://www.fenegosida.com/
- **Nepal Oil Corporation retail price:** https://noc.org.np/retailprice
- **Nepal Oil Corporation LPG history:** https://noc.org.np/lpg

### Credit rating
- **ICRA Nepal:** https://www.icranepal.com/
- **CareEdge Ratings Nepal:** https://www.careratingsnepal.com/

### Multilateral / international
- **World Bank Nepal:** https://data.worldbank.org/country/nepal
- **ADB Nepal:** https://www.adb.org/countries/nepal/main
- **IMF Nepal Article IV:** https://www.imf.org/en/Countries/NPL
- **CEIC Nepal (paid):** https://www.ceicdata.com/en/country/nepal
- **Trading Economics Nepal:** https://tradingeconomics.com/nepal/indicators
- **Open Data Nepal:** https://opendatanepal.com/
- **Nepal in Data:** http://nepalindata.com/
- **National Data Portal Nepal:** http://www.nationaldata.gov.np/

---

## 3. Nepal Academic Research (NEPSE-Specific)

### Foundational papers
- **Joshi & K.C. (2005) — The Nepalese Stock Market: Efficiency and Calendar Anomalies:**
  - NRB version: https://www.nrb.org.np/er-article/the-nepalese-stock-market-efficient-and-calendar-anomalies/
  - SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=743666
  - MPRA: https://mpra.ub.uni-muenchen.de/26999/
- **NRB Variance Ratio Test (2016):** https://ideas.repec.org/a/nrb/journl/v28y2016i2p61.html
- **Jha & Dhungana — Adaptive Market Hypothesis NEPSE:**
  - SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4046990
  - NECS: http://necs.org.np/wp-content/uploads/2022/03/03_Evidence-on-Presence-of-Adaptive-Market-Hypothesis-in-Nepal-Stock-Exchange.pdf
- **Dangal & Gajurel — NEPSE GARCH family:** https://www.nepjol.info/index.php/TUJ/article/view/43514
- **Bhattarai — Fundamentals of Stock Price in Nepalese Commercial Banks:** https://www.nepjol.info/index.php/irjms/article/download/27887/23026/82659
- **NRB Khatri — Macroeconomic Influence:** https://www.nrb.org.np/red/vol31-1_art3/
- **NRB Determinants of Stock Market Performance:** https://www.nrb.org.np/contents/uploads/2022/12/vol26-2_art2.pdf
- **NRB Rabindra Joshi — Effects of Dividends:** https://ideas.repec.org/a/nrb/journl/v24y2012i2p5.html
- **Pravaha — Stock Market Concentration at NEPSE:** https://nepjol.info/index.php/pravaha/article/view/57973
- **Pravaha 2024 — Month-of-year / festive effects:** https://nepjol.info/index.php/pravaha/article/download/76887/58848
- **Month-of-the-year Effects NepJOL:** https://www.nepjol.info/index.php/pycnjm/article/download/35919/28084
- **Fama-French Nepal (2016):**
  - https://file.scirp.org/Html/13-7201213_63860.htm
  - http://libra.article2submit.com/id/eprint/1474/1/ME_2016022614475393.pdf
- **KMC Journal Trading Day Effect (2024):** https://www.nepjol.info/index.php/kmcj/article/view/90651
- **Risk Behavior of Different Weekdays in NEPSE:** https://www.nepjol.info/index.php/NJS/article/view/73159
- **Day-of-the-Week Industry-Specific (Joshi SSRN):** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=927711
- **NEPSE IPO Short-Run Performance:** https://nepjol.info/index.php/jnma/article/download/62096/46883/182934
- **Sitaula et al. LSTM NEPSE prediction:** https://www.sciencedirect.com/science/article/pii/S2666827022000706
- **MDPI NEPSE direction + news headlines:** https://www.mdpi.com/2225-1146/12/2/16
- **Luitel — Nepalese Stock Market Predictive Analytics:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5030130

### Political / crisis studies
- **Effect of Major Political Change on NEPSE Volatility:** https://www.nepjol.info/index.php/njf2/article/view/92384
- **NRB Unanticipated Political Events Vol 20:** https://www.nrb.org.np/contents/uploads/2021/09/vol20_art7.pdf
- **NRB Economic Cost of General Strikes Vol 26:** https://www.nrb.org.np/contents/uploads/2022/12/vol26-1_art1.pdf
- **Stock Market's Reaction to Catastrophic Event (ACE):** https://ace.edu.np/wp-content/uploads/The-Stock-Markets-Reaction-to-Unanticipated-Catastrophic-Event.pdf
- **Evidence From Nepal Earthquake (CIRD):** https://cirdjournals.com/index.php/ajcr/article/download/337/319/802

### Market concentration / herding
- **Herding Behavior in Nepali Stock Market (NCC Journal):** https://nepjol.info/index.php/NCCJ/article/view/24746
- **Pokharel on herding (SSRN):** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3687104

### Calendar anomalies mirrors
- **ShareSansar Calendar Anomalies:** https://www.sharesansar.com/newsdetail/calendar-anomalies-how-nepse-return-varies-by-days-and-months
- **ShareSansar NEPSE sub-index seasonal trends:** https://www.sharesansar.com/newsdetail/in-depth-analysis-of-nepse-historical-data-seasonal-trends-across-sub-indices-2024-09-15

---

## 4. Global Academic — LLM in Finance & Microstructure

### "Mechanical beats LLM" papers (for L-011)
- **When Reasoning Fails (arXiv 2511.08608, Nov 2025):** https://arxiv.org/abs/2511.08608
- **StockBench (arXiv 2510.02209):** https://arxiv.org/abs/2510.02209
- **PriceSeer (arXiv 2601.06088):** https://arxiv.org/abs/2601.06088
- **Vidal — Efficacy of LLMs (SSRN 4947135):** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4947135
- **The New Quant survey (arXiv 2510.05533):** https://arxiv.org/abs/2510.05533
- **Lopez-Lira & Tang ChatGPT stocks (arXiv):** https://arxiv.org/abs/2304.07619
- **Lopez-Lira SSRN:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4412788
- **Glasserman & Lin look-ahead bias (arXiv 2309.17322):** https://arxiv.org/abs/2309.17322

### LLM calibration failure
- **KalshiBench (arXiv 2512.16030):** https://arxiv.org/html/2512.16030
- **FermiEval (arXiv 2510.26995):** https://arxiv.org/html/2510.26995
- **Verbalized Confidence (arXiv 2412.14737):** https://arxiv.org/pdf/2412.14737
- **Mind the Confidence Gap (arXiv 2502.11028):** https://arxiv.org/html/2502.11028v1

### LLM-as-feature-extractor (positive use cases)
- **Evolution of Alpha (arXiv 2505.14727):** https://arxiv.org/pdf/2505.14727
- **ChatGPT in Systematic Investing (SSRN 5680782):** https://papers.ssrn.com/sol3/Delivery.cfm/5680782.pdf
- **Pelster & Val (SSRN 4602452):** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4602452
- **From Limited Data (arXiv 2509.08140):** https://arxiv.org/abs/2509.08140
- **LLM Feature Selection for Low-Resource Markets (ScienceDirect):** https://www.sciencedirect.com/science/article/pii/S2773186325001471

### Industry perspective
- **Two Sigma 2026 Outlook Part I:** https://www.twosigma.com/articles/ai-in-investment-management-2026-outlook-part-i/
- **Two Sigma 2026 Outlook Part II:** https://www.twosigma.com/articles/ai-in-investment-management-2026-outlook-part-ii/
- **Institutional Investor — AI knows nothing about investing:** https://www.institutionalinvestor.com/article/2bswlvepw2hmezaphmcxs/opinion/the-most-powerful-artificial-intelligence-knows-nothing-about-investing-thats-perfectly-okay
- **Digital Finance — GenAI and quants:** https://www.digfingroup.com/genai-quants/

### Broker-identified order flow (for broker reputation work)
- **Linnainmaa & Saar (2012) — Lack of Anonymity and Inference from Order Flow:**
  - SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1543298
  - NY Fed: https://www.newyorkfed.org/medialibrary/media/research/conference/2010/cb/LinnainmaaSaar20101.pdf
- **Duong, Lajbcygier, Lu, Vu (2018) — Anonymity and Price Efficiency (SSRN):** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3197485
- **Comerton-Forde, Frino, Mollica — Paris, Tokyo, Korea anonymity:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=695602
- **Foucault, Moinas, Theissen — Does Anonymity Matter:** https://www.tse-fr.eu/sites/default/files/medias/doc/by/moinas/moinas_foucault_theissen.pdf
- **Grinblatt, Keloharju, Linnainmaa — IQ Trading Behavior (SSRN):** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1364014
- **Choi — Informed Trading and Expected Returns (Yale):** https://spinup-000d1a-wp-offload-media.s3.amazonaws.com/faculty/wp-content/uploads/sites/27/2019/06/informed.pdf
- **Informed Trading and Expected Returns (NBER Digest):** https://www.nber.org/digest/may13/informed-trading-and-expected-returns
- **Kaniel, Saar, Titman — Individual Investor Trading:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2008.01316.x
- **Boehmer, Jones, Zhang, Zhang (BJZZ) — Tracking Retail Investor Activity:** https://onlinelibrary.wiley.com/doi/10.1111/jofi.13033
- **Revisiting BJZZ (decay warning) arXiv 2403.17095:** https://arxiv.org/html/2403.17095v1
- **Revisiting BJZZ Springer FMPM:** https://link.springer.com/article/10.1007/s11408-025-00487-4
- **Barber, Lee, Liu, Odean — Cross-Section of Speculator Skill (Taiwan):** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=529063
- **Chordia & Subrahmanyam — Order Imbalance and Individual Stock Returns:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X03001752
- **Schultz — Who Makes Markets:** https://www.acsu.buffalo.edu/~keechung/MGF743/Readings/H4%20Who%20makes%20markets.pdf

### PIN measure (Probability of Informed Trading)
- **PIN measure (frds reference):** https://frds.io/measures/probability_of_informed_trading/
- **PIN R Journal 2013:** https://journal.r-project.org/archive/2013/RJ-2013-008/RJ-2013-008.pdf
- **PINstimation R package (R Journal 2023):** https://journal.r-project.org/articles/RJ-2023-044/
- **Does PIN measure information? Six emerging markets:** https://www.sciencedirect.com/science/article/abs/pii/S1059056015000659
- **Boehmer, Grammig, Theissen — PIN trade misclassification:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=887221

### Methodology
- **Backtesting — Harvey & Liu (SSRN):** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2345489
- **Statistical Overfitting (Bailey et al.):** https://sdm.lbl.gov/oapapers/ssrn-id2507040-bailey.pdf
- **Walk-Forward Permutation Tests (Medium):** https://medium.com/@alex.mountain.pa/how-i-develop-trading-strategies-permutation-tests-and-trading-strategy-development-with-python-5e8c50d0b256
- **Walk-Forward Validation for Microstructure (arXiv):** https://arxiv.org/html/2512.12924v1

### Adjacent emerging market microstructure
- **Bangladesh DSE AMH & Momentum (Hossain et al.):** https://doi.org/10.1080/23322039.2019.1650441
- **Mongolia MSE study:** https://ieeca.org/journal/index.php/JEECAR/article/download/1834/637/9901

---

## 5. Open-Source NEPSE Tools and Datasets

### Actively maintained Python libraries
- **polymorphisma/nepse_scraper (de-facto standard):** https://github.com/polymorphisma/nepse_scraper
- **nepse-scraper PyPI:** https://pypi.org/project/nepse-scraper/
- **basic-bgnr/NepseUnofficialApi:** https://github.com/basic-bgnr/NepseUnofficialApi
- **surajrimal07/NepseAPI-Unofficial (with MCP):** https://github.com/surajrimal07/NepseAPI-Unofficial
- **CaffeineDuck/nepse-api:** https://github.com/CaffeineDuck/nepse-api
- **nepse-api docs:** https://nepse-api.readthedocs.io/

### Floorsheet scrapers
- **suyogdahal/nepse-data:** https://github.com/suyogdahal/nepse-data
- **sbmagar13/sharesansar_datascrape:** https://github.com/sbmagar13/sharesansar_datascrape
- **OmitNomis/ShareSansarScraper:** https://github.com/OmitNomis/ShareSansarScraper
- **OmitNomis archive (downloadable):** https://omitnomis.github.io/ShareSansarScraper/
- **fuunshi/ShareSansarDataScrape:** https://github.com/fuunshi/ShareSansarDataScrape

### Analysis projects (mostly low-quality, for reference)
- **nlethetech/nepse-quant-terminal (closest comparable to our lab):** https://github.com/nlethetech/nepse-quant-terminal
- **pratyushmishra19/Nepse_floorsheet_analysis:** https://github.com/pratyushmishra19/Nepse_floorsheet_analysis
- **tejshahi/StockPricePrediction-NEPSE-:** https://github.com/tejshahi/StockPricePrediction-NEPSE-

### Kaggle datasets
- **shivaharisubedi/nepse-floorsheet:** https://www.kaggle.com/datasets/shivaharisubedi/nepse-floorsheet
- **sagyamthapa/nepali-stock-market-form-2012-to-2020:** https://www.kaggle.com/datasets/sagyamthapa/nepali-stock-market-form-2012-to-2020-till-march
- **qramkrishna/nepal-stock-exchange-data:** https://www.kaggle.com/datasets/qramkrishna/nepal-stock-exchange-data

### MCP servers
- **nepse-mcp-servers GitHub topic:** https://github.com/topics/nepse-mcp-servers
- **razaanstha/nepse-mcp-server:** https://github.com/razaanstha/nepse-mcp-server

---

## 6. Legal / Regulatory References (For Festival, AGM, Tax Cycle Work)

- **Companies Act 2063 Section 76 (AGM within 6 months of FY-end):** https://actnepal.com/en/section/76/0/section-76-annual-general-meeting-of-companies-act-2063
- **Companies Act 2063 Section 182 (dividend, 5-year unclaimed rule):** https://actnepal.com/en/section/182/0/section-182-dividend-of-companies-act-2063
- **Nepal Labor Act Dashain bonus guide:** https://www.nepallawyer.com/blog/dashain-bonus-in-nepal
- **Festival Allowance under Nepal Labor Law:** https://sushilparajuli.com/festival-allowance-in-nepal-under-labor-law/
- **AGM Process in Nepal (Tax Consultant Nepal):** https://taxconsultantnepal.com/annual-general-meeting-agm-process-in-nepal/
- **Conducting AGMs of Public Companies:** https://nepallaws.com/conducting-annual-general-meetings-agms-of-public-companies-in-nepal/
- **Tax on Dividends in Nepal:** https://taxconsultantnepal.com/tax-on-dividends-in-nepal/
- **Hydropower Taxation Nepal:** https://himalihydrofund.com.np/taxation-system-for-hydropower-companies-in-nepal/
- **Nepal Tax Fact 2024/25 (Baker Tilly):** https://bakertilly.com.np/storage/download/1718620336_Tax_Fact_2024-25.pdf

---

## 7. Political Shocks Catalog References

### 2015 Earthquake
- **Gorkha earthquake resumption news (Moneylife):** https://www.moneylife.in/article/nepal-stock-exchange-resumes-operations-after-one-month/41895.html
- **Nepse plunges on opening day post-quake (Kathmandu Post):** https://kathmandupost.ekantipur.com/news/2015-05-25/nepse-plunges-on-opening-day.html

### 2015-16 India Blockade
- **2015-16 Nepal blockade (Wikipedia):** https://en.wikipedia.org/wiki/2015%E2%80%9316_Nepal_blockade

### 2020 COVID
- **Stock Market Performance during Covid-19 (Adhyayan Journal):** https://nepjol.info/index.php/aj/article/view/57346

### 2020 Parliament Dissolution
- **2020-21 Dissolution (Wikipedia):** https://en.wikipedia.org/wiki/2020%E2%80%9321_dissolution_and_reinstatement_of_the_Parliament_of_Nepal

### 2021 Sarbottam / NEPSE CEO Insider Trading
- **Nepse CEO Saud resignation (myRepublica):** https://myrepublica.nagariknetwork.com/news/nepse-ceo-saud-tenders-resignation-amid-accusation-of-his-involvement-in-insider-trading/
- **Insider trading scandal (Kathmandu Post):** https://kathmandupost.com/money/2021/09/05/securities-board-of-nepal-caught-in-yet-another-insider-trading-scandal
- **Nepse plunges 108.26 (OnlineKhabar):** https://english.onlinekhabar.com/nepse-index-plunges-108-26.html

### 2022 MCC Compact
- **Progress in MCC lifts hydro shares (myRepublica):** https://myrepublica.nagariknetwork.com/news/progress-in-mcc-compact-ratification-lifts-share-prices-of-hydropower-companies-market-index-rises-by-25-41-points

### 2025 Pro-Monarchy Protests
- **2025 Nepal pro-monarchy protests (Wikipedia):** https://en.wikipedia.org/wiki/2025_Nepalese_pro-monarchy_protests

### Sept 2025 Gen Z Protest Crash ⭐ (missing from our event tables)
- **2025 Nepal Gen Z protests (Wikipedia):** https://en.wikipedia.org/wiki/2025_Nepalese_Gen_Z_protests
- **Gen Z fallout NEPSE -160.33 (myRepublica):** https://myrepublica.nagariknetwork.com/news/gen-z-protest-fallout-stock-market-closes-nepse-drops-16033-points-46-94.html
- **NEPSE plunges 160 trading halted (Kathmandu Post):** https://kathmandupost.com/money/2025/09/18/nepse-plunges-160-points-trading-halted
- **6% crash Rs 268 kharba wiped (ShareSansar):** https://www.sharesansar.com/newsdetail/nepse-suffers-6-crash-investment-worth-rs-268-kharba-wiped-out-in-minutes-2025-09-18

### March 2026 Balen Shah election / April 2026 Wagle crashes
- **Balen Shah 40th PM (Kathmandu Post):** https://kathmandupost.com/politics/2026/03/28/balendra-shah-becomes-40th-prime-minister-of-nepal
- **2026 Nepal general election (Wikipedia):** https://en.wikipedia.org/wiki/2026_Nepalese_general_election
- **NEPSE -74.73 Apr 1 (Kathmandu Post):** https://kathmandupost.com/money/2026/04/01/nepse-plunges-74-73-points-as-all-sub-indices-decline
- **NEPSE -105.50 Apr 5 (Kathmandu Post):** https://kathmandupost.com/money/2026/04/05/nepse-plunges-105-50-points-as-all-sub-indices-decline
- **Wagle meets brokers (ShareSansar):** https://www.sharesansar.com/newsdetail/finance-minister-dr-swarnim-wagle-holds-key-meeting-with-stock-brokers-to-address-market-concerns-2026-04-06
- **Shanker Group money laundering (Kathmandu Post):** https://kathmandupost.com/national/2026/04/05/money-laundering-probe-pulls-nepal-s-shanker-group-into-spotlight
- **Rs 3.73B fraud investigation (Kathmandu Post):** https://kathmandupost.com/money/2026/04/09/inside-the-rs-3-73-billion-fraud-investigation-shaking-nepal-s-business-elite
- **Deuba arrest warrants (Kathmandu Post):** https://kathmandupost.com/national/2026/04/08/arrest-warrants-issued-against-deuba-couple-in-money-laundering-probe

### NRB Margin Lending Changes 2025
- **Fiscal Nepal Rs 250M unified directive:** https://www.fiscalnepal.com/2025/07/17/21401/nrb-revises-unified-directive-share-loan-limit-raised-to-rs-250-mln-eases-credit-for-housebuyers/
- **ShareSansar CRR + risk weight cut:** https://www.sharesansar.com/newsdetail/bfis-now-required-to-maintain-90-of-crr-daily-with-nepal-rastra-bank-risk-weight-on-share-backed-loans-revised-to-100-2025-05-28
- **Bajarko Chirfar single-customer limit lifted:** https://eng.bajarkochirfar.com/2025/10/15/nrb-lifts-single-customer-margin-loan-limit/
- **Nepal Monitor share-backed lending ramp:** https://nepalmonitor.com/2025/08/25/commercial-banks-ramp-up-share-backed-lending-after-nepal-rastra-banks-policy-shift/
- **ictframe NEPSE Trends 2082:** https://ictframe.com/nepse-trends-2082/

### Regulatory enforcement / broker suspensions
- **Bhrikuti Broker #55 Suspension (Bajarko Chirfar):** https://eng.bajarkochirfar.com/2026/04/09/bhrikuti-stock-brokings-license-suspended-rs-5-11-billion-owed-to-investors/
- **Insider trading taints Nepal capital market (Nepali Times):** https://nepalitimes.com/here-now/insider-trading-taints-nepal-capital-market
- **SEBON list of 51 irregular companies:** https://english.khabarhub.com/2021/15/191064/

---

## 8. Hydropower-Specific References

### PPA economics
- **Energy Ministry fixes PPA rates (Kathmandu Post 2017):** https://kathmandupost.com/money/2017/01/10/energy-ministry-fixes-power-purchase-rates
- **PPA Flash Alert (PKF Trunco):** https://pkf.trunco.com.np/files/publications/1708424392_03_2024_Flash%20Alert%20on%20NEA's%20Decision%20to%20sign%20PPAs%20with%20small%20Hydropower%20Projects%20.pdf
- **Deconstructing Storage Hydro PPA Pricing (blog):** https://santoshthapa123.blogspot.com/2025/06/deconstructing-storage-hydro-ppa.html

### Take-and-pay crisis 2025
- **Nepal's energy sector rocked by take-and-pay (Kathmandu Post):** https://kathmandupost.com/national/2025/06/05/nepal-s-energy-sector-rocked-by-take-and-pay-budget-policy
- **IPAN Urges Scrap (Fiscal Nepal):** https://www.fiscalnepal.com/2025/06/04/20622/ipan-urges-government-to-scrap-take-and-pay-policy-in-ppa-energy-minister-khadka-expresses-concerns/
- **Rs 109bn at risk (Annapurna Express):** https://theannapurnaexpress.com/story/55401/

### Generation seasonality
- **Evolution of hydropower sector (ScienceDirect):** https://www.sciencedirect.com/science/article/pii/S2405844024071706
- **Climatic parameters on hydropower (PMC):** https://pmc.ncbi.nlm.nih.gov/articles/PMC9792739/
- **Khimti River Basin climate change (Springer):** https://link.springer.com/article/10.1007/s42452-025-07304-7
- **Winter Dry Spell Drains Hydropower:** https://nepalconnect.world/winter-dry-spell-drains-hydropower/

### Export dynamics
- **Nepal Rs 18.2bn electricity exports (Rising Nepal):** https://risingnepaldaily.com/news/73684
- **Dhalkebar-Muzaffarpur 1000 MW (Fiscal Nepal):** https://www.fiscalnepal.com/2025/02/12/19493/nepal-india-power-trade-boosted-dhalkebar-muzaffarpur-line-capacity-increased-to-1000-mw/

### Verified hydropower AGM examples (for Strategy C mechanism)
- **Chilime 12% FY 2080/81 (ShareSansar):** https://www.sharesansar.com/newsdetail/chilime-hydropower-proposes-12-dividend-for-fy-208081-calls-agm-on-poush-28-2024-12-17
- **Sanima Mai 10.52% (ShareSansar):** https://www.sharesansar.com/newsdetail/sanima-mai-hydropower-proposes-1052-dividend-for-fy-208081-calls-agm-on-poush-28-2024-12-10
- **HIDCL 5.25% (ShareSansar):** https://www.sharesansar.com/newsdetail/hydroelectricity-investment-and-development-company-proposes-525-cash-dividend-calls-agm-on-poush-24-2024-12-11
- **Butwal 32nd AGM (ShareSansar):** https://www.sharesansar.com/newsdetail/butwal-power-company-limited-holds-32nd-annual-general-meeting-approves-dividend-2025-01-13

### Project pipeline
- **Investopaper Top Hydropower Companies:** https://www.investopaper.com/news/top-hydropower-companies-listed-in-nepal-stock-exchange-based-on-market-cap/
- **Investopaper Electricity Production MW:** https://www.investopaper.com/news/electricity-production-in-mw-by-hydropower-companies-listed-in-nepse/

---

## 9. Structural Quirks References

### Circuit breakers
- **Understanding NEPSE Circuit Breakers (NEPSE Trading):** https://nepsetrading.com/blog/understanding-nepse-circuit-breakers-how-automatic-trading-halts-protect-the-market
- **New Circuit Breaker Rules 2020 (FirdiEye):** https://firdieye.blogspot.com/2020/05/new-circuit-breaker-rules-nepse.html
- **Momentum Stocks Five Circuits (NEPSE Trading):** https://nepsetrading.com/insights/momentum-stocks-on-nepse-five-circuits-and-what-comes-next-march-31-2026

### Right share deviation from textbook
- **Impact of Right Share Movement TU elibrary:** https://elibrary.tucl.edu.np/JQ99OgQIizUxyjI9nB0on9OyLkqsGIf4/api/core/bitstreams/f65882db-bb1b-4c8c-ac0f-be1b5a80b119/content
- **What is not right about rights shares (Kathmandu Post):** https://kathmandupost.com/columns/2021/11/18/what-is-not-right-about-rights-shares

### Reliance Spinning Mills "lost IPO"
- **Listing in limbo (ShareSansar):** https://www.sharesansar.com/newsdetail/reliance-spinning-mills-share-listing-in-limbo-investors-hit-hard-2026-02-12
- **Listed with opening band (ShareSansar):** https://www.sharesansar.com/newsdetail/ipo-shares-of-reliance-spinning-mills-now-listed-on-nepse-what-are-the-opening-ranges-2026-02-13

### Bank cross-holdings
- **NRB Forces Microfinance Cross-holding Unwinds (ShareSansar):** https://www.sharesansar.com/newsdetail/nrb-forces-microfinance-companies-with-more-than-10-crossholding-of-bfis-to-take-merger-acquisition-route-2022-01-03
- **BAFIA Separate Business from Banking (NEPSE Trading):** https://nepsetrading.com/blog/bafia-pushes-to-separate-business-from-banking-seven-dozen-commercial-bank-founders-at-risk

---

## 10. Sentiment / Social Sources (For Contrarian Work)

### Nepal finance communities
- **r/NepalStock subreddit stats:** https://subredditstats.com/r/nepalstock
- **Facebook Share Market Forum:** https://www.facebook.com/groups/sharemarketdiscussion/
- **Facebook Nepal Stock Forum:** https://www.facebook.com/groups/nepalstocks/
- **Telegram Nepal Stock Exchange channel:** https://t.me/NepalStockExchange
- **Share Durbar YouTube:** https://sharedurbar.com.np/about/
- **Sajha.com stocks thread:** https://sajha.com/sajha/html/index.cfm?threadid=131316

### Demat / investor statistics
- **6.55M demat accounts (NEPSE Trading):** https://nepsetrading.com/blog/demat-accounts-reach-655-million-mero-share-users-climb-to-559-million
- **3M demat accounts baseline (ShareSansar 2021):** https://www.sharesansar.com/newsdetail/there-are-3061668-demat-accounts-in-the-country-only-about-20-of-them-invest-in-the-secondary-market-actively-2021-03-05

### Nepal sentiment warnings (regulatory acknowledgment)
- **NEPSE warns against social media stock content:** https://english.khabarhub.com/2025/08/489790/
- **How influencers manipulate Nepal share market (OnlineKhabar):** https://english.onlinekhabar.com/how-influencers-are-manipulating-the-nepal-share-market.html
- **Nepse AI scam Rs 800M (TechPana):** https://techpana.com/2025/152435/nepse-ai-scam-cybersecurity-expert-reveals-rs-800-million-theft
- **Retail investors ignoring risk (Nepal Economic Forum):** https://nepaleconomicforum.org/are-retail-investors-ignoring-risk-in-nepals-bull-market/

### Global analogs for sentiment work
- **Sports Sentiment and Stock Returns (Edmans, Garcia, Norli):** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=677103
- **Air Pollution and Investor Behavior (Heyes, Neidell, Saberian NBER):** https://www.nber.org/papers/w22753
- **PM2.5 and daily stock returns 47 cities (Nature Sci Reports):** https://www.nature.com/articles/s41598-021-88041-w

### Nepal Nepali NLP
- **IOST-ASCOL/nepali-datasets (GitHub):** https://github.com/IOST-ASCOL/nepali-datasets
- **Nepali sentiment hybrid DL (Springer):** https://link.springer.com/article/10.1007/s13278-025-01508-w

---

## How To Use This File

1. **Before running a new web search, check this file first.** If we've already vetted the source, cite it from here.
2. **When you find a new resource not in this file, document it in your completion report.** The main team will add it during integration.
3. **When a URL goes dead, flag it in your completion report.** Link rot is real.
4. **Do NOT modify this file directly from a side-quest session.** Treat it as canonical. Updates happen through the main team during integration.

## Note On Parallel Work

The main team (Juliet, Romeo, Ishwor) is **also actively running research agents and web searches in parallel with you.** We are not dormant. If you see a signal that looks like a new finding we haven't documented, assume we might be working on the same thing independently. Write it up thoroughly in your completion report so the main team can reconcile.

## Provenance

This file was assembled from the master source lists at the end of each research file in:
- `market-gist/docs/resources/web-research-2026-04-10/01_*.md` through `06_*.md` (conventional wave)
- `market-gist/docs/resources/web-research-2026-04-10/10_*.md` through `14_*.md` (unconventional wave)
- `market-gist/docs/resources/web-research-2026-04-10/15_broker_reputation_deep_dive.md` (deep single-question research)

If a URL is in one of those source files but not here, it's because I judged it redundant or too narrow. You can still drill into the source files for full depth.
