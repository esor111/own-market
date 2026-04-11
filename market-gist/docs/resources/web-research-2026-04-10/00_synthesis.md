# Web Research Synthesis — 2026-04-10

> **Status: Juliet's synthesis only. Not yet cross-reviewed by Romeo.**
> All findings and strategic recommendations in this bundle are Juliet's reading of agent
> outputs. They have not been independently reviewed by Romeo. Treat the wording as
> provisional and the recommendations as unconfirmed until `99_romeos_takes.md` is filled in.
> A first wording-tightening pass was applied 2026-04-10 after Romeo flagged overstatements;
> see `99_romeos_takes.md` for the open review points.

## Context

After completing four experiments and eleven learnings (L-001 through L-011), the user asked: "Go to the web and do deep research on everything you think is worth researching." Six parallel research agents were launched in the background. This document is the top-level synthesis of all six threads.

## The Single Biggest Finding

**Our Nov→Jan hydro calendar trade now has a credible fundamental explanation. The status remains "promising, needs forward validation" — the mechanism is a candidate, not yet proven for our sample.**

The 71% historical win rate (Strategy C from `experiments/04-hydro-seasonality/phase2_calendar_strategy_backtest.py`) is NOT explained by generation cycle or PPA pricing. Both argue **against** a Nov-Jan rally:
- Generation collapses to 30% of installed capacity in those months
- Nepal's electricity export revenue hits its **lowest** monthly value (Rs 1.10B) in mid-Nov to mid-Dec

**Candidate mechanism: AGM/dividend statutory deadline.** Nepal's Companies Act 2063 Section 76 forces every public company to hold its AGM within 6 months of fiscal year end (Ashadh = mid-July). The hard deadline is **Poush 31 ≈ mid-January**. Hydropower dividends are observably concentrated in Mangsir-Poush (mid-Nov to mid-Jan).

**One independent corroborating dataset:** Investopaper found the NEPSE Hydropower Index has a **79% January win rate** (2007-2025 sample). Our 71% Nov→Jan figure on a smaller, different sample is consistent with this published index-level finding. One independent corroboration is not the same as multiple independent confirmations — we should not treat the question as settled.

**Verified examples (FY 2080/81):**
- Chilime Hydropower (CHCL): 12% dividend, AGM Poush 28
- Sanima Mai Hydropower (SHPC): 10.52%, AGM Poush 28
- Butwal Power (BPCL): 5% cash, AGM Poush 28
- HIDCL: 5.25%, AGM Poush 24

**Updated confidence:** Strategy C goes from "pattern of unknown origin" to "pattern with a credible mechanism, still pending forward validation." The mechanism is a hypothesis we can test, not yet a confirmed driver. Strategy C remains parked until forward evidence accumulates in the actual Nov 2026 → Jan 2027 window.

**The biggest fragility risk:** The May 2025 take-and-pay PPA budget proposal. If fully implemented, it freezes financing for 350+ hydro projects worth Rs 109 billion. Bank financing freeze → smaller dividends → weaker AGM pulse. **This is the watch item.** It was partially reversed but is still politically live.

See `05_hydropower_nepal_economic_deep_dive.md` for full sources and mechanism.

---

## Validations of Our Existing Findings

### L-011 (mechanical > LLM) is strongly consistent with adjacent-market literature

The LLM-vs-mechanical research thread found 5+ peer-reviewed papers from 2024-2025 reaching directionally similar conclusions on US equities, Indian NIFTY, and prediction markets. **None of these papers tested NEPSE directly.** The pattern is consistently observed in adjacent markets, not formally validated as universal:

| Paper | Year | Result |
|---|---|---|
| "When Reasoning Fails" (arXiv 2511.08608) | Nov 2025 | Tested on Indian NIFTY (NEPSE's closest cousin). Classical baselines stable, thinking LLMs deteriorate with complexity, **no net advantage under transaction costs**. |
| StockBench (arXiv 2510.02209) | Oct 2025 | "Most LLM agents fail to outperform a simple buy-and-hold baseline." LLMs show documented bullish bias, struggle in bearish regimes. |
| Lopez-Lira & Tang (canonical "ChatGPT predicts stocks" paper) | 2023, updated 2025 | Sharpe **decayed from 6.54 (2021Q4) to 1.22 (2024)** as adoption rose. The signal is being arbitraged away in real time. |
| KalshiBench (arXiv 2512.16030) | Dec 2025 | "Extended reasoning **worsens** calibration." Verbalized confidence scores "almost independent from accuracy." |
| The "New Quant" Survey (arXiv 2510.05533) | Oct 2025 | Synthesizes 50+ studies. Consensus: LLMs valuable for "reading and reasoning over disclosures, generating auditable hypotheses" — NOT direct price prediction. |

**Two Sigma's 2026 public outlook is directionally consistent:** "The next year won't be about LLMs making trades."

The pattern in adjacent markets is consistent with what we observed on NEPSE. Nepal may make it more extreme because we lack English news flow, but no paper has directly tested NEPSE so this remains an inference, not a confirmation. **L-011 can be cited as "strongly externally supported by adjacent-market literature," not as a universal finding.**

### NEPSE academic literature validates our work where overlap exists

| Our finding | Academic backing |
|---|---|
| Calendar seasonality (L-009) | Joshi & K.C. (2005), KMC Journal (2024) — day-of-week effects, Kartik-strong / Falgun-weak monthly pattern |
| Frozen-champion discipline | Jha & Dhungana — Adaptive Market Hypothesis applies to NEPSE (theoretical cover) |
| Dividend annotation (L-001) | Pradhan (2003), NRB Joshi (2012) — dividend signaling dominates retained earnings in Nepal, documented for 20+ years |
| Volatility clustering | Multiple GARCH-family papers — confirmed, leverage effects, no risk-return tradeoff |
| Bullish bias / herding | Multiple Nepal herding papers — herding strong in bulls, weak in bears |

### The work is academically virgin in one critical area

**Broker-floorsheet persistence as a return predictor in NEPSE has zero published academic studies.** From the literature review thread:

> "This is remarkable because NEPSE's transparency (buyer broker ID + seller broker ID on every trade) is rare globally and should be a natural laboratory for PIN, order imbalance, and order splitting studies."

We are doing something nobody has formally published. That is exciting and risky:
- **Exciting:** real research contribution, no prior art to refute us
- **Risky:** no external calibration to compare against; developed-market evidence (Boehmer et al.) showed retail order flow predictability decayed post-2017

### The open-source ecosystem confirms we are not reinventing wheels — except where it matters

> "Your `market-gist/automation` pipeline appears to be **more rigorous than anything public in NEPSE open-source right now**. You're not reinventing wheels on data access, but your core methodological contribution has no equivalent in the ecosystem."

The closest comparable project is `nlethetech/nepse-quant-terminal`. It has the trading UI and MCP tool surface but no outcome evaluation, no calibration discipline, no learnings file. We have those.

---

## New Things Worth Adding

### Candidate NRB event patch (deferred to backlog)

Up to 8 candidate dates surfaced from the NRB margin lending research. After dedup against the rows already in `experiments/03-nrb-rate-events/data/policy_events.csv`, the actual count of TRULY NEW NRB-specific events is **3-4**, not 6 and not 8. The proposed patch list lives in `proposal_experiment_03_patch.md` in this folder.

Documented headline impacts (for context, not yet patched):
- Share-backed lending: Rs 70.34B → Rs 116.80B (+66% YoY in FY 2024/25)
- Then surged to Rs 156.27B by mid-Feb 2026
- NEPSE FY 2024/25 gain: +29.77%

**This is the lowest-cost backlog item if and when we decide to extend experiment 03.** Under L-011 patience mode, it should not be patched before persistence forward evidence batch-scores. The proposal note exists so the prep work is captured for the eventual patch.

### Five new data sources — bookmark only, do not build

These are real and useful in principle, but L-011 patience mode says no new builds before forward evidence catches up. Categorizing each:

| Source | URL | Status |
|---|---|---|
| **NRB Public Debt Ownership Structure** | nrb.org.np/pdm/ | **Bookmark.** Best contrarian liquidity hypothesis. Build after persistence batch-scoring. |
| **ICRA Nepal rating actions** | icranepal.com/ | **Bookmark.** Real event lane. Build after persistence batch-scoring. |
| **NRB Forex API** | nrb.org.np/api-docs-v1/ | **Interesting only.** No FX-sensitive symbols in our universe yet. |
| **Open Data Nepal + Nepal in Data** | opendatanepal.com / nepalindata.com | **Interesting only.** Useful backfill source if we ever need historical macro joins. |
| **UrjaKhabar daily energy news** | urjakhabar.com/en/ | **Interesting only.** High-maintenance HTML scrape; brittle. |

### One new mechanical experiment hypothesis (deferred)

**NEPSE turnover collapse paradox.** Documented in FY 2025/26:
- Index up ~3%
- 18 new listings
- **But turnover down ~69% YoY**

This is the kind of regime change that historically precedes tops. A simple test would be: does turnover collapse (rolling 30-day turnover < trailing 90-day average × 0.6) precede negative NEPSE returns?

**Status: backlog only.** It would be a NEW experiment, and L-011 explicitly says no new experiments until forward evidence catches up. Captured here so the idea is not lost.

---

## Things We Should NOT Build

| Item | Why not |
|---|---|
| Reddit sentiment scraper | r/NepalStock has only ~304 subscribers |
| Twitter/X sentiment scraper | No meaningful Nepal finance community |
| Custom NEPSE HTTP client | `polymorphisma/nepse_scraper` is the de-facto standard, just use it |
| Specialist LLM agents | L-011 is now globally validated; rearranging the LLM layer doesn't add alpha |
| Experiment 05 (raw text context) | LLMs adding context doesn't beat mechanical rules; not the bottleneck |

---

## Tightened Strategic Recommendations (post-Romeo review)

### Recommendation 1: Update L-010 with the candidate mechanism — DO NOT upgrade Strategy C status

Add a short "Candidate Mechanism for Strategy C" section to L-010 in `experiments/LEARNINGS.md`. Cite the Companies Act AGM deadline and the Investopaper 79% corroboration.

**Critical:** keep Strategy C's status as "promising, needs forward validation." The mechanism is a hypothesis that explains the pattern, not proof that the pattern will continue. Strategy C is still parked.

### Recommendation 2: Capture the experiment 03 patch as a proposal note — do NOT patch yet

After dedup, the actual count of truly new NRB events is **3-4**, not 6 or 8. The patch is captured as `proposal_experiment_03_patch.md` in this folder for the eventual future patch.

**Under L-011 patience mode, this should not be patched before persistence forward evidence batch-scores.** The proposal note exists so the prep work is captured.

### Recommendation 3: Build NOTHING new now

The hydro forward watchlist (AGM count, dividend %, rainfall, take-and-pay status) was a reasonable idea but it is premature. Strategy C does not fire until November 2026. Build the watchlist in October 2026, not now.

The NRB Public Debt Ownership signal, ICRA rating actions, and NEPSE turnover collapse experiment are all worth bookmarking but should not be built before persistence forward evidence batch-scores.

**Build now: zero. Documentation update: ~30 minutes.**

---

## The Honest Bottom Line (post-tightening)

Six research threads. Three honest takeaways after Romeo's wording correction:

1. **Strategy C now has a credible mechanism** (Companies Act AGM deadline + dividend cycle) and one independent corroborating dataset (Investopaper Hydropower Index 2007-2025). The status remains "promising, needs forward validation." The mechanism explains the pattern; it does not prove the pattern will continue.

2. **L-011 is strongly consistent with adjacent-market academic and industry literature.** Multiple 2024-2025 papers reach directionally similar conclusions on US equities, Indian NIFTY, and prediction markets. None tested NEPSE directly. Cite this as "strongly externally supported," not as "universally validated."

3. **The research surfaced 8 candidate NRB event dates and 5 candidate new data sources, all of which are bookmark-only under L-011 patience mode.** The honest count of NEW NRB events worth patching is 3-4 after dedup, captured in `proposal_experiment_03_patch.md` for the eventual patch.

**Big things to NOT build:**
- Any new experiment (turnover collapse, sentiment, etc.)
- Any new scraper (NRB Public Debt Ownership, ICRA, UrjaKhabar, Forex API)
- Specialist LLM agents
- Forward watchlist for Strategy C (premature; build in October 2026)
- Experiment 05 raw text context

**Things worth bookmarking for after persistence forward batch-scoring (ranked):**
1. Patch experiment 03 with the 3-4 truly new NRB events from `proposal_experiment_03_patch.md`
2. Add NRB Public Debt Ownership Structure as a contrarian liquidity signal
3. Add ICRA rating actions as a new event lane
4. Build the Strategy C forward watchlist (in October 2026)
5. Eventually: VPIN applied to NEPSE floorsheet (academically novel; not user goal)

---

## Cross-references

- Experiment lab: `experiments/`
- Existing learnings: `experiments/LEARNINGS.md` (L-001 through L-011)
- NRB experiment to patch: `experiments/03-nrb-rate-events/`
- Hydro experiment to update: `experiments/04-hydro-seasonality/`
- Original Nepal source pack: `market-gist/docs/resources/nepal-market-source-pack-2026-04-08/`

Each individual research thread is documented in `01_*.md` through `06_*.md`. Romeo's commentary is in `99_romeos_takes.md`.
