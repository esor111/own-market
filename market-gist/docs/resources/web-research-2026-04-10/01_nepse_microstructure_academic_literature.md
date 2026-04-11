# Thread 1: NEPSE Microstructure Academic Literature

## Question
What does published academic research say about NEPSE microstructure and thin emerging market dynamics? Are our findings consistent with the literature, or are we discovering things that have been disconfirmed?

## Method
WebSearch across Google Scholar, NepJOL, ResearchGate, SSRN, MPRA, and NRB Economic Review. Direct PDF reading where available.

## Key Findings

### 1. NEPSE Calendar Anomalies (Strongly Validates L-009)

**Joshi & K.C. (2005/2006) — "The Nepalese Stock Market: Efficiency and Calendar Anomalies"**
- Sample: Daily NEPSE index, 1 Feb 1995 – 31 Dec 2004 (~10 years)
- Method: OLS with day-of-week, month, holiday, half-month, turn-of-month dummies
- **Persistent day-of-the-week anomaly** (significant)
- **No** month-of-the-year effect (January effect rejected at the index level)
- Holiday, turn-of-month, time-of-month effects disappeared over time
- URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=743666
- Mirror: https://mpra.ub.uni-muenchen.de/26999/

**KMC Journal (2024) — "Trading Day Effect and Volatility Clustering in NEPSE Returns"**
- EGARCH(1,1) with day-of-week effects
- Wednesday and Thursday returns significantly higher than Sunday
- URL: https://www.nepjol.info/index.php/kmcj/article/view/90651

**Pravaha (2024) — Month-wise return distribution in NEPSE**
- Highest average daily returns: Kartik (Oct/Nov)
- Lowest: Falgun (Feb/Mar)
- URL: https://nepjol.info/index.php/pravaha/article/download/76887/58848

**Cross-validation from Bangladesh (DSE)**
- Same Sunday-weak / Thursday-strong pattern (mirror of NEPSE)
- Hossain et al., Cogent Economics 2019: AMH and momentum in DSE
- URL: https://doi.org/10.1080/23322039.2019.1650441

**Implication for our work:** Our L-009 hydro Nov→Jan finding is consistent with the published Kartik-strong / Falgun-weak monthly pattern. Joshi (2005) rejected a January effect at the **index level**, but our finding is about the **hydro sub-index** specifically — see thread 5 for the dividend-cycle mechanism that amplifies January for hydros.

### 2. Adaptive Market Hypothesis (Theoretical Cover for Frozen-Champion Discipline)

**Jha & Dhungana — "Evidence on Presence of Adaptive Market Hypothesis in Nepal Stock Exchange"**
- Sample: NEPSE monthly returns 2003-2019, 12 rolling 5-year windows
- Method: Linear (autocorr, variance ratio) + non-linear (BDS, McLeod-Li, Engle LM)
- **Result:** NEPSE moves between efficient and inefficient regimes (AMH supported)
- URLs:
  - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4046990
  - http://necs.org.np/wp-content/uploads/2022/03/03_Evidence-on-Presence-of-Adaptive-Market-Hypothesis-in-Nepal-Stock-Exchange.pdf

**Why this matters:** This is the published theoretical justification for our frozen-champion + periodic re-evaluation discipline. The market is neither permanently efficient nor permanently inefficient, so rules have shelf lives. Romeo's "do not change rules without repeated evidence" feedback aligns directly with AMH.

### 3. Volatility Clustering (Validates GARCH-style Adjustments)

**Dangal & Gajurel (2021/2022) — GARCH Family Models on NEPSE**
- Sample: Daily NEPSE 2011-2020 (2,059 observations)
- Method: GARCH(1,1), GARCH-M, EGARCH, TGARCH
- **Strong volatility clustering confirmed**
- **Leverage effect present** (asymmetric)
- **No significant risk premium** — higher volatility does NOT command higher returns
- URL: https://www.nepjol.info/index.php/TUJ/article/view/43514

**NRB Variance Ratio Test**
- "Stock Market Efficiency in Nepal: A Variance Ratio Test", NRB Economic Review vol. 28(2), 2016
- Rejects random walk on daily and weekly returns across most sectors
- URL: https://ideas.repec.org/a/nrb/journl/v28y2016i2p61.html

### 4. Bank Stock Fundamentals (Things We Should Test)

**Bhattarai — "Fundamentals of Stock Price in Nepalese Commercial Banks"**
- Variables tested: EPS, BVPS, P/E, DPS, size
- **BVPS:** correlation 0.768 with bank stock price (significant at 1%) — strongest fundamental
- **P/E ratio:** correlation 0.516 (significant at 1%)
- **ROE:** correlation 0.384 (significant at 5%) — weakest
- **R²:** ~72.3% of stock price variation explained
- URL: https://www.nepjol.info/index.php/irjms/article/download/27887/23026/82659

**NRB — Rabindra Joshi — "Effects of Dividends on Stock Prices in Nepal"**
- NRB Economic Review vol. 24(2), 2012
- Confirms dividend signaling dominates retained earnings in Nepal
- **Directly validates our dividend annotation finding (L-001)**
- URL: https://ideas.repec.org/a/nrb/journl/v24y2012i2p5.html

**Pradhan (2003)** — foundational paper on dividend dominance in Nepal

**Critical gap for us:** The published literature tests fundamentals as **contemporaneous price explainers**, not as **out-of-sample return predictors**. Nobody has published a walk-forward backtest showing EPS or BVPS signals produce positive Sharpe in NEPSE after costs. This is a gap we could fill.

### 5. The Surprising Finding: Fama-French is REVERSED in Nepal

**"The Cross-Section of Stock Returns: An Application of Fama-French Approach to Nepal" (2016, Modern Economy)**
- Sample: 134 NEPSE companies, Dec 2004 – Jul 2011
- **Result:** Big value stocks **outperform**, small growth stocks **underperform** — opposite of US/global Fama-French
- Value factor and market factor more significant than size
- URLs:
  - http://libra.article2submit.com/id/eprint/1474/1/ME_2016022614475393.pdf
  - https://file.scirp.org/Html/13-7201213_63860.htm

**Why this matters for us:** If we ever build portfolio construction logic, this matters a lot. Most quant intuition assumes a small-cap premium. In Nepal, that's empirically wrong. Tilt toward larger-cap value in banks is empirically justified.

### 6. Macroeconomic Drivers

**NRB — "Determinants of Stock Market Performance in Nepal"**
- Sample: Monthly data Aug 2000 – Jul 2014
- Method: ARDL / cointegration
- **Money supply (M2):** positive significant, both short- and long-run
- **Interest rate (T-bill):** positive long-run; negative short-run dampening
- **CPI:** positive long-run
- **Exchange rate:** positive long-run
- **GDP:** **negative** relationship (counterintuitive — possibly because GDP growth in Nepal is agriculture-driven while NEPSE is bank-dominated)
- **NRB policy on loan-against-share collateral has detectable impact on NEPSE**
- URL: https://www.nrb.org.np/contents/uploads/2022/12/vol26-2_art2.pdf

### 7. Herding Behavior (Validates "Neutral Hides Bearish")

**"Herding Behavior in Nepali Stock Market" (NCC Journal)**
- Herding significant in **bullish** trends, absent/weaker in bearish trends
- URL: https://nepjol.info/index.php/NCCJ/article/view/24746

**Pokharel (SSRN, 2020)**
- Herding + social interaction + media effect all positive on equity decisions
- URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3687104

**Why this matters:** The "neutral hides bearish" problem we found (agents calling neutral when they should call bearish) maps onto regime-dependent herding. In bull regimes there's a herd to follow, in bear regimes there isn't.

### 8. Market Concentration

**"Status of Stock Market Concentration and Turnover at Nepal Stock Exchange" (Pravaha)**
- Sample: 2003/04 – 2019/20
- Top-10 firm concentration fell from 66% to 35%
- Commercial banking sector is 72% of concentration observations
- **Negative association between concentration and turnover** (lower concentration → higher liquidity)
- URL: https://nepjol.info/index.php/pravaha/article/view/57973

### 9. The Massive Gap: Broker Order Flow as Return Predictor

**Zero published academic studies on NEPSE broker-floorsheet persistence as a return predictor.**

Direct quote from the research agent:

> "This is remarkable because NEPSE's transparency (buyer broker ID + seller broker ID on every trade) is rare globally and should be a natural laboratory for PIN, order imbalance, and order splitting studies."

What exists in published literature for OTHER markets:
- Chordia, Roll, Subrahmanyam — order imbalance predicts returns globally
- Kelley & Tetlock (2013), Boehmer et al. — retail order flow imbalance positively predicts weekly returns (decayed post-2017)
- Easley et al. — PIN (Probability of Informed Trading) framework, foundational
- R package `PINstimation` exists and could be applied directly to NEPSE floorsheet data

**Implication for us:** Our broker-persistence work is academically virgin territory in NEPSE. The closest published applied work in adjacent markets says the edge is real but decays over time (5-10 years typically). This validates our frozen-champion + periodic re-evaluation discipline — we should expect decay.

## Things We Should Test (From Published NEPSE Validation)

The literature says these signals should work in NEPSE but we haven't tested them:

1. **BVPS cross-sectional ranking** — Bhattarai correlation 0.768. Strongest fundamental signal in published research.
2. **P/E ratio z-score** across bank universe — 0.516 correlation, consistently significant.
3. **Bonus issue announcements** — IRJMS paper finds significant positive price impact. We dismissed bonus shares in L-001 due to double-counting; should re-test with clean dedup.
4. **NRB share-collateral policy changes** as discrete events — NRB's own paper confirms detectable impact.
5. **Walk-forward backtest of NPL/CAR ranked bank portfolios** — published research only tests contemporaneous correlation; nobody has published an out-of-sample test.

## Things The Literature Says That Contradicts Naive Assumptions

- **GDP has a NEGATIVE relationship with NEPSE** (NRB Khatri paper). Not positive as intuition suggests.
- **January effect at the index level: rejected** (Joshi 2005). But the hydro sub-index January effect is real (see Investopaper data, thread 5).

## Caveats

- The agent could not access Google Scholar or SSRN directly; used WebSearch with public results
- Sri Lanka CSE and Pakistan PSX coverage was thin
- Some Nepal papers are by regional journals without full indexing; quality varies
- The "no published broker persistence study" finding is by absence of evidence; possible (unlikely) that a paywalled working paper exists

## Conclusion

**Our findings are consistent with published NEPSE literature where overlap exists.** We are not rediscovering things that have been disconfirmed. The five-month seasonal pattern, dividend-driven price effects, volatility clustering, and herding behavior all have published academic backing.

**Our broker persistence work is in academically virgin territory** for NEPSE specifically. The data type (broker-identified floorsheet) is rare globally and should be treated as a natural laboratory. Decay risk is the primary concern from analogous developed-market evidence.

**The cleanest academic contribution we could make:** apply VPIN (Volume-synchronized Probability of Informed Trading) to the NEPSE floorsheet using the off-the-shelf `PINstimation` R package. Nobody has done it. The data is unique. We are not building toward publication, but knowing the gap exists tells us our work has value beyond personal use.

## Master Source List

- Joshi & K.C. (2005) calendar anomalies: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=743666
- NRB variance ratio efficiency: https://ideas.repec.org/a/nrb/journl/v28y2016i2p61.html
- Jha & Dhungana AMH: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4046990
- Dangal & Gajurel GARCH: https://www.nepjol.info/index.php/TUJ/article/view/43514
- Bhattarai fundamentals (BVPS/PE/ROE): https://www.nepjol.info/index.php/irjms/article/download/27887/23026/82659
- NRB Khatri macro: https://www.nrb.org.np/red/vol31-1_art3/
- NRB "Determinants of Stock Market Performance": https://www.nrb.org.np/contents/uploads/2022/12/vol26-2_art2.pdf
- NRB Rabindra Joshi dividends: https://ideas.repec.org/a/nrb/journl/v24y2012i2p5.html
- Pravaha market concentration: https://nepjol.info/index.php/pravaha/article/view/57973
- Fama-French Nepal: http://libra.article2submit.com/id/eprint/1474/1/ME_2016022614475393.pdf
- Sitaula et al. LSTM NEPSE: https://www.sciencedirect.com/science/article/pii/S2666827022000706
- MDPI NEPSE direction + news headlines: https://www.mdpi.com/2225-1146/12/2/16
- Bangladesh DSE momentum + AMH: https://doi.org/10.1080/23322039.2019.1650441
- KMC Trading Day Effect (2024): https://www.nepjol.info/index.php/kmcj/article/view/90651
- NEPSE IPO short-run performance: https://nepjol.info/index.php/jnma/article/download/62096/46883/182934
- Pravaha monthly return distribution: https://nepjol.info/index.php/pravaha/article/download/76887/58848
