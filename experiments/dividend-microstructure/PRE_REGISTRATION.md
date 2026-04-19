# Pre-Registration — Dividend Microstructure H1 (Revision 3)

> Written 2026-04-13 BEFORE any code runs.
> Revision 1: initial draft by Juliet.
> Revision 2: 2026-04-17, integrated Romeo's first adversarial review (all blocking items + 5 review items + additional issues).
> **Revision 3: 2026-04-18, integrates Romeo's second adversarial review: bootstrap p-value sign corrected, cohort event-type scope clarified, baseline-fragility quantitative thresholds added, CONTRACT.md and README.md staleness fixed. Self-catches: block-bootstrap sample-size wording tightened.**
> Changes after this point require Romeo review and a documented reason.
> Required by the sandbox protocol and the lab doctrine ("no post-hoc parameter choice").

---

## Event Anchor Definition (T_ex) — Revised per Romeo Blocking Item 1

**T_ex is defined as:** the first NEPSE trading session on which the stock trades **without entitlement** to the announced cash dividend.

Operationally:

1. Let `book_closure_start` = the first calendar date of the book-closure period as published on ShareSansar's corporate-action feed for the specific dividend event.
2. If `book_closure_start` is a NEPSE trading day (per `nepse_trading_calendar.py`), then **T_ex = book_closure_start**.
3. If `book_closure_start` falls on a non-trading day (weekend, public holiday, NEPSE closure), then **T_ex = next trading session after book_closure_start**.
4. If the NEPSE trading regime changed inside the event window (e.g. April 10, 2026 Sun-Thu → Mon-Fri transition), use the regime-aware calendar helper for all offset arithmetic. Do not convert to calendar-day offsets.
5. Document the book_closure_start value AND the computed T_ex value for every event. Any discrepancy (i.e. T_ex ≠ book_closure_start) must be logged in the event table.

This replaces the earlier "first official book-closure date" language which conflated the corporate-calendar entry with the price-tape reality.

---

## Primary Hypothesis (H1) — Revised per Romeo Blocking Item 5

**Statement:**

For the sample of NEPSE-listed commercial bank and hydropower stocks that announce a cash dividend, the average baseline-adjusted excess return in the trading-day window **[T_ex + 1, T_ex + 5]** is statistically negative under **date-cluster block-bootstrap inference**, with directionally negative hit rate ≥ 60% and mean excess return ≤ −1.0%.

Wording note: if the historical test passes this threshold, the finding is "**H1 historically passes the pre-registered test.**" It is **not** confirmed as a tradable signal until it also accumulates forward evidence (N ≥ 25 post-pre-registration cases) and passes the 6-class audit. Historical pass = hypothesis survives; promotion requires separate forward evidence.

- "Baseline-adjusted" = event return minus the per-symbol trailing 120-day rolling mean for the same window type (post_1_5), with a minimum of 30 baseline observations. L-001 / L-003 convention.
- "Trading-day window" = offsets counted in actual NEPSE trading sessions per `nepse_trading_calendar.py`. Not calendar days.
- "Commercial banks and hydropower" = sectors per the existing L-001 symbol mapping. Not expanded.

---

## Cohort Split — Revised per Romeo Blocking Item 4 + Methodology Clarification

The event universe is split into **two cohorts** BEFORE any test runs. Each cohort has its own pre-registered role. Do not merge them post-hoc.

### Event-type scope for the cohort split

The split depends specifically on whether an **L-001 book-closure notice event for the SAME dividend cycle** falls within the event window. Exact definitions:

- **"L-001 book-closure notice event"** = the specific L-001 event type labeled as book-closure announcement in the L-001 event-family column. This is the announcement that informs the market that a book-closure will occur on a stated future date for a specific cash-dividend cycle.
- **"Same dividend cycle"** = the L-001 notice and the dividend event share the same announced-dividend identifier (symbol + announced dividend % + approximate AGM cycle). In practice: the notice whose `book_closure_announced_date` matches the T_ex of the dividend event being tested.

Other L-001 event types (AGM notices, rights notices, bonus notices, earnings releases) are **not** used to split cohorts. They are handled separately:

- Same-symbol AGM notice, rights notice, bonus notice, earnings release, or another dividend cycle in `[T_ex - 10, T_ex + 10]` → **HARD DROP** (already covered in "Sample Definition → Hard drops" below).
- Market-wide events (NRB, SEBON, political) → **SENSITIVITY FLAG**, not cohort split.

This distinction matters: the cohort split is specifically about the one event type (book-closure notice) that could be measuring the same underlying effect as T_ex. Other corporate-action noise is removed before the split.

### Cohort A — "Pure date-led"

Events where **no L-001 book-closure notice event for the same dividend cycle** falls within `[T_ex - 10, T_ex + 10]`.

In practice this means the book-closure notice was published MORE than 10 trading days before T_ex (which should be the typical case given Nepal's Companies Act and SEBON disclosure timing requirements, typically 15-21 days advance notice).

**Role in H1:** this is the **primary cohort** for the independence claim. H1 pass/fail is decided on Cohort A alone.

### Cohort B — "Notice-overlap"

Events where an L-001 book-closure notice event **for the same dividend cycle** falls within `[T_ex - 10, T_ex + 10]`.

This happens when the notice-to-book-closure gap is unusually compressed (< 10 trading days).

**Role in H1:** attribution evidence. Report Cohort B's own hit rate and mean excess return. Compare to Cohort A and to the full L-001 notice-anchored result. This tells us what share of the existing L-001 drift is actually a date-anchored effect seen through the notice lens.

**Cohort B cannot pass H1 on its own.** If Cohort A fails H1 but Cohort B looks strong, that is evidence that L-001's original signal was the date drift, not the notice itself — interesting but not a new signal.

---

## Sample Definition — Revised per Romeo Blocking Items 3 and 4 + Additional Issue 2

**Included:**
- Cash dividend events only (interim + final **combined** for the primary test)
- Sectors: commercial banks + hydropower only. No insurance / microfinance / finance / other.
- Event dates between 2021-01-01 and the latest T_ex with a complete [T_ex + 10] forward window in the price archive.

**Diagnostic tags (tracked but not used to rescue H1):**
- interim vs final dividend
- sector (bank vs hydro)
- dividend yield tercile
- size bucket

These tags are reported alongside results but cannot split the primary test. If H1 fails overall, no tag-based subset rescues it.

**Hard drops (all must occur BEFORE cohort split):**
- Bonus shares (different mechanism; dilutive, no cash payment)
- Rights issues (confounded with capital raise)
- Stock splits
- **Same-symbol** corporate-action overlaps in `[T_ex - 10, T_ex + 10]`: AGM result publication, rights record date, bonus record date, earnings release, other dividend events on the same symbol
- Dividend events where announcer has < 30 prior trading days in the archive

**Market-wide events treated as sensitivity tests, not hard drops:**
- NRB monetary policy events, SEBON major circulars, nationally disruptive political events: flag events whose T_ex falls within 5 trading days of such market-wide events. Run a sensitivity analysis excluding them. Report both versions.

This replaces the earlier "drop any overlap" rule which would have discarded useful data and conflated stock-specific and market-wide confounds.

---

## Statistical Inference — Revised per Romeo Blocking Item 2

### Primary significance gate — date-cluster block-bootstrap

Implementation:
1. Identify unique T_ex calendar dates in Cohort A. Let `N_dates` be the count.
2. Draw `N_dates` samples **with replacement** from the set of unique T_ex dates. This is the bootstrap date-cluster resample. (Duplicates are expected and correct — they represent uncertainty about which dates dominate.)
3. For each drawn date, include ALL Cohort A events with that T_ex.
4. Recompute mean excess return and hit rate for the replicate.
5. Repeat for **10,000 iterations**.
6. Report:
   - 2.5th and 97.5th percentile of the bootstrap distribution of the mean excess return (95% CI)
   - **One-sided bootstrap p-value for H1 (mean < 0):** `p = share of bootstrap replicates with mean excess return >= 0` — i.e., the fraction of replicates under which the observed data would be consistent with a non-negative true mean.

**Decision rule (directionally negative H1):**
- The 97.5th percentile of the bootstrapped mean excess return must be **< 0** for the test to pass. Equivalently, the 95% CI excludes zero on the negative side.
- The one-sided bootstrap p-value (share of replicates with mean **≥ 0**) must be **≤ 0.025**.

Sanity check: these two conditions are logically equivalent for a correctly-computed bootstrap — if the 97.5th percentile of the replicate distribution is below zero, then by construction < 2.5% of replicates are ≥ 0. Both are reported to make the decision rule legible and double-check the implementation.

### Descriptive only — plain t-statistic

The plain one-sample t-statistic is reported for reference (to permit comparison with prior L-001 work), but it is **not the decision statistic**. Text must label it "descriptive only, not decision-grade because rows cluster on event dates."

---

## Windows — Revised per Romeo Review Item 1

### Primary (pre-registered for H1 decision)
- `post_1_5`: trading-day window `[T_ex + 1, T_ex + 5]`

### Diagnostic — reported alongside, non-promotional

- `ex_day`: `[T_ex, T_ex]` — the immediate price drop itself. May be the whole effect.
- `ex_day_plus_one`: `[T_ex, T_ex + 1]` — captures any one-day continuation.
- `pre_-5_-1`: `[T_ex - 5, T_ex - 1]` — pre-ex run-up check.
- `post_1_10`: `[T_ex + 1, T_ex + 10]` — slower-drift check.
- `post_6_10`: `[T_ex + 6, T_ex + 10]` — late-window isolation.

Any diagnostic can pass the visual pattern expected from Pakistan / Blau-Fuller-Van Ness without H1 passing. Diagnostic success does not promote H1. If the diagnostic-window pattern looks strong but primary fails, the lane is still killed.

---

## Success Criterion (Pre-Registered) — Revised per Romeo Review Items 2 and 5

H1 **historically passes** the pre-registered test if **all three** hold simultaneously on **Cohort A**:

1. **Economic magnitude:** mean baseline-adjusted excess return in post_1_5 is **≤ −1.0%**.
2. **Directional hit rate:** directionally negative hit rate is **≥ 60%**.
3. **Cluster-robust significance:** the 95% block-bootstrap confidence interval for mean excess return excludes zero on the negative side. Equivalently, one-sided bootstrap p-value (share of replicates with mean ≥ 0) ≤ 0.025.

All three required. Two-out-of-three is not a pass. "Almost significant" is not a pass.

---

## Failure Criterion (Pre-Registered) — Revised per Romeo Review Item 5

The lane is **killed** — not rescued, not re-sliced, not re-windowed, not cohort-merged — if any of the following:

1. Cohort A hit rate < 55%, OR
2. Cohort A mean excess return > −0.5% (insufficient economic magnitude), OR
3. Block-bootstrap 95% CI for Cohort A mean excess return includes zero, OR
4. Gate 1 fails before the test runs (sample inadequacy).

If "failure" fires, the only permitted follow-up is: document the result honestly in `results/H1_<date>.md`, flag to Romeo, close the lane. No escape hatches.

---

## Intermediate Zone — Rewritten per Romeo Review Item 5

If Cohort A results fall into the region:
- Hit rate 55-60%, OR
- Mean excess return between −0.5% and −1.0%, OR
- Bootstrap CI touches but does not strictly exclude zero on the negative side

The result is labeled: **"Failed H1. At most directionally consistent with L-001. Not actionable. Not promoted."**

No phrase like "supportive," "encouraging," or "borderline significant" appears in the writeup. The result is not built on. The lane is closed for this hypothesis; the lab's forward-evidence budget moves to other Tier 1 signals.

The only exception: if Cohort B separately shows very strong effects, this is documented as "evidence that L-001 notice drift is partly a date-anchored effect" — this is L-001 attribution information, not a new signal, and the lane is still closed for H1 promotion purposes.

---

## Gate 1 — Sample Adequacy — Revised per Romeo Review Item 4

Before the H1 test runs, these must all hold on **Cohort A**:

1. **Total N ≥ 80 events** (post-drops, Cohort A only).
2. **Unique T_ex calendar dates ≥ 30** in Cohort A.
3. **Sample concentration:** the top-3 T_ex dates must account for **≤ 30%** of total Cohort A events. (Prevents a repeat of the L-012 two-day-cluster trap.)
4. **Notice→T_ex gap distribution** is documented: median, p25, p75, and share of events within 5 / 10 / 15 days of their nearest L-001 notice. This is a descriptive requirement; it does not by itself trigger a pass/fail but must be reported so the cohort split is defensible.
5. **Cohort B N ≥ 20**. If Cohort B is too thin, attribution evidence is inconclusive. This is not a hard fail but must be flagged.

If any of (1), (2), (3) fails, Gate 1 fails. H1 does not run.

---

## Gate 2 — Independence Documentation (pre-Gate-1 complement)

After the cohort split, compute and report:

- Overlap rate = `Cohort_B_count / total_post_drops_count`
- Share of dividend events where the nearest L-001 notice falls within 5 days of T_ex
- Share within 10 days

If overlap rate ≥ 50%, add a banner to the H1 results page: *"High overlap with L-001 notices: independence claim for this signal is structurally weak. Treat Cohort A result as marginal at best."*

This is not a kill condition; it is a disclosure requirement.

---

## Sample Concentration Reporting — L-012 Discipline

Every H1 result file must include:

- Total N, unique T_ex date count
- Distribution of events by T_ex calendar date
- Share of events in top-1, top-3, top-5 dates
- Gini coefficient over event dates
- Sector breakdown (bank vs hydro)

If the top-3 concentration exceeds 30% but Gate 1 was passed by some marginal arithmetic quirk, still label the result "clustered-sample, interpret with caution."

---

## Baseline Fragility Check (Bear-Market Contamination)

95% of 2021-2026 NEPSE data is below SMA-200 (L-001). Report the test's sensitivity:

- **Primary:** 120-day trailing per-symbol baseline (pre-registered).
- **Sensitivity 1:** matched-sector market drift subtracted in addition to per-symbol baseline.
- **Sensitivity 2:** restricted to events where SMA-200 regime was "above" at T_ex - 1 (likely small N; report descriptively).

**Quantitative "baseline-fragile" threshold:** label the result "baseline-fragile, do not promote" if ANY of the following hold when comparing primary vs Sensitivity 1:

- Opposite signs (primary negative but Sensitivity 1 positive, or vice versa)
- Magnitude collapse: |Sensitivity 1 mean| ≤ 40% of |primary mean|
- Sensitivity 1 fails the pre-registered success criteria (hit rate < 60% OR mean > -1.0% OR CI includes zero)

The primary pre-registered decision is made on the primary baseline. Sensitivities are diagnostic only, never used to rescue. But if primary passes and Sensitivity 1 also passes independently, confidence increases and can be noted in the writeup.

---

## Multiple-Testing Discipline

Only Cohort A on post_1_5 is the pre-registered primary test. Everything else — Cohort B, diagnostic windows, sector slices, yield terciles, sensitivity versions — is exploratory and labeled as such.

No p-hacking. No "but banks-only from 2024 passed." No "the broader window at [T_ex + 1, T_ex + 10] was significant." If the primary test fails, the lane fails.

---

## Historical Evidence ≠ Forward Evidence (Romeo Blocking Item 5 — restated)

Even if H1 historically passes all three success criteria on Cohort A, the signal is **not promoted** to canon until:

1. It accumulates N ≥ 25 forward-resolved cases (post-pre-registration events only).
2. The forward result also satisfies the pre-registered success criteria within the block-bootstrap framework.
3. The 6-class audit is passed.
4. Romeo re-reviews the audit output.
5. Juliet writes a L-xxx learning; Romeo verifies wording.
6. Integration into LEARNINGS.md at a clean gate.

Historical pass = hypothesis survives the first test. Forward pass = hypothesis earns promotion. Two separate gates.

---

## Romeo Review Items — Final Status

1. **Primary window** (review item 1): resolved per this revision. [T_ex + 1, T_ex + 5] with T_ex properly defined; [T_ex, T_ex + 1] added as diagnostic.
2. **Success threshold** (review item 2): revised to require magnitude (−1.0%) AND hit rate (≥60%) AND block-bootstrap CI excluding zero.
3. **Overlap rule** (review item 3): revised to cohort split. Same-symbol hard drops; L-001 notice overlaps become Cohort B; market-wide events sensitivity-tested.
4. **Gate 1 minimums** (review item 4): revised to N ≥ 80, unique dates ≥ 30, top-3 concentration ≤ 30%.
5. **Intermediate zone** (review item 5): rewritten as "Failed H1, at most directionally consistent with L-001, not actionable, not promoted."

All blocking items integrated. All additional issues addressed (insurance/microfinance not added; interim vs final combined with tags, no split-rescue). CONTRACT.md and README.md updated in companion edits.

---

## Commit Discipline

This revision 3 must be committed to git before any .py file in this sandbox is executed. Commit message:

```
dividend-microstructure: PRE_REGISTRATION revision 3 after Romeo's second review

- Corrected bootstrap one-sided p-value sign (share of replicates >= 0, not < 0)
- Clarified cohort event-type scope: split uses L-001 book-closure notice
  for SAME dividend cycle only; other L-001 event types handled by hard drops
- Tightened baseline-fragility threshold with three quantitative conditions
- Tightened block-bootstrap sample-size wording
- Synced CONTRACT.md and README.md to match revision 3 (stale Gate 1, stale
  decision rule, stale status/next-step lines fixed)

Prior revisions preserved for audit trail:
- Revision 2 introduced: T_ex definition, block-bootstrap framework, Cohort
  A/B split, Gate 1 tightening, economic-magnitude criterion, historical-vs-
  forward evidence separation.
- Revision 1 was the initial draft.
```

Future changes to this file require Romeo review and a new commit with explicit justification.

---

## Sign-Off

- **Juliet (author, revision 1):** 2026-04-13
- **Romeo (first blocking review):** 2026-04-17 — blocking items returned, revision 2 requested.
- **Juliet (author, revision 2):** 2026-04-17 — all first-round blocking items addressed.
- **Romeo (second blocking review):** 2026-04-17 — additional issues returned (bootstrap p-value sign, stale CONTRACT.md/README.md), revision 3 requested.
- **Juliet (author, revision 3):** 2026-04-18 — this document. All second-round blocking items addressed + self-catches on sample-size wording and baseline-fragility thresholds.
- **Romeo (sign-off on revision 3):** 2026-04-18 — signed off with recommendation to patch metadata labels (this patch addresses that; Item 3 of the 2026-04-18 Romeo review).
- **Ishwor (lab operator):** validated Romeo's 2026-04-18 review independently; agreed on substance with small framing nuances. Approved.
- **Benvolio (optional exploration-team review):** pending (non-blocking).

Code may now run in this sandbox in the sequence defined in `README.md` → `CONTRACT.md` → Gate 1 → Gate 3. Do not run `run_h1.py` until Gate 1 passes.
