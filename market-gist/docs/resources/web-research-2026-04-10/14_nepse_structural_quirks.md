# Thread 4: NEPSE Structural Quirks and Hidden Mechanics

## Question
Document NEPSE structural quirks and hidden market mechanics that mainstream finance research ignores. Circuit breakers, matching algorithm, broker discretion, IPO lottery selling pressure, bonus dilution, right share gaps, true float, intraday patterns, settlement, dividend credit, day-of-week, half-day sessions, margin cascades, currency mismatch, cross-holdings, and the Reliance Spinning Mills "lost IPO."

## Method
WebSearch across NEPSE Trading blog, Nepalytix, ShareSansar, Kathmandu Post, CDSC, SEBON, Bajarko Chirfar, Securities Act texts, and case files.

## TL;DR

NEPSE has many documented structural quirks but **almost no published high-quality empirical microstructure research**. Day-of-week is the one exception. Everything else (intraday patterns, bonus drift, right drift, IPO listing-day dump, dividend-credit reinvestment) is **folk knowledge waiting for a data team.** The Reliance Spinning Mills "lost IPO" case is the cleanest illustration of structural prospectus risk in Nepal. The 10% individual circuit doesn't halt trading (it just caps price), which is different from regional peers and creates a distinct mechanical signature.

---

## 1. Circuit Breakers & Trading Halts — PARTIALLY EXPLOITABLE

**Rules (DOCUMENTED, revised 2020 and 2026):**
- **Individual stock:** hard 10% daily price band based on last-traded price. **Critically: price cannot move past the band, but trading does NOT halt** — orders inside the band still execute. **Different from NSE/BSE India where circuit = hard halt.**
- **Index level (trading halt):** 4% → 20-min halt (if in first hour), 5% → 40-min halt (before 1 PM), 6% → rest of day closed.
- SEBON revised circuit breakers in April 2026 (Farsight) — implying the old ones were being gamed.

**Patterns (DOCUMENTED on NEPSE Trading blog):**
- Small-caps **repeatedly hit 10% upper circuit on tiny volume** ("momentum carry-over buying"). NEPSE Trading blog names BJHL, SKHL hitting circuit multiple consecutive days.
- The 10% individual circuit is a **magnet** — once touched, the rest of the day is one-sided queue. This is a mechanical signature you can detect: "time-to-circuit + residual queue imbalance."

**Exploitable:** YES, mechanically. NEPSE Trading explicitly publishes a "5-circuits-in-5-sessions" small-cap screen ("Momentum Stocks on NEPSE: Five Circuits and What Comes Next — March 31, 2026"). Recurring.

---

## 2. NEPSE Matching Algorithm & Pre-Open Auction — DOCUMENTED, UNDER-DISCUSSED

**Rules:**
- **Pre-open session: 10:30–10:45 AM** (some sources say 9:30–9:45 — this is legacy/outdated)
- Orders only allowed **+/- 2% from prior close** during pre-open (one source says 5% — there is genuine inconsistency in published material)
- Uses **call auction (equilibrium price)** — price chosen to maximize matched volume
- Unmatched orders spill into the 11:00 continuous session
- Continuous session 11:00 AM – 3:00 PM; closing session 3:00–3:05 PM
- System: NOTS (NEPSE Online Trading System), brokers via TMS (Trade Management System)

**Quirks (mechanically verifiable):**
- The 2% pre-open collar means the opening print is **capped**. On big gap-up news the opening is artificially suppressed then explodes at 11:00:01. **The first-second-of-continuous tape is a distinctive pattern.**
- Unmatched pre-open orders carry as priority in continuous — documented but rarely modeled.

**Exploitable:** YES — the "pre-open clipped at 2%, then continuous gap" pattern is deterministic. Recurring.

---

## 3. TMS Broker Discretion & Front-Running — DOCUMENTED, RECURRING

**Documented cases:**
- **Securities Act 2007, Clause 91** explicitly prohibits front-running
- **Nepali Times** explicitly states regulators and brokers have engaged in front-running "in contravention of existing rules"
- **Bhrikuti Stock Broking (Broker #55) suspended April 2026** — SEBON found firm: (a) used one client's funds/collateral to settle another client's trades, (b) failed to pay for Himalayan Reinsurance shares sold, (c) used unpaid proceeds to buy shares from businessman Deepak Bhatt, (d) failed to maintain mandatory 25% margin. **Rs 5.11 BILLION owed to investors**
- **Multiple SEBON AML fines** against share brokers
- **CIAA raided NEPSE itself (Aug 2024)** — two IT staff accused of trading in relatives' names on leaked info
- **Ridi Hydropower** — former chairman Guru Prasad Neupane charged by SEBON for insider trading (Mar 2021 – Jul 2022 window)
- **Karnali Development Bank** — price jumped Rs 76.90 the day AFTER NRB declared it "troubled"; SEBON investigating

**Exploitable:** NOT directly — this is **counterparty risk to manage**, not trade. Choice of broker matters; suspended brokers create forced-migration events you can observe.

---

## 4. Mero Share Lottery IPO Selling Pressure — DOCUMENTED AS STRUCTURAL, UNDER-MEASURED

**Documented facts:**
- Allotment is pure lottery for retail (SEBON rule: min 10 units per lucky applicant)
- Oversubscription 50–100x is normal → lucky retail get ~10 shares (~Rs 1,000 equity stake each)
- **Gap between allotment and listing: 7–30 days** (sometimes months, see Reliance Spinning #16)
- ShareSansar's "10 Shares and a Dream" article (Dec 2025) and multiple Nepalytix pieces call this "recycling of liquidity from artificially inflated IPO listings pressuring the overall market"

**The mechanical claim:** Because hundreds of thousands of retail get a 10-share lot worth ~Rs 1,000, **day-1 of listing is a forced-sell avalanche.** Transaction-cost-dominated holders just dump. Classic folk knowledge in Nepal but **no rigorous study measures the day-1 / week-1 return curve.**

**Exploitable:** YES — listing-day short-side signal, recurring with every IPO. **Gap in the literature you could close with your own data.** Symbol listing dates are public.

---

## 5. Bonus Share Price Adjustment — MECHANICAL, DOCUMENTED

**Rules (DOCUMENTED, multiple calculators published):**
- Formula: `Adjusted Price = LTP_before_book_close / (1 + bonus%)`
- Example: Atmabirha Laghubitta — 14.25% bonus, LTP Rs 6,365.40 → adjusted Rs 5,571.47 (April 2026 example)
- Adjustment happens **on the book closure date**, trading resumes at adjusted price next session
- Nepal uses bonus shares heavily instead of cash because cash dividends are taxed; bonus shares historically had tax advantages

**Opportunity angle (FOLK):**
- The theoretical adjustment is exact, but **the open after the adjusted-price reset often drifts** — bonus-heavy stocks show a "post-bonus drift" that Nepal's research platforms talk about anecdotally. **Nobody has published a clean quantitative study.**
- **Bonus share listing delay:** new bonus shares take additional time to hit demat accounts — the "float expansion lag" creates a period when the adjusted price exists but the new shares aren't yet tradeable.

**Exploitable:** YES, mechanically. The bonus-drift hypothesis is testable on our existing symbol history.

---

## 6. Right Share Gap Arbitrage — CONTRADICTS TEXTBOOK THEORY

**Documented research:**
- TU elibrary paper ("Impact of Right Share on Share Price Movement of Commercial Banks in Nepal") explicitly finds: **"Share price of Nepalese commercial banks decreases after the announcement of right, despite the increase in the market index in the corresponding period. Findings are not consistent with the theory of rights offering."**
- Kathmandu Post ("What is not right about rights shares") argues the structure is broken
- **Key structural fact:** rights issues in Nepal are **always at face value (Rs 100)** — so the higher the market price, the bigger the "free money" per right, and prices get bid up on announcement (opposite to textbook)

**Folk claim:**
- Nepal has standard "right share adjustment calculator" tools — the theoretical ex-rights price is formulaic, yet realized prices deviate systematically because the Rs 100 par creates asymmetric payoff
- Deviation direction is reportedly NOT random — documented **pre-announcement run-up** and **post-ex-rights underperformance**

**Exploitable:** YES. Two distinct trades:
1. Pre-announcement momentum
2. Ex-rights reversion

Recurring. Academic evidence exists.

---

## 7. True Float / Promoter Lock-In — DOCUMENTED BUT NO PUBLISHED "TRUE FLOAT" DATASET

**Rules (Securities Registration and Issuance Regulations 2073, Rule 38):**
- Promoter shares locked ~3 years from allocation
- NEPSE computes a **Float Index** that excludes promoter, government, strategic, and other locked shares — but this is an aggregate index, not per-stock float data published in a structured way
- **Promoter vs ordinary shares trade separately**; promoter shares on block trades only, **usually at ~50% discount** (e.g., Mega Bank: ordinary Rs 183, promoter Rs 102 at one snapshot)
- Investor groups have been **demanding separate ISIN numbers** for promoter and ordinary — they're the same ISIN today, which is a hidden structural issue
- **Upcoming Promoter IPO Lock-In Unlock 2082/2025** (`nepsestock.com`) — there IS a public list of upcoming unlocks, the cleanest "supply shock calendar" available

**Exploitable:** YES. The promoter unlock calendar is a real, public, under-used event signal. The promoter-ordinary discount is also mean-reverting when reforms are discussed.

**Important link to existing experiment:** Our experiment 02 (lock-in expiry) was inconclusive at N=27. **The `nepsestock.com` upcoming unlock list lets us collect more events going forward** — the parked experiment can be revived if more unlocks accumulate.

**Gap to fill:** No one has published a clean time-series "true float %" per symbol. We could build it from paid-up capital + promoter/public split + lock-in calendar.

---

## 8. Intraday Patterns in the 4-Hour Window — FOLK, SOME PUBLISHED HEURISTICS

**Documented (NEPSE Trading, Nepalytix):**
- Trading hours: 11:00 AM – 3:00 PM (pre-open 10:45–11:00; close auction 3:00–3:05)
- **First 30 minutes (11:00–11:30) have highest volume AND volatility**
- **Most active continuous period: 12:00 PM – 2:00 PM**
- "Opening Range Breakout" strategy is taught as the dominant intraday Nepal strategy — 15–30 min range, breakout with volume

**Gap:** No rigorous published intraday study with statistics (nothing like Harris's intraday U-curve for US markets). **All advice is narrative.**

**Exploitable:** YES if we collect tick/minute data.

---

## 9. T+2 Settlement Patterns — DOCUMENTED, UNDER-EXPLORED

**Rules (CDSC Settlement Procedure):**
- T+2 cycle: trade file load (T), CGT base price (T to T+1), funds/security payin, CGT calculation, shortage/closeout, payout — all on T+2
- **Capital Gains Tax is computed and deducted at settlement (T+2), not at year-end** — a Nepal-specific quirk
- ShareSansar notes Nepal still lacks a formal auction market system for failed settlements

**Folk patterns:**
- "T+2 wash" — sell on Monday, cash on Wednesday. Mid-week is reported cash-inflow day; Sunday is sell-to-raise day. Maps directly onto the day-of-week research.

**Exploitable:** Weakly. Recurring.

---

## 10. Mero Share Dividend Credit Timing — FOLK, LARGELY UN-DOCUMENTED

**Documented (CDSC FAQ):**
- Cash dividends credited direct-to-bank via "My Bank" linked account in Mero Share
- Dividend details appear in "My Portfolio" section

**Not documented:**
- **No published study** on whether dividend credit dates trigger reinvestment surges. Genuine research gap.
- The exact date of mass credit per company is scheduled but not aggregated anywhere — we'd have to build the calendar from each company's AGM record date + payment date announcement.

**Exploitable:** Potentially — but requires manually building the credit-date calendar from filings. One-time data engineering, then recurring signal.

---

## 11. Sunday / Day-of-Week Effect — STRONGLY DOCUMENTED

(Covered in detail in `13_retail_psychology_signals.md` thread 3 finding 5.)

**Most empirically grounded signal in this whole research wave.** Multiple independent peer-reviewed sources confirm Sunday weak / Wednesday-Thursday strong. ANOVA significant, p = 0.0115.

---

## 12. Half-Day Trading Sessions — DOCUMENTED, UNSTUDIED

**Documented:**
- **Friday: 11:00 AM – 1:00 PM** (2 hours instead of 4) — regular half-day
- Holidays create erratic half-day scenarios sometimes

**No published study** on whether Friday half-days behave differently. Pure research gap.

**Exploitable:** Unknown, testable. Recurring weekly.

---

## 13. Margin Call Cascades — DOCUMENTED HISTORICALLY, FRESHLY EXPANDED RISK 2025

**Documented:**
- **2021–2023 crash:** NEPSE 3,200 → 1,615 (≈50%), explicitly attributed to "margin lending tightening → panic → bank capital adequacy pressure → negative feedback loop of forced sales"
- **Margin Trading Directive 2082 (2025)** replaced 2017 framework: now investors need only **30% initial margin** (was more conservative), maintenance margin 20%, brokers can lend up to 5x certified net worth, single client cap 10% of broker's lending
- **Share pledge loans = Rs 156.27 billion (+11.07% YoY)** — leverage stack sitting under NEPSE
- Merolagani lists **102 companies including 16 commercial banks** as margin-eligible — cascade concentration risk in commercial banks

**Exploitable:** As risk signal. Detect when margin-eligible stocks have abnormal drawdowns as potential cascade initiation. Recurring tail event.

---

## 14. Currency Mismatch in NEPSE Companies — REAL FOR A NARROW SUBSET

**Documented:**
- NPR pegged to INR; floats vs USD
- **World Bank Nepal Energy Infrastructure Assessment (2019)** and NEA guidelines: since 2017, NEA signs **partly USD-denominated PPAs**:
  - **216 MW Upper Trishuli** — partly USD PPA
  - **120 MW Rasuwa-Bhotekoshi** — partly USD PPA
- nepsetrading.com confirms NPR depreciation hurts hydropower import-heavy input costs but helps those with USD revenue

**Gap:** No clean mapping of "which NEPSE-listed hydropower has USD PPA share = X%, USD debt = Y%". Information exists in prospectuses but is not aggregated.

**Exploitable:** YES — currency regime shifts (INR weakness vs USD translates directly to NPR) create a narrow basket of hydropower winners vs losers. **One of the few real FX plays in NEPSE.** Recurring.

---

## 15. Bank Subsidiary / Cross-Holdings — DOCUMENTED AS SYSTEMIC RISK

**Documented:**
- **NRB forced cross-holding unwinds (2022):** if a commercial/development/finance institution owns >10% of a microfinance, they MUST submit a merger action plan. If ≥51%, mandatory merger/acquisition.
- **BAFIA amendment (2025):** proposed separation of business-from-banking; "**88 individuals hold >1% founder shares across 14 banks, 82 of them actively engaged in other businesses**"
- Known example: Laxmi Bank → Prime Life Insurance (15%) + Laxmi Laghubitta subsidiary
- **Commercial banks historically = 82% of NEPSE turnover, 62% of market cap** (NRB paper) — **the market IS the banks**

**Mapped?** Not publicly and comprehensively. Nobody has built a "Nepal bank cross-ownership graph" dataset. **Genuine research gap.**

**Exploitable:** As contagion signal. When one bank moves, identify cross-held subsidiaries and trade the secondary shocks. Recurring.

---

## 16. Reliance Spinning Mills "Lost" IPO — STRUCTURAL TEMPLATE FOR PROSPECTUS RISK

**Fully documented timeline:**
- **Dec 8–11, 2025:** IPO opened for Nepalese migrants abroad
- **Dec 22–26, 2025:** General public IPO, **book-building** method. Cut-off Rs 912; retail Rs 820.80
- **Dec 25, 2025:** Collected Rs 15.30 arba, oversubscribed 20.16x
- **Jan 2, 2026:** Allotted to 18,495 applicants
- **Dec 2025 / Jan 2026:** **~Rs 1.7465 arba collected was effectively locked** — no listing, no liquidity, no refund
- **Feb 12, 2026 (ShareSansar "listing in limbo"):** Stock market analyst Ramhari Nepal blamed "lack of coordination between SEBON and Nepal Electricity Authority" — specifically, **"the net worth after adjustment of electricity arrears has not been included in the prospectus."** Translation: the company had unpaid electricity bills that hadn't been subtracted from book value, SEBON/NEPSE caught it after allotment, listing frozen pending prospectus fix.
- **Feb 13, 2026:** Finally listed. **NEPSE imposed an opening price band of Rs 100–300** (versus Rs 820.80 retail issue price — a **brutal ~60% regulatory haircut** disguised as price discovery)

**What it tells us about NEPSE structural risk:**
1. **Book-building prospectus approval is leaky.** SEBON signed off on a prospectus with an undisclosed electricity liability; NEPSE's listing committee caught it later. **The retail investor bore the delay and implicitly the valuation correction.**
2. **"Allotted but not listed" is a real state** in Nepal. Money debited, shares allocated, nothing trades. Can last 30+ days with no published remedy.
3. **The Rs 100–300 opening band** is a regulatory mark-down protecting neither retail (capital stuck) nor book-building QIBs (paid Rs 912).
4. **NEA coordination failure** implies cross-agency information asymmetry — SEBON doesn't cross-check regulated-utility arrears against listed-company balance sheets.

**Recurring?** The specific mechanism (electricity arrears vs prospectus) is one-time, but **the general "allotted-but-not-listed" failure mode is a recurring structural vulnerability.**

**Exploitable:** NO, but critical risk knowledge. Add `listing_delay_risk` as an IPO metadata feature.

---

## Cross-Cutting Meta-Findings

1. **NEPSE's most exploitable quirks are calendar-driven, not price-driven.** Day-of-week, bonus book-closure drift, rights announcement drift, IPO listing-day dump, promoter unlock calendar. **A reliable calendar beats a reliable forecast.**

2. **"The market is the banks"** — 82% turnover, 62% cap, systemic cross-holdings, Rs 156 billion margin leverage stack. **Any model that doesn't have a bank-sector contagion factor is mis-specified.**

3. **The 10% individual circuit doesn't halt trading, it just caps price.** Different from all regional peers. The "queue behind the cap" is a distinct mechanical signature.

4. **Nepal has NO published high-quality empirical microstructure research.** Day-of-week is the ONE exception (two independent sources confirm with ANOVA). Everything else — intraday, bonus drift, right drift, IPO listing day, dividend-credit reinvestment — **is folk knowledge waiting for a data team.** We are positioned to be that team.

5. **Regulatory enforcement is real but lagged.** CIAA raided NEPSE itself, SEBON suspended Broker #55 with Rs 5.11 billion owed, Ridi Hydropower chairman prosecuted. **Counterparty/broker selection is a non-trivial risk.**

6. **The Reliance Spinning Mills case is the cleanest illustration that prospectus quality in Nepal is opaque.** An IPO can clear SEBON, collect Rs 1.7+ billion, then get frozen for undisclosed liabilities caught by NEPSE's listing committee.

---

## Master Source List

### Circuit Breakers
- [Circuit Breakers in NEPSE — Nepalytix](https://nepalytix.com/blog/circuit-breakers-in-nepse-how-upper-and-lower-limits-protect-and-trap-traders)
- [Understanding NEPSE Circuit Breakers — NEPSE Trading](https://nepsetrading.com/blog/understanding-nepse-circuit-breakers-how-automatic-trading-halts-protect-the-market)
- [New Circuit Breaker Rules of NEPSE (2020) — FirdiEye](https://firdieye.blogspot.com/2020/05/new-circuit-breaker-rules-nepse.html)
- [NEPSE eases circuit breaker rules — myRepublica](https://myrepublica.nagariknetwork.com/news/nepse-flexible-on-circuit-break-rules-on-share-trading-allows-more-fluctuat-87-60.html)
- [Momentum Stocks on NEPSE: Five Circuits — NEPSE Trading](https://nepsetrading.com/insights/momentum-stocks-on-nepse-five-circuits-and-what-comes-next-march-31-2026)
- [Market dips marginally, SEBON revises circuit breakers — Farsight Nepal](https://farsightnepal.com/news/market-dips-marginally-sebon-revises-circuit-breakers-suspends-broker/)

### Pre-Open / Matching
- [Pre-Open Market in NEPSE — Nepalytix](https://nepalytix.com/blog/pre-open-market-in-nepse-how-it-works-and-why-it-matters-for-investors)
- [What Is TMS in NEPSE — Nepalytix](https://nepalytix.com/blog/what-is-tms-in-nepse-a-complete-guide-to-how-the-trading-management-system-works)
- [Nepse Pre Open Price Calculator — anilpathak.com.np](https://anilpathak.com.np/nepse-pre-open-price-calculator)
- [NEPSE Online Trading System (NOTS) — SlideShare](https://www.slideshare.net/slideshow/nepse-online-trading-system-nots/144305188)

### Insider Trading & Broker Discretion
- [Insider trading taints Nepal capital market — Nepali Times](https://nepalitimes.com/here-now/insider-trading-taints-nepal-capital-market)
- [Bhrikuti Stock Broking's license suspended, Rs 5.11 billion owed — Bajarko Chirfar](https://eng.bajarkochirfar.com/2026/04/09/bhrikuti-stock-brokings-license-suspended-rs-5-11-billion-owed-to-investors/)
- [Broker number 55 has been suspended — Bajarko Chirfar](https://eng.bajarkochirfar.com/2026/04/07/broker-number-55-has-been-suspended-how-long-will-he-not-be-allowed-to-buy-or-sell-shares/)
- [SEBON Fines Share Brokers For AML Breach — ICT Frame](https://ictframe.com/sebon-fines-share-brokers-aml/)
- [CIAA Grills NEPSE Staff for Insider Trading — New Business Age](https://newbusinessage.com/article/ciaa-grills-nepse-staff-for-insider-trading)
- [Insider Trading in Nepal's Stock Market — ShareSansar](https://www.sharesansar.com/newsdetail/insider-trading-in-nepals-stock-market-and-its-effect-on-middle-class-investors-2025-05-16)

### IPO Lottery
- [IPO Allotment Process in Nepal — ShareGyan Nepal](https://www.sharegyannepal.com/ipo-allotment-process-in-nepal/)
- [10 Shares and a Dream — ShareSansar](https://www.sharesansar.com/newsdetail/10-shares-and-a-dream-how-nepal-turned-ipos-into-a-market-lottery-2025-12-26)
- [IPO Pipeline and NEPSE Blocked — Nepalytix](https://nepalytix.com/blog/ipo-pipeline-and-nepse-blocked-how-market-closures-delay-capital-raising-in-nepal)

### Bonus & Right Share
- [Stock Price Adjustment: Bonus and Rights Shares — NEPSE Trading](https://nepsetrading.com/news/stock-price-adjustment-process-for-bonus-and-rights-shares-?lang=en)
- [Bonus Share Adjustment Calculator — Nepse Khabar](https://nepsekhabar.com/calculator/bonus-share-adjustment)
- [Price adjustment in bonus shares — Bajarko Chirfar](https://eng.bajarkochirfar.com/2026/04/08/price-adjustment-in-bonus-shares-of-2-companies-on-nepse-at-what-price-will-trading-open-now/)
- [Rights Share Issue Practice in Nepal — ResearchGate](https://www.researchgate.net/publication/277847616_Rights_Share_Issue_Practice_in_Nepal)
- [Impact of Right Share on Share Price Movement of Commercial Banks in Nepal — TU elibrary](https://elibrary.tucl.edu.np/JQ99OgQIizUxyjI9nB0on9OyLkqsGIf4/api/core/bitstreams/f65882db-bb1b-4c8c-ac0f-be1b5a80b119/content)
- [What is not right about rights shares — Kathmandu Post](https://kathmandupost.com/columns/2021/11/18/what-is-not-right-about-rights-shares)
- [Right Share Adjustment Calculator — ShareSansar](https://www.sharesansar.com/right-adjustment-price-calculator)

### Promoter Lock-In / True Float
- [NIFRA Clarifies Misconception on Trading of Promoter Shares — Merolagani](https://eng.merolagani.com/NewsDetail.aspx?newsID=98933)
- [Upcoming Promoter IPO Lock-In Unlock — NEPSE Stock](https://nepsestock.com/upcoming-lock-in-unlock-in-nepal-stock-market)
- [Why the huge price gap between ordinary & promoter shares — ShareSansar](https://www.sharesansar.com/newsdetail/why-the-huge-price-gap-between-ordinary-promoter-shares-of-nabil-and-nib-when-both-are-easily-tradable)
- [NEPSE to remove price difference between ordinary and promoter shares — ShareSansar](https://www.sharesansar.com/newsdetail/nepse-to-remove-price-difference-between-ordinary-and-promoter-shares)
- [Investor Groups Demand Separate ISIN Numbers — NEPSE Trading](https://news.nepsetrading.com/investor-groups-demand-separate-isin-numbers-for-promoter-and-ordinary-shares?lang=en)
- [Time for one class of shares — Kathmandu Post](https://kathmandupost.com/columns/2019/12/10/time-for-one-class-of-shares)

### Intraday & Settlement
- [Intraday Trading in Nepal: Strategy, Risk and Profit Guide — NEPSE Trading](https://nepsetrading.com/insights/intraday-trading-in-nepal-strategy-risk-and-profit-guide)
- [NEPSE Market Hours and Settlement Rules — Nepalytix](https://nepalytix.com/blog/nepse-market-hours-and-settlement-rules-everything-investors-should-know)
- [CDSC Settlement Procedure](https://cdsc.com.np/cmsettlementprocedure)
- [Understanding the CDSC — Nepalytix](https://nepalytix.com/blog/understanding-the-cdsc-how-settlement-demat-and-trading-actually-work-in-nepal)

### Day-of-Week & Trading Schedule
- [NEPSE to open on Fridays, remain closed on Sundays — epardafas](https://english.pardafas.com/nepse-to-open-on-fridays-remain-closed-on-sundays/)
- [NEPSE to operate six days a week — The Himalayan Times](https://thehimalayantimes.com/business/nepse-to-operate-six-days-a-week-effective-june-15)

### Margin Trading
- [NEPSE Market Crash: Causes, History and Recovery — NEPSE Trading](https://nepsetrading.com/insights/nepse-market-crash-causes-history-and-recovery-analysis)
- [Nepal Introduces New Margin Trading Framework — NEPSE Trading](https://nepsetrading.com/blog/nepal-introduces-new-margin-trading-framework-expanding-investment-access-while-raising-risk-awareness)
- [102 companies including 16 commercial banks approved for margin trading — Bizness News](https://english.biznessnews.com/posts/102-companies-including-16-commercial-banks-approved-for-margin-trading)
- [NEPSE Trends 2082: Why Banks Pouring Billions Share Loans — ICT Frame](https://ictframe.com/nepse-trends-2082/)

### Currency Mismatch
- [Exchange Rate and Foreign Investment Trends in NEPSE — NEPSE Trading](https://nepsetrading.com/blog/exchange-rate-and-foreign-investment-trends-in-nepse)
- [Nepal Energy Infrastructure Sector Assessment — World Bank](https://documents1.worldbank.org/curated/en/592481554093658883/pdf/Nepal-Energy-Infrastructure-Sector-Assessment.pdf)

### Cross-Holdings
- [NRB Forces Microfinance Companies — ShareSansar](https://www.sharesansar.com/newsdetail/nrb-forces-microfinance-companies-with-more-than-10-crossholding-of-bfis-to-take-merger-acquisition-route-2022-01-03)
- [BAFIA Pushes to Separate Business from Banking — NEPSE Trading](https://nepsetrading.com/blog/bafia-pushes-to-separate-business-from-banking-seven-dozen-commercial-bank-founders-at-risk)
- [Investing in Shares of Commercial Banks in Nepal — NRB](https://www.nrb.org.np/red/no_14investing_in_shares_of_commercial_banks/)

### Reliance Spinning Mills "Lost IPO"
- [Reliance Spinning Mills share listing in limbo — ShareSansar](https://www.sharesansar.com/newsdetail/reliance-spinning-mills-share-listing-in-limbo-investors-hit-hard-2026-02-12)
- [NEPSE's New Pricing Rule Draws Objection from Reliance Spinning Mills — New Business Age](https://www.newbusinessage.com/news/47433/nepses-new-pricing-rule-draws-objection-from-reliance-spinning-mills/)
- [IPO Shares of Reliance Spinning Mills Now Listed on NEPSE — ShareSansar](https://www.sharesansar.com/newsdetail/ipo-shares-of-reliance-spinning-mills-now-listed-on-nepse-what-are-the-opening-ranges-2026-02-13)
- [Reliance Spinning Mills IPO Allotted to 18,495 Applicants — ShareSansar](https://www.sharesansar.com/newsdetail/reliance-spinning-mills-ipo-allotted-to-lucky-18495-applicants-2026-01-02)
- [Why is the listing of Reliance Spinning Mills delayed — Insurance Khabar](https://english.insurancekhabar.com/why-is-the-listing-of-reliance-spinning-mills-delayed-nepse-says-2/)
- [Unregulated pre-IPO boom raises alarms — Fiscal Nepal](https://www.fiscalnepal.com/2025/07/29/21569/unregulated-pre-ipo-boom-raises-alarms-in-nepals-capital-market-amid-sebon-inaction/)
