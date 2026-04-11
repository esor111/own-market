# Romeo's Takes — Partial (One Pass Complete)

## Status

This file captures Romeo's commentary on the bundle. As of 2026-04-10:

- **First pass complete:** Romeo reviewed `00_synthesis.md`, the six thread files, `99_romeos_takes.md`, and `experiments/LEARNINGS.md` and identified four wording overstatements and two internal consistency issues.
- **Wording tightening pass applied** based on Romeo's feedback (see "Romeo's First Pass" section below).
- **Full thread-by-thread review still pending.**

## How to Use This File

When Romeo reviews the web research, his takes should be added here organized by thread. The format used elsewhere in the project (Romeo's reviews, Juliet's syntheses) suggests a section per thread with:

1. **One-line verdict** (agree, mostly agree, disagree)
2. **What Juliet got right**
3. **What Juliet is overstating or missing**
4. **The single biggest disagreement** (if any)
5. **What Romeo would do differently**

## Romeo's First Pass (2026-04-10)

Romeo's review of the bundle and `experiments/LEARNINGS.md` identified four wording overstatements and two internal consistency issues. All four were valid catches and the wording was tightened in response.

### Romeo's verdict on the bundle (one line)
"Useful but overstated in places."

### What Romeo agreed with

1. Hydro Nov→Jan likely has a much better mechanism story than before, and the AGM/dividend-cycle explanation is believable.
2. L-011 is strongly supported by adjacent academic/industry literature.
3. Experiment 03 does look incomplete around the 2025-2026 margin-lending / policy timeline.
4. Reusing existing NEPSE data-access tools is sensible, but our real edge remains evaluation discipline, not scraping.

### Where Romeo pushed back (and Juliet agreed)

1. **Hydro upgrade was too strong.** Romeo: "I think that is directionally right but still a bit too strong until we decide how much to upgrade L-010." → Wording softened from "mechanically grounded with regulatory backing and 18 years of independent corroboration" to "credible mechanism with one independent corroborating dataset."

2. **L-011 framing was too strong.** Romeo: "'universally validated' is stronger than I would use. I would say 'strongly consistent with adjacent-market literature' rather than universal." → Wording softened across `00_synthesis.md`, `02_llm_vs_mechanical_finance.md`, and `experiments/LEARNINGS.md` L-011 addendum.

3. **New source enthusiasm was too strong.** Romeo: "NRB Public Debt Ownership Structure, ICRA, UrjaKhabar are good ideas, but I don't think they outrank patience mode from L-011 yet." → All five Tier-1 sources reframed from "should add soon" to "bookmark only, do not build under patience mode."

4. **Internal consistency issue: 6 vs 8 events.** Romeo: "the synthesis/README often says Experiment 03 has 6 missing events, but thread 6 effectively lists 8 dated rows." → Created `proposal_experiment_03_patch.md` with strict dedup pass. Honest count is **3 truly new events**, not 6, not 8.

5. **Internal consistency issue: 99_romeos_takes.md was empty.** Romeo: "we should be careful not to talk as if the disagreement loop is already complete." → Added an explicit unconfirmed-by-Romeo banner to `00_synthesis.md` and to `README.md`.

### Specific wording changes made

| File | Before | After |
|---|---|---|
| `00_synthesis.md` | "L-011 is now globally validated" | "L-011 is strongly consistent with adjacent-market literature" |
| `00_synthesis.md` | "Mechanical regulatory effect with academic-grade backing" | "Pattern with a credible mechanism, still pending forward validation" |
| `00_synthesis.md` | "We were rediscovering a real, structurally-driven seasonal" | "Our small-sample finding is consistent with a longer-sample published index-level finding" |
| `00_synthesis.md` | "The cheapest high-leverage work" | "The lowest-cost backlog item if and when we decide to extend experiment 03" |
| `02_llm_vs_mechanical_finance.md` | "NOT unique to Nepal. It is well-documented" | "Strongly consistent with 2024-2025 literature on adjacent markets" |
| `04_nepal_data_sources_we_missed.md` | "Should Probably Add Soon" / "Best new experiment idea" | "Worth Knowing Exists, Not Actionable Under Patience Mode" / "Bookmarked" |
| `05_hydropower_nepal_economic_deep_dive.md` | "Mechanistically grounded by Nepal's Companies Act" | "Has a credible candidate mechanism" |
| `06_nrb_margin_lending_impact_and_retail_sentiment.md` | "Add 8 events" | "3 truly new events after dedup; see proposal_experiment_03_patch.md" |
| `experiments/LEARNINGS.md` L-010 | (no addendum) | New "Candidate Mechanism for Strategy C" section that adds the AGM mechanism without changing Strategy C status |
| `experiments/LEARNINGS.md` L-011 | (no addendum) | New "External Corroboration" section explicitly noting no paper tested NEPSE directly |

## What Romeo Still Has Open (Full Thread Review Pending)

These are open questions where Romeo's full review is still pending:

1. **Thread 1 (NEPSE academic literature):** Are the academic citations correctly characterized? Particularly the Bhattarai BVPS finding and the Fama-French reversal — should we test these as new experiments, or are they background context only?

2. **Thread 2 (LLM vs mechanical):** The 5+ papers cited are real but Romeo has not verified each one. If any single paper turns out to be misrepresented or not actually directionally consistent, the L-011 corroboration story weakens.

3. **Thread 3 (open-source ecosystem):** The recommendation to switch to `polymorphisma/nepse_scraper` is plausible but has not been tested against our actual data needs. Is the de-facto standard claim accurate?

4. **Thread 4 (Nepal data sources):** Five Tier-1 sources are now bookmarked. Romeo should sanity-check the bookmark list — is the contrarian liquidity hypothesis (NRB Public Debt Ownership) actually as plausible as Juliet says, or is Juliet still slightly enthusiastic about it?

5. **Thread 5 (hydropower):** The candidate AGM/dividend mechanism is plausible. Romeo should verify the Investopaper 79% number is real and the Companies Act citation is accurate.

6. **Thread 6 (NRB events + sentiment):** The 3-event patch list is captured. Romeo should review whether the dedup is correct, particularly whether 2025-07-11 should or should not be added as a separate announcement-date row.

7. **`proposal_experiment_03_patch.md`:** The dedup logic is documented. Romeo should review before any patch is actually applied.

## Why The Disagreement Loop Matters (Original Note)

Throughout this project, the value of Romeo and Juliet's interaction has been the **disagreement loop**. Romeo has caught real bugs and overclaims that Juliet missed (the Phase 1 hydro overreach, the calendar-day bug in the scorer, the wording bug in the seasonal-fight check, the 6-vs-8 NRB events count). Juliet has caught things Romeo missed (the dedup issue in the corporate action study, the L-007 calendar mismatch in the live shadow report). Both directions of the loop have caught real issues.

## Cross-Reference

- Original synthesis: `00_synthesis.md`
- Threads: `01_*.md` through `06_*.md`
- Prior Romeo reviews: scattered across `experiments/01-corporate-action/results/` and the conversation history
