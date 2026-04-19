# w7 Seller-Persistence Replay — PRE_REGISTRATION (Revision 4)

**Revision history**
- r1: 2026-04-19 initial draft (superseded)
- r2: 2026-04-19 Romeo fixes applied — rule scoped to w7 sub-rule only; coverage failure recorded; forward-price calendar corrected; backfill-first sequence added (superseded)
- r3: 2026-04-19 Romeo r2 re-review patch — symbol scope is all-or-nothing; no subset hit rate; no subset recommendation; per-symbol diagnostic requires separate pre-registration (superseded)
- r4: 2026-04-19 Romeo w7-audit verdict applied — rule definition tightened to production-code semantics (top-weighted broker, not any-broker); sparse-window behavior explicitly accepted with reporting requirement; replay_cases.csv fields expanded; fragility labeling rule added

**Status:** Locked once r4 is committed. No further parameter changes without a new revision.
**Evidence label:** `recent_w7_seller_persistence_replay`
**Authorization:** Romeo verdict 2026-04-19, revisions required before run.

---

## Purpose

Replay the w7 seller-persistence sub-rule over a recent 6-month window as an audit / calibration exercise. The goal is to see what the sub-rule would have said in-sample, what patterns emerge in its firings, and whether the forward N=25 result is consistent with a broader historical readback of this one sub-rule.

**This replay is NOT out-of-sample evidence.** The window overlaps the rule's development period. Results are diagnostic only. Under no condition does this replay promote the signal. Forward N=25 remains the sole promotion gate.

---

## Rule — w7 Seller-Persistence Sub-Rule ONLY

This replay does not test the full frozen persistence policy. The full policy also includes the `w10` CAUTION rule, which is NOT evaluated here.

**Sub-rule definition** (locked, matches production code `market-gist/automation/broker_persistence_tracker.py`):

- **Metric:** `w7_seller_persistence_score >= 1.0`
- **Production-code semantics:** the *top-weighted* seller broker — selected by `max(frac × avg_share)` across the prior available ledger sessions, where a broker's `frac` = distinct prior sessions that broker was in top-10 sellers ÷ `n_days` — must have `frac >= 1.0`. This is NOT an "any broker with frac=1.0" rule. If a more-weighted broker with `frac<1.0` dominates a `frac=1.0` broker by share, the CAUTION does not fire.
- **Window semantics:** prior window uses available broker-ledger sessions. If fewer than 7 prior sessions exist but at least 3 exist, production code computes the score against that smaller `n_days`. The replay MUST report the `prior_days_used` distribution (see Reporting Requirements).
- **Anchor-day:** seller alignment is NOT required. The score is computed from prior sessions only. `today_seller_is_persistent` is a separate flag and is NOT wired into the CAUTION trigger.
- **Side:** seller side only.
- **Stricter variants NOT tested:** "any broker with frac=1.0" and "n_days >= 6 required" are future challenger rules. They are out of scope for this replay. A challenger-rule replay would require its own pre-registration.

Because only this sub-rule is tested, the replay is named **w7 seller-persistence replay**, not "frozen persistence policy replay." Any result framing must preserve this scope and these semantics.

---

## Locked Parameters

| Parameter | Value |
|---|---|
| Sub-rule tested | w7 seller-persistence only (`w7_seller_persistence_score >= 1.0`) |
| Symbols | NABIL, EBL, SANIMA (active_shadow tier only) |
| Window | 2025-10-19 to 2026-04-18 |
| Last fire-eligible trading day in window | 2026-04-17 (Friday; 2026-04-18 is Saturday) |
| Policy version | `v1_frozen_2026-04-05`, w7 sub-rule only |
| Outcome measurement | 10 trading-day forward return |
| Forward-data required through | **2026-05-01** (10th Mon-Fri trading day after 2026-04-17) |
| Evidence label | `recent_w7_seller_persistence_replay` |

Any deviation aborts the replay. No iteration. No window tweaks. No symbol expansion. No rule modifications. No sub-rule substitution.

---

## Pre-Run Coverage State (as of 2026-04-19, per Romeo)

| Symbol | Broker-flow coverage in window | Pass 80% gate? |
|---|---:|---|
| NABIL | 27.5% | FAIL |
| EBL | 49.6% | FAIL |
| SANIMA | 41.2% | FAIL |

All three symbols fail the 80% coverage gate. **Scoring cannot run until broker-flow coverage reaches ≥80% per symbol via backfill.**

---

## Required Sequence

The replay proceeds through these steps in order. Each step gate-guards the next.

**Step 1 — Backfill broker-flow data**
- Target: ≥80% trading-day broker-flow coverage for NABIL, EBL, SANIMA across 2025-10-19 to 2026-04-18
- Source: ShareSansar or MeroLagani historical floorsheet (date-parameterized)
- Backfill scraper is a one-time historical scrape for these 3 symbols. It does NOT modify `scrape_symbol_list.json` or the daily scrape pipeline.
- Backfill work requires its own Romeo authorization before code is written. This pre-registration does not authorize scraper construction.

**Step 2 — Post-backfill coverage report (all-or-nothing)**
- Confirm per-symbol coverage ≥80% for **all three** symbols (NABIL AND EBL AND SANIMA)
- If any single symbol remains below 80% after backfill, the replay aborts with coverage report only
- No subset hit rate is produced
- No subset recommendation is produced
- Any per-symbol diagnostic (e.g., running the replay on just the symbols that passed) requires a separate pre-registration, not a relaxation of this one

**Step 3 — Verify w7 sub-rule implementation**
- Confirm the current code implements `w7_seller_persistence_score >= 1.0` exactly as defined above: same broker in top-10 sellers on all prior 7 available ledger sessions, no anchor-day alignment requirement.
- If the current code uses a different definition, the replay aborts and the discrepancy is reported to Romeo. No silent reconciliation.

**Step 4 — Run the replay once**
- Fires are detected for every trading day in the window where the sub-rule condition is met
- Fires in the last 10 trading days of the window (roughly 2026-04-04 onward for full Mon-Fri coverage) are marked **pending** until forward price data through 2026-05-01 is available
- Verdict pass waits until 2026-05-01 price data exists, OR the replay reports "partial" results with pending cases flagged

**Step 5 — Publish results**
- Deliverables listed below

No step skips. No re-runs with adjusted parameters.

---

## Interpretation Bands (locked before seeing results)

"Resolved" = fire with 10d forward price data available.
"Hit" = resolved case where forward 10-day return is strictly negative.

| Hit rate on resolved | Clustering | Verdict |
|---|---|---|
| ≥ 70% | Low (no anchor date or symbol >30% share) | Strong but in-sample; NO promotion |
| ≥ 70% | High (single anchor date or symbol >30% share) | Fragile; flag confound |
| 55–65% | any | Weak / moderate but plausible |
| 50–55% | any | Weak, close to noise |
| < 50% | any | Warning sign — sub-rule may be overfit or wrong |
| N < 10 resolved | any | Inconclusive — report and stop |

Clustering diagnostic is dual: (a) top anchor-date share of total fires, (b) dominant-symbol share. Either >30% triggers the clustering-fragile flag.

**Sparse-window fragility override (added r4):** if more than **30% of fires** have `prior_days_used < 7`, the replay result is additionally labeled **fragile** regardless of hit rate or clustering. Fragile replays do not corroborate the forward signal without the sparse-window qualifier stated alongside any reference to the replay. A replay may be simultaneously "strong but in-sample" and "fragile (sparse windows)" — both labels must appear.

---

## What This Replay Does NOT Do

- Does NOT test the full frozen persistence policy (w10 CAUTION is out of scope)
- Does NOT replace the forward N=25 gate
- Does NOT promote the signal under any outcome
- Does NOT authorize universe v2 experiments
- Does NOT authorize rule modifications
- Does NOT claim out-of-sample validation
- Does NOT touch the forward-shadow scorecard or `persistence_shadow_reports/` directory
- Does NOT produce subset hit rates or subset recommendations if any symbol fails the coverage gate

---

## Deliverables

1. `experiments/persistence-recent-replay/PRE_REGISTRATION.md` — this file (revision 3)
2. `experiments/persistence-recent-replay/data/backfill_coverage_report.md` *(proposed output)* — produced after Step 2, before Step 3
3. `experiments/persistence-recent-replay/data/replay_cases.csv` *(proposed output)* — one row per fire with columns: `date`, `symbol`, `prior_days_used`, `top_seller_frac`, `top_seller_avg_share`, `top_seller_weighted`, signal snapshot fields, 10d forward return (or pending flag), hit flag
4. `experiments/persistence-recent-replay/data/replay_summary.json` *(proposed output)* — aggregate stats: N fired, N resolved, N pending, hit rate on resolved, clustering metrics, anchor-date histogram
5. `experiments/persistence-recent-replay/RESULTS.md` *(proposed output)* — beginner-friendly summary
6. `experiments/persistence-recent-replay/RECOMMENDATION.md` *(proposed output)* — one-paragraph verdict: `strengthens`, `weakens`, or `inconclusive`

---

## Abort Conditions

The replay aborts — producing only a coverage report, no hit-rate — if any of:

- **Any one** of the three symbols remains below 80% broker-flow coverage after backfill (all-or-nothing gate)
- The w7 sub-rule code differs from Romeo's spec and cannot be reconciled by inspection
- Forward price data does not reach 2026-05-01 at the time of the verdict pass (in which case the replay reports partial + pending, not aborted)

If aborted, no cherry-picking of surviving symbols or days. No subset reporting. Report the failure to Romeo and stop.

---

## Reporting Requirements

RESULTS.md must include:

1. What fired: count of fires per symbol, count of unique anchor dates
2. How many resolved, how many pending (reason per row), how many skipped
3. Hit rate on resolved cases
4. Clustering: top-3 anchor-date share, top-symbol share
5. Corporate-action overlap count if L-001 coverage exists for the window and these symbols
6. **Prior-sessions distribution:** count of fires that used `prior_days_used` = 3, 4, 5, 6, 7 (separate counts per bucket)
7. **Fragility label:** if >30% of fires used `prior_days_used < 7`, the result is labeled "fragile" and the sparse-window share is reported alongside every hit-rate claim in the memo
8. **Top-seller detail summary:** distribution of `top_seller_frac`, `top_seller_avg_share`, and `top_seller_weighted` values at fire time (so future review can tell whether fires were dominated by a single high-share broker or a diverse set)
9. A plain-language paragraph beginner-friendly
10. The locked-band verdict, with fragility qualifier attached if applicable

---

## Sign-Off

Revision 4 committed before any code runs or backfill work begins. Any deviation requires revision 5, not an amendment. The frozen v1 rule is not modified under any outcome of this replay. Backfill work uses the existing `market-gist/automation/backfill_merolagani_floorsheet.py` per the separate Backfill Authorization Request; no new scraper code is permitted unless schema-match fails and a new authorization is written.
