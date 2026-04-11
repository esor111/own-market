# Thread 6: NRB Margin Lending Impact + Nepal Retail Sentiment

## Two Questions in One Thread

1. What was the measured impact of the NRB margin lending rule changes (May 2025 onward) on NEPSE? We need this to patch experiment 03.
2. Where does Nepal retail stock sentiment live online and can it be measured? We need this to evaluate a contrarian sentiment experiment.

---

## TOPIC 1: NRB Margin Lending Impact

### The Policy Sequence (Confirmed Timeline)

Up to 8 candidate event dates surfaced. **Not all 8 are truly new** — some overlap existing rows in `policy_events.csv`, some collapse together as a single regime shift, and some are SEBON/NEPSE events (not NRB) that may not belong in an NRB-named experiment. The honest count of TRULY NEW events worth patching is **3-4** after dedup. See `proposal_experiment_03_patch.md` for the corrected list. The 8 candidates are listed below for completeness:

| Date | Event | Source |
|---|---|---|
| **2025-05-28** | Risk weight on share-backed loans cut from 125% to 100%; CRR daily maintenance raised to 90% (immediately after new Governor Bishwanath Paudel took office) | [ShareSansar](https://www.sharesansar.com/newsdetail/bfis-now-required-to-maintain-90-of-crr-daily-with-nepal-rastra-bank-risk-weight-on-share-backed-loans-revised-to-100-2025-05-28), [Investopaper](https://www.investopaper.com/news/nepal-rastra-bank-reduces-risk-weight-on-share-loans-to-100-following-new-governors-appointment/) |
| **2025-07-11** | Monetary Policy FY 2082/83 released: individual margin loan cap lifted from Rs 150M to Rs 250M; bank rate -0.5pp to 6%; policy rate 5% → 4.5%; SDF 3% → 2.75% | [NRB Monetary Policy PDF](https://www.nrb.org.np/contents/uploads/2025/08/Monetary-policy-in-English-2025_26.pdf), [Nepal Economic Forum](https://nepaleconomicforum.org/key-highlights-of-the-monetary-policy-for-fy-2025-26-ad-2082-83-bs/) |
| **2025-07-17** | NRB revised unified directive operationalizes Rs 250M cap; also eases housing credit | [Fiscal Nepal](https://www.fiscalnepal.com/2025/07/17/21401/nrb-revises-unified-directive-share-loan-limit-raised-to-rs-250-mln-eases-credit-for-housebuyers/), [Bajarko Chirfar](https://eng.bajarkochirfar.com/2025/07/17/nepal-rastra-bank-margin-loan-home-loan-limit-2082/) |
| **2025-10-15** | NRB lifts single-customer margin loan limit; BFIs can mobilize up to 40% of primary capital via margin lending, with single-stock cap 10% of primary capital | [Bajarko Chirfar](https://eng.bajarkochirfar.com/2025/10/15/nrb-lifts-single-customer-margin-loan-limit/), [Merolagani](https://eng.merolagani.com/NewsDetail.aspx?newsID=34295) |
| **2026-02-10** | SEBON Margin Trading Facility Directive — broker-originated margin with 30% initial / 20% maintenance margin (separate from bank margin lending) | [Kathmandu Post](https://kathmandupost.com/money/2026/02/10/nepal-s-share-market-faces-unprecedented-lockdown-as-regulators-battle-industry-over-trading-rules), [Bajarko Chirfar](https://eng.bajarkochirfar.com/2026/02/16/margin-trading-facility-up-to-2-crores-by-naasa-securities/) |
| **2026-03-26** | NEPSE Margin Trading Procedure 2082 passed, 123 eligible companies listed | [Bajarko Chirfar](https://eng.bajarkochirfar.com/2026/03/26/nepse-opens-the-way-for-margin-trading-procedure-2082-passed-now-the-way-to-buy-shares-by-paying-30-percent-is-open/) |
| **2026-04-01** | Finance minister speech causes NEPSE -2.62% (-74.73 points) | [Kathmandu Post](https://kathmandupost.com/money/2026/04/01/nepse-plunges-74-73-points-as-all-sub-indices-decline) |
| **2026-04-05** | Finance minister speech causes NEPSE -3.79% (-105.50 points) | [Kathmandu Post](https://kathmandupost.com/money/2026/04/05/nepse-plunges-105-50-points-as-all-sub-indices-decline) |

### Measured Impact on NEPSE

**Immediate market reaction to July 11 monetary policy:**
- **2025-07-17** (first trading day of FY 2025/26): NEPSE +2.71% (+75.84 pts) to 2,870.63 — explicitly attributed to monetary policy
- **2025-07-21–25:** Five-day winning streak, cumulative +112 pts to 2,982.64
- **2025-07-22:** Record turnover Rs 20 billion
- **2025-08-27:** NEPSE +~2%, banking +1.38%, hydropower +1.85%
- **2025-11-23:** NEPSE crosses 2,600 with turnover >Rs 6 billion

Sources:
- Kathmandu Post 2025-07-13: https://kathmandupost.com/money/2025/07/13/nepse-jumps-29-points-as-turnover-hits-rs11-41-billion
- New Business Age: https://www.newbusinessage.com/news/44694/nepse-soars-271-as-fy-202526-begins-turnover-crosses-rs-1659-billion/
- Khabarhub: https://english.khabarhub.com/2025/25/487400/
- Kathmandu Post 2025-07-22: https://kathmandupost.com/money/2025/07/22/nepse-jumps-80-97-points-turnover-hits-rs20-97-billion
- Kathmandu Post 2025-08-27: https://kathmandupost.com/money/2025/08/27/nepse-index-jumps-nearly-2-percent-as-turnover-crosses-rs7-68-billion

### Share-Backed Lending Volume (The Headline Number)

| Period | Value | YoY Change |
|---|---|---|
| FY 2080/81 (2023/24) | Rs 70.34 billion | baseline |
| FY 2081/82 (2024/25) full-year | **Rs 116.80 billion** | **+66.05% YoY** |
| 8 months of FY 2082/83 (mid-Feb 2026) | **Rs 156.27 billion** | +11.07% YoY again |
| Q1 FY 2082/83 alone | +37% QoQ | — |

**Single largest issuer:** Nabil Bank at Rs 16.76 billion (+46.68%)

Sources:
- Nepal Monitor: https://nepalmonitor.com/2025/08/25/commercial-banks-ramp-up-share-backed-lending-after-nepal-rastra-banks-policy-shift/
- ictframe: https://ictframe.com/nepse-trends-2082/
- NEPSE Trading liquidity analysis: https://nepsetrading.com/insights/nepal-stock-market-liquidity-analysis
- NEPSE Trading Q1 +37% report: https://nepsetrading.com/blog/share-backed-loans-surge-nearly-37-percent-in-first-quarter-reflecting-renewed-investor-activity-in-capital-market

### Full FY Performance
- **NEPSE FY 2024/25 gain: +29.77%** before stagnating

### The "Turnover Collapse Paradox" (Major Finding)

This is the most interesting unintended consequence — and the basis for a potential new experiment:

- FY 2025/26: NEPSE index up ~3% with 18 new listings
- **But turnover down ~69% YoY**
- Liquidity drying up even as price levels hold
- Central bank lending rate moved from 7.26% → 8.40%, undoing the stimulus
- Commercial banks parking money in margin lending instead of real-sector credit
- **NPLs rising:** Gross NPL ratio ~5.4%, with **9 banks above NRB's 5% ceiling**

Sources:
- NEPSE Trading liquidity analysis: https://nepsetrading.com/insights/nepal-stock-market-liquidity-analysis
- World Bank Nepal Development Update Nov 2025: https://www.worldbank.org/en/country/nepal/publication/nepaldevelopmentupdate
- B360 Nepal NPL surge: https://www.b360nepal.com/detail/10570/npl-of-commercial-banks-surge-exponentially

### Manipulation Case (Demonstrates Risk)

**December 2025: Dipendra Agrawal arrested** for multi-crore pump-and-dump (15 accounts, Clubhouse / social media coordination). The leverage made possible by expanded margin capacity enabled the manipulation.

Sources:
- Clickmandu: https://english.clickmandu.com/2025/12/5409/
- Rising Nepal: https://risingnepaldaily.com/news/65481

### April 2026 Negative Shocks

- **2026-04-01:** Finance Minister capital-market policy statement → NEPSE -2.62%
- **2026-04-05:** Same → NEPSE -3.79%

These are negative events useful for **asymmetry testing** in experiment 03 — we have only positive events currently.

Source: NEPSE Trading liquidity report 2026-04-06: https://nepsetrading.com/insights/nepal-stock-market-closing-report-2026-04-06-index-liquidity-and-smart-money-flow

### Academic / Formal Event Study Status

**No published peer-reviewed event study on the July 2025 changes.** Closest formal analysis:
- NRB working paper vol 26-2 on determinants of NEPSE (data 2000-2014, predates this policy)
- Nepal Economic Forum's "Are Retail Investors Ignoring Risk in Nepal's Bull Market?" — qualitative
- No NRB self-retrospective found publicly

**This means our experiment 03 patch would produce genuinely novel findings** because nobody in Nepal has done it rigorously.

### Implication for Experiment 03

**The corrected proposal is to add 3-4 truly new events (not 8) after a strict dedup pass.** See `proposal_experiment_03_patch.md` in this folder for the dedup'd list with rationale.

**Under L-011 patience mode, this should NOT be patched before persistence forward evidence batch-scores.** The proposal note exists so the prep work is captured for the eventual patch. Estimated time when we do patch: 1-2 hours.

---

## TOPIC 2: Nepal Retail Sentiment Infrastructure

### TL;DR

Nepal retail sentiment is **fragmented but measurable**. The signal is dominated by unverified influencers, often **actively manipulated** (per the Dipendra Agrawal case), with **no existing Nepal-specific sentiment tracker/dataset**. This is a greenfield opportunity but with significant data-quality caveats.

**For a contrarian sentiment experiment, the manipulation evidence is actually good news** — it means social sentiment is reliably wrong, which is the condition under which fading the crowd has edge.

### Platform-by-Platform Inventory

#### Reddit — Thin, Low Priority
- **r/NepalStock**: ~304 subscribers. Too small.
- **r/nepal**: 170k+ subs, general
- Verdict: Not worth the build
- URL: https://subredditstats.com/r/nepalstock

#### Facebook — The Real Hive Mind, Hard to Scrape
- **"Share Market Discussion Forum Nepal"** — https://www.facebook.com/groups/sharemarketdiscussion/
- **"Nepal Stock Discussion Forum"** — https://www.facebook.com/groups/nepalstocks/
- **Hamro Share Market** — https://www.facebook.com/hamrosharemarketofficial/
- **Sharemandu** — https://www.facebook.com/Sharemaandu/
- **Quality:** Mix of news sharing, rumor, tip-posting, pump schemes. Highest-velocity Nepal-specific sentiment on any platform.
- **Scrapable?** Public groups: partial via Graph API (rate-limited) or headless browser. Private groups: not without membership. **Hardest to scrape.**

#### Telegram — Active but Mostly Closed
- **@NepalStockExchange** — https://t.me/NepalStockExchange (public, broadcast-style)
- SEBON-flagged private "signal" channels exist with unverified tips
- Public channels scrapable via Telethon/Pyrogram. **One-day build.**

#### YouTube — Concentrated, High Audience, Easy to Scrape
- **Share Durbar (Shakti Koirala): ~65.2k subscribers** — most-cited Nepal stock YouTuber
  - URL: https://sharedurbar.com.np/about/
  - vidIQ stats: https://vidiq.com/youtube-stats/channel/UCM3G0qLnOD3NEI2ixgXUi7Q/
- **Grow More** — frequently cited as top Nepal stock channel
- **Sharemandu Official** — third in commonly-cited trio
- **Ram Hari Nepal** — live share market
- **Scrapable?** Yes — YouTube Data API v3 gives transcripts, comments, publish times, views
- **Comments on daily-update videos are a high-quality proxy for retail mood (panic vs euphoria)**

#### TikTok & Instagram — The Pump-and-Dump Zone
- **@nepse.trader, @stocknepal, @nepsenepalstock, @nepaliarthasansar** on TikTok
- Instagram: @nepal_stock_market, @nepalstockexchangenepse, @nepse.limited
- **Quality:** OnlineKhabar explicitly flagged these as locus of market manipulation. The Dipendra Agrawal case confirmed this with criminal arrest.
- TikTok: unofficial APIs (TikTokApi Python lib) work but fragile
- Source on manipulation: https://english.onlinekhabar.com/how-influencers-are-manipulating-the-nepal-share-market.html

#### Forums / Discussion Sites
- **Sajha.com** — https://sajha.com — oldest Nepali diaspora forum
  - "What stocks to buy" thread: 1,884+ posts at https://sajha.com/sajha/html/index.cfm?threadid=131316
  - Plain HTML, trivially scrapable
  - Older/NRN demographic
- **Merolagani Investor Forum** — https://merolagani.com/
- **ShareSansar comments** — Disqus-style on every news article; scrapable

#### Twitter / X — Surprisingly Thin
- No major Nepal-specific stock Twitter personalities surfaced
- **Verdict:** Not worth the build

#### Existing Sentiment Tools
- **None found.** NepseAlpha, Nepalytix, NEPSE Trading all advertise "AI signals" but they are technical/price-driven, not social-sentiment-driven.
- **No academic sentiment dataset** for Nepali financial text. Closest: general Nepali NLP corpora (IOST-ASCOL/nepali-datasets) — no finance labels.

### Feasibility Ranking

**Easiest (high leverage):**
1. **YouTube comments on Share Durbar / Grow More / Sharemandu** — YouTube Data API v3, cleanest single-channel option
2. **Sajha.com "What stocks to buy" thread** — plain HTML, long history, low volume
3. **Merolagani / ShareSansar article comments** — already tied to corporate-action news
4. **Public Telegram channels** — Telethon, one-day build

**Hard but highest-signal:**
5. **Facebook groups** — genuine hive mind; scraping is the blocker
6. **TikTok hashtag scanning** — pump-and-dump detection

**Not worth it:**
7. Reddit (~300 subs)
8. Twitter/X (no Nepal finance community)

### Signal Quality Caveat

Nepal Economic Forum's bull-market analysis explicitly warned of FOMO-driven herd behavior. SEBON has repeatedly warned against acting on Facebook/TikTok/Telegram tips. The Dipendra Agrawal case demonstrated the social feeds are **actively being manipulated**.

**For a contrarian experiment, this is good news** — it means social sentiment is likely to be very wrong very often, which is the condition under which a contrarian signal has edge. But it also means you have to be careful to identify *organic* sentiment vs planted pump content.

---

## Bottom Line

### NRB Rate Events Experiment — Patch deferred to backlog

There is no published event study on the July 2025 → April 2026 NRB changes, and the event dates are crisp and documented. The unintended-consequences narrative (turnover -69%, NPLs up, manipulation arrests) is interesting downstream context.

**Honest count of truly new events after dedup: 3-4, not 8.** See `proposal_experiment_03_patch.md`.

**Action under L-011 patience mode:** capture the proposal note, do not patch yet. Patch after persistence forward evidence batch-scores.

### Contrarian Sentiment Experiment — Viable but Scope Carefully

The sentiment exists and is measurable but fragmented. Recommended MVP stack:
- YouTube comments on top 3 channels (Share Durbar, Grow More, Sharemandu)
- Merolagani / ShareSansar article comments
- Public Telegram channels

Skip Facebook/Instagram/TikTok until the MVP proves the signal has edge — scraping cost is disproportionate.

Build a Nepali / Romanized-Nepali sentiment classifier (LLM zero-shot is adequate to start, despite L-011 — text classification is one of the documented LLM strengths).

Expect signal to be dominated by hype/pumping, which is **ideal for a contrarian (fade-the-crowd) strategy**, terrible for trend-following.

---

## Master Source List

### NRB Margin Lending Events
- Fiscal Nepal Rs 250M unified directive: https://www.fiscalnepal.com/2025/07/17/21401/nrb-revises-unified-directive-share-loan-limit-raised-to-rs-250-mln-eases-credit-for-housebuyers/
- myRepublica Rs 150M to 250M: https://www.myrepublica.nagariknetwork.com/news/limit-on-margin-loans-raised-from-rs-150-million-to-rs-250-million-91-38.html
- Nepal Economic Forum FY 2025/26 Monetary Policy: https://nepaleconomicforum.org/key-highlights-of-the-monetary-policy-for-fy-2025-26-ad-2082-83-bs/
- NRB Monetary Policy 2025/26 PDF: https://www.nrb.org.np/contents/uploads/2025/08/Monetary-policy-in-English-2025_26.pdf
- NepalNews explainer: https://english.nepalnews.com/s/explainers/everything-you-should-know-about-nepals-2025-26-monetary-policy/
- Rising Nepal NRB rate cuts: https://risingnepaldaily.com/news/64962
- Rising Nepal risk weight to 100%: https://risingnepaldaily.com/news/62503
- ShareSansar CRR + risk weight: https://www.sharesansar.com/newsdetail/bfis-now-required-to-maintain-90-of-crr-daily-with-nepal-rastra-bank-risk-weight-on-share-backed-loans-revised-to-100-2025-05-28
- Investopaper risk weight cut: https://www.investopaper.com/news/nepal-rastra-bank-reduces-risk-weight-on-share-loans-to-100-following-new-governors-appointment/
- Bajarko Chirfar single customer limit lifted: https://eng.bajarkochirfar.com/2025/10/15/nrb-lifts-single-customer-margin-loan-limit/
- Bajarko Chirfar Rs 250M from today: https://eng.bajarkochirfar.com/2025/07/17/nepal-rastra-bank-margin-loan-home-loan-limit-2082/
- Merolagani primary capital ratio: https://eng.merolagani.com/NewsDetail.aspx?newsID=34295

### Impact Numbers
- Nepal Monitor share-backed lending ramp: https://nepalmonitor.com/2025/08/25/commercial-banks-ramp-up-share-backed-lending-after-nepal-rastra-banks-policy-shift/
- ictframe NEPSE Trends 2082: https://ictframe.com/nepse-trends-2082/
- NEPSE Trading liquidity analysis: https://nepsetrading.com/insights/nepal-stock-market-liquidity-analysis
- NEPSE Trading Q1 +37%: https://nepsetrading.com/blog/share-backed-loans-surge-nearly-37-percent-in-first-quarter-reflecting-renewed-investor-activity-in-capital-market
- Annapurna Express margin loans +35.57%: https://theannapurnaexpress.com/story/52046/

### NEPSE Daily Reaction Reports
- Kathmandu Post Rs 20bn turnover: https://kathmandupost.com/money/2025/07/22/nepse-jumps-80-97-points-turnover-hits-rs20-97-billion
- Kathmandu Post 2% jump banking +1.38%: https://kathmandupost.com/money/2025/08/27/nepse-index-jumps-nearly-2-percent-as-turnover-crosses-rs7-68-billion
- Kathmandu Post NEPSE crosses 2600: https://kathmandupost.com/money/2025/11/23/nepse-jumps-to-2-600-as-turnover-crosses-rs6-billion
- Kathmandu Post share market lockdown: https://kathmandupost.com/money/2026/02/10/nepal-s-share-market-faces-unprecedented-lockdown-as-regulators-battle-industry-over-trading-rules
- Kathmandu Post April 5 plunge: https://kathmandupost.com/money/2026/04/05/nepse-plunges-105-50-points-as-all-sub-indices-decline
- Kathmandu Post April 1 plunge: https://kathmandupost.com/money/2026/04/01/nepse-plunges-74-73-points-as-all-sub-indices-decline

### Manipulation / NPL Crisis
- World Bank Nepal Development Update: https://www.worldbank.org/en/country/nepal/publication/nepaldevelopmentupdate
- B360 NPL surge: https://www.b360nepal.com/detail/10570/npl-of-commercial-banks-surge-exponentially
- Nepal Economic Forum bull market risk: https://nepaleconomicforum.org/are-retail-investors-ignoring-risk-in-nepals-bull-market/
- OnlineKhabar influencer manipulation: https://english.onlinekhabar.com/how-influencers-are-manipulating-the-nepal-share-market.html
- Clickmandu Dipendra Agrawal: https://english.clickmandu.com/2025/12/5409/
- Rising Nepal Agrawal arrested: https://risingnepaldaily.com/news/65481

### Sentiment Sources
- subredditstats r/nepalstock: https://subredditstats.com/r/nepalstock
- Facebook Share Market Forum: https://www.facebook.com/groups/sharemarketdiscussion/
- Facebook Nepal Stock Forum: https://www.facebook.com/groups/nepalstocks/
- Telegram NepalStockExchange: https://t.me/NepalStockExchange
- Share Durbar about: https://sharedurbar.com.np/about/
- vidIQ Share Durbar stats: https://vidiq.com/youtube-stats/channel/UCM3G0qLnOD3NEI2ixgXUi7Q/
- Sajha "What stocks to buy" thread: https://sajha.com/sajha/html/index.cfm?threadid=131316&noofposts=1884
- Feedspot top Nepal YouTubers 2026: https://videos.feedspot.com/nepal_youtube_channels/

### Existing Open Source Scrapers
- suyogdahal/nepse-data: https://github.com/suyogdahal/nepse-data
- sbmagar13/sharesansar_datascrape: https://github.com/sbmagar13/sharesansar_datascrape
- polymorphisma/nepse_scraper: https://github.com/polymorphisma/nepse_scraper
- IOST-ASCOL nepali-datasets: https://github.com/IOST-ASCOL/nepali-datasets

### Background
- Nepali sentiment hybrid DL — Springer: https://link.springer.com/article/10.1007/s13278-025-01508-w
- ShareSansar 3M demat accounts: https://www.sharesansar.com/newsdetail/there-are-3061668-demat-accounts-in-the-country-only-about-20-of-them-invest-in-the-secondary-market-actively-2021-03-05
- NEPSE Trading 6.55M demat accounts: https://nepsetrading.com/blog/demat-accounts-reach-655-million-mero-share-users-climb-to-559-million
- NRB working paper vol 26-2: https://www.nrb.org.np/contents/uploads/2022/12/vol26-2_art2.pdf
