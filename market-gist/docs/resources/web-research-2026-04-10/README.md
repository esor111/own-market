# Web Research — 2026-04-10

> **Status: Juliet's synthesis. First wording-tightening pass applied 2026-04-10 after Romeo
> flagged overstatements. Romeo has not yet completed a full review of the threads.
> See `99_romeos_takes.md` for the open review points.**

This folder contains six parallel deep-research threads run on 2026-04-10, a synthesis document, and one proposal note. The research was launched to test, validate, and extend the experiment lab findings (L-001 through L-011 in `experiments/LEARNINGS.md`) against published academic literature and external Nepal data sources.

## Files in this folder

**First wave — Conventional research (six threads):**
- `00_synthesis.md` — top-level summary and tightened strategic recommendations across all six threads
- `01_nepse_microstructure_academic_literature.md` — published research on NEPSE and thin emerging markets
- `02_llm_vs_mechanical_finance.md` — academic and industry evidence consistent with L-011 in adjacent markets
- `03_open_source_nepse_tools.md` — existing open-source projects, scrapers, datasets, MCP servers
- `04_nepal_data_sources_we_missed.md` — additional structured Nepal data sources beyond the obvious financial ones (bookmarked, not for immediate build)
- `05_hydropower_nepal_economic_deep_dive.md` — candidate mechanism (AGM/dividend cycle) for the L-009 / L-010 hydro Nov→Jan seasonal
- `06_nrb_margin_lending_impact_and_retail_sentiment.md` — verified May 2025 → April 2026 NRB events plus Nepal retail sentiment infrastructure
- `proposal_experiment_03_patch.md` — deduped patch proposal for experiment 03 (3 truly new events, not 6 or 8). DEFERRED, do not patch yet.

**Second wave — Unconventional research (four threads):**
- `10_unconventional_synthesis.md` — top-level summary and standout findings across all four unconventional threads
- `11_festival_cash_cycles.md` — Dashain/Tihar/Baisakh effects, remittance lag, FD maturity, August unclaimed-dividend mystery, civil service payday, Ashad insurance tax-rush
- `12_political_shocks_catalog.md` — full NEPSE shock catalog 2015-2026 including the September 2025 Gen Z crash (largest shock in our window, missing from event tables) and enriched April 2026 Wagle/money-laundering context
- `13_retail_psychology_signals.md` — Mero Share outages, air pollution, cricket, demat opening growth, day-of-week, monsoon flood × hydro watershed, Bikram Sambat turn-of-month
- `14_nepse_structural_quirks.md` — circuit breakers, pre-open auction, IPO listing-day dump, bonus drift, right share gap, promoter unlock calendar, Reliance Spinning Mills lost IPO

**Third wave — Deep single-question research:**
- `15_broker_reputation_deep_dive.md` — broker reputation as a return predictor on NEPSE. Six sections covering NEPSE-specific research, practitioner tools, adjacent emerging markets, global academic literature (Linnainmaa-Saar, BJZZ, Choi, Barber-Lee-Liu-Odean), methodology recommendations (Choi/Linnainmaa-Saar composite template), and three structural confounds. Two-track recommendation (broker skill spike + insider-pipeline detection). The most rigorously researched side-project candidate in the entire backlog.

**Cross-cutting:**
- `99_romeos_takes.md` — Romeo's commentary (first pass complete on conventional research; unconventional wave review still pending)

## Why this was run

After completing experiments 01-04 and the L-011 meta-learning ("mechanical signals consistently beat LLM judgment on NEPSE"), the user asked Juliet to run deep web research on whatever was worth researching. Six parallel threads were launched in the background covering:

1. **Academic literature** — what does published research say about NEPSE microstructure and thin-market findings?
2. **L-011 globally** — is "mechanical beats LLM" a universal finding or Nepal-specific?
3. **Open-source ecosystem** — what tools, datasets, and projects already exist for NEPSE?
4. **Data sources** — what Nepal-specific structured data are we not yet using?
5. **Hydropower deep dive** — what fundamental story explains the validated hydro seasonal calendar?
6. **NRB margin lending + retail sentiment** — measured impact of the July 2025 reforms and where Nepal retail sentiment lives online

## How to read this folder

- Start with `00_synthesis.md` for the top-level findings and recommendations.
- Each numbered file is a self-contained deep-dive on one thread, with sources and URLs.
- `99_romeos_takes.md` is a separate file capturing Romeo's perspective so the disagreement loop is preserved.

## Status of findings (post-tightening)

### From the conventional wave (files 01-06)
- **L-009 / L-010 hydro Nov→Jan seasonal:** Has a credible candidate mechanism (Companies Act AGM deadline → dividend cycle) and one independent corroborating dataset (Investopaper Hydropower Index 2007-2025, 79% January win rate). Strategy C status remains "promising, needs forward validation."
- **L-011 mechanical-beats-LLM:** Strongly consistent with adjacent-market literature (5+ peer-reviewed 2024-2025 papers). No paper tested NEPSE directly. Cite as "strongly externally supported," not "universally validated."
- **Experiment 03 NRB events:** Up to 8 candidates surfaced; honest count after dedup is **3 truly new events**. Captured in `proposal_experiment_03_patch.md`. Do not patch yet under L-011 patience mode.
- **Five candidate new data sources:** All bookmarked, none worth building now under patience mode.

### From the unconventional wave (files 10-14)
- **Sept 2025 Gen Z crash is missing from our event tables.** Largest single shock in our entire data window: NEPSE -6.00% (-160.33 pts), Rs 268 billion wiped in minutes, market closed 2 weeks. Should be added to `proposal_experiment_03_patch.md`.
- **April 2026 events need enrichment.** Our docs say "finance minister speech" generically. Real chain: Balen Shah PM → Wagle FM → Deepak Bhatta arrest → Sulabh Agrawal/Shanker Group → Rs 3.73B from 5 listed companies → Wagle broker meeting recovery → Deuba arrest warrants.
- **Ashad insurance tax-rush hypothesis** is the highest-novelty new candidate. Mechanism anchored in tax law. Directional-opposite to festival literature. Bookmark.
- **Bikram Sambat month-boundary effect** is a cheap novel candidate. Published research used Gregorian dates, but the specific civil-service payday mechanism is still unverified. Treat as an exploratory BS-boundary turnover test, not an established salary-timing effect.
- **Monsoon flood × hydro watershed event study** is the cleanest fundamental signal in either wave. Difference-in-differences design isolates the effect. Bookmark.
- **Day-of-week effect** is the most-studied NEPSE calendar anomaly, but published findings are inconsistent across papers and all historical work is from older trading-week regimes. Treat as a replication / calibration lane, not a validated signal.
- **NEPSE turnover collapse paradox** (turnover -69% YoY in FY 2025/26): bookmarked. Building it now violates L-011.

### From the deep single-question research (file 15)
- **Broker reputation as return predictor:** rigorously researched. Two tracks recommended (broker-skill feasibility spike + insider-pipeline detection). Track B (insider-pipeline) is probably more promising than Track A (broker ranking). Both bookmark-only under L-011.
- **Reframe required:** "which brokers are skilled" → "which broker TYPES are skilled" (Linnainmaa-Saar style). 3-5 segmented groups, not 90 individual brokers. The individual-broker framing is the wrong frame.
- **Decay warning from BJZZ revisit:** signals in this family decay. Design in-sample/out-of-sample splits from day one.
- **Side warning that affects existing work:** published broker-flow signal hit rates are 52-57%, not 65%+. **If our existing 7-day persistence signal claims a hit rate above 65%, that's outside the published range and warrants a lookahead-bias check.** Add this to the eventual persistence batch-score audit.
- **Critical legal caveat:** Insider-pipeline findings cannot be acted on without legal review. Front-running insider flow is itself MNPI dealing.
- **Promoted to BACKLOG.md as Tier A0** — top of the side-project priority queue, but still bookmark-only under patience mode.
