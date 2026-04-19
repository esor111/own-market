# Pre-Registration — Reversal Specialist H1 (Revision 4)

> Written 2026-04-18.
> Revision 1: initial draft by Juliet (2026-04-18 early afternoon).
> Revision 2: 2026-04-18 afternoon, integrated Romeo's first adversarial review (5 findings: trading-day window, Layer B data-driven filter, corp-action ex-date, return construction, circuit-limit).
> Revision 3: 2026-04-18 late afternoon, integrated Romeo's second adversarial review (2 measurement fixes: `h1_eligible` gate, active-symbol denominator).
> **Revision 4: 2026-04-18 evening, integrates Romeo's third adversarial review (4 small-but-required consistency fixes): (a) pre-reg's Layer B co-trigger wording updated from "30% of the 26 scrape-universe symbols" to match the code's active-symbol denominator; (b) stale "revision 1" text in check_gate1.py (docstring + markdown output) bumped to revision 4; (c) gate-drift diagnostic added to check_gate1.py showing rows that are `include_in_primary` but not `h1_eligible`, split by reason (no forward window / insufficient baseline); (d) baseline method aligned with L-003 / future H1 — `baseline_obs_count` now counts "last N prior trading observations" (capped at 120), not "trading rows within 120 calendar days." This is a small semantic change, but it guarantees Gate 1 and H1 use the same baseline universe.**
> Changes after this point require Romeo review and a documented reason.
> Locks the hypothesis, thresholds, and methodology in advance.
> Applies the lab's core discipline: pre-registered hypothesis, block-bootstrap inference, hard success/fail criteria, historical pass ≠ promotion.

---

## Mechanism (1 sentence)

In thin markets, single-day price moves beyond a liquidity-provision-cost threshold tend to mean-revert over short horizons because the marginal buyer/seller who moved the price is compensated for providing liquidity and the subsequent trading day(s) partially unwind the overshoot.

## Academic Anchors

- Lo & MacKinlay (1988) — variance ratio test for mean-reversion in stock prices.
- Jegadeesh (1990) — 1-month reversals in US equities.
- De Bondt & Thaler (1985) — overreaction hypothesis.
- Emerging-market extensions (Ho Chi Minh, NIFTY): loser portfolios outperform winner portfolios by 1.8-2.2% over 2-3 month horizons.
- Benvolio's earlier research pass validated: **reversion is stronger in small, illiquid, volatile stocks** — NEPSE's core structural profile.

---

## Primary Hypothesis (H1)

**Statement:**

For NEPSE-listed symbols in the current 26-symbol scrape universe, after a single trading session on which the stock's daily return is ≤ **−5.0%** (sharp-down trigger) and the trigger is not on a circuit-breaker-limit close, the baseline-adjusted excess return over the trading-day window **[T+1, T+5]** is statistically positive under block-bootstrap inference by trigger date.

Symmetric secondary hypothesis (H1b, tested as a secondary test — NOT gating H1):

After a single-session return ≥ **+5.0%** (sharp-up trigger), the baseline-adjusted excess return over **[T+1, T+5]** is statistically negative.

Only H1 (sharp-down reversal) is the primary test.

---

## Trigger Definition

**Sharp-down trigger = day t such that all hold:**

1. Daily return on day t = (close_t − close_{t-1}) / close_{t-1} ≤ **−5.0%**.
2. **Not at or near the NEPSE lower price limit.** NEPSE has a ±10% intraday circuit breaker (widened to ±15% from April 17, 2026 onwards — see research agent 2026-04-18 timeline). Operationally: daily return is between **−9.5% and −5.0%** (before April 17, 2026) or **−14.5% and −5.0%** (from April 17, 2026 onwards). Triggers with `|daily_return| > 9.5%` (pre-2026-04-17) or `> 14.5%` (post) are tagged `near_price_limit = True` and **hard-dropped** from primary analysis because they confound circuit-breaker mechanics with real reversal.
3. **Volume threshold:** volume on day t > 0 AND volume on day t ≥ the 5-day median volume for that symbol (excludes tiny no-trade carry-forward rows and thin-market artifacts).
4. Day t is a valid trading session per `nepse_trading_calendar.is_trading_weekday`.
5. **No corporate-action mechanical adjustment on or adjacent to day t.** Hard-drop triggers where L-001's event table lists any of `bonus_share`, `bonus_and_cash_dividend`, `right_share`, `cash_dividend` for the same symbol with `book_close_date` within ±2 trading days of day t. Reason: bonus and rights issues create mechanical price drops on ex-date (a 10% bonus drops price ~9.1% mechanically), which masquerade as sharp-down triggers but are accounting adjustments, not real reversal opportunities.

**Exclusion filters for market-wide regime events (applied BEFORE cohort analysis):**

Two layers are applied together:

### Layer A — Hand-picked documented regime dates

These are dates where independent sources document NEPSE-wide shocks. The window is ±5 **trading days** (computed via `nepse_trading_calendar`, not calendar-day approximation).

- 2026-02-18 (Gyalpo Lhosar holiday)
- 2026-02-19 (Democracy Day holiday)
- 2026-03-05 (General Election, non-trading)
- 2026-03-09 (Post-election triple circuit-breaker day, NEPSE +6%)
- 2026-04-14 (Nepali New Year)

This list is documentation of KNOWN events, with citations. It is NOT intended to be exhaustive.

### Layer B — Data-driven market-wide shock filter

Because hand-picked dates can only capture events the team knows about, we also flag any trigger day where the market behaved as a system. A trigger day t is flagged `market_wide_shock = True` if ANY of:

1. **Co-trigger density:** ≥ 30% of **active symbols that actually traded on day t** (volume > 0) also triggered on day t (either sharp-down or sharp-up). Denominator is per-date active count, not the fixed 26-symbol universe, because historical dates with fewer actively-traded symbols would otherwise be under-flagged. Safeguard: the flag only fires when active-symbol count ≥ 5 — below that threshold the share is too jumpy to trust. Computed from the SAME trigger-event table being built.
2. **Equal-weighted market proxy:** the mean daily return across all symbols that traded on day t (i.e. had non-zero volume) satisfies `|market_proxy_return| ≥ 3.0%`. Computed from the price data available at trigger-day time (no lookahead).

Flagged days from Layer A OR Layer B are **hard-dropped** from the primary analysis.

**Sharp-up trigger** (H1b secondary): same definition but `daily_return ≥ +5.0%` and `≤ +9.5%` (or `≤ +14.5%` post-2026-04-17). Same volume, calendar, corporate-action, and regime-filter rules apply.

---

## Symbol Universe

Per `market-gist/automation/scrape_symbol_list.json` (26 symbols):

- **Commercial Banks:** NABIL, EBL, SANIMA, NBB, NICA, PCBL
- **Hydropower:** AKPL, UPPER, API, BHCL, RADHI, AHPC, RHPL
- **Development Banks:** JBBL, MNBBL, SAPDBL, EDBL
- **Life Insurance:** CLI, NLIC, HLI
- **Non-Life Insurance:** LGIL, NIL
- **Microfinance:** RMDC, CBBL
- **Finance:** MFIL, NFS

All sectors included because reversal is a cross-sectional effect on thin markets — restricting to banks+hydros (the corporate-action-heavy sectors) would throw away information. Sector will be tracked as a diagnostic tag.

---

## Historical Window

- Start: earliest available NEPSE price in the archive (2020-2021 for most symbols).
- End: 2026-04-17 (the newest confirmed-clean price day).

Triggers in the forward end of the window that don't have [T+5] completed at scoring time are dropped from the historical test and re-classified as "pending forward evidence" for Gate 3.

---

## Baseline Adjustment

L-003 convention (revised 2026-04-18 to match code):

- For each trigger event at trading session T for symbol S, baseline = per-symbol mean of [T+1, T+5] 5-day returns across **the last 120 prior trading observations** for S (not 120 calendar days — Romeo clarification rev-4). If S has fewer than 120 prior trading observations, use all that exist; the Gate 1 minimum of 30 still applies.
- Minimum 30 prior trading observations required to establish baseline (`baseline_obs_count ≥ 30`).
- Excess return = raw post-event [T+1, T+5] return − baseline.

The shift from "120 calendar days" to "last 120 prior trading observations" is a small semantic change but guarantees Gate 1 and H1 use the exact same baseline universe — no gate-vs-test proxy mismatch.

This ensures we are not simply rediscovering bear-market drift (L-001's historical-window caution).

## Return Construction (Research vs Executable) — clarified per Romeo

For the H1 primary test (historical pass, research grade):

- **Close-to-close return** from close(T) to close(T+5). The holding period is from the trigger-day close to the 5th-next-trading-day close. This is the conventional research return and is what the block-bootstrap test uses.

For any future promotion to a trading signal, a separate executable-return audit is required:

- **Executable return** = entry at open(T+1) (the first opportunity to act after seeing the trigger close), exit at close(T+5). This is what a real trader would actually earn.

Close-to-close vs executable difference depends on overnight gap behavior. On NEPSE, gaps are often non-trivial. Historical H1 passes on close-to-close does NOT imply executable-return viability. The audit at promotion (Gate 4) must re-run the test using executable returns and require the same success criteria. If executable returns fail, the signal is NOT promoted even if close-to-close passes.

---

## Statistical Inference

Same framework as `dividend-microstructure/PRE_REGISTRATION.md` revision 3:

- **Primary significance gate:** date-cluster block-bootstrap.
  - Cluster = trigger calendar date. Resample trigger dates with replacement, N_dates times per iteration.
  - 10,000 iterations.
  - Report: 2.5th / 97.5th percentile of mean excess return; share of replicates with mean ≤ 0 (one-sided bootstrap p-value for H1 that mean is POSITIVE).
- **Decision rule (H1 that mean > 0):** 2.5th percentile of bootstrap CI > 0 (CI excludes zero on positive side); OR equivalently, share of replicates with mean ≤ 0 is ≤ 0.025.

Plain t-statistic reported as descriptive only, labeled "not decision-grade because rows may cluster on trigger dates."

---

## Success Criterion (H1 historical pass — all three required)

1. **Economic magnitude:** mean baseline-adjusted excess return in [T+1, T+5] is **≥ +1.0%** (for sharp-down trigger, expecting positive rebound).
2. **Directional hit rate:** share of trigger events with positive excess return over [T+1, T+5] is **≥ 60%**.
3. **Cluster-robust significance:** 95% block-bootstrap CI for mean excess return excludes zero on the positive side. One-sided bootstrap p ≤ 0.025.

All three required. Two-out-of-three is not a pass.

Historical pass = "H1 historically passes the pre-registered test." Promotion still requires forward evidence (Gate 3).

---

## Failure Criterion (lane killed)

ANY of:

1. Mean excess return < +0.5% (insufficient economic magnitude).
2. Hit rate < 55%.
3. Bootstrap 95% CI includes zero.
4. Gate 1 fails before the test (sample inadequacy).

No post-hoc rescue. No window-shopping. No symbol-subset rescue.

---

## Gate 1 — Sample Adequacy (per-direction, run BEFORE H1)

**Revision 3 clarification:** Gate 1 counts rows with `h1_eligible == True` only. A row is `h1_eligible` if and only if:

- `include_in_primary == True` (all Revision-2 filters pass — volume, price-limit, regime, corp-action)
- `has_forward_5d == True` (symbol has at least 5 future trading sessions after the trigger date in the price archive)
- `baseline_obs_count ≥ 30` (symbol has ≥ 30 prior observations in the trailing 120-day baseline window)

This prevents "gate drift" — the failure mode where Gate 1 passes on `include_in_primary` count but H1 then drops rows that lack forward data or baseline, shrinking sample below the 80-event threshold mid-test.

For the primary direction (sharp-down triggers), all must hold **counting only `h1_eligible` rows**:

1. **Total N ≥ 80** h1-eligible sharp-down trigger events.
2. **Unique trigger calendar dates ≥ 30** across h1-eligible rows.
3. **Top-3 trigger-date concentration ≤ 30%** of h1-eligible sharp-down events.
4. **At least 5 symbols contribute ≥ 1 h1-eligible event each.** (Prevents single-symbol dominance.)

If ANY fails → Gate 1 FAIL → H1 not run → lane closed.

For the secondary direction (sharp-up), same thresholds applied for H1b. If only one direction passes Gate 1, only that direction's H1 is tested.

---

## Intermediate Zone (reported as FAILED, not supportive)

If H1 lands with:
- Mean excess return between +0.5% and +1.0%, OR
- Hit rate 55-60%, OR
- Bootstrap CI touches but does not strictly exclude zero

The result is labeled: **"Failed H1. Directionally consistent with reversal but not promotable."** No "supportive" / "encouraging" language. The lane closes for this hypothesis.

---

## Diagnostic Windows (Reported, Non-Promotional)

After the primary [T+1, T+5] test, report for diagnostic only:

- **post_1_1**: [T+1, T+1] (next-day-only bounce)
- **post_1_10**: [T+1, T+10] (medium-horizon continuation)
- **post_6_10**: [T+6, T+10] (late-window isolation)

Diagnostic outputs live in `results/diagnostic_<date>.json`. They are NOT the primary decision. Diagnostic success does not rescue a failed primary test.

---

## Sample Concentration Reporting (L-012 Discipline)

Every H1 output must include:

- Total N, unique trigger date count.
- Distribution of triggers by calendar date.
- Share in top-1, top-3, top-5 dates.
- Symbol breakdown with N per symbol.

If top-3 concentration exceeds 30% but Gate 1 was passed by some marginal quirk, still label the result "clustered-sample, interpret with caution."

---

## Baseline Fragility Check (Bear-Market Contamination)

Report:
- **Primary:** 120-day trailing per-symbol baseline (pre-registered).
- **Sensitivity 1:** matched-sector market drift subtracted in addition to per-symbol baseline.
- **Sensitivity 2:** restricted to triggers where SMA-200 regime was "above" at T-1 (likely small N; descriptive only).

Label "baseline-fragile, do not promote" if ANY of:
- Opposite signs (primary positive but Sensitivity 1 negative, or vice versa).
- Magnitude collapse: |Sensitivity 1 mean| ≤ 40% of |primary mean|.
- Sensitivity 1 fails the pre-registered success criteria.

---

## Multiple-Testing Discipline

Only the primary sharp-down H1 is the promotion-grade test. Everything else — sharp-up H1b, diagnostic windows, sector slices, threshold sensitivity — is exploratory and labeled as such.

---

## Historical Evidence ≠ Forward Evidence

Even if H1 historically passes, promotion is not granted until:

1. N ≥ 25 forward-resolved trigger events (post-pre-registration only).
2. Forward result also satisfies the pre-registered success criteria.
3. 6-class audit passed.
4. Romeo re-reviews the audit output.
5. Juliet writes a L-xxx learning; Romeo verifies.
6. Integration into LEARNINGS.md at a clean gate.

Historical pass = hypothesis survives first test. Forward pass = hypothesis earns promotion.

---

## Romeo Review Items — Status

Romeo's 2026-04-18 first review verdicts:

1. **5.0% threshold:** APPROVED (do not test 3/5/7 variants now)
2. **Primary window [T+1, T+5]:** APPROVED with clarification — return construction must be defined explicitly (close-to-close for research, executable audited separately). **Fixed in "Return Construction" section above.**
3. **Regime exclusion:** REVISE — hand-picked 2026 dates miss 2020-2025 shocks. **Fixed: Layer A + Layer B approach. Hand-picked documented events retained with citations; data-driven market-wide filter added (co-trigger density + equal-weighted market proxy).**
4. **Symbol universe (all 26):** APPROVED
5. **Baseline-fragility 40%:** APPROVED

Romeo's 2026-04-18 first review additional findings:

- **P1.2 (calendar vs trading days):** code used `days_diff = (trigger_date - rd).days` which is calendar days + 2, not trading days. **Fixed: code now computes via `nepse_trading_calendar.is_trading_weekday` iteratively, matching pre-reg's trading-day semantics.**
- **P1.3 (corporate-action mechanical adjustment):** bonus share ex-dates create 5-17% mechanical price drops that masquerade as reversal triggers. **Fixed: hard-drop triggers within ±2 trading days of same-symbol corporate-action book-close-date, using L-001's event table.**
- **P2.5 (circuit-limit exclusion not operationally defined):** **Fixed: numerically defined. |daily_return| > 9.5% (pre-2026-04-17) or > 14.5% (post) tagged `near_price_limit = True` and hard-dropped.**

All 5 Romeo verdicts from the first review integrated into revision 2. Romeo's second review surfaced 2 additional measurement issues (gate drift + Layer B denominator) integrated into revision 3. Romeo's third review flagged 4 small consistency items (Layer B wording mismatch, stale revision 1 text in check_gate1.py, gate-drift diagnostic, baseline-method alignment with H1) — all integrated into revision 4. Revision 4 pending Romeo's final re-review.

---

## Commit Discipline

This file (revision 4) must be committed to git before any `.py` in this sandbox runs. Commit message:

```
reversal-specialist: pre-register H1 revision 4 after Romeo third review

Revision 4 fixes (consistency / sealing):
- Pre-reg Layer B wording matches code: "30% of active symbols that traded that
  date" (was "30% of the 26 scrape-universe symbols").
- Check_gate1.py stale "revision 1" docstring + markdown text bumped to rev 4.
- Gate-drift diagnostic added: reports include_in_primary vs h1_eligible split
  by reason (no forward window / insufficient baseline). Exposure is now visible.
- Baseline method aligned with L-003 / future H1: "last 120 prior trading
  observations" (was "trading rows within 120 calendar days"). Same baseline
  universe across Gate 1 and H1.

Revision 3 fixes (measurement):
- h1_eligible gate (Gate 1 counts only rows that can enter H1).
- Layer B denominator uses active-symbol count per date, not fixed 26.

Revision 2 fixes (prior):
- Trading-day regime-exclusion windowing (was calendar-day bug)
- Layer B data-driven market-wide shock filter added
- Corporate-action ex-date hard-drop
- H1 return construction defined (close-to-close; executable audit at promotion)
- Circuit-limit exclusion numerical (9.5% pre / 14.5% post 2026-04-17)

Primary hypothesis unchanged across revisions:
sharp-down trigger (<= -5%) on NEPSE symbols, baseline-adjusted excess return
over [T+1, T+5] positive.
Success: mean >= +1.0% AND hit rate >= 60% AND bootstrap CI excludes zero.
Failure: mean < +0.5% OR hit rate < 55% OR CI includes zero OR Gate 1 fails.
```

---

## Sign-Off

- **Juliet (author, revision 1):** 2026-04-18 morning — initial draft.
- **Romeo (first blocking review):** 2026-04-18 afternoon — REQUEST CHANGES. 5 findings: calendar-vs-trading-day bug, corp-action mechanical adjustment, regime-exclusion scope, return construction definition, circuit-limit numerical definition. All integrated into revision 2.
- **Juliet (author, revision 2):** 2026-04-18 afternoon.
- **Romeo (second blocking review):** 2026-04-18 late afternoon — REQUEST CHANGES. 2 measurement issues: (a) Gate 1 must count `h1_eligible`, not `include_in_primary`, to prevent gate drift; (b) Layer B co-trigger denominator must be active-symbol count per date, not fixed 26. Also caught stale `"pre_registration_revision": "1"` in check_gate1.py output. All integrated into revision 3.
- **Juliet (author, revision 3):** 2026-04-18 late afternoon.
- **Romeo (third blocking review):** 2026-04-18 evening — REVISE SMALL ITEMS. 4 consistency fixes: (a) pre-reg Layer B wording mismatch with code; (b) stale revision 1 text in check_gate1.py docstring and markdown; (c) add gate-drift diagnostic; (d) align baseline method with L-003 / H1 (last 120 prior trading observations, not 120 calendar-day window). All integrated into revision 4. Uncertainties resolved: MIN_ACTIVE_FOR_CO_TRIGGER = 5 frozen; gate-drift diagnostic is required not optional; baseline method explicitly aligned.
- **Juliet (author, revision 4):** 2026-04-18 evening — this document. All Romeo third-review findings addressed.
- **Romeo (sign-off on revision 4):** pending — Romeo said "Revise small items, then sign off," so sign-off is imminent on confirming these 4 fixes landed correctly.
- **Ishwor (lab operator):** validated all three Romeo reviews independently; agreed on all findings (data checks confirmed the Layer B wording mismatch, the stale revision 1 text count, and the baseline-method-vs-H1 alignment need).
- **Benvolio (optional exploration-team review):** pending (non-blocking).

No code runs in this sandbox until Romeo signs off on revision 4.
