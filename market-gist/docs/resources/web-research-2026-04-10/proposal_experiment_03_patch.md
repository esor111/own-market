# Proposal: Experiment 03 NRB Event Patch (Deferred)

> **Status: PROPOSAL ONLY. NOT YET PATCHED.**
> Under L-011 patience mode, this should not be applied before persistence forward
> evidence batch-scores. This document captures the prep work so the eventual patch
> is fast and doesn't have to re-derive the dedup logic.

## Why this exists

The NRB margin lending research (thread 6) surfaced 8 candidate event dates for `experiments/03-nrb-rate-events/data/policy_events.csv`. The original synthesis claimed "6 missing events" and Romeo correctly flagged that the count was inconsistent and that the dedup against existing rows had not been done.

This document is the corrected, dedup'd patch list for the eventual experiment 03 extension.

## Existing rows in policy_events.csv (relevant slice)

From a read of the current `experiments/03-nrb-rate-events/data/policy_events.csv` (as of 2026-04-10):

| Existing date | Event type | Description |
|---|---|---|
| 2024-07-26 | monetary_policy_announcement, bank_rate_change, policy_rate_change | Monetary Policy 2081-82 + rate changes (easing) |
| 2025-07-11 | monetary_policy_announcement | Monetary Policy 2082-83 (full text release) |
| 2025-07-17 | bank_rate_change, policy_rate_change | Rate changes operational under new monetary policy (easing) |
| 2025-12-01 | monetary_policy_q1_review | Monetary Policy 2082-83 1st Quarter Review |
| 2025-12-02 | bank_rate_change, policy_rate_change | Rate changes operational under Q1 review (easing) |
| 2026-02-24 | monetary_policy_midterm_review | Midterm review |

## The 8 candidate events from thread 6, evaluated

| # | Candidate date | Candidate event | Verdict | Reason |
|---|---|---|---|---|
| 1 | 2025-05-28 | Risk weight on share-backed loans 125% → 100%; CRR daily maintenance to 90% | **NEW — KEEP** | Not in current table. Pre-monetary-policy directive change. Real regime shift. |
| 2 | 2025-07-11 | Monetary Policy FY 2082/83 release | **DUPLICATE** | Already in current table as `monetary_policy_announcement`. Skip. |
| 3 | 2025-07-17 | Unified directive Rs 250M margin cap operational | **DUPLICATE** | Already in current table as bank/policy rate change rows on the same date. The Rs 250M margin cap is the operational form of the same monetary policy. Skip OR enrich existing row with `margin_loan_change` event_type. |
| 4 | 2025-10-15 | Single-customer margin loan limit lifted | **NEW — KEEP** | Not in current table. Discrete directive change between Q1 review and midterm review. Real regime shift. |
| 5 | 2026-02-10 | SEBON MTF directive operational | **SKIP** | SEBON, not NRB. Experiment is named "NRB Rate Events." Belongs in a separate broker-margin experiment if at all. |
| 6 | 2026-03-26 | NEPSE Margin Trading Procedure 2082 passed | **SKIP** | NEPSE, not NRB. Same reason as #5. |
| 7 | 2026-04-01 | Finance Minister speech → NEPSE -2.62% | **NEW — KEEP (collapsed)** | Not in current table. Negative shock useful for asymmetry testing. Collapse with #8 as a single regime event. |
| 8 | 2026-04-05 | Finance Minister speech → NEPSE -3.79% | **COLLAPSE INTO #7** | Same speaker, same theme, 4 days apart. Treat as a single April 2026 negative-policy regime event, not two separate events. Use 2026-04-01 as anchor. |

## Final patch list — 3 truly new events

```csv
event_date,event_type,event_label,direction,detail,source
2025-05-28,nrb_directive_change,NRB risk weight on share-backed loans cut 125% to 100% + CRR daily maintenance to 90%,easing,New Governor Bishwanath Paudel,https://www.sharesansar.com/newsdetail/bfis-now-required-to-maintain-90-of-crr-daily-with-nepal-rastra-bank-risk-weight-on-share-backed-loans-revised-to-100-2025-05-28
2025-10-15,nrb_directive_change,Single-customer margin loan limit lifted; BFIs can mobilize 40% of primary capital via margin lending,easing,Discrete directive between Q1 and midterm review,https://eng.bajarkochirfar.com/2025/10/15/nrb-lifts-single-customer-margin-loan-limit/
2026-04-01,policy_speech_shock,Finance Minister capital-market policy speech caused NEPSE -2.62%; -3.79% on follow-up speech 04-05,tightening,Negative regime event collapsing 04-01 and 04-05 together,https://kathmandupost.com/money/2026/04/01/nepse-plunges-74-73-points-as-all-sub-indices-decline
```

That's the entire patch. **3 rows, not 6, not 8.**

## Optional 4th event (split decision)

There is a case for adding **2025-07-11** as a separate `monetary_policy_announcement_date` row even though it's the same monetary policy that the existing 2025-07-17 row covers. The argument: announcement date ≠ operational date, and event studies often want to test both. The argument against: it's the same regime change, already counted once, and the existing run should not double-count.

**Recommended decision:** do NOT add it as a separate row. The existing 2025-07-17 row is sufficient. If we ever want to test announcement-vs-operational asymmetry, do that as a separate experiment with explicit dual-date columns, not by inflating the event count.

## When to apply the patch

**Trigger:** persistence shadow batch scores at 25+ resolved cases AND we want to extend experiment 03 for any reason.

**Until then:** do not apply. The patch list is captured here. The dedup work is done. The eventual run is ~30 minutes once we decide to pull the trigger.

## What re-running with the patch would test

The 3 new rows specifically test:

1. **2025-05-28** — does the NRB risk weight cut + CRR change show a measurable price reaction independent of the monetary policy that came 6 weeks later?
2. **2025-10-15** — does the single-customer margin loan lift show a measurable price reaction in the gap between Q1 and midterm reviews?
3. **2026-04-01** — does a NEGATIVE policy speech shock show asymmetric impact compared to easing announcements? (This is the most interesting one — all our existing events are easing.)

The third test is the most novel: **we have ZERO tightening events in the current sample.** Adding even one negative event lets us check whether the "anticipation then reversal" pattern from L-008 reverses sign for tightening events.

## What this would NOT test

- Whether SEBON MTF directives (broker-side margin trading) move prices — that requires a separate experiment scope
- Whether announcement vs operational date matters — needs a different experiment design
- Whether the impacts hold cross-sector — the existing experiment design already covers this

## Cross-references

- Source thread: `06_nrb_margin_lending_impact_and_retail_sentiment.md`
- Existing experiment: `experiments/03-nrb-rate-events/`
- Existing event table: `experiments/03-nrb-rate-events/data/policy_events.csv`
- L-008 (the existing NRB rate events learning): `experiments/LEARNINGS.md`
- L-011 (patience mode rationale): `experiments/LEARNINGS.md`
