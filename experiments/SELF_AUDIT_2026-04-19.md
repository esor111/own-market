# Lab Self-Audit — 2026-04-19

## Summary

- Total corrections found: **23**
- By pass: P1=5, P2=8, P3=2, P4=3, P5=4, P6=1
- Files touched in application: 6
  - `experiments/signal-decay-tracker/README.md`
  - `experiments/signal-decay-tracker/CONTRACT.md`
  - `experiments/CURRENT_STATE_MEMO.md`
  - `experiments/BACKLOG.md`
  - `experiments/EXPLORATION_CHARTER.md`
  - `experiments/INDEX.md`

Out-of-scope and untouched: `INTERPRETATION_GATE.md` v3, `effective_n_analysis_2026-04-19.md`, `universe_v1_frozen.csv`, `universe_v2_candidate.csv`, `L001_V2_VERSIONING_PLAN.md`, all code, all session logs (historical records).

---

## Pass 1 findings — retired-framing sweep

Retired framings per L-012 addendum (2026-04-18): the headlines "88.9%" and "still above chance" are retired in favor of "72.7% on N=11 resolved CAUTION cases, directionally suggestive but not statistically significant (binomial p ≈ 0.11)".

| File:line | Current text | Suggested replacement | Applied? |
|---|---|---|---|
| `CURRENT_STATE_MEMO.md:34` | `10-day negative hit rate: 88.9% (8/9)` | Update scorecard to post-addendum numbers: resolved 11, hit rate 72.7% (8/11), binomial p ≈ 0.11 | **yes** |
| `signal-decay-tracker/README.md:10` | `The persistence signal currently shows 88.9% hit rate on 9 resolved CAUTION cases.` | Replace with post-addendum numbers and retire the 30+pp-over-ceiling framing (that calculation was against the 88.9% headline) | **yes** |
| `LEARNINGS.md:499` (L-011 table) | `Broker w7 seller persistence vs LLM CAUTION calls \| 8/9 negative 10d (88.9%) on small forward sample` | Post-addendum: `8/11 (72.7%) on small preliminary forward sample` — but this edits a Romeo-verified L-entry comparison | **no — flagged for Romeo** |
| `LEARNINGS.md:693` (L-012 data-advantage table) | `Our persistence signal claims \| 88.9%` | Add "(retired per L-012 addendum)" annotation | **no — flagged for Romeo** |
| `market-gist/automation/SCRAPE_EXPANSION_2026-04-12.md:16` | `The persistence shadow signal claims 88.9% (8/9) hit rate, but...` | Historical memo (dated 2026-04-12); contextually OK but uncalibrated against addendum | **no — session-log-class historical; flag only** |

## Pass 2 findings — evidence-label audit

Weakest-accurate-label rule: prefer "suggests"/"candidate"/"historical" over "confirms"/"strong"/"validated" unmarked.

| File:line | Current text | Suggested replacement | Applied? |
|---|---|---|---|
| `BACKLOG.md:24` | Exp 01 status: `Validated, partially deployed` | `Historical pattern (14-symbol seed, p=0.004 in-sample); annotation deployed in shadow report, not a trade rule` | **yes** |
| `BACKLOG.md:27` | Exp 04 status: `Validated, with credible mechanism` (conflicts with same row's `Status: parked, needs forward validation`) | Remove top-level "Validated" label, keep the "parked, needs forward validation" status | **yes** |
| `BACKLOG.md:45` | `L-001 \| Corporate action timing creates measurable drift \| Validated, dividend signal deployed` | `In-sample validated on 14-symbol seed; annotation deployed` | **yes** |
| `BACKLOG.md:53` | `L-009 \| Hydropower has a strong, stock-level seasonal calendar \| Validated` | `Historical pattern, 2021-2026 window; needs forward evidence` | **yes** |
| `MANIFESTO.md:42` | `71% bank hit rate, p=0.004, validated. Doesn't change verdicts yet.` | `71% bank hit rate, p=0.004 in-sample on 14-symbol seed; annotation only, no verdict change` | **no — flagged for Romeo** (MANIFESTO is Romeo-reviewed canon) |
| `EXPLORATION_CHARTER.md:79` | `Annotates a validated dividend-family signal on bank stocks (live in shadow report, does not change verdicts)` | `Annotates an in-sample-validated dividend-family signal on bank stocks (14-symbol seed; live in shadow report; does not change verdicts)` | **yes** |
| `EXPLORATION_CHARTER.md:95` | `71% bank hit rate, p=0.004, validated. Doesn't change verdicts yet.` | `71% bank hit rate, p=0.004 in-sample on 14-symbol seed; does not change verdicts` | **yes** |
| `INDEX.md` Exp 04 row | `strong seasonal confirmed: Jan bullish (89%)...year-stable` | `historical seasonal pattern, 2021-2026 window: Jan bullish (89%)...year-stable within window; needs forward evidence` | **yes** |

## Pass 3 findings — cross-doc consistency

| Experiment | INDEX status | README status | LEARNINGS status | Canonical | Applied? |
|---|---|---|---|---|---|
| 04 Hydro Seasonality | `completed` → "strong seasonal confirmed" | n/a (no dedicated README) | L-009/L-010 "Promising, parked" | INDEX label too strong | **yes** (fixed in Pass 2 row above) |
| 07 Dividend Microstructure | `closed at Gate 1` (today) | `Lane CLOSED (2026-04-18)` | L-016 closure documented | Consistent | no action needed |
| 08 Reversal Specialist | `closed at Gate 1` (today) | `Lane CLOSED (2026-04-19)` | L-016 closure documented | Consistent | no action needed |

## Pass 4 findings — stale status / next-action lines

| File:line | Current text | Suggested replacement | Applied? |
|---|---|---|---|
| `BACKLOG.md:3` | `> Status as of 2026-04-10. This is the canonical "what next?" document.` | `> Status as of 2026-04-19. This is the canonical "what next?" document.` | **yes** (date refresh + note that Section 2 numbers updated) |
| `BACKLOG.md:33,35` | Persistence shadow row: `14 of ~30 needed cases resolved` | `20 of 61 total / 11 of 11 resolved in persistence_caution_only; gate is N≥25 in caution_only group per INTERPRETATION_GATE.md v3` | **yes** |
| `signal-decay-tracker/CONTRACT.md:67` | `Current resolved case count: 14 (as of 2026-04-13). Below the gate.` | `Current resolved case count: 20 total / 11 in persistence_caution_only (as of 2026-04-19). Below the N≥25 gate.` | **yes** |

## Pass 5 findings — "latest" / "most recent" claims

| File:line | Current text | Suggested replacement | Applied? |
|---|---|---|---|
| `EXPLORATION_CHARTER.md:81` | `Documents every learning in experiments/LEARNINGS.md (currently L-001 through L-011)` | `currently L-001 through L-016` | **yes** |
| `EXPLORATION_CHARTER.md:94` | `Running daily, ~14 of ~30 needed cases resolved \| Most validated thing we have. 8 of 9 negative on small sample.` | `Running daily, 20/61 cases resolved, 11 of 11 in persistence_caution_only, hit rate 72.7% (binomial p≈0.11, directionally suggestive, not statistically significant at current N per L-012 addendum). Gate is N≥25 in caution_only group.` | **yes** |
| `MANIFESTO.md:41` | `Running daily, 14/37 cases resolved \| 8 of 9 CAUTION cases negative, but clustered: 7/8 wins from 2 consecutive Aug 2025 days with overlapping forward windows. Effective independent episodes ~2-3, not 9 (audit 2026-04-12, Romeo-verified). Evidence is preliminary. The 23 pending forward cases from Mar-Apr 2026 are the real test.` | Numerical refresh to post-addendum state | **no — flagged for Romeo** (Romeo-verified canon paragraph) |
| `MANIFESTO.md:28` | `broker persistence (8 of 9 negative on a small sample)` | `broker persistence (preliminary at N=11 resolved, 72.7%, not statistically significant at current N per L-012 addendum)` | **no — flagged for Romeo** (same reason) |

## Pass 6 findings — persistence gate wording

The persistence promotion gate per `INTERPRETATION_GATE.md` v3:
- Gate 1 (forecast validity): N≥25 resolved in `persistence_caution_only`, hit rate ≥65%, top-3 dates ≤40%, effective independent episodes ≥5, sub-period stability, F.1 pre-reg, A.1–A.3 structural
- Gate 2 (actionability): post-cost EV > baseline by ≥1σ promotion margin; three-lens reporting; avoid-buy OR exit/sell must pass; short-like alone cannot promote
- Verdicts: `BELOW_GATE`, `HOLD`, `FORECAST_UNVALIDATED`, `FORECAST_VALID_COST_UNMEASURED`, `FORECAST_VALID_COST_NEGATIVE`, `FORECAST_VALID_COST_MARGINAL`, `TRADE_READY`

| File:line | Current text | Suggested replacement | Applied? |
|---|---|---|---|
| `BACKLOG.md:14` | `the next thing to do is keep running run_persistence_shadow_daily.py...until 25+ cases resolve` | Add cross-reference: "Verdict interpretation at N≥25 follows `experiments/batch-score-playbook/INTERPRETATION_GATE.md` v3 (Gate 1 forecast + Gate 2 actionability; `TRADE_READY` requires post-cost EV > baseline by ≥1σ)." | **yes** (appended cross-reference, not replacement) |

## Corrections applied

Applied 16 distinct corrections across 6 files (some bundled into single Edit operations). Exact changes are enumerated per file below.

A verification grep after application surfaced 4 additional "L-001 through L-011" references (EXPLORATION_CHARTER.md × 3, BACKLOG.md × 1 cross-references section). All 4 updated to "L-001 through L-016" in the same pass.

Corrections flagged but NOT applied (11 total):
- 4 in `MANIFESTO.md` (lines 28, 41, 42, 62): Romeo-verified canonical paragraphs. Numerical updates to the lab's foundational "what's actually working" table should go through Romeo.
- 1 in `LEARNINGS.md:499` (L-011 comparison table): Romeo-verified L-entry. Replacing the 88.9% number in a published comparison is substantive; Romeo should sign off.
- 1 in `LEARNINGS.md:693` (L-012 data-advantage table): a "retired" annotation would edit a Romeo-verified L-entry body.
- 1 in `market-gist/automation/SCRAPE_EXPANSION_2026-04-12.md:16`: dated historical memo, session-log-class.
- 2 session logs with historical framing (SESSION_LOG_2026-04-12 and 2026-04-13): session logs record state at the time; edits would rewrite history. Not applied.
- 1 universe v2 sector-count inconsistency: session log 2026-04-19 reports `COMMERCIAL_BANK:17` but `universe_v2_candidate.csv` contains 16. CSV is out of scope; session log is historical; flag only.
- 1 `BACKLOG.md` section 3 (ranked side projects): uses older "25+ resolved cases" framing throughout. Text is consistent with v3 Gate 1 but predates Gate 2. Adding cross-reference in section header covers this; deep rewrite not warranted.

---

## Flagged items — for Romeo to decide

1. **MANIFESTO.md numerical refresh.** The "What's actually working" table (lines 41-47) and the "We are betting that" paragraph (line 28) both cite pre-L-012-addendum numbers. Recommended replacement preserves the honest-assessment character but updates numbers and adds "not statistically significant at current N" framing. Requires Romeo sign-off because the MANIFESTO is the lab's canonical statement.

2. **LEARNINGS.md L-011 table row.** The mechanical-vs-LLM comparison cites 8/9 (88.9%) in a table Romeo verified. Post-addendum, the persistence row should read 8/11 (72.7%). The CONCLUSION of L-011 (mechanical > LLM) does not change, but the cited number is stale.

3. **LEARNINGS.md L-012 data-advantage table (line 693).** Contains "Our persistence signal claims | 88.9%" as part of a gap analysis. Either add "(retired headline)" annotation or leave as historical context within L-012 itself.

4. **Universe v2 sector count** — `SESSION_LOG_2026-04-19.md` morning section reports 17 commercial banks. `universe_v2_candidate.csv` (out-of-scope) contains 16. Out-of-scope; flag for check.

5. **Historical memos** (SCRAPE_EXPANSION_2026-04-12.md, session logs 2026-04-12 and 2026-04-13) contain 88.9%-era framing. Session-log discipline says don't rewrite history; but these predate the retirement. Romeo's call whether to annotate with "(retired headline)" banners.

---

## Gap flagged for future research (NOT applied)

The `effective_n_analysis_2026-04-19.md` memo's three-tier independence framework (market-wide / sector-pooled / within-trigger) is now the canonical effective-N language. Older docs (e.g., `BACKLOG.md` Section 3 side-project descriptions referring to "effective independent episodes ≥5") use the older single-tier framing. No edit applied — the old usage is still technically accurate for stock-specific signals, it's just not cross-referenced to the new framework. Romeo may want a forward pass to add the cross-reference across older docs.

---

```
SELF-AUDIT:
- Metadata checked: yes — v1 of audit doc, dated 2026-04-19, scope statement explicit, out-of-scope files enumerated
- Scope checked: yes — no edits to INTERPRETATION_GATE.md / effective_n_analysis / universe CSVs / L001_V2 plan / any code; session logs and MANIFESTO left intact per rule "don't apply substantive changes without Romeo"
- Paths checked: yes — all cited file:line references verified via grep before inclusion; no invented paths
- Data gates checked: yes — no signal computation, no outcome reinterpretation, no new claims added; every applied edit is a wording tighten or number refresh citing canonical source (L-012 addendum, INTERPRETATION_GATE v3, or existing L-entries)
- Evidence label checked: yes — every application weakens a claim toward "suggests/historical/in-sample", not the reverse
- Any known uncertainty: the precise current resolved-case count (used for BACKLOG, CURRENT_STATE_MEMO, decay tracker) is sourced from the 2026-04-18 scorecard JSON (`latest__shadow_batch_scorecard_v1.json`) showing `persistence_caution_only: resolved_rows=11`, total resolved=20, total rows=61. If a fresh daily run has produced new resolutions since, these numbers drift again.
- Do you need Romeo review: yes — for the 11 flagged items above, especially the 4 MANIFESTO numerical refreshes and the 2 LEARNINGS edits. Applied items (12) are all wording tightens without substantive claim changes and per audit rules (weakest-accurate-label, retired-framing retirement) are authorized.
```
