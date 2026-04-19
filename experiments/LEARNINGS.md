# Experiment Learnings

This file captures what we learned, what resources we used, and what conclusions we reached. Each entry is a self-contained learning that future work can reference.

---

## L-001: Corporate Action Timing Creates Measurable Price Drift on NEPSE (2026-04-09)

### What We Tested
Whether corporate action announcements (AGM notices, book closures, dividend notices, rights issues, bonus shares) create predictable price moves on NEPSE stocks.

### Data Used
- **Price data:** 1,570 daily Sharesansar CSV snapshots (2021-2026), 14 symbols (8 banking + 6 hydropower)
- **Corporate action data:** Scraped from ShareSansar per-company feeds (company-dividend, company-rightshare, company-agm, company-announcements, company-events). 1,496 raw events built into a standardized event table.
- **Baseline method:** Per-symbol trailing 120-day rolling baseline with 30-day minimum history. Each event's return is compared to what the stock typically did in the same window recently. This strips out "the market was falling anyway."
- **Market regime:** Synthetic market proxy from median daily diff_pct across all traded symbols, with SMA-200 regime classification (above/below).

### Key Finding: Two Forward-Actionable Signals Survived

After baseline adjustment, anchoring fix (max 10-day forward gap), and phase-2/phase-3 filtering:

| Signal | Window | N | Neg Hit Rate | Excess Mean | p-value | Scope |
|---|---|---|---|---|---|---|
| **book_closure_notice** | drift_2_10 | 116 | 62.1% | -3.68% | 0.0006 | Cross-sector (banks + hydro) |
| **dividend-family notice** | drift_2_10 | 93 | 68.8% | -1.83% | 0.001 | Bank-led (75.8% for banks, hydro inconclusive) |

"drift_2_10" means: stock return from trading day +2 to trading day +10 after the announcement. This is forward-actionable — you see the notice, then the move happens.

### What Collapsed Under Baseline Adjustment

The original (no-baseline) run showed 12 signals with 77-97% hit rates. After baseline adjustment, 8 collapsed to noise. The survivors dropped from spectacular-looking numbers to honest 62-69% hit rates. This is expected — the study period was dominated by a bear market (2021-2024), so raw negative drift was mostly just "the market was falling."

Specific collapses:
- **Right share notice:** 82.9% raw negative → 52.9% adjusted. Dead.
- **Bonus share notice:** 97.1% raw negative → survived only in small N with weak p. Dead.
- **AGM drift_2_10:** 58.8% adjusted, p=0.014 — real but below the 60% threshold.

### Book-Closure Timing Discovery

We traced the AGM → book-closure → meeting timeline across 113 matched pairs:

- **45% of book closure notices arrive the same day or before the AGM notice** (median gap = 1 day overall, 0 days for banks)
- **90% arrive within 12 days of AGM notice**
- Book closure to AGM meeting gap: median 19 days, range 7-33

This means the "pre-window leakage" signal on book_closure_notice is not mysterious — it's that AGM notices and book closure notices often arrive together, and stocks drift down after both. The real actionable trigger is the announcement itself, not some hidden insider leakage.

**AGM seasonality:** 48% of bank AGMs happen in Dec-Jan. 62% of hydro AGMs in Sep-Jan. This is a predictable calendar window.

### Regime Limitation

95% of our data falls in below-SMA200 (weak market). Only 101 of 2,421 event returns are in above-SMA200. We cannot conclude these signals don't work in bull markets — we just can't test it yet. All four phase-2 survivors were labeled "mostly below-SMA200 dependent" but this is a data scarcity problem, not necessarily a real regime dependency.

### What This Means Operationally

These signals are independent from the broker persistence signal (which uses floorsheet microstructure). They fire on a different trigger (public announcement vs broker behavior). When both agree — persistent selling AND a recent book closure/dividend notice — confidence in a CAUTION call increases because two independent evidence sources align.

Rough contribution: ~20-30 trading days per symbol per year fall within the 10-day post-notice windows during AGM season. On those days, a second independent confirmation layer is available.

### Resources and Files
- Experiment folder: `experiments/01-corporate-action/`
- Event table: `experiments/01-corporate-action/data/events.csv` (1,496 events)
- Event returns with baselines: `experiments/01-corporate-action/results/event_returns.csv` (2,421 rows)
- Phase-2 shortlist: `experiments/01-corporate-action/results/phase2_shortlist.csv`
- Phase-3 sector/regime review: `experiments/01-corporate-action/results/phase3_review.md`
- Shared framework: `experiments/shared/` (price_loader.py, event_study.py, stats.py)

### What We Did NOT Test Yet
- Whether these signals work in above-SMA200 (bull market) — insufficient data
- Whether expanding to more symbols strengthens or weakens the signals
- Whether the compound signal (persistence + corporate action) actually improves joint accuracy
- Whether the signals work on development banks, microfinance, or insurance sectors

---

## L-002: Lock-In Expiry Signal Is Directionally Correct but Statistically Inconclusive (2026-04-09)

### What We Tested
Whether hydropower stocks experience negative returns around the estimated promoter lock-in expiry date (listing date + 3 years).

### Data Used
- 154 hydropower listing proxies scraped from ShareSansar (using first-trade-date as listing proxy)
- 27 unlock events that fell within local price archive range (2021-2026)
- Baseline: rolling per-symbol returns for comparison

### Finding
| Window | N | Neg Hit Rate | Baseline Neg Hit | Delta | p-value |
|---|---|---|---|---|---|
| post_1_20 | 27 | 74.1% | 54.8% | +19.3% | 0.25 |
| pre_-20_-1 | 27 | 59.3% | 54.9% | +4.4% | 0.22 |

Direction is right (more negative than baseline around unlock). But N=27 with p=0.22-0.25 means it could be noise. Not actionable yet.

### Why It's Thin
- Many hydropower companies listed before 2018, so their 3-year unlock happened before our price data starts (2021)
- The proxy (first-trade-date ≈ listing date) is approximate — actual listing date may differ
- 15+ more unlocks are coming in 2025-2026, which will help

### Conclusion
Mark as "research-only weak proxy." Re-test when more unlock events accumulate. Consider upgrading to CDSC's actual lock-in expiry data if available.

### Resources
- Experiment folder: `experiments/02-lockin-expiry/`
- Listing dates: `experiments/02-lockin-expiry/data/listing_dates.csv` (154 proxies)
- Unlock events: `experiments/02-lockin-expiry/data/unlock_events.csv` (27 events)

---

## L-003: Baseline Adjustment Is Non-Negotiable for NEPSE Event Studies (2026-04-09)

### Learning
Any event study on NEPSE data from 2021-2024 without baseline adjustment will produce massively inflated bearish hit rates because the market was in a prolonged downturn. Our first run showed 12 signals with 77-97% hit rates. After baseline adjustment, 8 collapsed.

### Rule
Never report raw event-study hit rates as actionable signals. Always compute excess returns (event return minus trailing baseline return for the same stock in the same window).

### Technical Detail
The baseline is: for each event, take the same stock's trailing 120 returns in the same window type (e.g., drift_2_10), require at least 30 observations, and compute the mean. The event's excess return is its actual return minus this baseline mean.

This is conservative. It means a stock that's already falling fast needs to fall even faster than its recent trend to register as a signal. Only genuinely event-driven moves survive.

---

## L-004: Nepal AGM Season Is a Predictable Calendar Window (2026-04-09)

### Finding
From 163 AGM records in the scraped data:

| Sector | Peak Months | Concentration |
|---|---|---|
| Commercial Banks | Dec + Jan | 48% of all bank AGMs |
| Banks broader | Oct - Jan | 64% of all bank AGMs |
| Hydropower | Sep + Jan | 42% of all hydro AGMs |
| Hydro broader | Sep - Jan | 62% of all hydro AGMs |

### Implication
Corporate action signals (book closure, dividend notices) cluster in these months. The system should heighten attention during Oct-Jan for banks and Sep-Jan for hydropower. Outside these windows, corporate action signals will be sparse.

### Resource
AGM seasonality data extracted from: `experiments/01-corporate-action/data/events.csv`, event_type='agm', meeting_date field.

---

## L-005: ShareSansar DataTable API Has a 50-Row Page Size Limit (2026-04-09)

### Technical Finding
ShareSansar's AJAX datatable endpoints (company-dividend, company-rightshare, company-agm, company-announcements, company-events) return empty `data: []` when the `length` parameter exceeds 50. The server silently drops the request content.

### Rule
Always use `length <= 50` when paginating ShareSansar datatable endpoints. The scraper hardcodes `page_size = min(page_size, 50)`.

### Resource
Scraper: `experiments/01-corporate-action/scrape_sharesansar_history.py`, line 129.

---

## L-006: Sharesansar CSV Archive Contains Non-Trading-Day Clones (2026-04-09)

### Technical Finding
The local Sharesansar daily CSV archive (`sharesansar_datascrape/data/`) contains a CSV file for every calendar day, including weekends and holidays. Non-trading days clone the previous trading day's data exactly (same OHLCV, same turnover, same trades).

Nepal trades Sunday-Thursday. Friday and Saturday are weekends. Plus ~30-40 holidays per year.

### Solution
The price loader (`experiments/shared/price_loader.py`) has a `collapse_duplicate_sessions` flag that removes rows where all 15 numeric columns match the previous row. Verified safe: across 7 symbols, zero removed rows had a different close from their predecessor.

Raw file count: ~1,570 CSVs → ~986 actual trading days for most symbols (2021-2026).

### Resource
Price loader: `experiments/shared/price_loader.py`, `_collapse_duplicate_sessions()` function.

---

## L-007: Forward Shadow Scoring Must Use The Same Per-Symbol Trading Calendar As The Experiment Framework (2026-04-10)

### Learning
The first forward shadow scorer used whole-file hashing to collapse duplicate Sharesansar CSV snapshots. That produced a different trading calendar from the experiment framework, which collapses duplicate sessions at the **symbol row** level using 15 numeric columns.

This matters because:

- whole-file dedupe can keep extra dates that are still clones for a specific symbol
- that shortens or distorts the intended forward horizon
- a "10 trading day" score can quietly become closer to 8 real trading sessions for a given symbol

### Correct Rule
Any forward scorer that evaluates symbol-level outcomes must use the same per-symbol duplicate-session collapse logic as `experiments/shared/price_loader.py`.

### Practical Effect
After fixing the scorer:

- the persistence caution lane still held at `8/9` negative 10-day cases
- but the exact mean return changed from the rough first pass to the corrected value
- this confirms the signal direction was robust, while also showing why calendar consistency matters

### Additional Caution
Current forward shadow evidence is still clustered:

- most resolved persistence cases come from only a few report dates
- symbol rows from the same report date are not fully independent observations

So forward hit rates should be reported with explicit caution until more dates resolve.

### Resources
- Scorer: `market-gist/automation/score_persistence_shadow_reports.py`
- Scorecard: `market-gist/data/validation/persistence_shadow_reviews/latest__shadow_batch_scorecard_v1.json`

---

## L-008: NRB Rate Events Show Anticipation Then Reversal; Daily Interbank Moves Are Mostly Noise (2026-04-10)

### What We Tested
Experiment 03 tested two macro tracks:

1. discrete NRB policy events
2. daily interbank-rate move events

### Data Used
- Official NRB AJAX endpoint:
  - `https://www.nrb.org.np/wp-admin/admin-ajax.php`
  - `action=get_rates`
- Interbank daily series:
  - `SHORT_TERM_RATE`, `rate_id=62`
- Policy-rate change series:
  - `POLICY_RATE`, `rate_id=99`
- Bank-rate change series:
  - `POLICY_RATE`, `rate_id=80`
- Official NRB monetary-policy archive dates for annual, Q1, midterm, and Q3 reviews

### Key Finding
The cleanest macro pattern was not "easing is bullish."

Instead, easing events often showed:

- positive excess returns in the `pre_-5_-1` window
- weaker or negative excess returns after the event

This is a classic **anticipation then reversal** shape:

- market expects easing
- stocks rise before the announcement
- post-announcement drift often weakens or turns negative

For commercial banks specifically:

- easing `policy_rate_change -> pre_-5_-1`: positive excess
- easing `policy_rate_change -> drift_5_20`: negative excess

### Interpretation
This is better treated as:

- "buy the rumor, sell the news" context

not:

- a standalone macro trigger

### Daily Interbank Moves
Daily interbank move signals were much weaker:

- low thresholds produced huge N but weak hit rates near coin flip
- higher thresholds produced somewhat stronger results, but mostly in hydropower and not consistently enough for promotion

Conclusion:

- daily interbank moves are mostly technical noise for a signal layer
- keep them as research context, not a promoted mechanical rule

### Operational Rule
Use NRB rate events as background context in interpretation, not as a live CAUTION or SUPPORTIVE trigger.

### Resources
- Experiment folder: `experiments/03-nrb-rate-events/`
- Interbank data: `experiments/03-nrb-rate-events/data/interbank_daily.csv`
- Policy events: `experiments/03-nrb-rate-events/data/policy_events.csv`
- Results: `experiments/03-nrb-rate-events/results/`

---

## L-009: Hydropower Has a Strong, Stock-Level Seasonal Calendar (2026-04-10)

### What We Tested
Whether the published NEPSE hydropower sub-index seasonal pattern (Jan/Jul strong) holds at the individual stock level for 6 hydro stocks across 2021-2026, with 8 commercial banks as a control group.

### Data Used
- 703 monthly return observations across 14 symbols
- 6 hydro stocks: SMHL, HIDCL, NGPL, API, AKPL, UPPER
- 8 bank stocks (control): NABIL, NBL, EBL, HBL, KBL, SANIMA, PRVU, NIMB
- Local Sharesansar CSV archive 2021-2026
- Per-month return = first close to last close in calendar month
- Cross-stock agreement metric: % of individual stocks leaning the same direction
- Year stability metric: % of individual years matching the overall pattern

### Key Finding: Five Months Pass The Bar

| Month | Hit Rate | Mean Return | Cross-Stock Agreement | Year Stability |
|---|---|---|---|---|
| **Jan** | 89% positive | +12.00% | 5/6 stocks | 5/5 years |
| **Feb** | 82% negative | -5.25% | 6/6 stocks | 4/5 years |
| **Jul** | 70% positive | +9.35% | 5/6 stocks | 3/4 years |
| **Aug** | 78% negative | -6.78% | 6/6 stocks | 3/4 years |
| **Nov** | 71% negative | -2.31% | 5/6 stocks | 4/5 years |

All five reach >65% directional consistency AND >67% cross-stock agreement.
March, May, June, October, December are noisier and not actionable.

### Most Important Findings

1. **January is the strongest hydro month, NOT July.** January is peak dry season. The strength is likely a value-recovery rally after November weakness, not a generation-driven move. 89% positive hit rate, +12% mean return, every year (5/5) matches the pattern. This contradicts common assumption that monsoon season is when hydro is strongest.

2. **The monsoon rally is one month, not a season.** July is bullish (+9.35%, 70% positive), but August immediately reverses it (-6.78%, 78% negative, all 6 stocks agree). Holding hydro through monsoon is a losing trade. The trade is the monsoon onset only.

3. **February and August are mirror bearish months** — both with 100% cross-stock agreement (6/6). Late dry season and post-monsoon disappointment.

4. **Hydro pattern diverges from banks in January.** Banks are slightly negative in January (54% negative). Hydro is massively positive (89%). This is hydro-specific, not a market-wide effect. July is bullish for both but banks even stronger (100% positive, +17.9%).

### Why This Matters For The System

Romeo's agents currently score **14% direction accuracy on hydropower** — catastrophically bad. This experiment likely identifies the cause: agents are fighting the calendar.

The seasonal is not a trading signal. It is a **calibration filter** for existing signals:

- When broker persistence says CAUTION on a hydro stock in **January** → suspicious. January is the strongest month. The CAUTION must be very strong to overcome the seasonal, otherwise it is likely a false positive.
- When persistence says CAUTION in **February or August** → confirmation. The seasonal already expects weakness. Two independent bearish signals agree.
- When an agent predicts bearish on a hydro stock in January → likely the 14% accuracy problem firing. The agent is fighting the seasonal.

### Operational Rule Candidates

1. **Hydro CAUTION dampening**: in January and July, raise the threshold to flag a hydro CAUTION. The calendar already favors upside, so only very strong persistence signals should override it.
2. **Hydro CAUTION confirmation**: in February, August, November, treat persistence CAUTION as a high-confidence avoid because the seasonal agrees.
3. **Hydro agent prompt context**: feed the agent the seasonal expectation for the current month so it stops calling bearish in seasonally bullish months.

### Limitations

- Only 4-5 years of observations per month per stock — small sample
- All data falls in mostly bear-market regime, so the seasonal might be amplified by weak market dynamics
- Pattern needs forward validation before becoming a hard rule

### Resources
- Experiment folder: `experiments/04-hydro-seasonality/`
- Monthly returns: `experiments/04-hydro-seasonality/data/monthly_returns.csv`
- Findings report: `experiments/04-hydro-seasonality/results/findings.md`
- Sector summary: `experiments/04-hydro-seasonality/results/sector_monthly_summary.csv`
- Cross-stock consistency: `experiments/04-hydro-seasonality/results/cross_stock_consistency.csv`

---

## L-010: The Original Hydro Seasonal-Fight Hypothesis Was Wrong; The Real Finding Is The Nov→Jan Calendar Trade (2026-04-10)

### Background
After confirming the hydro seasonal calendar in L-009, we hypothesized that the agents' 14% hydro direction accuracy came from "fighting the calendar" — predicting bearish in seasonally bullish months. Phase 1 of the integration plan was a sanity check on that hypothesis, followed by Phase 2 testing the seasonal as an actual trading strategy.

### Phase 1: The Fight-The-Calendar Hypothesis Is Not Supported (But Not Cleanly Rejected Either)

**First pass (Phase 1)**: 106 scored hydro predictions across Romeo, Juliet, and Grok. Only API, AKPL, UPPER had data — SMHL, HIDCL, NGPL had zero scored predictions.

| Relationship | N | Direction Accuracy |
|---|---|---|
| No seasonal | 55 | 32.7% |
| Agent neutral in a seasonal month | 13 | 30.8% |
| Agreeing with seasonal | 33 | 66.7% |
| Fighting seasonal | 5 | 80.0% |

The first pass concluded "agents are bad in non-seasonal months." Romeo's review caught two real problems with that framing:

1. **The fighting bucket (N=5) is too small to interpret** — and all 5 cases are bullish-in-bearish-month, not the symmetric mix the hypothesis needs.
2. **The non-seasonal sample is essentially Oct/Dec 2025** — there are zero scored hydro predictions in March-June or September. Generalizing "agents fail in non-seasonal months" from Oct/Dec was overreach.

### Phase 1B: Strict Rerun (Romeo's Spec)

Stricter rules: one row per (symbol, prediction_date), drop agent neutrals, compare against two dumb baselines (seasonal-sign and month-majority).

**Final sample**: 39 directional predictions across 3 symbols, covering Jul/Aug/Oct/Nov/Dec only.

| Predictor | N | Accuracy |
|---|---|---|
| Agent | 39 | **56.4%** |
| Seasonal-sign baseline | 23 | **60.9%** |
| Month-majority baseline | 39 | **56.4%** |

**The agent ties one dumb baseline and slightly underperforms the other.** It does not add measurable directional value over a calendar lookup in this sample.

**Per-symbol breakdown shows API drags the agent average:**

| Symbol | N | Agent | Seasonal Baseline | Month-Majority |
|---|---|---|---|---|
| AKPL | 9 | 88.9% | 83.3% | 88.9% |
| API | 16 | 43.8% | 50.0% | 37.5% |
| UPPER | 14 | 50.0% | 55.6% | 57.1% |

AKPL is fine. API is the problem. UPPER is mediocre. The 14% headline number from the original review combined multiple issues; the directional-only number for these three symbols is closer to ~56%.

### Honest Conclusion (Phase 1 + 1B)

- The "agents fight the seasonal" hypothesis is **not supported** but the data is too thin and one-sided to call it cleanly rejected.
- The "agents are bad in non-seasonal months" claim was **overreach** — only Oct and Dec 2025 are in the sample for non-seasonal months.
- The agent does not consistently beat dumb calendar baselines in the small sample we have.
- The 14% original accuracy figure was a different metric (action verdict, all sectors, May 2025 only) — directional accuracy on this hydro subset is closer to 56%.
- Seasonal integration is **not a clear win and not a clear loser** with current data. Build forward evidence before committing to any integration shape.

**Caveats**: only 3 of 6 hydro symbols had scored predictions; the sample is missing Jan, Feb, Mar-Jun, and Sep entirely; all five years overlap a prolonged bear market.

### Phase 2: The Calendar Trade Backtest

Tested three "buy weak month, sell strong month" strategies derived from the L-009 calendar.

**Hydropower results:**

| Strategy | N | Win Rate | Mean Return | Verdict |
|---|---|---|---|---|
| A: Feb → Jul (5 months) | 22 | 50.0% | +1.9% | **FAILED** — coin flip |
| B: Aug → Jan (5 months) | 23 | 56.5% | +6.9% | **WEAK** |
| **C: Nov → Jan (2 months)** | **28** | **71.4%** | **+11.9%** | **PROMISING** |
| Z: Buy-and-hold full year | 34 | 47.1% | -1.4% | benchmark |

**Strategy C is the cleanest finding.** Buy hydro at end of November, sell at end of January. 20 wins out of 28 trades across 6 hydro stocks and 5 years. Mean return +11.9%. The losses when they happen are large (-32% to -38% on individual trades), and 5 of the 8 losses cluster in 2024 — meaning the strategy has a single bad year that drags the win rate.

**Strategy A (Feb → Jul) is fake**. The win rate splits cleanly by market regime: every 2022-2023 trade lost (NGPL -52%, API -46%, AKPL -45%, HIDCL -25%), every 2024-2025 trade won. It is a bull-market follower disguised as a seasonal.

### Surprise Bank Finding: Aug → Jan Is Catastrophic For Banks

The same Strategy B applied to commercial banks as a control:

- N=31 trades, **1 winning trade** (3.2% win rate), -9.1% mean return
- Best trade: +2.4%, worst: -21.3%
- This is far more reliable than any positive hydro pattern

**Banks have a strong NEGATIVE seasonal from late August through January.** Only 1 of 31 historical bank-year trades made money in that window. This is actually a stronger signal than the positive hydro pattern.

### Operational Implications

1. **Hydro Nov → Jan calendar buy**: promising (71% win rate, ~12% mean) but small N. **Do not trade live yet.** Track forward: when Nov 2026 closes, mark the buy signal and watch through Jan 2027. Build forward evidence over multiple years before sizing real positions.

2. **Bank Aug → Jan avoid**: 1/31 historical wins is catastrophic. Combined with the existing broker persistence CAUTION lane, the Aug-Jan window should reinforce CAUTION on bank longs almost automatically.

3. **The seasonal calendar does NOT fix the agent hydro accuracy problem.** The 14% accuracy lives in non-seasonal months, not seasonal ones. Adding seasonal context to agent prompts is not the right intervention.

4. **The non-seasonal months are unreliable for both sides.** Mar-Jun and Sep-Dec hydro behavior is closer to noise. The right move there is to lower confidence in any hydro call, not to flip the agent's prediction.

### Key Caveats

- N=28 for Strategy C is small. 5 years × 6 stocks. If 2024 was an unusual year, the win rate is fragile.
- All 5 historical years overlap a prolonged NEPSE bear market. Bull-market behavior may differ.
- Only 3 hydro symbols had scored agent predictions, so the Phase 1 conclusion is partial.
- The bank Aug-Jan finding is statistically stronger than the hydro Nov-Jan finding (1/31 vs 20/28) but it points to an avoid signal, not a buy signal.

### Resources
- Phase 1 script: `experiments/04-hydro-seasonality/phase1_seasonal_fight_check.py`
- Phase 1 results: `experiments/04-hydro-seasonality/results/phase1_seasonal_fight_*`
- Phase 1B strict rerun script: `experiments/04-hydro-seasonality/phase1b_strict_rerun.py`
- Phase 1B results: `experiments/04-hydro-seasonality/results/phase1b_strict_*`
- Phase 2 script: `experiments/04-hydro-seasonality/phase2_calendar_strategy_backtest.py`
- Phase 2 results: `experiments/04-hydro-seasonality/results/phase2_strategy_*`

### Addendum (2026-04-10): Candidate Mechanism for Strategy C

Web research on Nepal hydropower economics surfaced a credible candidate mechanism for the Strategy C (Nov→Jan hydro buy) seasonal: **the AGM/dividend statutory deadline driven by Nepal's Companies Act 2063 Section 76**.

The mechanism:
- Nepal fiscal year ends Ashadh 31 (mid-July)
- Companies Act Section 76 requires every public company to hold its AGM within 6 months of fiscal year end
- The hard deadline is Poush 31 (≈ mid-January)
- Dividends are endorsed AT the AGM
- Hydropower AGMs observably cluster in Mangsir-Poush (mid-Nov to mid-Jan), generating dividend-capture buying pressure

Verified concrete examples (FY 2080/81): Chilime CHCL, Sanima Mai SHPC, Butwal Power BPCL all held AGMs on Poush 28, 2081 with 5-12% dividends. HIDCL on Poush 24.

**One independent corroboration:** Investopaper found the NEPSE Hydropower Index has a 79% January win rate over 2007-2025. Our 71% Nov→Jan figure on a smaller, different sample is consistent with this published index-level finding.

**Important: Strategy C status is unchanged.** The candidate mechanism explains the pattern; it does not yet prove the pattern will continue on our specific data. Strategy C remains:
- Promising
- Small sample (28 historical trades)
- **Parked until forward evidence accumulates in November 2026 → January 2027**

The mechanism IS now a credible reason to keep tracking it, and it gives us specific watch items. The single biggest fragility risk is the May 2025 take-and-pay PPA budget proposal, currently partially reversed but politically live. If take-and-pay fully kicks in, bank financing for hydro projects freezes, dividends shrink, and the AGM-driven buying pulse weakens.

**Forward watchlist (do NOT build now — premature, build in October 2026):**
- Count of hydro AGMs announced Nov-Dec each year
- Cumulative dividend % announced by NEPSE hydros as of Mangsir 15
- Take-and-pay PPA policy status
- NEA payment-arrears reports to IPPAN
- Ashadh rainfall anomaly

### Resources for the Addendum
- Web research bundle: `market-gist/docs/resources/web-research-2026-04-10/`
- Hydropower deep dive: `market-gist/docs/resources/web-research-2026-04-10/05_hydropower_nepal_economic_deep_dive.md`
- Investopaper independent corroboration: https://www.investopaper.com/news/analysis-of-performance-of-hydropower-index-compared-to-nepse-index-2007-2025/
- Companies Act 2063 Section 76: https://actnepal.com/en/section/76/0/section-76-annual-general-meeting-of-companies-act-2063

---

## L-011: The Whole Lab Keeps Saying The Same Thing — Mechanical Signals Beat LLM Judgment On NEPSE (2026-04-10)

### The Pattern Across All Experiments So Far

This is a meta-learning that combines findings across the whole experiment lab. Each individual experiment is documented separately, but the pattern across them is what matters strategically.

| Comparison | Mechanical Result | LLM Result | Winner |
|---|---|---|---|
| Broker w7 seller persistence vs LLM CAUTION calls | 8/9 negative 10d (88.9%) on small forward sample | LLM direction accuracy 55-57% on 245 scored predictions | **Mechanical** |
| SMA50 mechanical avoid rule vs LLM avoid recommendations | 84% accuracy on 19 cases | LLM avoid accuracy weaker on same set | **Mechanical** |
| Calendar lookup vs LLM hydro direction calls (L-010) | Seasonal-sign baseline 60.9%, month-majority 56.4% | LLM agent 56.4% | **Tied or mechanical wins** |
| Dividend notice rule vs LLM explanation of dividend events | 71% bank hit rate, p=0.004 (validated) | LLM does not produce a comparable trigger | **Mechanical** |
| Hydro Nov→Jan calendar strategy vs LLM hydro buy calls | 71% win rate, +12% mean over 28 historical trades | LLM hydro direction 56% | **Mechanical** |

Five independent comparisons. Mechanical signals win or tie every time. There is not a single comparison where the LLM judgment cleanly beats a mechanical alternative.

### What This Suggests About The System Design

The original prediction system was built around LLM agents (Romeo, Juliet, Grok) making the core "buy/avoid/neutral" judgment. The expectation was that the LLM would integrate broker flow, structure, fundamentals, news, and calendar context into a better-than-mechanical call.

The accumulated evidence does not support that expectation on NEPSE data:

- The agent's "skill" on hydropower is statistically indistinguishable from a 10-line month lookup (L-010)
- The agent's direction accuracy across 245 scored predictions is 55-57%, barely above coin flip
- Every signal that has actually held up under independent verification has been mechanical
- Self-calibration of LLM conviction also fails (this was learned earlier in feedback_llm_prediction_learnings)

### What This Does NOT Mean

This is not a verdict that LLMs are useless for the project. They remain valuable for:

1. **Cross-checking each other** — this conversation is proof. Romeo's review caught real overclaims in my analysis. Juliet caught real bugs in Romeo's scorers. The multi-agent verification loop is the most honest part of the system.
2. **Writing explanations** — humans still need readable narratives. The LLM is good at producing them.
3. **Synthesizing context** — agents are useful for integrating raw events into a structured packet for review, even if the final trigger is mechanical.
4. **Hypothesis generation** — agents propose ideas; mechanical tests validate them.

What it does mean: **the trigger for action should be mechanical, not LLM judgment.** The LLM can describe the situation, but the "should I avoid this stock" decision should come from a script that reads broker persistence, calendar position, and event annotations.

### The Honest Strategic Direction

1. **Lean harder into mechanical signals.** Persistence shadow is mechanical. Strategy C is mechanical. Bank Aug-Jan avoid is mechanical. None of these need an LLM at the trigger point.

2. **Stop trying to fix LLM accuracy through prompt engineering.** L-010 suggests the ceiling is at the level of a calendar lookup. Better prompts will not get past that ceiling. Better data sources will not get past that ceiling. The information needed for the next 5% accuracy is not in the prompt-able context.

3. **Use LLMs for explanation and verification, not for triggers.** The agent-on-agent verification loop has caught real mistakes (this session's wording bug, Phase 1 overclaim, calendar-day bug in the scorer). That is high-leverage LLM work. Replacing that with a script would be a step backward.

4. **The forward-evidence pipeline is the most important infrastructure.** Persistence shadow scoring, dividend annotation tracking, and the eventual Strategy C / Bank Aug-Jan tests are all forward-evidence collectors. These are how we will distinguish "promising in 28 historical trades" from "real". Keep building that pipeline. Do not over-fit to the historical sample.

### Practical Implications For The Next 2-3 Months

- **Do not deploy anything new.** The persistence shadow is the only mechanical signal with forward evidence accumulating, and it still has only 14 resolved cases. Wait for 25-30+ before promotion decisions.
- **Track Strategy C forward.** When November 2026 ends, mark the buy signal across the 6 hydro stocks. Score in February 2027.
- **Track the bank Aug-Jan avoid forward.** August 2026 onward, log whether banking shadow CAUTION coincides with the seasonal weakness.
- **Score the persistence shadow when 25+ resolved cases exist.** That is the first real promotion decision.
- **Stop adding new experiments until forward evidence catches up.** L-007 through L-011 are enough findings. Building experiments 06, 07, 08 now would be churning. The bottleneck is forward time, not historical analysis.

### Why This Matters
The most expensive mistake this lab could make is to keep generating new experiments faster than we can validate the existing ones forward. Romeo's framing — "frozen champion approach, do not change rules without repeated evidence" — should be applied to the lab itself, not just to individual policies. The lab has produced enough hypotheses. The next 2-3 months should be evidence collection on what we already have, not generation of more.

### Resources
- Cross-references: L-001 (corporate action), L-002 (lock-in), L-007 (scorer calendar), L-008 (NRB), L-009 (hydro seasonal), L-010 (hydro agents vs calendar)
- Forward shadow scoring: `market-gist/automation/score_persistence_shadow_reports.py`
- Persistence shadow reports: `market-gist/data/validation/persistence_shadow_reports/`
- Frozen policy: `market-gist/agents/shared/PERSISTENCE_SHADOW_POLICY_V1_FROZEN.md`

### Addendum (2026-04-10): External Corroboration From Adjacent-Market Literature

Web research surfaced 5+ peer-reviewed 2024-2025 papers reaching directionally similar conclusions on US equities, Indian NIFTY, and prediction markets:

- "When Reasoning Fails" (arXiv 2511.08608, Nov 2025) — Indian NIFTY, classical baselines stable, thinking LLMs deteriorate, no net advantage under transaction costs
- StockBench (arXiv 2510.02209, Oct 2025) — "Most LLM agents fail to outperform a simple buy-and-hold baseline"
- Lopez-Lira & Tang — Sharpe **decayed from 6.54 (2021Q4) to 1.22 (2024)** as adoption rose
- KalshiBench (arXiv 2512.16030, Dec 2025) — "Extended reasoning **worsens** calibration"
- The "New Quant" Survey (arXiv 2510.05533, Oct 2025) — consensus: LLMs valuable for reading disclosures and generating hypotheses, NOT direct prediction
- Two Sigma 2026 outlook: "The next year won't be about LLMs making trades"

**Important caveat:** None of these papers tested NEPSE directly. The pattern observed on adjacent markets is consistent with what we observed, but the inference that it extends to Nepal specifically is reasonable, not proven on our data.

**Wording update:** L-011 should be cited as "**strongly externally supported by adjacent-market literature**" rather than "universally validated." The direction is the same; the framing is more honest about what the evidence actually shows.

The substantive direction does not change: trigger should be mechanical, LLMs are valuable for verification and explanation, build forward evidence, don't churn on new experiments.

Full review of the literature is at `market-gist/docs/resources/web-research-2026-04-10/02_llm_vs_mechanical_finance.md`.

---

## L-012: The 88.9% Persistence Hit Rate Is Clustered and Preliminary, Not 9 Independent Cases (2026-04-12)

### What We Did
Ran Benvolio's 6-class audit checklist (designed by the exploration team, executed by Juliet) against the real `score_persistence_shadow_reports.py` code and the `latest__shadow_batch_cases_v1.csv` case data.

### The Key Finding: Sample Clustering

The 9 resolved `persistence_caution_only` cases come from only **3 report dates**:

| Date | Symbol cases | Wins | Forward window |
|---|---|---|---|
| 2025-08-04 | NABIL, EBL, AKPL, UPPER, API (5 cases) | 4 wins, 1 loss (EBL went up) | Aug 4 → Aug 18 |
| 2025-08-05 | NABIL, AKPL, UPPER (3 cases) | 3 wins | Aug 5 → Aug 19 |
| 2025-12-07 | UPPER (1 case) | 1 win | Dec 7 → Dec 21 |

**The Aug 4 and Aug 5 forward windows overlap almost entirely** (14 of 15 trading days shared). The 7 wins from those 2 days are not independent — they're measuring the same market decline across multiple symbols simultaneously. The effective independent episodes are closer to **2-3, not 9** (Romeo-verified, 2026-04-12).

### What Else The Audit Found

| Class | Item | Verdict |
|---|---|---|
| F.1 | Pre-registration artifact | **PARTIAL PASS** — frozen policy on disk dated Apr 5, names exact (w7, seller, >=1.0) tuple. Never committed to git. |
| F.2 | Search space enumerated | **FAIL** — not documented what other (window, side) combos were tested before freezing. |
| A.1 | Dedupe function | **PASS** — scorer's own `collapse_duplicate_sessions` is identical to shared library. L-007 fix present. |
| A.2 | Trading-day arithmetic | **PASS** — `anchor_idx + offset` on deduplicated DataFrame. Correct. |
| A.3 | Regime breaks | **PASS** — uses CSV file dates. Immune to Sun-Thu/Mon-Fri change. |
| C | Baseline adjustment | **FLAG** — raw returns only. Baseline comparison group = 3 no_signal cases. Too thin. |
| B | Frozen policy drift | **UNVERIFIABLE** — no git history to compare. |
| E | Decay diagnostic | **PARTIAL** — only 5d and 10d available. Mean 5d=-1.59%, mean 10d=-1.65%. Inconclusive. |

### What This Means

**The code is clean. The sample is not.** The plumbing works correctly (dedupe, trading-day math, regime-immunity). The problem is that the current evidence base is much thinner than the headline "8/9 = 88.9%" suggests.

The 23 pending forward cases from Mar 31 – Apr 10, 2026 are the **real** test. They span multiple weeks, multiple independent market regimes, and will provide genuinely independent observations. They need ~10 more trading days of price data to resolve.

### What This Does NOT Mean

This does not mean the signal is broken. It means the current evidence is insufficient to conclude it works. The distinction matters: "we don't know yet" is different from "it doesn't work." Keep running the daily routine. Do not change the frozen policy. Wait for the pending cases.

### Resources
- Audit checklist design: `C:\Users\ishwor\Music\own-organize\market-expirement-labs\04_persistence_lookahead_audit.md` (Benvolio)
- Case data: `market-gist/data/validation/persistence_shadow_reviews/latest__shadow_batch_cases_v1.csv`
- Scorer code: `market-gist/automation/score_persistence_shadow_reports.py`
- Romeo review: appended to `market-gist/automation/SCRAPE_EXPANSION_2026-04-12.md`

### Addendum (2026-04-18): Clean-Data Correction — Hit Rate Dropped From 88.9% To 72.7%

After fixing 16 price CSV files corrupted by unresolved git merge conflict markers (see L-015 for the data integrity incident), the scorer correctly resolved 2 additional `persistence_caution_only` cases:

- **2026-03-31 NABIL:** 10-day forward return = +0.17%, not negative → **success_10d = False** (CAUTION failed to predict a drop)
- **2026-04-01 NABIL:** 10-day forward return = +1.53%, not negative → **success_10d = False**

**The headline number moved:**

| Metric | Before clean-data fix | After clean-data fix |
|---|---|---|
| Resolved `persistence_caution_only` | 9 | **11** |
| Hit rate (pure persistence CAUTION) | 88.9% | **72.7%** |
| Hit rate (all CAUTION, including dividend annotation group) | 88.9% | **66.7% (8/12)** |
| Unique report dates (all cases) | 3 | 5 |
| Unique WIN dates | 3 | 3 (new cases both losses) |
| Top-1 date share | 55.6% | 45.5% |

**Honest framing (Romeo-verified 2026-04-18):**

- The signal is **still directionally suggestive but not statistically significant**. One-sided binomial test on 8/11 vs 50% null gives p ≈ 0.11. This is NOT "still above chance" in any decision-grade sense. It is "directionally consistent with a real signal, too thin to conclude."
- Effective independent episodes remain **3** because the two new cases are losses and the win-dates set did not grow.
- Mar 31 and Apr 1 cases have heavily overlapping 10-day forward windows (14 of 15 trading days shared) — they are not fully independent either.
- L-012's core claim (the 88.9% is clustered and preliminary) is **confirmed**, not revised. The new number is simply the clean-data version of the same preliminary result.

**What this does NOT change:**

- The frozen policy remains frozen.
- The batch-score gate at N≥25 remains the next real decision point.
- The lab's discipline around forward evidence is unchanged.

**What this changes going forward:**

- Report BOTH the pure-persistence rate (72.7%) and the all-CAUTION rate (66.7%) in any batch-score memo. Do not cherry-pick.
- No headline claims containing the phrase "88.9%" or "still above chance." These framings are officially retired.
- If further resolved cases move the hit rate below 60%, this experiment is on track for a `KILL` verdict at the batch-score gate. If above 65% with broad episode independence, it earns a `PROMOTE` review.

**Promotion-to-L-014 deferred per Romeo:** this addendum captures the correction. A full L-014 entry waits for the N=25 batch-score gate to confirm whether the revised number is stable or continues to drift.

---

## L-013: Published Broker-Flow Benchmarks Were Misquoted; NEPSE Data Advantage Is Real But Modest (2026-04-12)

### What Happened

Benvolio (exploration team) traced every academic paper the lab has been citing back to the original source via web research. Found **8 errors** in our files across two rounds of verification.

### The Errors That Matter Most

**1. The "52-57% hit rate" benchmark was never in any paper.**
BJZZ (2021) reports ~10 bps/week return spread between retail-buying and retail-selling stocks. That is a return number, not a directional accuracy number. The lab converted it to an implied hit rate and then wrote it down as if the papers said "52-57%." They didn't. The lab's own back-calculation gives ~50.5-51.5%, and with measurement-error correction (EIV, λ≈0.30) the ceiling with perfect data is ~53%.

**2. Wrong author on BJZZ decay paper.**
The signal-decay finding is from Ardia, Aymard & Cenesizoglu (2025), NOT Barber et al. (2024). Barber et al. wrote a different paper about BJZZ's algorithm having 28% signing errors. The decay finding (BJZZ predictive power dropped 34%, "completely disappears" for large-cap post-2016) is real — it was just attributed to the wrong people.

**3. Linnainmaa-Saar is not a broker-skill study.**
Our deep dive framed Linnainmaa & Saar (2012) "Lack of Anonymity and the Inference from Order Flow" as a broker-skill methodology template with "3-5 segmented groups." The paper is actually about how broker identity reveals information about order flow direction — a different question. The classification methodology is reusable, but the framing was wrong.

**4. Units conflated.**
"5-15 bps/day" lumped BJZZ (~10 bps/week) and Taiwan day-traders (61.3 bps/day) into one range. These are incompatible: weekly institutional-flow return vs daily individual-trader skill.

### The Data Quality Advantage Calculation (Benvolio's `08_data_quality_advantage.md`)

NEPSE has a structural data advantage: 100% trade identification with 100% correct broker names, vs BJZZ's ~65% identification with 28% signing errors. Benvolio calculated what this means:

| Data quality | Implied directional accuracy |
|---|---|
| BJZZ observed (noisy US data) | ~50.5% |
| EIV-corrected (perfect data, US market) | ~53% |
| + thin market + transparency bonuses | ~55-58% (theoretical ceiling) |
| Our persistence signal claims | 88.9% |

**The data advantage is real but modest** — it closes ~3pp of a 38pp gap. The remaining 30+ pp is unexplained. This makes the L-012 audit findings more urgent, not less.

### Corrections Applied (Romeo-verified 2026-04-12)

- `BACKLOG.md`: "52-57% from papers" replaced with honest "lab's inference ~50-52%, not a published number"
- `BACKLOG.md`: Choi → "Choi, Jin & Yan"; BJZZ decay → "Ardia, Aymard & Cenesizoglu (2025)"
- `EXPLORATION_CHARTER.md`: 65% rule language softened in 2 places
- `MANIFESTO.md`: Persistence scorecard updated to acknowledge clustering

### What This Means For The Lab

**The directional claims are right.** Broker flow predicts returns, the signal is modest, it decays, nobody has done this on NEPSE. The lab's thesis holds.

**The specific numbers used as benchmarks had errors.** None are catastrophic, but the lab was less rigorous on citations than it thought. Romeo's assessment: "B-minus foundation."

**The data quality advantage is a real structural edge** — NEPSE's broker-identified transparent market gives ~3x stronger signal recovery than noise-corrupted US data. This supports the lab's core thesis that the research frontier is real. But it does not explain the 88.9%.

### Resources
- Benvolio's deliverables (read-only reference, not canonical):
  - `C:\Users\ishwor\Music\own-organize\market-expirement-labs\04_persistence_lookahead_audit.md` — audit checklist
  - `C:\Users\ishwor\Music\own-organize\market-expirement-labs\06_day_of_week_validation.md` — day-of-week papers + 3 errors
  - `C:\Users\ishwor\Music\own-organize\market-expirement-labs\07_academic_claim_verification.md` — 8 citation errors
  - `C:\Users\ishwor\Music\own-organize\market-expirement-labs\08_data_quality_advantage.md` — data quality math
- Romeo review: `market-gist/automation/SCRAPE_EXPANSION_2026-04-12.md` (appended)
- BJZZ original: Boehmer, Jones, Zhang & Zhang (2021) "When Do Retail Investors Improve Price Discovery?"
- Decay paper: Ardia, Aymard & Cenesizoglu (2025) — BJZZ signal decay study
- Linnainmaa & Saar (2012) "Lack of Anonymity and the Inference from Order Flow"
- Choi, Jin & Yan (journal-published 2025) — Shanghai institutional flow

### Addendum (2026-04-12): Operating Doctrine

Romeo wrote `experiments/PARALLEL_EXPLORATION_SERIAL_PROMOTION.md` — the operating law for how the lab uses AI parallelism without drifting into random experimentation. Core law: **search wide, promote narrow.** Three layers: exploration (parallel, cheap) → verification (adversarial) → validation (forward evidence, serial). The anti-randomness rules codify what L-012 and L-013 discovered: no fake benchmarks, no correlated rows as independent observations, no skipping the funnel from idea to promotion.

---

## L-015: Silent Data Corruption (Git Merge Conflict Markers) Can Hide For Months And Break The Evidence Base (2026-04-18)

### What Happened

On 2026-04-18, during a catch-up scrape for Apr 14-17, the scorer returned "insufficient_forward_bars_for_10d" for persistence cases from Mar 31 and Apr 1 NABIL — even though the price data window had closed. Investigation revealed 16 price CSVs in `sharesansar_datascrape/data/` contained unresolved git merge conflict markers (`<<<<<<< HEAD`, `=======`, `>>>>>>>`) on line 1. Affected dates: Mar 20, 22-26, 29-31, Apr 1-2, 5-9, 2026. Total: 16 files across the window where the persistence signal's forward outcomes live.

The scraper had dutifully written clean CSVs months earlier. Some later git merge (branch sync, pull, rebase) introduced conflict markers that were never resolved. The CSVs remained on disk and were picked up by the scorer's glob. The CSV parser either failed or silently produced empty records. Either way, the dedupe logic saw these days as "no valid row change" and collapsed them.

**Observable symptoms (before diagnosis):**

- NABIL trading frequency looked artificially low (7 Apr CSVs with NABIL vs expected 10+)
- All three active banks (NABIL, EBL, SANIMA) had *identical* trading-date patterns (impossibly uniform)
- Persistence cases from Mar 31 onward refused to resolve their 10-day forward windows
- Earlier diagnosis blamed "NABIL has been trading very infrequently" — wrong root cause.

**Real cause:** the price data the scorer needed was on disk but corrupted at the bytes level. Neither the scorer nor the human reviewers noticed because the CSV parser failed gracefully to "no row" rather than erroring out.

### What It Cost

- 16 data points silently missing from the scorer's input for weeks or months.
- The persistence signal scorecard showed 9 resolved cases when it should have shown 11.
- The headline hit rate showed 88.9% when the clean-data number is 72.7%.
- We almost raised a false alarm ("3.5 months of missing price data") because an unrelated check misread `ls | tail` alphabetical-vs-chronological ordering (Pattern 5 in `WORKING_DISCIPLINE.md`).
- Time spent chasing the wrong diagnosis before identifying the merge-conflict root cause.

### Why It Matters

This is NOT an operational lesson. It directly changed the evidence base: the lab was making claims ("88.9%") about a signal using a corrupted subset of the data. Under the SANDBOX_PROTOCOL's discipline of "no silent changes to production state," this is a serious category of failure — worse than an overclaim in a review, because there was no visible signal that anything was wrong.

### The Fix (Landed)

Built `market-gist/automation/price_data_integrity.py`. Functionality:

1. Scans all CSVs in the sharesansar data directory.
2. Detects: git merge conflict markers, empty files, missing/wrong headers, header-only files.
3. Exit 0 if clean, exit 1 if corrupt. CLI form works standalone.
4. Library function `check_data_dir(raise_on_corrupt=True)` raises `IntegrityError`.

**Wired into production:** `score_persistence_shadow_reports.py:main()` now calls `check_data_dir(raise_on_corrupt=True)` at the top. If corruption is present, the scorer fails loudly with a clear error message instead of silently producing mis-scored outputs.

**Architectural note (Romeo 2026-04-18):** the utility lives in Layer 1 (`market-gist/automation/`) rather than `experiments/shared/` so Layer 1 code doesn't long-term depend on `experiments/shared/`. Scorer is the must-have location because people can run the scorer directly. The daily runner (`run_persistence_shadow_daily.py`) can optionally mirror the check for UX; not yet wired there as of 2026-04-18.

### Prevention Rules

1. **Any CSV-parsed data source needs an integrity pre-check before consumption.** Silent parse failures are the dangerous kind.
2. **Git merge operations on data directories require human review before the merge commits.** Even on branches that touch code, incidentally modified data files can pick up conflict markers.
3. **Periodic `grep -r "<<<<<<<" data_dir/` is a cheap prophylactic.** Should run as a sanity check before any batch-score decision fires.
4. **Signals that look "too clean" (identical trading patterns across supposedly independent symbols) deserve investigation, not acceptance.** Pattern 6 of WORKING_DISCIPLINE is now updated.

### Resources

- Integrity utility: `market-gist/automation/price_data_integrity.py`
- Wired into: `market-gist/automation/score_persistence_shadow_reports.py` (top of `main()`)
- Incident reconstruction: `experiments/SESSION_LOG_2026-04-18.md` (once written)
- Related learning: L-012 (the clustering finding that partially masked this — now corrected in L-012 addendum)
- Self-discipline follow-through: `experiments/WORKING_DISCIPLINE.md` Pattern 5 (ls misread) and Pattern 6 (coverage questions)

---

## L-016: Reversal Specialist Closed At Gate 1 — Clean Sharp-Down Sample On 26-Symbol 2021-2026 Universe Was Too Small For H1 (2026-04-19)

### What We Tested
Whether NEPSE symbols mean-revert after sharp single-day price moves (≤ -5% for the primary direction). Pre-registration revision 4 locked: primary H1 sharp-down ≤ -5% daily return, window [T+1, T+5], success criteria mean excess return ≥ +1.0% AND hit rate ≥ 60% AND block-bootstrap CI excluding zero. Gate 1 required N ≥ 80 h1-eligible events, unique dates ≥ 30, top-3 date concentration ≤ 30%, ≥ 5 contributing symbols.

### Data Used
- 26 symbols across banks + hydros + allied sectors, 2021-2026 daily price archive
- L-001 events.csv for corporate-action contamination filtering (read-only cross-experiment input)
- Per-symbol trailing 120 prior trading observations for baseline adjustment (L-003 convention)

### Result: Gate 1 FAIL On Primary Direction

```
Raw sharp-down symbol-day candidates:   333
Filter flags (non-exclusive — one candidate can trip multiple):
  Volume-threshold flag:                134  (thin-market artifact)
  Near-price-limit / circuit flag:       64  (mechanical cap adjacent)
  Layer B market-wide-shock flag:       178  (53.5% of raw candidates)
  Layer A documented regime-date flag:    2
  Corporate-action overlap flag:         16
Passed all filters (include_in_primary): 68
Forward-window + baseline gap drift:     2 + 50
H1-eligible:                             66  ← below the 80 threshold
```

Note: filter flag counts sum to more than 333 because filters are not mutually exclusive. Layer B is the data-driven market-wide-shock detector (≥30% of active symbols sharp-moving the same direction that date). Layer A is the pre-registered list of hand-picked documented regime dates. The two layers answer different questions; they are not interchangeable.

| Direction | N | Gate | Verdict |
|---|---:|---:|---|
| Sharp-down (primary H1) | **66** | ≥ 80 | **FAIL** |
| Sharp-up (secondary H1b) | 258 | ≥ 80 | PASS (non-promotion per pre-reg) |

Every other Gate 1 criterion passed comfortably for the primary direction: 62 unique dates (gate ≥ 30), top-3 concentration 9.1% (gate ≤ 30%), 17 contributing symbols (gate ≥ 5). The failure is purely sample size.

### What This Tells Us About The Tested Slice Of NEPSE

**The dominant filter is Layer B: 178 of 333 raw sharp-down symbol-day candidates (53.5%) were Layer-B market-wide-shock flagged**, not confirmed regime events. Layer B is a data-driven co-movement detector, not a hand-picked regime-date list. After applying all pre-registered filters, the pre-registered clean / idiosyncratic sharp-down rate in this 26-symbol 2021-2026 universe is roughly 13 events per year. That is not enough for a properly-powered reversion test with N ≥ 80.

What this does and does not say:
- **Says:** within ≤ -5% sharp-down candidates, market-wide-shock flags were common — roughly half of raw candidates co-moved with the broader tape that day
- **Says:** circuit-breaker caps and thin-market artifacts remove another slice of raw candidates, leaving a small residual
- **Does not say:** NEPSE daily volatility as a whole is dominated by regime-wide moves (we did not test all daily moves, only the ≤ -5% slice)
- **Does not say:** NEPSE lacks reversion signal (we measured sample availability under our filters, not the underlying hypothesis)

### What The Pre-Registration Discipline Caught

Without the pre-registered N ≥ 80 gate, the raw "333 sharp-down days" number would have invited post-hoc rescues: soften the threshold to -4%, expand the symbol universe, merge directions, skip Layer B. All were explicitly forbidden by revision 4. The lane closed cleanly after one Gate 1 decision, in one session of code.

This is the **second Tier 1 lane closed at Gate 1** (after dividend-microstructure on 2026-04-18, closed at 24/80 Cohort A events + 71% L-001 overlap). Both closures were informative: they characterized what NEPSE data can and cannot power.

### What Is Preserved

- Full `PRE_REGISTRATION.md` revision 4 (Romeo-approved) as methodology record
- `data/trigger_events.csv` (1,098 rows across 26 symbols) — the detected event table with all filter flags
- `data/gate1_decision.md` — verdict memo with full funnel
- Gate-drift diagnostic (2.7% drift — small, confirms include_in_primary and h1_eligible align)
- All code (`build_trigger_events.py`, `check_gate1.py`) at revision-4 fidelity

If in the future (a) the symbol universe expands materially, (b) a NEW pre-registration revises the trigger definition via the same Romeo cycle (NOT a post-hoc relax), or (c) an alternative reversion horizon is tested, the infrastructure is here. A new Gate 1 would require a fresh pre-registration.

### What Is Explicitly Not Done

- H1 historical test did not run and will not run from revision 4
- H1b sharp-up secondary is not run — pre-reg made it non-promotion-grade from the start, and Romeo authorized only Gate 1, not H1b
- No threshold softening, no symbol expansion, no window-shopping

### Cross-Experiment Implication

Two successive Tier 1 candidates failed at Gate 1, for different reasons:
- **dividend-microstructure** failed because independence collapsed into L-001 overlap (71% of Cohort B events had an L-001 book_closure_notice within ±10 trading days — the proposed T_ex signal and L-001 were structurally measuring the same corp-action cycle)
- **reversal-specialist** failed because the pre-registered clean sharp-down sample on the 26-symbol 2021-2026 universe was too small (66 h1-eligible vs required 80)

Honest lab state, combined with L-011 (mechanical signals beat LLM judgment) and L-012 addendum (persistence hit rate 72.7% preliminary):
- **One forward-evidence lane still live** (persistence shadow, N=20, expected N=25 gate around Apr 27 - May 5)
- **No additional historical-test lanes promoted**
- **Gate 1 has now prevented two under-powered H1 runs before inference**

Meta-observation (to be validated forward, not canonical yet): both failures were caught at the sample-power / independence gate, not at H1. This suggests future lanes should run sample-power and independence diagnostics earlier in scaffold — ideally before the full pre-registration round. It does NOT mean NEPSE lacks signals. It means attractive hypotheses on this universe often become under-powered after honest filters, and that fact is worth learning as early and cheaply as possible.

### Resources
- Experiment folder: `experiments/reversal-specialist/`
- Pre-registration: `experiments/reversal-specialist/PRE_REGISTRATION.md` (revision 4, Romeo-approved 2026-04-19)
- Event table: `experiments/reversal-specialist/data/trigger_events.csv`
- Gate 1 decision memo: `experiments/reversal-specialist/data/gate1_decision.md`
- Related closures: dividend-microstructure (closed 2026-04-18, see `experiments/dividend-microstructure/README.md`)
- Working discipline: `experiments/WORKING_DISCIPLINE.md` Pattern 9 was added during this experiment's revision cycle
