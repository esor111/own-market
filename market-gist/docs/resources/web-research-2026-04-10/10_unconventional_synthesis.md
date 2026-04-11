# Unconventional Research Synthesis — 2026-04-10

> **Status: Juliet's synthesis. Not yet cross-reviewed by Romeo.**
> This is the second wave of web research from 2026-04-10. The first wave (files 01-06)
> covered the obvious angles. This wave deliberately pursued unconventional, sideways
> framings — things mainstream finance research ignores. Four parallel threads were
> launched: festival/cash-flow effects, political shocks catalog, retail psychology
> signals, and NEPSE structural quirks.

## Why this wave was launched

After completing the first research bundle (files 01-06), the user asked: "go to the web with different framing, kinda different lens, maybe unconventional things that you are curious to research." I (Juliet) chose four directions that felt genuinely unexplored and personally interesting:

1. **Festival / cash-flow calendar effects** — Dashain bonuses, remittance peaks, FD maturity, insurance premium tax rush
2. **Political shocks and crash catalog** — government turnover, earthquake, blockade, Gen Z protests, finance minister speeches
3. **Retail psychology weird signals** — Mero Share outages, air pollution, cricket, university exams, monsoon floods
4. **NEPSE structural quirks** — circuit breakers, IPO listing-day dump, rights gap arbitrage, hidden cross-holdings

## TL;DR — Three Standout Findings

### Finding 1: The Ashad Insurance Tax-Drain Hypothesis
**The single most novel idea from this wave.** Nepal life insurance premiums are tax-deductible. The tax year ends Ashad-end (mid-July). Households rush to pay premiums before Ashad-end to lock in the deduction (structurally identical to India's 80C rush before March 31). This creates a forced cash drain from NEPSE into insurance during the Chaitra-Ashad window.

**Why it's interesting:** Pravaha 2024 found April is one of the LOWEST months for commercial bank stock prices (seasonal index 0.917). They reported it but didn't explain it. This hypothesis explains it AND predicts continued weakness through Baisakh-Jestha-Ashad. Directional-opposite to typical festival/calendar literature. Mechanism is anchored in tax law. Measurable from NIA monthly premium data + NEPSE turnover.

**Status:** Bookmark only. Not built. Real candidate experiment after persistence batch-scoring.

### Finding 2: The September 2025 Gen Z Protest Crash Is Missing From Our Event Table
**The biggest single-day NEPSE shock in our entire data window — and we don't have it.**

- Sept 8-21, 2025: social-media ban triggered Gen Z anti-corruption protests, 19+ dead, parliament burned, PM Oli resigned
- NEPSE shut for ~2 weeks
- **Reopened Sept 18, 2025: crashed -160.33 points (-6.00%)**
- Rs 268 BILLION wiped in minutes
- Triple negative circuit break, full-day shutdown
- 255 of 313 traded companies down

**Why it matters:** Our `experiments/03-nrb-rate-events/data/policy_events.csv` and `proposal_experiment_03_patch.md` are missing this event entirely. It's the largest political shock in the available data and would dramatically improve experiment 03's coverage of the negative-event side.

**Status:** Documentation gap to fix. Pending.

### Finding 3: The Bikram Sambat Turn-of-Month Effect
**A novel angle nobody has tested because everyone uses the wrong calendar.**

Published NEPSE research has tested "turn-of-month effect" using Gregorian dates and found it weak/absent. But Nepal's largest single employer is the government, and government employees get paid on the **Nepali month start** (Baisakh 1, Jeth 1, etc.) — NOT January 1.

**Nobody has tested turn-of-month using Bikram Sambat dates.** This is a published-research blind spot we can exploit cheaply with data we already have. Pure calendar lookup, no scraping required.

**Status:** Bookmark only. Cheapest novel test in the entire backlog.

## The Other Substantial Findings

### From Thread 1 (festival/cash cycles)
- **The October Effect IS published** — K.C. & Joshi found it back in 2004, attributed it to Dashain/Tihar information release timing. Pravaha 2024 confirmed on commercial banks. **Decomposition (bonus vs remittance vs disclosure) is open.**
- **Tihar secondary cash wave: rejected.** No mechanism — cash circulates intra-household, not new liquidity. Bleed-through from Dashain.
- **Nepali New Year (Baisakh 1) rally: rejected.** Pravaha shows April is one of the LOWEST months. There is no Baisakh rally.
- **August "uncollected dividend" cluster: solved.** Companies Act Section 182 requires unclaimed-dividend notices 5 years after declaration. The August cluster is the **shadow of the AGM cluster from 5 years prior.** Our filtering of these as noise was correct.
- **FD maturity rotation: not measurable.** Banks don't publish FD issuance by tenor at usable frequency. Skip.
- **Civil service payday effect: untested but cheap.** Day-of-Nepali-month effect is testable in our data with 20 lines of code.

### From Thread 2 (political shocks catalog)
A complete catalog of NEPSE shocks since 2015 emerged. The most important patterns:

- **Parliament dissolution alone is NOT a crash trigger.** Dec 2020 Oli dissolution: ~-90 points, shrugged off in 3 days. Pure political crisis without economic policy change = noise.
- **Full regime collapse IS a crash trigger.** Sept 2025 Gen Z = -6% reopening crash, 2 weeks closed. 2015 Earthquake = 19 trading days closed. **Pattern: multi-day exchange closure → opening-day crash → recovery within a month.**
- **Liquidity reallocation is the dominant Nepal-specific mechanism.** 2015 blockade, COVID 2020, any event that freezes real estate and depresses FD rates sends money INTO equities. This is counter-intuitive and recurring.
- **Regulator credibility shocks compound with liquidity tightening.** Sarbottam (Aug 2021) + NRB margin circular = the largest historical single-day crash at the time. Wagle speeches + money-laundering crackdown = second largest.
- **Hydropower sector is the geopolitical beta.** MCC news, China/BRI news, US-Nepal relations all hit hydropower index first.
- **Corporate corruption scandals matter ONLY when they touch listed companies.** Bhutanese refugee scam: no NEPSE impact. Lalita Niwas: no NEPSE impact. Deepak Bhatta / Shanker Group: direct crash because Rs 3.73B was diverted from 5 listed companies including Himalayan Reinsurance.

### From Thread 3 (retail psychology signals)
- **Sun/Thu day-of-week effect is the most empirically grounded signal in this whole wave.** Multiple independent studies (KC & Joshi, Investopaper, ShareSansar) all confirm Sunday weak (-0.029% to -0.12%), Wednesday-Thursday strong. ANOVA significant. **Already validated in published research.** Schedule changes complicate testing — Nepal has switched between Sun-Thu, Sun-Fri, Mon-Fri at different times.
- **Mero Share / TMS app outages are real and recurring.** March 2026 TMS-wide login failure documented. Nov 2023 NEPSE power outage delayed open. Multiple IPO concurrency failures. **Treat as a confound control variable, not a signal.**
- **Kathmandu PM2.5 → trading psychology** has strong global priors (Heyes/Neidell/Saberian on Manhattan; 47-city study) but Nepal-specific test is unpublished. Confound clustering in Dec-Feb is severe.
- **Cricket attention drain has strong India analog.** Edmans/Garcia/Norli paper documents -49 bps next-day return after World Cup losses. India cricket → 36-48% volume drops on match days. Nepal cricket impact untested but plausible.
- **Demat account opening growth as contrarian sentiment indicator.** CDSC publishes monthly. The COVID 2020-21 demat surge coincided with the NEPSE peak. Easy to test.
- **Monsoon flood × hydro watershed event study** is the cleanest fundamental signal. Sep 2024 floods caused Rs 2.45B damage to 16 hydro projects. Mechanism is direct: flood damages plant → revenue loss for that specific company. Difference-in-differences design (affected vs unaffected watersheds) would isolate the effect cleanly.

### From Thread 4 (NEPSE structural quirks)
- **The 10% individual circuit doesn't halt trading, it just caps price.** Different from NSE/BSE India where circuit = hard halt. The "queue behind the cap" is a distinct mechanical signature. Repeat-circuit small-caps (BJHL, SKHL named in NEPSE Trading blog) are a documented momentum signature.
- **Pre-open auction collared at +/-2%** from prior close. On big gap-up news the opening is artificially suppressed then explodes at 11:00:01. The first-second-of-continuous tape is a distinctive pattern.
- **TMS broker discretion / front-running is real.** Bhrikuti Stock Broking (Broker #55) suspended April 2026 with Rs 5.11 BILLION owed to investors. CIAA raided NEPSE itself in Aug 2024. This is **counterparty risk to manage, not a signal to trade.**
- **IPO listing-day dump from lottery selling pressure.** Hundreds of thousands of retail get 10-share lots worth ~Rs 1,000. Day-1 of listing is a forced-sell avalanche. Documented as folk knowledge, not measured rigorously. Cheap to test with our data.
- **Bonus share post-adjustment drift.** The arithmetic adjustment is exact, but realized prices drift in the days after. Not measured rigorously. Cheap to test.
- **Right share gap deviates from textbook theory.** TU paper: "Findings are not consistent with the theory of rights offering." Rights issues at face value (Rs 100) create asymmetric payoff. Pre-announcement run-up + post-ex-rights underperformance documented anecdotally.
- **Promoter unlock calendar exists publicly.** `nepsestock.com/upcoming-lock-in-unlock-in-nepal-stock-market` publishes upcoming unlocks. This is the cleanest "supply shock calendar" available — and we know lock-in expiry experiment 02 was inconclusive at N=27. This calendar lets us collect more events going forward.
- **Reliance Spinning Mills "lost IPO" case is a structural risk template.** SEBON approved a prospectus with undisclosed electricity arrears. NEPSE caught it after allotment. Rs 1.74 billion locked for 30+ days. Listing eventually happened with an opening band of Rs 100-300 vs issue price of Rs 820.80 — a brutal ~60% regulatory haircut. **Pattern: book-building IPO → regulatory delay → opening-band haircut.**
- **Day-of-week effect is the only published high-quality empirical microstructure finding for NEPSE.** Everything else (intraday, bonus drift, right drift, IPO listing day, dividend-credit reinvestment) is folk knowledge waiting for a data team. **We are positioned to be that data team.**

## Cross-Cutting Meta-Observations

1. **The absence of Nepal-specific microstructure research is itself an edge.** Published NEPSE literature focuses almost entirely on calendar anomalies by Gregorian date, broad index efficiency, and individual corporate events. Nobody is studying physical/infrastructural/attention channels because they aren't sexy enough for Nepali finance PhDs. **Genuinely uncontested research frontier.**

2. **NEPSE's most exploitable quirks are calendar-driven, not price-driven.** Day-of-week, bonus book-closure, rights announcement, IPO listing-day, promoter unlock, festival calendar, fiscal calendar. **A reliable calendar beats a reliable forecast.**

3. **"The market is the banks."** 82% of turnover, 62% of cap, systemic cross-holdings, leverage stack of Rs 156 billion in pledge loans. Any model that doesn't have a bank-sector contagion factor is mis-specified.

4. **Confound clustering in Dec-Feb is severe.** Kathmandu air pollution + dry-season load shedding + wedding season + cricket NPL + dividend credits + CDSC reporting cycles all overlap. Any Dec-Feb signal needs heavy residualization.

5. **Liquidity reallocation is the dominant macro-shock mechanism.** Real estate freeze + FD rate drop → equity inflow. This explains 2015 blockade, COVID 2020, and probably future regime shocks.

6. **The Sept 2025 Gen Z crash + April 2026 Wagle/money-laundering crashes establish the negative-shock template** for the experiment 03 patch. Combined with the Sarbottam crash (Sept 2021) and the parliament dissolution (Dec 2020), we have a 4-event catalog of political/regulator shocks worth studying as a unified asymmetry test.

## What Should Change in the Bundle (Documentation Gaps Found)

### Real gap: missing Sept 2025 Gen Z crash
This is the biggest political shock in our data window and it's not in `policy_events.csv` or `proposal_experiment_03_patch.md`. Should be added to the patch proposal.

### Enrichment needed: April 2026 events
Our existing docs say "finance minister speech" generically. The actual chain is:
- New PM **Balendra "Balen" Shah** (RSP landslide, sworn in March 27, 2026)
- New FM **Dr. Swarnim Wagle** (appointed same day)
- April 1: Wagle capital-market speech + Deepak Bhatta money-laundering arrest
- April 5: Money-laundering crackdown widens to Sulabh Agrawal (Shanker Group) + Rs 3.73B diverted from 5 listed companies including **Himalayan Reinsurance**
- April 6: Wagle meets brokers, "investors should not panic" → +83.33 rebound
- April 8: Arrest warrants for Deuba couple

### NOT a real gap (correction to a previous claim)
An earlier note said "our docs attribute April 2026 crashes to 'Finance Minister Paudel.'" This was wrong. Our docs use generic "finance minister speech" language, never naming Paudel. The "Bishwanath Paudel" reference in our docs correctly identifies the May 2025 NRB Governor (a different person). The "Bishnu Prasad Paudel" reference is correctly the Oli-era FM in May 2025. Both Paudel references in the bundle are accurate.

## Strategic Status (under L-011 patience mode)

**Build now: nothing.** Same rule as before. The findings are bookmark material.

**Documentation fix worth doing now (small surgical edit):**
- Add Sept 2025 Gen Z crash to `proposal_experiment_03_patch.md`
- Enrich April 2026 entries with Wagle name and the money-laundering crackdown context

**Genuinely novel hypotheses to add to BACKLOG.md (Tier C, research curiosity):**
1. **Ashad insurance tax-drain hypothesis** (highest novelty)
2. **Bikram Sambat turn-of-month effect** (cheapest test)
3. **Monsoon flood × hydro watershed event study** (cleanest mechanism)
4. **Demat account growth as contrarian sentiment indicator** (cheapest sentiment proxy)
5. **IPO listing-day dump from lottery selling pressure** (folk knowledge waiting for data team)
6. **Bonus share post-adjustment drift** (folk knowledge waiting for data team)
7. **Day-of-Nepali-month payday effect** (cheap, novel angle on existing data)
8. **Promoter unlock calendar as forward supply-shock signal** (extends parked experiment 02)
9. **NEPSE turnover collapse paradox** (already in BACKLOG from earlier wave)
10. **Bank cross-holding contagion mapping** (research-level project)

All bookmark only. None to be built before persistence batch-scoring.

## Cross-references

- Original 6-thread research bundle: `00_synthesis.md` through `06_*.md`
- This unconventional wave: `10_unconventional_synthesis.md` (this file), `11_*.md` through `14_*.md`
- Romeo's first-pass review: `99_romeos_takes.md` (still pending review of this unconventional wave)
- Backlog: `experiments/BACKLOG.md`
- Existing learnings: `experiments/LEARNINGS.md` (L-001 through L-011)
