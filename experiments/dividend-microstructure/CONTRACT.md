# Experiment Contract: dividend-microstructure

## Purpose

Test whether NEPSE-listed banks and hydropower firms show a statistically negative excess return in the **[T_ex + 1, T_ex + 5]** window, where **T_ex** is defined as the first trading session on which the stock trades without entitlement to the announced cash dividend (see `PRE_REGISTRATION.md` for exact T_ex rules). Extends L-001 from book-closure **notices** (the event L-001 anchored on) to book-closure **dates** (the ex-date analog). See `RESEARCH_BRIEFING.md` for literature foundation and `PRE_REGISTRATION.md` for the pre-registered hypothesis.

---

## Inputs (read-only paths)

- `market-gist/data/corporate_actions/**` (L-001 event table — need to verify exact path before Step 1)
- `sharesansar_datascrape/data/<MM_DD_YYYY>.csv` (price CSVs)
- `market-gist/broker_flow_ledger/<SYMBOL>/<DATE>.json` (for H3 broker-flow layer, later)
- `experiments/shared/event_study.py` (framework)
- `experiments/shared/price_loader.py` (dedupe, baseline computation)
- `experiments/shared/stats.py` (hit rate, t-statistics)
- `market-gist/automation/nepse_trading_calendar.py` (trading-day arithmetic across schedule regimes)

Reads nothing outside Layers 1 and 2.

---

## Outputs (paths this experiment writes to)

- `experiments/dividend-microstructure/data/event_table.csv` (preprocessed events)
- `experiments/dividend-microstructure/data/overlap_analysis.json` (Gate 1 output)
- `experiments/dividend-microstructure/results/H1_<date>.json` (primary test)
- `experiments/dividend-microstructure/results/H1_<date>.md` (human-readable)
- `experiments/dividend-microstructure/results/diagnostic_<date>.json` (secondary windows, controls)
- `experiments/dividend-microstructure/alerts/<date>_<severity>.md` (if gates breached)

All outputs land inside this experiment's folder. Nothing else.

---

## Never Touches

- `market-gist/**` (production + shared, all read-only)
- `experiments/LEARNINGS.md`
- `experiments/BACKLOG.md`
- `experiments/INDEX.md`
- `experiments/MANIFESTO.md`
- Any other experiment's folder

---

## Kill Condition

Delete `experiments/dividend-microstructure/`. Nothing else breaks.

**What depends on this:** nothing yet. Results may eventually inform LEARNINGS.md via serial promotion, but only through Romeo review, not automatic integration.

---

## Runnable As

Planned runner commands (not yet built):

```
python experiments/dividend-microstructure/build_event_table.py   # Step 1
python experiments/dividend-microstructure/check_gate1.py          # Gate 1 decision
python experiments/dividend-microstructure/run_h1.py               # Step 3 (after pre-reg)
python experiments/dividend-microstructure/run_diagnostic.py       # Secondary windows
```

NOT invoked by the production daily routine. Manual invocation only.

---

## Forward Evidence Gate

See `PRE_REGISTRATION.md` (revision 2) for the authoritative gate definitions. Summary here must match — if this section drifts, the pre-registration wins.

**Gate 1 (sample adequacy, Cohort A only):** BEFORE any H1 test runs, this experiment must confirm:
- Total N ≥ **80** events (Cohort A only, post-hard-drops)
- Unique T_ex calendar dates ≥ **30**
- Top-3 T_ex date concentration ≤ **30%** of Cohort A events
- Notice→T_ex gap distribution documented (median, p25, p75, share within 5/10/15 days)
- Cohort B N ≥ **20** flagged (soft; attribution feasibility)

**If Gate 1 fails:** pause. Do not run H1. Either expand scraping or kill the lane.

**Gate 2 (independence documentation):** compute Cohort B overlap rate. If ≥ 50%, add "structurally weak independence" banner to H1 results. Not a kill condition; disclosure requirement.

**Gate 3 (H1 historical pass, Cohort A only, all three required):**
- Mean baseline-adjusted excess return in post_1_5 ≤ **−1.0%**
- Directionally negative hit rate ≥ **60%**
- 95% block-bootstrap CI for mean excludes zero on the negative side (one-sided bootstrap p-value `share of replicates with mean ≥ 0` ≤ **0.025**)

**H1 failure (ANY triggers kill of lane):** hit rate < 55% OR mean > −0.5% OR bootstrap CI includes zero OR Gate 1 failed.

**Gate 4 (forward evidence, for promotion):** N ≥ 25 forward-resolved cases post-pre-registration, passing the same criteria on forward data.

**Gate 5 (audit + Romeo review):** 6-class audit before any canon integration.

---

## Naming

All signal outputs from this experiment use the prefix `x-dividend-micro-`:
- `x-dividend-micro-NABIL-post-ex-alert` (hypothetical, not yet firing)
- `x-dividend-micro-EBL-signal`

---

## Output File Header

Every output markdown/JSON/CSV file begins with:

```
[EXPERIMENTAL SIGNAL] shadow only, not a trading decision.
Experiment: dividend-microstructure
Historical-test sample (Cohort A): N=<current> / minimum=80 for Gate 1
Forward evidence (post-pre-registration): N=<current> / required=25 for promotion
Layer: 3 (research)
```

Note: "historical-test sample" and "forward evidence" are distinct per Romeo's revision 2 blocking item 5. Historical N satisfies Gate 1 and enables the H1 test; forward N is a separate gate required for any promotion to canon.

---

## Romeo / Benvolio Verification Status

- **Designed by:** Juliet, 2026-04-13 / 2026-04-17
- **Research foundation:** general-purpose research agent, 2026-04-17. Citation corrections flagged (see RESEARCH_BRIEFING.md header).
- **Reviewed by Romeo (revision 1):** 2026-04-17 — blocking items returned, revision 2 requested.
- **Reviewed by Romeo (revision 2):** 2026-04-17 — additional bugs returned (bootstrap p-value sign, stale CONTRACT/README), revision 3 requested.
- **Revision 3 (this document):** 2026-04-17 by Juliet — all Romeo findings patched; cohort event-types clarified; self-catches applied (bootstrap sample wording, baseline-fragile quantitative threshold).
- **Reviewed by Romeo (revision 3):** pending — please confirm revision 3 before Step 1 code runs.
- **Reviewed by Benvolio:** pending (exploration-team reviews may be parallel; not blocking).
- **Promotion path status:** pre-evidence, pre-code. Research foundation laid. PRE_REGISTRATION revision 3 awaiting final sign-off.
