# Backlog — What's Done, What's Work, What's Side-Project

> Status as of 2026-04-19. This is the canonical "what next?" document.
> The structure deliberately puts WORK first and SIDE PROJECTS last.
> Under L-011 patience mode, side projects should not start until persistence
> forward batch-scoring is done.
> Gate interpretation at N≥25 follows `experiments/batch-score-playbook/INTERPRETATION_GATE.md` v3 (Gate 1 forecast + Gate 2 actionability; `TRADE_READY` requires post-cost EV > baseline by ≥1σ promotion margin).

## How to read this document

- **Section 1** is what we have already researched and learned. This is the inventory.
- **Section 2** is the boring necessary daily/weekly/calendar work. Do this first. This is what actually moves the system forward.
- **Section 3** is the side-project backlog, ranked. Do nothing here until Section 2 produces a real promotion decision (persistence shadow batch-score at 25+ resolved cases).

If you only read one line: **the next thing to do is keep running `run_persistence_shadow_daily.py` after every trading session and let the forward evidence accumulate until 25+ cases resolve.** Everything in Section 3 is on hold until then.

---

# Section 1: What We Have Researched

## Experiments Completed

| # | Experiment | Status | Headline Finding |
|---|---|---|---|
| 01 | Corporate Action Timing | **In-sample validated (14-symbol seed); annotation deployed** | Dividend-family bank notice → 10-day drift, 71% hit, p=0.004 in-sample. Annotation deployed in shadow report (not a trade rule). Book closure → drift_2_10 also strong but hydro-only. |
| 02 | Lock-In Expiry | **Parked** | N=27, p=0.25. Directionally correct, statistically inconclusive. Re-test when more unlocks happen. |
| 03 | NRB Rate Events | **Parked** | Anticipation-then-reversal pattern. Easing events show pre-window rally + post-window drift. Use as context, not signal. |
| 04 | Hydro Seasonality | **Parked, needs forward validation** | Strategy C (Nov→Jan hydro buy): 71% historical win rate, +12% mean over 28 historical trades in 2021-2026 window. Candidate mechanism: Companies Act AGM deadline → dividend cycle. Independent corroboration: Investopaper 79% Jan win rate over 2007-2025. Historical pattern only; forward validation required before any trade use. |

## Production Systems Running

| System | Status | Maturity |
|---|---|---|
| Persistence shadow report (daily) | Running, frozen v1 policy | 20 of 61 cases resolved across all groups; 11 of 11 in `persistence_caution_only` (N≥25 gate in that group per `INTERPRETATION_GATE.md` v3) |
| Dividend-family bank annotation | Live in shadow report (annotation only) | Patched 2026-04-09 |
| Forward shadow scorer | Running, calendar fixed (L-007) | Same 20/61 across groups |
| One-command daily runner | Built 2026-04-10 | New |
| Defensive tweaks (L-007 fix, exception fix, sanity checks) | Applied 2026-04-10 | New |

## Documented Learnings

11 entries in `experiments/LEARNINGS.md`:

| ID | Topic | Status |
|---|---|---|
| L-001 | Corporate action timing creates measurable drift | In-sample validated on 14-symbol seed; dividend annotation deployed |
| L-002 | Lock-in expiry directionally correct but inconclusive | Parked |
| L-003 | Baseline adjustment is non-negotiable on NEPSE 2021-2024 data | Operational rule |
| L-004 | Nepal AGM season is a predictable calendar window | Context for Strategy C |
| L-005 | ShareSansar API has 50-row page size limit | Technical gotcha, fixed |
| L-006 | Sharesansar CSV archive contains non-trading-day clones | Technical gotcha, fixed |
| L-007 | Forward scorers must use the same trading calendar as the experiment framework | Fixed both in scorer and live shadow report (2026-04-10) |
| L-008 | NRB rate events show anticipation-then-reversal | Context only |
| L-009 | Hydropower has a stock-level seasonal calendar | Historical pattern in 2021-2026 window; needs forward evidence |
| L-010 | The hydro seasonal-fight hypothesis was wrong; the real finding is the Nov→Jan calendar trade | Strategy C parked + candidate mechanism added 2026-04-10 |
| L-011 | Mechanical signals beat LLM judgment on NEPSE | Strongly externally supported by adjacent-market literature |

## Web Research Bundle (2026-04-10)

Six parallel threads documented in `market-gist/docs/resources/web-research-2026-04-10/`:

1. **NEPSE microstructure academic literature** — our findings consistent with published Nepal/Bangladesh research where overlap exists; broker persistence is academically virgin territory in NEPSE
2. **LLM vs mechanical in finance** — L-011 strongly externally supported by 5+ peer-reviewed 2024-2025 papers on adjacent markets
3. **Open-source NEPSE ecosystem** — our work is more rigorous than anything public; data access libraries we should consider using; one closest comparable project (`nepse-quant-terminal`)
4. **Nepal data sources we missed** — 5 candidate sources bookmarked, none worth building under patience mode
5. **Hydropower deep dive** — candidate mechanism for Strategy C (AGM/dividend cycle) with one independent corroborating dataset
6. **NRB margin lending impact + retail sentiment** — 3 truly new NRB events identified for eventual experiment 03 patch (deferred)

Romeo's first-pass review applied 2026-04-10. Wording tightened across the bundle. Full thread-by-thread review still pending.

---

# Section 2: The Work (Do This First)

This is what should happen before anything in Section 3 starts. It is not glamorous. It is the only thing that moves the system forward right now.

## Daily Work

**Every trading session:**
```
cd market-gist/automation
python run_persistence_shadow_daily.py --date <today's session date>
```

This single command:
1. Sanity-checks input directories
2. Verifies broker flow data exists for the date
3. Generates the shadow report (with dividend annotation, with seasonal expectations later if added)
4. Refreshes the forward scorer

**Time cost:** ~1-2 minutes after the floorsheet scrape completes.

## Weekly Work

**Once a week:**
1. Run the scorer manually if you want to see progress: `python score_persistence_shadow_reports.py`
2. Count resolved cases. Write the number down somewhere (or check the latest scorecard JSON).
3. Note any pending rows that resolved.

**Time cost:** ~5 minutes.

## Maintenance Work

**Whenever Sharesansar price data updates:**
- The 17 pending shadow rows resolve automatically as price data passes their +10 trading day window
- This is the single piece of upstream maintenance that matters
- Without it, pending stays pending forever

## Calendar Triggers (Must-Hit Dates)

| When | What | Why |
|---|---|---|
| **As soon as 25+ cases resolve** | Batch-score persistence shadow. Make first promotion decision. | This is the decision that determines whether the entire mechanical foundation works. Everything else waits on this. |
| **August 2026** | Mark bank Aug→Jan avoid window opens. Track NABIL/EBL/SANIMA shadow CAUTION coincidence. | Bank Aug-Jan negative seasonal: 1/31 historical wins (3.2%), strongest single pattern in the lab. |
| **October 2026** | Build Strategy C forward watchlist | One month before Strategy C fires. Premature now. |
| **November 2026** | Mark Strategy C buy window opens across 6 hydro stocks | First real-time forward test of Strategy C. |
| **February 2027** | Score Strategy C across the 6 hydro stocks | First real-time evaluation of the validated calendar trade. |

## Decision Points That Matter

| Trigger | Decision |
|---|---|
| Persistence shadow at 25+ resolved | Promote, demote, or kill the persistence policy |
| Dividend annotation at 15+ resolved | Promote dividend annotation from "annotation only" to verdict-affecting |
| Strategy C 1 forward year (Feb 2027) | Promote, demote, or kill the Nov→Jan hydro calendar trade |
| Bank Aug-Jan 1 forward year (Feb 2027) | Promote, demote, or kill the bank Aug-Jan avoid signal |

**That's the entire work list for the next 2-3 months.** Everything in Section 3 is bookmark-only until at least the first decision point fires.

---

# Section 3: Side Projects (Backlog, Ranked)

These are real ideas worth doing eventually. **None of them should start before Section 2 produces a promotion decision.** They are listed in rough priority order within each category.

## Tier A — Highest-Value, Smallest, Most Mechanical

These are the side projects that would most directly extend what already works.

### A0. Broker Reputation as Return Predictor — Two Tracks ⭐ NEW (deep research 2026-04-10)
- **What:** Test whether NEPSE brokers have measurable directional skill across the stocks they touch, AND/OR whether specific brokers consistently appear in stocks before corporate-action announcements (insider-pipeline detection).
- **Why:** This is the most rigorously researched side-project candidate in the entire backlog. Linnainmaa & Saar (2012) validated the methodology in Finland; Choi (2013) validated the portfolio sort approach in Shanghai; nobody has done it in a thin South Asian market. NEPSE floorsheet data is broker-identified — we have everything needed.
- **Caveats:** Three structural confounds. (1) **Client-order dilution** — every broker's net is a blend of prop + thousands of client orders, so individual-broker signals will be diluted. (2) **Market-maker pollution** — top-volume brokers are zero-net market makers and need segmenting. (3) **Insider-pipeline contamination** — sharp signals on NEPSE are likely insider leaks (Ridi Hydropower, Sarbottam, Bhrikuti #55), not forecasting skill. **Acting on insider-pipeline findings without legal review may itself be MNPI dealing.**

#### Track A — Broker Skill Feasibility Spike (~2 weeks)
- **Steps:**
  1. Compute per-broker 10-day forward-return hit rate for all ~90 brokers on existing floorsheet
  2. Compute cross-period Spearman rank correlation between two halves of the sample
  3. Plot the skill distribution against a permutation null
  4. Apply the 5-criterion verdict matrix (see deep dive doc)
- **Decision rule:**
  - Rank correlation **>0.4** AND distribution distinguishable from null → promote to full experiment with **broker-TYPE** framing (3-5 segmented groups, not 90 individuals — Linnainmaa-Saar style)
  - Rank correlation **<0.3** → kill the project entirely
  - In between → publishable curiosity but not actionable
- **Watch out for:** lookahead bias, survivorship (suspended brokers), market-maker pollution. Use block bootstrap and Benjamini-Hochberg FDR correction at 5% — with ~90 brokers, expect 4-5 false positives at p<0.05 by chance.

#### Track B — Insider-Pipeline Detection (~1-2 weeks)
- **Steps:**
  1. Use existing corporate action event table from Experiment 01
  2. For each event, compute each broker's net position change in the [-10, -3] window before the announcement
  3. Identify brokers with consistent anomalous positioning across multiple events
  4. Test: same brokers across multiple event types (= structural pipeline) or single events (= noise)
  5. Cross-reference with SEBON enforcement actions to validate
- **Why probably MORE promising than Track A:** mechanical (not behavioral), directly extends Experiment 01, has a defensible mechanism (insider trading is documented to exist on NEPSE), and produces a regulatory-risk early-warning signal as a bonus.
- **Critical legal caveat:** Do NOT trade on identified insider-pipeline signals without legal review. Front-running insider flow is itself MNPI dealing in many jurisdictions. SEBON enforcement is tightening.

#### When to start
- **Not now.** L-011 patience mode applies. After persistence shadow batch-scores at 25+ resolved cases.

#### Key citations
- Linnainmaa & Saar (2012) "Lack of Anonymity and the Inference from Order Flow" — methodology anchor
- Choi, Jin & Yan (journal-published 2025, circulated earlier) on Shanghai institutional flow — emerging-market analog (10.8% is raw return spread, not risk-adjusted alpha)
- Barber, Lee, Liu, Odean (2014) Taiwan day-trader skill — statistical power template
- BJZZ (2021) and Ardia, Aymard & Cenesizoglu (2025) revisit — decay precedent (BJZZ predictive power dropped 34%; "completely disappears" for large-cap post-2016). *(Attribution corrected 2026-04-12: previously said "Barber et al. 2024" which is a different paper about BJZZ algorithm signing errors.)*
- Full deep dive: `market-gist/docs/resources/web-research-2026-04-10/15_broker_reputation_deep_dive.md`

#### Side warning that affects existing work
Published broker-flow papers (BJZZ, Barber-Lee-Liu-Odean, Choi-Jin-Yan) report modest return spreads (~10 bps/week for BJZZ), not direct directional hit-rate benchmarks. **The lab's implied directional accuracy estimate from these return spreads is ~50-52%, but this is our inference, not a published number.** If our existing 7-day persistence signal claims a hit rate well above this range, that warrants a lookahead-bias check. Add this to the eventual persistence batch-score audit. *(Wording tightened 2026-04-12 per Romeo review after Benvolio traced the original papers.)*

### A1. Patch Experiment 03 with 3 new NRB events
- **What:** Add 3 truly new NRB event dates from `proposal_experiment_03_patch.md` to `policy_events.csv` and re-run experiment 03
- **Why:** Adds asymmetric (negative) events that we don't have. Tests whether the L-008 anticipation-reversal pattern reverses sign for tightening events.
- **When:** After persistence shadow batch-scores. Not before.
- **Effort:** 1-2 hours
- **Watch out for:** Dedup is documented in the proposal note. Romeo should review before patching.

### A2. NRB Public Debt Ownership Structure → Contrarian Liquidity Signal
- **What:** Scrape NRB monthly Public Debt Management ownership reports. Test the hypothesis: when commercial banks decrease T-bill holdings month-over-month, they're shifting liquidity into margin → leads NEPSE rally; when they increase holdings → leads decline.
- **Why:** Genuinely new lens. Mechanical. Monthly granularity. Public PDF source.
- **When:** After persistence shadow batch-scores AND after experiment 03 patch is complete.
- **Effort:** 1 day to build the scraper + 1 day to run the experiment with the existing event_study framework.
- **Watch out for:** New experiment, violates L-011 if started early. Bookmark only until trigger.

### A3. ICRA Nepal rating actions → New event lane
- **What:** Scrape ICRA Nepal credit rating upgrade/downgrade announcements. Run as a new event lane through the existing experiment_study framework.
- **Why:** Documented to lead stock price by days-to-weeks in Nepal. Independent from broker persistence and corporate action signals.
- **When:** After A2.
- **Effort:** Half day to scrape, half day to run the event study.
- **Watch out for:** Same as A2 — new experiment, bookmark only.

### A4. Strategy C Forward Watchlist
- **What:** Daily/weekly script that tracks: (a) count of hydro AGMs announced Nov-Dec, (b) cumulative dividend % declared by NEPSE hydros as of Mangsir 15, (c) take-and-pay PPA policy status, (d) NEA payment-arrears reports to IPPAN, (e) Ashadh rainfall anomaly
- **Why:** Tells you whether Strategy C will fire this year before November arrives
- **When:** **October 2026** (one month before Strategy C buy window opens)
- **Effort:** 4-6 hours
- **Watch out for:** Premature now. Build it in October, not before.

### A5. Confirmed-Damage Hydropower Event Study
- **What:** Build a symbol registry and flood-damage event table for listed hydropower names, then test whether specifically damaged hydros underperform undamaged hydro peers after the first credible named damage report.
- **Why:** The UPPER Sep 2024 sanity check kept this lane alive, but narrowed the claim. The right frame is company-level damage confirmation, not generic monsoon or basin-only exposure.
- **When:** Research scaffolding is fine now; full event-table scoring should wait until persistence batch-scoring is no longer the only live gate.
- **Effort:** Half day for structure, 1-2 days for event-table build, half day for first scoring pass.
- **Watch out for:** Use the **first named public damage report** as the anchor date, not the rainfall date. Test multiple windows (`[0,+5]`, `[0,+10]`, `[0,+20]`, slower drift). Market-wide disaster panic may swamp short-window effects.
- **Workspace:** `experiments/06-hydro-flood-damage/`

## Tier B — Infrastructure That Makes Future Work Easier

These don't add new signals. They make the existing system more usable.

### B1. Use polymorphisma/nepse_scraper instead of custom HTTP code
- **What:** Replace any custom NEPSE HTTP client code with the de-facto standard PyPI library
- **Why:** Less maintenance, more reliability
- **When:** Whenever we next need to add a new NEPSE data source
- **Effort:** 2-3 hours when it's needed
- **Watch out for:** Don't refactor proactively. Let the next data need pull this in.

### B2. Personal NEPSE Data API (FastAPI local server)
- **What:** Wrap everything we've scraped (prices, broker flow, corporate actions, persistence scores) in a simple local FastAPI server. Future questions hit a URL instead of reading files.
- **Why:** Single source of truth, versioned, cacheable. Makes everything else easier.
- **When:** After at least one Tier-A side project completes
- **Effort:** 2-3 days
- **Watch out for:** Easy to over-engineer. Build the smallest possible version first.

### B3. "What did we say about this stock on this date" sandbox
- **What:** Given a symbol and date, show every signal computed: persistence score, calendar position, active corporate actions, dividend annotation, agent predictions
- **Why:** Retrospective debugging. When a prediction goes wrong, you can see exactly what the system was thinking.
- **When:** After B2
- **Effort:** 1 day
- **Watch out for:** Useful for learning, not for prediction.

### B4. Generic Backtest Engine
- **What:** A function that takes ANY rule definition (not just the ones we've built) and runs it against local data with proper baseline adjustment
- **Why:** Future experiments take 30 minutes instead of 3 hours
- **When:** After at least 2 Tier-A side projects
- **Effort:** 2-3 days
- **Watch out for:** Easy to over-engineer. Start with the experiment 04 phase2 backtest pattern and generalize from there.

## Tier C — Research Curiosity (Low Priority)

These are interesting questions, none directly improve prediction.

### C1. NEPSE Turnover Collapse Paradox → New Mechanical Experiment
- **What:** Test whether turnover collapse (rolling 30-day turnover < trailing 90-day average × 0.6) precedes negative NEPSE returns
- **Why:** FY 2025/26 documented turnover -69% YoY while index up. This kind of regime change historically precedes tops.
- **When:** After persistence batch-score AND after at least one Tier-A side project
- **Effort:** 1 day
- **Watch out for:** New experiment, violates L-011 if started early.

### C2. Broker Reputation Ranking
- **What:** For each NEPSE broker, compute: when they buy heavily, what happens next? When they sell heavily, what happens next? Build a ranking by predictive value, not volume.
- **Why:** Could become a real edge. Nobody has done this systematically on NEPSE.
- **When:** After persistence batch-score
- **Effort:** 1 week
- **Watch out for:** Closest to the broker persistence work we already do, but at the broker level instead of the symbol level.

### C3. Information Diffusion Timing Study
- **What:** When a corporate action announcement is made, how fast does the price react? Some stocks react in minutes, others in days. Variance is more interesting than average.
- **Why:** Slow-diffusion stocks have a window before the move completes — potential signal
- **When:** After persistence batch-score
- **Effort:** 1 week
- **Watch out for:** Requires intraday timestamps which our current data lacks.

### C4. NEPSE vs Other Thin Emerging Markets
- **What:** Compare NEPSE seasonal patterns and broker concentration to Sri Lanka CSE, Bangladesh DSE, Pakistan PSX
- **Why:** Tells us if our findings are Nepal-specific or universal in thin markets
- **When:** Eventually
- **Effort:** 1-2 weeks
- **Watch out for:** Pure curiosity, not directly actionable for prediction.

### C5. Lab Self-Audit
- **What:** Go through every claim in LEARNINGS.md and re-test it with whatever fresh data is available. Catch any overclaims.
- **Why:** Documentation discipline. Romeo caught my Phase 1 overclaim; what other overclaims am I sitting on?
- **When:** Eventually, when documentation discipline drift becomes visible
- **Effort:** 1 week
- **Watch out for:** Easy to be sloppy. The whole point is being strict.

### C6. Dashain/Tihar/Election Cycle Effects
- **What:** Same script as Experiment 04, different event calendar. Test pre-Dashain rallies, post-Tihar weakness, election year volatility.
- **Why:** Nepal-specific cultural/political effects we haven't tested
- **When:** Eventually
- **Effort:** 2-3 days

## Tier D — Things We Should NOT Build

These came up in research but are not worth building.

| Idea | Why not |
|---|---|
| Reddit r/NepalStock sentiment scraper | Only ~304 subscribers, sample too small |
| Twitter/X Nepal finance sentiment | No meaningful Nepal finance Twitter community |
| Custom NEPSE HTTP client | `polymorphisma/nepse_scraper` exists |
| Specialist LLM agents (broker-flow, calendar, macro, structure, etc.) | L-011 says LLM topology is not the bottleneck. Premature. |
| Experiment 05: Raw text context for LLM | LLMs adding context doesn't beat mechanical rules. Wrong layer to optimize. |
| Facebook group sentiment scraping | Highest-velocity sentiment in Nepal but scraping is brutal; not worth the engineering cost until we have a proven sentiment pipeline elsewhere |
| TikTok/Instagram sentiment scraping | Documented as the locus of pump-and-dump manipulation. Useful as adversarial signal in theory, hard to extract organic sentiment. |
| UrjaKhabar daily news scraping | High-maintenance HTML scrape for marginal lead time. Brittle. |
| NRB Forex API | We don't track FX-sensitive symbols |
| VPIN applied to NEPSE floorsheet | Academically novel but we are not building toward publication |

## Tier E — Outright Wild Ideas (Low Confidence, Worth Mentioning)

These are pure curiosity. I include them because the brainstorm earlier in the conversation surfaced them and they might unlock something unexpected.

| Idea | Category |
|---|---|
| YouTube comment sentiment on Share Durbar/Grow More/Sharemandu | Contrarian sentiment hypothesis |
| Sajha.com stock thread scraping | Long-history Nepal forum, plain HTML |
| Public Telegram channel scraping | Nepal stock signal channels via Telethon |
| NRB monetary policy PDF parser using LLM | The one place LLMs might genuinely help: unstructured-to-structured extraction |
| "Skeptic agent" — narrow Broker-Flow LLM specialist test | Romeo's open question from the architecture discussion. Test ONE narrow specialist against the generalist on archived broker-heavy cases. Small experiment, settles a real uncertainty. |
| Complete NEPSE floorsheet historical archive (all 250 listed companies) | Pure research infrastructure. Irreplaceable once built. |
| Broker network graph (which brokers connect which stocks) | NEPSE-specific microstructure question nobody has answered |

---

# Section 4: The Honest Strategic Picture

After all this documentation, here is what's actually true:

1. **The system has more research than evidence.** 11 documented learnings, 4 experiments, web research bundle, validated mechanism for Strategy C — but only 14 forward-resolved persistence cases. The bottleneck is forward time.

2. **The work that matters in the next 2-3 months is in Section 2, not Section 3.** Daily routine, calendar triggers, batch-scoring decisions. Boring. Necessary.

3. **Section 3 is real and worth doing eventually, but it's a backlog, not a roadmap.** L-011 patience mode says no new experiments until forward evidence catches up. The backlog exists so the ideas are not lost, not so they get built next week.

4. **Romeo's frozen-champion discipline applies to the lab itself, not just to individual policies.** Stop generating new hypotheses faster than we can validate the existing ones forward. This is L-011 applied to lab management.

5. **The most expensive mistake at this stage is churn.** Every new experiment is another pending evaluation. Every new scraper is another thing to maintain. Adding to the system right now makes it harder to run reliably, not easier.

## The Single Sentence Version

**The next thing to do is run the daily routine, wait for 25 resolved cases, batch-score, then re-read this document.** Sections 2 and 3 can both wait until that decision point fires.

---

# Cross-references

- Experiment lab: `experiments/`
- Documented learnings: `experiments/LEARNINGS.md` (L-001 through L-016)
- Web research bundle: `market-gist/docs/resources/web-research-2026-04-10/`
- Experiment 03 patch proposal: `market-gist/docs/resources/web-research-2026-04-10/proposal_experiment_03_patch.md`
- Daily runner: `market-gist/automation/run_persistence_shadow_daily.py`
- Forward scorer: `market-gist/automation/score_persistence_shadow_reports.py`
- Persistence shadow reports: `market-gist/data/validation/persistence_shadow_reports/`
- Frozen policy: `market-gist/agents/shared/PERSISTENCE_SHADOW_POLICY_V1_FROZEN.md`
