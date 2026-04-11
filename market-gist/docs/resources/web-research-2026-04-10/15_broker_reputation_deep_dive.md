# Thread 5 (Unconventional Wave): Broker Reputation as a Return Predictor

> **Status: Juliet's synthesis. Not yet cross-reviewed by Romeo.**
> This is the deepest research thread of the entire 2026-04-10 session. The
> question — "are there NEPSE brokers whose buying/selling consistently predicts
> directional stock returns?" — is the most actionable side-project hypothesis
> surfaced anywhere in the research bundle. But it has structural confounds
> severe enough that the original framing needs to be reworked.

## Question

Are there NEPSE brokers whose buying/selling consistently predicts directional stock returns?

The setup: we already have a validated mechanical signal called **broker persistence** (when the same brokers keep selling a stock for 7+ days, the stock tends to fall, validated as L-001 in `experiments/LEARNINGS.md`). That's at the **stock level** — we measure whether persistent broker activity in stock X predicts stock X's future move. The question now is at the **broker level**: across all stocks a broker touches, is broker X better or worse than chance at picking winners?

This is the proper "smart money tracking" question. Nepalytix and NEPSE Trading have written instructional content about it but never published actual hit rates or named brokers.

## Method
WebSearch across NepJOL, ResearchGate, SSRN, Google Scholar, NEPSE Trading, Nepalytix, ShareSansar, NepseAlpha, ShareHub, GitHub. Six sections covering: NEPSE-specific research, practitioner tools, adjacent emerging markets, global academic literature, methodology, and counter-arguments.

## TL;DR

**At the "rank all 90 NEPSE brokers by alpha" level: probably no.**
**At the "broker-identified order flow contains information" level: probably yes, but with structural ceilings.**

Zero published academic studies on NEPSE broker-level performance attribution. Zero practitioner leaderboards scored by predictive accuracy (only by turnover volume). NEPSE is **genuinely unexplored territory**. The closest validated analog is Korea, where research studies the regime change (anonymous → transparent) but not individual brokers.

The developed-market literature has settled the principle: **broker-identified order flow contains return-predictive information** in transparent regimes (Linnainmaa & Saar 2012 Finland, Pham 2015 Korea, Duong et al. 2018 multi-market). But typical hit rates are 52-57%, not 65%+, and the cleanest signals are at the **broker-type level** (institutional vs retail vs foreign), not individual broker level.

The most promising reframe is **insider-pipeline detection**: brokers with anomalous net positions 3-10 days before price-moving corporate actions. This overlaps directly with our existing Experiment 01 work on book-closure drift and is closer to mechanical than behavioral.

---

## Section 1: NEPSE-Specific Research and Commentary

### What Exists

**Peer-reviewed academic work on NEPSE broker-level performance attribution: ZERO.**

Searches across NepJOL, ResearchGate, SSRN return NEPSE papers on:
- Index prediction via LSTM/ARIMA/GARCH (multiple)
- Technical analysis and EMH tests on NEPSE
- Stock market concentration and turnover (Pravaha journal — sector concentration, NOT broker concentration)
- Macroeconomic drivers, behavioral factors, dividend policy

**None of these use broker-identified floorsheet data at the broker-as-unit-of-analysis level.** The closest analog (Pravaha "Status of Stock Market Concentration and Turnover at NEPSE") looks at sector and market concentration, not broker concentration.

### What Practitioners Claim (And What They Don't)

**Nepalytix runs a broker-tracking blog series:**
- "How Broker Behavior Shapes NEPSE: Spotting Smart Moves Before the Crowd"
- "Decoding Broker Data: The Hidden Signals Behind NEPSE's Stock Moves"
- "Smart Money Signals: How Institutional Flows Predict NEPSE Rallies"
- "Broker Summary Analysis in NEPSE: Protecting Yourself from Manipulation"
- "Operator Playbook: How Smart Money Accumulates NEPSE Stocks Before Big Moves"

**Critical hedge in Nepalytix's own content:** *"smart money is not always right — institutional investors can and do lose money"* and *"broker data should be used as one tool among many, not as a guaranteed predictor."*

**No article publishes a ranked list of which broker numbers are actually predictive. None publishes a backtested hit rate.**

**NEPSE Trading has a more aggressive series:**
- "How to Track Smart Money Using Broker Data in Nepal"
- "NEPSE Floor Sheet Analysis: Smart Money Tracking Method"
- "Smart Money Concept in NEPSE: How Big Players Move the Market"

**Methodology prescription:** *"track broker activity for at least 5-7 consecutive trading days to confirm accumulation or distribution patterns."* Qualitatively aligned with our validated 7+ day persistence signal but **no named brokers, no hit rates, no statistical validation.**

**ShareSansar, Merolagani, NepseAlpha, ShareHub Nepal, Chukul, nepsebrokeranalysis.com** all publish broker turnover/holdings ranked by **volume**, not by **predictive performance**.

**NepseAlpha has a Broker Holdings page** showing per-stock broker holdings snapshots — useful for feature engineering but not scored for skill.

**ShareSansar's "Top Brokers" page** is purely turnover ranking.

### GitHub Projects

| Project | What it does |
|---|---|
| `suyogdahal/nepse-data` | Scrapes Mero Lagani daily floorsheet |
| `madhuko/nepse_analytics` | "Insights from floorsheet" — minimal |
| `pratyushmishra19/Nepse_floorsheet_analysis` | Flags small-volume transactions as manipulation; has `broker_list.csv` |
| `rajanprasad460/NEPSE_EXTRACTOR` | Extraction library |
| `basic-bgnr/NepseUnofficialApi` | Extraction library |
| `surajrimal07/NepseAPI-Unofficial` | Extraction library |
| `saharshtapi/Nepse-FloorSheet-Analysis` | Extractor |

**None of these compute per-broker forward-return attribution.** Infrastructure exists; analysis does not.

### NEPSE AI Scam Context

The "Nepse AI" app is **not** a broker-signal product — it's a social-engineering malware campaign that used NEPSE branding to push a ScreenConnect remote-access tool and drained bank accounts. ~Rs 800M losses. The branding was incidental — it doesn't represent any claim about brokers.

### Section 1 Verdict

**The question has not been answered anywhere in the NEPSE space.** What exists is narrative content that **assumes** broker tracking works, framed as a teaching tool. **This is a research opportunity, not a signal that the question has been resolved.**

---

## Section 2: Practitioner Tools That Already Do This

**None of the Nepal platforms publish broker skill rankings.** They publish:
- Turnover rank (volume only)
- Holdings snapshots (per stock, per broker)
- Net position per broker per stock per day
- Concentration measures

| Platform | What they have | What they DON'T have |
|---|---|---|
| Nepalytix | Broker-tracking blog series, qualitative methodology | No leaderboard, no hit rates |
| NepseAlpha | Broker Holdings page (per-stock snapshots) | No skill scoring |
| ShareSansar | "Top Brokers" page | Turnover rank only, no skill |
| ShareHub Nepal | Broker dashboard | No predictive metrics |
| Chukul | "Top Broker Top Holding" | No scoring |
| nepsebrokeranalysis.com | Broker analytics | No public skill ranking |
| Merolagani | Floorsheet | No broker-level scoring |

**There is no public NEPSE leaderboard scored by forward-return accuracy.**

Telegram/YouTube channels in the Nepali space mostly sell paid signals **without verifiable track records**. The Nepalytix and NEPSE Trading guides explicitly warn against unverified signal services.

---

## Section 3: Adjacent Emerging Markets

### Bangladesh DSE
**No papers found** on broker-level informed trading. There is broader microstructure literature (Rahman et al. case studies, market development) but nothing isolating broker identity as a return predictor. TREC holder lists are public, FIX API certification exists, but **broker-identified order flow attribution is absent from published literature.**

### Sri Lanka CSE
Only 15 member firms (very small). **No broker-level informed-trading papers found.** Microstructure work on CSE exists (liquidity, EMH) but not broker attribution.

### Pakistan PSX
**No papers found** on broker-identified informed trading in PSX, despite an active retail base and broker-level data availability. **Real gap.**

### Vietnam HOSE
Search returned only general market-access and broker certification guides. **No broker-attribution academic work.**

### The Important Adjacent Finding: Korea KRX

**This is the closest validated analog to NEPSE.** The Korea Stock Exchange has displayed the **identity of the five most active brokers in each stock since October 25, 1999.** This is even more transparent than NEPSE (which shows all broker IDs post-close via floorsheet).

**Pham (2015) "Broker ID transparency and price impact of trades: evidence from the Korean Exchange"** (International Journal of Managerial Finance):
- **Broker identity carries information**
- Orders routed through particular broker types have different permanent price impacts

**Comerton-Forde, Frino, Mollica (2005) "The impact of limit order anonymity on liquidity: evidence from Paris, Tokyo and Korea":** Cross-market study of the natural experiment when these exchanges removed broker IDs. Found price discovery slowed when broker IDs went away.

**But:** Korean research studies the **regime** (anonymous vs transparent), NOT individual brokers. Nobody has published a specific Korean broker skill ranking.

### Section 3 Verdict

**Broker-identified informed-trading research in South Asian markets is essentially nonexistent.** The Korean case is the one emerging-market jurisdiction where it has been studied rigorously, and the finding supports the **existence** of broker-level information content but does not publish individual broker rankings. **NEPSE work would be genuinely novel.**

---

## Section 4: Global Academic Literature

This is where the question is well-answered in principle.

### The Canonical "Broker ID Contains Information" Papers

**1. Linnainmaa & Saar (2012), "Lack of Anonymity and the Inference from Order Flow", Review of Financial Studies**

⭐ **The single most relevant paper for this project.** Uses Finnish data where broker IDs are visible.

Key findings:
- The type of brokers (retail vs institutional vs foreign) is significantly associated with the type of clients they serve
- The permanent price impact of orders from different brokers fits the information profile of the investors associated with those brokers
- Broker ID is a powerful signal about investor identity
- **Institutional-broker-initiated trades have higher permanent price impact than retail-broker trades**
- **Cleanest signal at the broker-TYPE level, not individual broker level**

URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1543298

**2. Grinblatt & Keloharju on Finnish daily data**
Foundational for investor-type performance attribution. Grinblatt-Keloharju (2000) result: **institutional performance > individual performance on 6-month horizons in Finland.** Subsequent work (Grinblatt, Keloharju, Linnainmaa 2009, "IQ, Trading Behavior, and Performance") documents cross-sectional skill differences among traders visible in the same broker-identified dataset.

**3. Duong, Lajbcygier, Lu & Vu (2018), "The effect of anonymity on price efficiency: Evidence from the removal of broker identities", Pacific-Basin Finance Journal**

Documents that when Euronext Paris (April 2001), Tokyo (June 2003), and ASX (November 2005) **removed** broker identity, price discovery slowed:
- In **transparent** markets: ~50% of the 1-hour price reaction occurred in the first 5 minutes
- In **anonymous** markets: only ~20% in the first 5 minutes

**Direct evidence that broker ID accelerates price discovery — i.e., it carries information.**

**4. Foucault, Moinas & Theissen, "Does Anonymity Matter in Electronic Limit Order Markets?"**
Theoretical framework for why broker ID reveals informed trading.

### PIN and Informed-Trading Detection

**5. Easley, Kiefer, O'Hara, Paperman (1996), "Liquidity, Information, and Infrequently Traded Stocks"**
Introduces PIN (Probability of Informed Trading). PIN uses trade-direction counts to back out the probability that a given trade is informed.

**Use case for NEPSE:** PIN can be computed per stock but also per broker-stock pair if we aggregate. R package `PINstimation` (2023) automates this.

**Critical advantage for NEPSE:** Boehmer, Grammig, Theissen (SSRN 887221) show PIN is sensitive to Lee-Ready trade-direction misclassification. **In NEPSE, broker buy/sell sides are labeled directly in the floorsheet — we don't have classification problems.** This is actually an advantage over US data.

**6. Gan et al., "Does PIN measure information? Informed trading effects on returns and liquidity in six emerging markets"**
Mixed results. PIN works but its correlation with returns is noisy.

### Order Imbalance and Retail/Institutional Flow

**7. Chordia & Subrahmanyam (2004), "Order imbalance and individual stock returns"**
Lagged imbalances positively predict current returns.

**8. Kaniel, Saar & Titman (2008), "Individual Investor Trading and Stock Returns", Journal of Finance**
Individuals provide liquidity. Intense retail buying predicts positive excess returns the following month on NYSE.

**9. Boehmer, Jones, Zhang & Zhang (2021), "Tracking Retail Investor Activity", Journal of Finance** ⭐
The BJZZ paper. **Retail net buying predicts ~10 bps outperformance the following week** on a cross-section of US stocks. Most predictive power is not explained by persistence, contrarianism, or news sentiment.

**10. Barber, Huang, Jorion, Odean, Schwarz (2024), "Revisiting BJZZ: Recent Period, Alternative Method, Different Conclusions"** ⭐⭐ **CRITICAL DECAY WARNING**

Replicating BJZZ on 2016-2021 data, the predictive power of the retail order imbalance signal **weakens significantly.**

**Lesson: signals in this family DO decay, sometimes fast.** This is the single most important warning from the literature.

URL: https://arxiv.org/html/2403.17095v1

**11. Choi (2013), "Informed Trading and Expected Returns"**
Shanghai Stock Exchange study. **Top-quintile by institutional-trading-aggressiveness outperforms bottom quintile by ~10.8% annualized for up to 10 months.**

**This is methodologically the closest published analog to what we want to do** — use past institutional trading as an ex ante predictor of future information advantage, sorted into quintiles.

URL: https://www.nber.org/digest/may13/informed-trading-and-expected-returns

### Taiwan Day-Trader Skill Persistence

**12. Barber, Lee, Liu, Odean (2014), "The Cross-Section of Speculator Skill: Evidence from Day Trading", Journal of Financial Markets** ⭐ **STATISTICAL POWER TEMPLATE**

Taiwan 1992-2006:
- Top 500 day traders earned **+61.3 bps/day before fees**
- Bottom-ranked earned **−11.5 bps/day**
- **Critical finding: skill is persistent in a small minority. Only ~1% of day traders consistently earn positive abnormal returns after fees.**
- **The distribution is extremely right-skewed.**

**Direct relevance:** if we apply this template to NEPSE brokers (instead of individual day traders), we should **expect** most brokers to cluster near zero alpha and a small tail to be genuinely skilled. **Statistical test must handle multiple comparisons.**

URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=529063

### Settled Answers From The Developed-Market Literature

| Question | Answer |
|---|---|
| Does broker-identified order flow contain return-predictive information? | **Yes** (Linnainmaa-Saar, Duong et al., Grinblatt-Keloharju) |
| At what granularity? | Intraday-to-daily; predictive power 1 day to several months |
| Typical Sharpe / hit rate? | **5-15 bps/day** for top-decile informed flow (BJZZ, Barber-Lee-Liu-Odean). Hit rates **52-57% directional**, NOT 65%+ |
| Does the signal decay? | **Yes.** Boehmer signals weakened post-2016 in US. Decay is real and fast in liquid markets. Thin markets unknown. |
| Has anyone done it on a broker-identified floorsheet from a thin market? | **No.** Finnish HEX is closest but Finland is not thin. Korean work studies regime, not individual brokers. **NEPSE genuinely unexplored.** |

⚠️ **If our NEPSE signal claims a 65% hit rate, that's suspicious — should trigger a check for lookahead bias or survivorship.** This applies to our existing 7-day persistence signal too. Worth re-checking it at some point.

---

## Section 5: Methodology Recommendation

From the literature, here's the methodology with direct citations.

### Unit of Observation and Reference

- **Unit:** broker × stock × day. Aggregate up to broker × day (across all stocks) and broker × stock (across all days).
- **Signal:** net shares traded = buys − sells in shares, or in NPR value. Use both. BJZZ use both.
- **Normalization:** divide each broker's net by that broker's total turnover in the stock, OR by market turnover, to avoid volume bias. **Top NEPSE brokers do ~6% of turnover, smallest do <0.1% — this is a dominant confound.**

### Forward Windows

- Run **multiple horizons in parallel**: 1d, 5d, 10d, 20d
- Choi uses monthly. BJZZ use weekly. Linnainmaa-Saar look at 1-day permanent price impact.
- **The signal decay profile is itself a diagnostic:** real informed-broker signal should peak at 1-20 days and fade. Spurious signal is either flat or peaks at t+0 (lookahead).
- **Our existing 7-day persistence signal is in the right window.** Use 5d and 10d as primary forward horizons to stay consistent.

### Aggregation

Two separate measures per broker, computed independently:

1. **Cross-sectional skill** (Linnainmaa-Saar style): for each day, compute `sign(broker_net) × forward_return(stock)`. Time-average per broker across all days.

2. **Per-stock consistency:** for each broker × stock pair, compute hit rate across all days with non-trivial activity. Then aggregate distribution per broker. Catches brokers who are only skilled in specific stocks (plausible for a thin market where brokers serve local client bases).

**Report both. If they disagree, that's information.**

### Statistical Test

- **Bootstrap, not t-test.** Returns are fat-tailed, broker volumes are fat-tailed, ~90 brokers × 200-ish stocks × thousands of days kills parametric assumptions.
- **Block bootstrap over days** (not trades) to preserve serial correlation. Politis-Romano stationary bootstrap with mean block length ≈ 20 days is standard.
- **Multiple-comparison correction:** with 90 brokers, expect ~4-5 to hit p<0.05 by chance. Use Benjamini-Hochberg FDR at 5% or White's Reality Check / Hansen's SPA test. Barber-Lee-Liu-Odean explicitly use this framing for Taiwan day traders.
- **Random permutation test:** shuffle broker labels across trades, recompute the skill metric, generate null distribution. Very clean and non-parametric.
- **Report Information Ratio** (mean signal / std signal), not Sharpe — we're measuring a classification-like quantity not a strategy return.

### The Three Structural Confounds

#### Confound 1: Market-Making vs Directional
**Cannot cleanly separate from floorsheet-only data.**

Proxy: a market maker has (a) high turnover, (b) low absolute net position (buys ≈ sells), (c) tight holding period, (d) presence on both sides of the same stock on the same day.

**Flag brokers with `|net| / turnover < 0.1` as likely market-makers and either exclude or segment them.** Standard in the literature (Schultz "Who Makes Markets", Journal of Financial Markets 2003).

#### Confound 2: Proprietary vs Client Flow ⭐ **THE BIGGEST CEILING**
**Cannot separate at all without account-type tags. NEPSE does not expose these publicly.**

Every broker's "net" is a blend of prop + 1000s of client orders. Even if 5% of a broker's flow is informed prop, the other 95% of client noise drowns it.

**This is a structural ceiling on the signal.**

Linnainmaa-Saar dealt with this by looking at broker **types** (retail-focused vs institutional-focused) rather than individual brokers. **We should probably segment NEPSE brokers into tiers by client-mix proxy** (e.g., online-client ratio, which ShareSansar publishes — 28.56% of active clients use online trading).

#### Confound 3: Volume Heterogeneity
Top brokers do 60x the volume of small ones.

**Use broker-volume tertiles/quintiles and report results within each tier.** Never rank raw — small brokers will dominate the leaderboard with lucky streaks. Always weight by trade count and report sample size per broker.

### Survivorship and Suspensions

Include suspended brokers (Bhrikuti #55, suspended April 2026 for Rs 5.11 BILLION client fund misuse; earlier suspensions) in training but exclude their suspension period.

**Track them as a natural experiment:** did Bhrikuti's broker signal quality change in the months before suspension? If it did, we've found a regulatory-risk leading indicator, not alpha.

### Stability Over Time (THE MAKE-OR-BREAK TEST)

Barber-Lee-Liu-Odean find Taiwan day-trader skill **is** persistent at the individual level but the mass of the distribution is not.

**Test cross-period stability explicitly:** split the sample into two halves, rank brokers in each half, compute Spearman rank correlation.
- **<0.3:** skill is not persistent and the leaderboard rotates → no usable signal
- **0.3-0.5:** weak persistence → publishable but not actionable
- **>0.5:** real signal

BJZZ and the BJZZ-revisit paper show this stability collapsing in the US after 2016.

### Composite Methodology Template

**Choi (2013) on Shanghai institutional ownership + Linnainmaa-Saar (2012) on Finnish broker IDs** is the composite template:

1. Sort brokers into **quintiles** by past-period net-flow aggressiveness or past-period realized informed-trading measure
2. Build portfolios that **long-follow the top quintile and short-follow the bottom quintile**
3. Measure **forward-horizon return spread**
4. Test **cross-period persistence** (Spearman rank correlation)
5. Use **block bootstrap and FDR correction**

**This is implementable on NEPSE floorsheet data. Nobody has published it.**

---

## Section 6: Counter-Arguments and Known Confounds

### Reasons It May NOT Work on NEPSE

1. **Client-order dilution (structural ceiling).** Already covered. Strongest a priori reason to expect the signal will be weak. Linnainmaa-Saar found the signal primarily at broker-TYPE level, not individual broker level — Finland had clearer type segmentation than NEPSE.

2. **Decay precedent.** BJZZ's US retail-flow signal decayed sharply after 2016. NEPSE is much earlier in its informational efficiency curve, so decay may be slower, but **design in-sample/out-of-sample splits from day one** and watch for decay.

3. **Cross-sectional rotation.** If skilled broker identity rotates year to year (informed clients move between brokers), the signal is not capturable in real-time.

4. **Broker mergers, license transfers, rebranding.** NEPSE has ~90 active brokers but ID numbers persist through ownership changes. A broker that was "skilled" under old ownership may not be after new ownership. **Non-trivial data problem.**

5. **Regulatory asymmetry masquerading as skill.** ⚠️ **THE BIGGEST RISK**

The Ridi Hydropower case (Guru Prasad Neupane, Rs 32.3M insider offenses, March 2023), the NEPSE CEO Saud / SEBON Chair Dhungana Sarbottam Cement scandal, and SEBON's list of 51 overvalued/irregular companies (2021) together suggest that in NEPSE, **"which broker is trading ahead of news" is probably more about insider pipelines than forecasting skill.**

**If our top-quintile "skilled" brokers turn out to be the ones facilitating insider trades, our signal is a regulatory-risk early-warning system, not alpha — and acting on it may itself be legally fraught.** Front-running insider flow is still dealing on MNPI in many jurisdictions, and SEBON enforcement is tightening.

6. **Selection bias / survivorship.** Brokers that blew up (Bhrikuti) leave the tape. Their "skill" during their life is measured; their failure is not in the return series.

7. **Market maker pollution.** Top-turnover brokers disproportionately market-make in the most liquid stocks. Their "net" is close to zero. If we don't segment them out, they anchor the distribution at zero and we lose statistical power.

8. **Thin-market microstructure noise.** NEPSE has circuit breakers, low float, high concentration in banking/hydro. Forward returns are contaminated by mechanical effects (circuit hits, book-closure drift — which we already know from Experiment 01).

9. **The Boehmer decay finding** — explicit precedent that this signal class decays even in liquid markets.

### What Would Constitute Evidence the Hypothesis Is Real

**Minimum bar (all 5 required):**
- Top-quintile − bottom-quintile 10-day forward return spread of **>30 bps**, significant after FDR correction
- Cross-period Spearman rank correlation of broker skill **>0.4**
- Effect survives segmenting out market makers (`|net|/turnover < 0.1`) and controlling for stock-level momentum and book-closure effects
- Effect is **not driven by 1-2 brokers** (Gini of skill distribution matters — if one broker carries the signal, it may be a single insider pipeline)
- Effect **decays monotonically** from t+1 to t+20 (not spiky — spikes are lookahead or microstructure)

**Verdict matrix:**
- **All 5: real signal.** Promote to research-shadow lane.
- **3-4 of 5:** publishable microstructure paper but not actionable alpha
- **<3 of 5: walk away.** The hypothesis is folk knowledge that doesn't survive contact with data.

---

## The Reframe That Actually Matters

> **"Reframe from 'which brokers are skilled' to 'which broker types are skilled.'"**

Linnainmaa-Saar's clean signal was at the broker-TYPE level (institutional vs retail vs foreign), not individual broker.

We don't have type tags but we have **proxies**:
- Volume tier (top 10 brokers vs bottom 30)
- Online-client ratio (ShareSansar publishes 28.56% of active clients use online trading)
- Historical prop-desk reputation
- Geographic concentration (Kathmandu vs out-of-valley)

**3-5 broker types instead of 90 individual brokers** is a much smaller multiple-comparison burden and matches the validated methodology.

---

## The Side Discovery That's Probably MORE Promising

The agent recommended a parallel workstream that's actually more promising than the main hypothesis:

> **"Brokers that show anomalous net position 3-10 days before price-moving corporate actions (book-closure, right-issue, bonus announcement) are potentially leaking. This overlaps your existing Experiment Lab work on book-closure drift and is probably the more defensible signal on NEPSE — it's mechanical, not behavioral."**

This is interesting because it **directly extends our existing corporate action work (Experiment 01)** with a new lens. Instead of "did the stock move after the announcement?" we'd ask "did specific brokers move into the stock 3-10 days before the announcement?"

If yes, we have an **insider-pipeline detection signal**.

If no, the announcement was a clean surprise.

**This is closer to how real microstructure research would attack NEPSE.**

---

## Two Tracks Recommendation

### Track A — Broker Skill Feasibility Spike (~2 weeks)

**Goal:** Determine whether individual NEPSE brokers have measurable directional skill.

**Steps:**
1. Compute per-broker 10-day forward-return hit rate for all 90 brokers on existing floorsheet data
2. Compute cross-period Spearman rank correlation between two halves of the sample
3. Plot the skill distribution
4. Apply the 5-criterion verdict matrix

**Decision rule:**
- Rank correlation >0.4 AND distribution distinguishable from permutation null → promote to full experiment with broker-TYPE framing (Linnainmaa-Saar style)
- Rank correlation <0.3 → kill the project entirely
- In between → publishable curiosity but not actionable

### Track B — Insider-Pipeline Detection (~1-2 weeks)

**Goal:** Identify brokers whose net positions consistently predict corporate-action announcements 3-10 days in advance.

**Steps:**
1. Use existing corporate action event table from Experiment 01
2. For each event, compute each broker's net position change in the [-10, -3] window before the announcement
3. Identify brokers with consistent anomalous positioning across multiple events
4. Test: same brokers appearing across multiple event types (= structural pipeline) or single events (= noise)
5. Cross-reference with SEBON enforcement actions to validate

**Output:** A "broker pipeline detection" feature that flags suspicious pre-announcement positioning. Mechanical, not behavioral.

**Bonus:** If we find consistent insider pipelines, that's both a signal AND a regulatory risk warning. **Important caveat: do not act on this signal without legal review.** Trading on identified MNPI flows is itself MNPI dealing in many jurisdictions.

---

## Specific Names Worth Following

### Papers To Read First (In Order)
1. **Linnainmaa & Saar (2012)** — methodology anchor
2. **Barber, Lee, Liu, Odean (2014)** — statistical power template
3. **Boehmer, Jones, Zhang, Zhang (2021), BJZZ** — signal construction template
4. **Barber et al. (2024) BJZZ revisit** — decay warning
5. **Choi (2013)** — emerging-market analog
6. **Duong, Lajbcygier, Lu, Vu (2018)** — anonymity removal regime study

### People To Follow
- Juhani Linnainmaa
- Gideon Saar
- Ekkehart Boehmer
- Matti Keloharju
- Brad Barber
- Terrance Odean

### Tools
- R package `PINstimation` (2023) for PIN estimation
- R package `frds` for information-asymmetry measures
- Arrow/Polars for floorsheet aggregation at scale

---

## Final Honest Assessment

**Is "broker reputation as a return predictor" a real research direction?**

**Qualified yes at the methodology level** — the developed-market literature has validated that broker-identified order flow carries information, and the Korean, Finnish, and Taiwanese natural experiments confirm this in transparent-broker-ID regimes (which NEPSE is).

**Qualified no at the individual NEPSE broker skill ranking level.** The structural confound — 95% client dilution + market-making contamination + insider-pipeline contamination — means the raw signal at the individual-broker level is probably weak and noisy. Any sharp signal is more likely to be an insider-pipeline leak than forecasting skill.

**The real discovery opportunity is not "which broker is best" — it's the first published broker-identified order-flow study of a thin South Asian market.** That is a novel empirical contribution regardless of whether the individual-broker ranking works, because the current literature has nothing in this market class.

### Recommendations Summary

| Priority | Action |
|---|---|
| **DO NOW** | Nothing. L-011 patience mode applies. |
| **DO AFTER PERSISTENCE BATCH-SCORING** | Run Track A feasibility spike (2 weeks). 5-criterion verdict matrix. Only proceed to full experiment if rank correlation >0.4. |
| **DO IN PARALLEL WITH TRACK A** | Run Track B (insider-pipeline detection) — directly extends Experiment 01, more mechanical, more defensible. |
| **REFRAME** | "Which brokers are skilled" → "which broker TYPES are skilled". 3-5 segmented groups, not 90 individuals. |
| **DO NOT** | Build either track now. Build either track without the 5-criterion verdict matrix. Act on insider-pipeline findings without legal review. |
| **ALSO: re-check existing persistence signal** | If our 7-day persistence hit rate exceeds 65%, that's outside the published range (52-57%) and warrants a lookahead-bias check. |

---

## Master Source List

### NEPSE Practitioner Sources
- [How Broker Analysis Helps You Predict NEPSE Market — NEPSE Trading](https://nepsetrading.com/insights/how-broker-analysis-helps-you-predict-nepse-market)
- [How to Track Smart Money Using Broker Data in Nepal — NEPSE Trading](https://nepsetrading.com/insights/how-to-track-smart-money-using-broker-data-in-nepal)
- [NEPSE Floor Sheet Analysis: Smart Money Tracking Method — NEPSE Trading](https://nepsetrading.com/insights/nepse-floor-sheet-analysis-smart-money-tracking-method)
- [Smart Money Concept in NEPSE — NEPSE Trading](https://nepsetrading.com/insights/smart-money-concept-in-nepse-how-big-players-move-the-market)
- [How Broker Behavior Shapes NEPSE — Nepalytix](https://nepalytix.com/blog/how-broker-behavior-shapes-nepse-spotting-smart-moves-before-the-crowd)
- [Decoding Broker Data — Nepalytix](https://nepalytix.com/blog/decoding-broker-data-the-hidden-signals-behind-nepses-stock-moves)
- [Smart Money Signals — Nepalytix](https://nepalytix.com/blog/smart-money-signals-how-institutional-flows-predict-nepse-rallies)
- [Broker Summary Analysis in NEPSE — Nepalytix](https://nepalytix.com/blog/broker-summary-analysis-in-nepse-protecting-yourself-from-manipulation)
- [Operator Playbook — Nepalytix](https://nepalytix.com/blog/operator-playbook-how-smart-money-accumulates-nepse-stocks-before-big-moves)
- [How to Read NEPSE Floor Sheets — Nepalytix](https://nepalytix.com/blog/how-to-read-nepse-floor-sheets-a-complete-guide-for-investors)
- [NepseAlpha Broker Holdings](https://nepsealpha.com/broker-holding)
- [NepseAlpha Broker Holding Changes](https://nepsealpha.com/broker-holding-changes)
- [ShareSansar Top Brokers](https://www.sharesansar.com/top-brokers)
- [ShareHub Nepal Broker Dashboard](https://sharehubnepal.com/broker/dashboard)
- [Chukul Top Broker Top Holding](https://chukul.com/top-broker-top-holding)

### NepJOL NEPSE Research
- [Stock Market Concentration and Turnover at NEPSE — Pravaha](https://nepjol.info/index.php/pravaha/article/view/57973)

### NEPSE GitHub Tooling
- [suyogdahal/nepse-data](https://github.com/suyogdahal/nepse-data)
- [madhuko/nepse_analytics](https://github.com/madhuko/nepse_analytics)
- [pratyushmishra19/Nepse_floorsheet_analysis](https://github.com/pratyushmishra19/Nepse_floorsheet_analysis/blob/master/Broker_list_scrape.py)
- [rajanprasad460/NEPSE_EXTRACTOR](https://github.com/rajanprasad460/NEPSE_EXTRACTOR)
- [basic-bgnr/NepseUnofficialApi](https://github.com/basic-bgnr/NepseUnofficialApi)
- [surajrimal07/NepseAPI-Unofficial](https://github.com/surajrimal07/NepseAPI-Unofficial)

### NEPSE Regulatory and Survivorship
- [Bhrikuti Broker #55 Suspension — Bajarko Chirfar](https://eng.bajarkochirfar.com/2026/04/09/bhrikuti-stock-brokings-license-suspended-rs-5-11-billion-owed-to-investors/)
- [SEBON Suspends Broker 55 — Farsight Nepal](https://farsightnepal.com/news/market-dips-marginally-sebon-revises-circuit-breakers-suspends-broker/)
- [Insider trading taints Nepal capital market — Nepali Times](https://nepalitimes.com/here-now/insider-trading-taints-nepal-capital-market)
- [Insider Trading in Nepal's Stock Market — ShareSansar](https://www.sharesansar.com/newsdetail/insider-trading-in-nepals-stock-market-and-its-effect-on-middle-class-investors-2025-05-16)
- [SEBON list of 51 companies with irregular trading — Khabarhub](https://english.khabarhub.com/2021/15/191064/)
- [Insider Trading in Nepal — Khatapana](https://khatapana.com/blogs/21/insider-trading-in-nepal-is-sebon-finally-taking-c)

### Global Academic — Broker ID and Informed Trading
- [Linnainmaa & Saar — Lack of Anonymity and the Inference from Order Flow (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1543298)
- [Linnainmaa & Saar — NY Fed working paper](https://www.newyorkfed.org/medialibrary/media/research/conference/2010/cb/LinnainmaaSaar20101.pdf)
- [Duong, Lajbcygier, Lu, Vu — Effect of Anonymity on Price Efficiency (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3197485)
- [Comerton-Forde, Frino, Mollica — Paris, Tokyo, Korea anonymity](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=695602)
- [Foucault, Moinas, Theissen — Does Anonymity Matter](https://www.tse-fr.eu/sites/default/files/medias/doc/by/moinas/moinas_foucault_theissen.pdf)
- [Grinblatt, Keloharju, Linnainmaa — IQ, Trading Behavior and Performance (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1364014)
- [Choi — Informed Trading and Expected Returns (Yale)](https://spinup-000d1a-wp-offload-media.s3.amazonaws.com/faculty/wp-content/uploads/sites/27/2019/06/informed.pdf)
- [Informed Trading and Expected Returns — NBER Digest](https://www.nber.org/digest/may13/informed-trading-and-expected-returns)
- [Kaniel, Saar, Titman — Individual Investor Trading and Stock Returns (JF)](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2008.01316.x)
- [Boehmer, Jones, Zhang, Zhang — Tracking Retail Investor Activity (JF)](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13033)
- [Revisiting BJZZ — arXiv 2403.17095](https://arxiv.org/html/2403.17095v1)
- [Revisiting BJZZ — Springer FMPM](https://link.springer.com/article/10.1007/s11408-025-00487-4)
- [Barber, Lee, Liu, Odean — Cross-Section of Speculator Skill (Taiwan)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=529063)
- [Order Imbalance and Individual Stock Returns — Chordia & Subrahmanyam](https://www.sciencedirect.com/science/article/abs/pii/S0304405X03001752)
- [Schultz — Who Makes Markets?](https://www.acsu.buffalo.edu/~keechung/MGF743/Readings/H4%20Who%20makes%20markets.pdf)

### PIN Measure
- [PIN measure — frds reference](https://frds.io/measures/probability_of_informed_trading/)
- [PIN: Measuring Asymmetric Information — R Journal 2013](https://journal.r-project.org/archive/2013/RJ-2013-008/RJ-2013-008.pdf)
- [PINstimation R package — R Journal 2023](https://journal.r-project.org/articles/RJ-2023-044/)
- [Does PIN measure information? Six emerging markets](https://www.sciencedirect.com/science/article/abs/pii/S1059056015000659)

### Methodology
- [Walk-Forward Permutation Tests — Medium](https://medium.com/@alex.mountain.pa/how-i-develop-trading-strategies-permutation-tests-and-trading-strategy-development-with-python-5e8c50d0b256)
- [Walk-Forward Validation Framework for Market Microstructure Signals — arXiv](https://arxiv.org/html/2512.12924v1)
