# Thread 3: NEPSE Retail Psychology and Weird Signals

## Question
Research unconventional signals that might affect Nepal stock market retail behavior. Mero Share outages, Kathmandu air pollution, load shedding, cricket, civil service exams, weddings, day-of-week, fuel shortages, social media trends, demat openings, university exams, salary days, monsoon floods.

## Method
WebSearch across NepJOL, Edmans/Garcia/Norli sports paper, Heyes/Neidell/Saberian air pollution paper, Nepal news (Kathmandu Post, ShareSansar, NEPSE Trading, OnlineKhabar), CDSC publications, and global analogs.

## TL;DR

Mainstream Nepal-specific research on these angles is extremely thin. The strongest finding is the **Sun/Thu day-of-week effect** which is published and replicated. The most novel candidates are: **Bikram Sambat turn-of-month effect** (cheap to test, untested because everyone uses Gregorian dates), **monsoon flood × hydro watershed event study** (cleanest fundamental signal), **CDSC demat account growth as contrarian sentiment**, and **Mero Share / TMS outages as a confound control variable**. The agent flagged severe **confound clustering in Dec-Feb** (air pollution + load shedding + wedding + cricket NPL + dividend credits all overlap).

---

## Tier 1 — Highest Priority (Build First)

### 1. Mero Share / TMS App Outages
**Documented?** No formal study. Anecdotal news reports only.

**Documented incidents:**
- Aug 24, 2025: planned 6-hour CDSC maintenance downtime
- May 2023: server rack relocation full-day downtime
- Multiple IPO overload incidents
- Nov 2023: NEPSE power outage delayed open 24 min
- March 2026: TMS-wide login failure at open
- 2021: Mero Share "not loading" — CDSC publicly held retail responsible for missed settlements

**Mechanism:** Mero Share/TMS is the only retail access path. When down, demand is queued, not destroyed. Expect: **volume dip during outage + make-up spike next session.** Distinct from sentiment-driven drops because both sides are throttled.

**Measurability:** Very high. Maintain own uptime ledger, scrape CDSC/NEPSE/Sharesansar announcements, cross-reference turnover.

**Plausibility:** High. Mechanical constraint, not folk knowledge. Treat as **confound control variable** in same-day return models.

### 2. Monsoon Flood × Hydro Watershed Event Study
**Documented?** Strong descriptive evidence.

- Sep 2024 floods: **NPR 2.45B damage**, 1,100 MW production shutdown, **16 hydro projects damaged**
- Recurring (2020, 2021, 2023, 2024 all had significant events)
- Melamchi June 2021: under-construction dam inundated
- Post-flood NEPSE: declines reported across 186 companies, 12 of 13 sectors down

**Mechanism:** **Cleanest fundamental signal in the entire wave.** Direct cash-flow story:
1. Flood damages plant → forced outage → revenue loss for that specific hydro company
2. Broader sector sell-off if systemic
3. **Watershed-specific:** flood in Koshi basin should hit Koshi hydro stocks more than Gandaki stocks

**Measurability:** Very high. DHM publishes flood bulletins. Match flood dates and watersheds to hydro project locations. **Difference-in-differences design** (affected vs unaffected watersheds) isolates the effect cleanly. Event window: [-3, +10] around flood date.

**Plausibility:** Very high. Mechanical, fundamentally justified, unique to Nepal. Probably underexploited because international analysts don't track Nepali watersheds.

### 3. Bikram Sambat Turn-of-Month Effect
**Documented?** **No.** Published research has tested turn-of-month using Gregorian dates and found it weak.

**Mechanism:** Nepal's largest single employer is the government. Government employees get paid on **Nepali month start** (Baisakh 1, Jeth 1, etc.) — NOT January 1. **Nobody has tested turn-of-month using Bikram Sambat dates.**

**Measurability:** Trivial. Day-of-Nepali-month dummies on existing data. 20 lines of code.

**Plausibility:** Medium-high. Could be a genuinely novel finding because prior researchers used the wrong calendar.

### 4. CDSC Demat Account Growth as Contrarian Sentiment
**Documented?** No academic study, but CDSC publishes monthly/quarterly data.

**Data:**
- Mid-July 2022: 5.346M demat accounts
- Mid-July 2023: 5.823M (+8.9%)
- Mid-March 2024: 6.224M (~21% of population)
- June 2024: 6.287M
- Most COVID-era openings (2020-21) coincided with the NEPSE peak

**Mechanism:** Classic sentiment-peak indicator. New account growth is a **lagging indicator of the retail FOMO phase** — surges AFTER the bull move is well underway, often near the top. Analog: US brokerage account openings peaked Feb-Mar 2021 during Gamestop mania.

**Measurability:** High. CDSC publishes monthly. Compute monthly delta, align with NEPSE level, test as contrarian indicator (bearish next 3-6 months).

**Plausibility:** High. Canonical sentiment indicator just not formalized for Nepal. Easy to implement. **Should be one of the top additions.**

---

## Tier 2 — Already Validated, Replicate and Formalize

### 5. Sun/Thu Day-of-Week Effect — PUBLISHED
**Most empirically grounded signal in this wave.** Multiple independent sources:
- KC and Joshi (2005): Thursday significantly *lower*
- Pant (2010): Friday (pre-change) significantly higher
- Maharjan (2013): Thursday significantly *higher*
- Recent NEPJOL studies: Wednesday and Thursday highest; Sunday negative returns and high volatility
- NRB-published study: day-of-week anomaly persistent

**Synthesis:** **Sunday behaves like "Monday blues" in US markets** — more negative, more volatile (weekend news accumulates with no trading outlet). Thursday (Friday-equivalent) drifts higher.

**Schedule complication:** Nepal has switched between Sun-Thu, Sun-Fri, Mon-Fri at different times. **Anyone analyzing day-of-week must adjust for schedule-change regime breaks.**

**Status:** Validated. Trivially testable in our data.

### 6. Dashain/Tihar Pre-Holiday Drift — PRACTITIONER-DOCUMENTED
- Nepalytix and ShareSansar both report ~+3.5% pre-Dashain rally, ~-2.5% post-Dashain decline
- Practitioner tally not academic-rigor

**Status:** Replicate rigorously with our existing framework.

### 7. Kathmandu PM2.5 → Trading Psychology
**Strong global priors:**
- Heyes/Neidell/Saberian (NBER w22753, 2016): 1 SD increase in Manhattan PM2.5 reduces same-day S&P 500 returns by ~12%; mechanism is risk aversion
- Nature Scientific Reports (2021): 47-city global study, PM2.5 linked to daily returns and volatility
- China study (Pacific-Basin Finance Journal, 2018): air pollution affects trading activity

**No Nepal-specific study.**

**Mechanism:** Cognitive/mood degradation in traders. Plus physical: heavy smog days in Dec-Feb may cause retail to physically avoid broker offices.

**Data sources:** aqicn.org Kathmandu station, pollution.gov.np, US Embassy Phora Durbar station.

**Confound risk:** **Severe.** PM2.5 correlates with dry-season hydropower deficit, winter festivals, fiscal calendar. Need residualization to isolate.

### 8. Cricket Match-Hour Attention Drain
**Strong India/global analogs:**
- Edmans/Garcia/Norli (2007, JoF): World Cup soccer loss in elimination = -49 bps abnormal return next day
- India studies: cricket World Cup match hours see volume drops up to 48% in India's market
- Verstoep et al (SSRN 2491318): cricket performance impacts India/Australia markets

**Not measured for Nepal.** ESPNCricinfo has complete schedule archive. Easy to scrape and overlay.

**Note on timing:** IPL finals are 7:30pm IST (evening) — not contemporaneous with NEPSE 11am-3pm window. So IPL effect would be **next-day mood**, not contemporaneous volume. Nepal national team T20 matches are often day games, potentially overlapping NEPSE window.

---

## Tier 3 — Lower Priority

### 9. Wedding Sait Dates × Mangsir Drag
- Magh, Falgun, Mangsir, Baisakh are peak wedding seasons
- Wedding budgets in millions NPR; gold central
- NRB previously slashed daily gold import quota to 10kg during wedding seasons — explicit acknowledgment of capital outflow
- Calendar-anomaly research found **Mangsir is the worst month for NEPSE, -2.16%**
- Nepali astrologers publish auspicious wedding dates ("sait") each year

**Status:** Worth testing; the Mangsir negative finding aligns with the cash-drain hypothesis.

### 10. Social Media Rumor Pumps
- NEPSE itself published August 2025 notice warning investors against Facebook/TikTok/X stock advice
- "Nepse AI" scam stole **~Rs 800 million** through social media ads
- Industry commentary: rumors via Facebook groups, Telegram channels, YouTube creators "move markets faster than official news"
- Telegram/Viber are the real channels in Nepal (not Twitter/X)

**Mechanism:** Retail-heavy, low-float stocks vulnerable to coordinated hype. Regulatory acknowledgment is strong evidence the phenomenon is real.

**Measurability:** Hard. Requires scraping closed Facebook groups and Telegram channels. Significant project.

### 11. 2015 Blockade as Natural Experiment
Single one-time natural experiment with clean start/end dates. Could calibrate the "physical access shock" channel for the Mero Share outage model.

---

## Tier 4 — Skip or Deprioritize

### 12. Lok Sewa (Civil Service) Exam Dates
- No published research
- Demographic mismatch: PSC exam-takers are job-seekers, not active investors
- Lok Sewa exams are regional, hard to define "the" exam day
- **Skip.** Likely null.

### 13. University Exam Season
- No published research
- No clear mechanism
- Student-investor demographic small
- **Skip.**

### 14. Load Shedding Historical Correlation
- Strong historical evidence (2010-2017 era, up to 14 hours/day cuts)
- 2018: NEA declared load-shedding-free
- Dec 2024: NEA reintroduced industrial load shedding in peak evening
- March 2025: facing power crisis as India slashed imports, up to 12 hours daily cuts in industrial areas

**But:** Trading window 11am-3pm historically had fewer cuts than peak evening. Effect may be more muted than raw hour-count suggests. Also confounded with everything else in Dec-Feb.

**Status:** Historical only. Currently weak. Skip unless we want to run a 2010-2017 historical study.

---

## Cross-Cutting Meta-Findings

1. **The absence of Nepal-specific academic research is itself an edge.** Published NEPSE literature focuses on calendar anomalies, broad index efficiency, and corporate events. Nobody is studying physical/infrastructural/attention channels because they aren't sexy enough for Nepali finance PhDs. **Genuinely uncontested research frontier.**

2. **Confound clustering in Dec-Feb is severe.** Kathmandu AQI peaks + dry-season load shedding + wedding season + cricket NPL + dividend credits + CDSC reporting cycles all overlap. Any Dec-Feb signal needs heavy residualization.

3. **The 2015 blockade is a clean natural experiment.** Well-defined start/end, macro-sized shock, documented access disruption. Run as a single event study to calibrate the physical-access-shock channel.

4. **Beware the "mechanical vs LLM narrative" trap from L-011.** Several signals here are narrative-rich. Bias toward mechanical versions:
   - Measure the **volume drop** during cricket hours, not the mood-driven return
   - Measure **flood damage to specific watersheds**, not "investor panic"
   - Measure **outage duration**, not "retail frustration"

5. **One thing NOT to research:** do NOT add any of these as decision rules until 10-15 out-of-sample sessions of evidence per L-011 patience mode. The work here is hypothesis generation, not policy change.

---

## Master Source List

### Core Global Priors
- [Sports Sentiment and Stock Returns (Edmans, Garcia, Norli 2007)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=677103)
- [Effect of Air Pollution on Investor Behavior: S&P 500 (Heyes, Neidell, Saberian, NBER w22753)](https://www.nber.org/papers/w22753)
- [Ambient PM2.5 and daily stock returns 47 cities (Nature Sci Reports)](https://www.nature.com/articles/s41598-021-88041-w)
- [Cricket World Cup 2019 stock market evidence](https://ideas.repec.org/a/ibn/ibrjnl/v16y2023i6p15.html)

### Day-of-Week Effect (NEPSE)
- [Nepalese Stock Market: Efficiency and Calendar Anomalies (NRB)](https://www.nrb.org.np/er-article/the-nepalese-stock-market-efficient-and-calendar-anomalies/)
- [Risk Behavior of Different Weekdays in NEPSE Index](https://www.nepjol.info/index.php/NJS/article/view/73159)
- [Day-of-the-Week Effect: Industry-Specific (Joshi, SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=927711)
- [Calendar Anomalies: How NEPSE return varies by days and months — ShareSansar](https://www.sharesansar.com/newsdetail/calendar-anomalies-how-nepse-return-varies-by-days-and-months)
- [Performance of NEPSE Index by Days of the Week — Investopaper](https://www.investopaper.com/news/performance-of-nepse-index-by-days-of-the-week/)

### Mero Share Outages
- [MeroShare facing issues — ShareSansar](https://www.sharesansar.com/index.php/newsdetail/meroshare-app-facing-issues-since-yesterday-what-do-the-officials-have-to-say-about-it)
- [Nepse AI Scam Rs 800 million — TechPana](https://techpana.com/2025/152435/nepse-ai-scam-cybersecurity-expert-reveals-rs-800-million-theft)

### Monsoon Floods × Hydropower
- [Floods damage 16 hydropower projects, NPR 2.45B — NEPSE Trading](https://nepsetrading.com/news/floods-and-landslides-cause-npr-245-billion-in-damage-to-nepals-hydropower-sector-1100-mw-power-production-halted)

### Demat Accounts (Sentiment)
- [Nepal demat accounts nearing 6.3 million — myRepublica](https://myrepublica.nagariknetwork.com/news/investor-participation-rising-in-stock-market-demat-accounts-nearing-6-3-million)

### Load Shedding
- [Economic costs of electricity load shedding in Nepal — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1364032121004007)
- [NEA Reintroduces Load Shedding in Industrial Areas — New Business Age](https://www.newbusinessage.com/article/nea-officially-reintroduces-load-shedding-in-industrial-areas-six-and-a-half-years-after-declaring-its-end)

### 2015 Blockade
- [2015 Nepal blockade — Wikipedia](https://en.wikipedia.org/wiki/2015_Nepal_blockade)

### Social Media Manipulation
- [NEPSE warns investors against social media stock content — Khabarhub](https://english.khabarhub.com/2025/08/489790/)

### Other
- [Why NEPSE so volatile — Nepalytix](https://nepalytix.com/blog/why-is-nepse-so-volatile-understanding-the-chaos-of-nepals-stock-market)
- [Month-of-the-year Effects in Nepalese Stock Market](https://www.nepjol.info/index.php/pycnjm/article/download/35919/28084)
- [NEPSE plunges 160 points, trading halted (Sept 18, 2025)](https://kathmandupost.com/money/2025/09/18/nepse-plunges-160-points-trading-halted)
