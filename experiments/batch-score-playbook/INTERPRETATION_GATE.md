# Batch-Score Interpretation Gate — Pre-Code Contract (v3)

**Written:** 2026-04-19
**Status:** Pre-code contract v3. No code changes authorized by this document.
**Scope owner:** Juliet
**Folder in scope:** `experiments/batch-score-playbook/` only
**Companion docs:** `README.md`, `CONTRACT.md` (this doc does NOT modify either; it specifies what a future revision of the playbook's verdict logic must enforce)

**Revision history**
- v1: 2026-04-19 initial draft — single `FORECAST_VALID_CONTEXT_ONLY` bucket, three CAUTION lenses (avoid-buy default; others secondary), no expiry rule, no influence rule (superseded)
- v2: 2026-04-19 reviewer follow-up — `FORECAST_VALID_CONTEXT_ONLY` split into four explicit states; expiry rule added for unmeasured-cost verdicts; influence rule added for all non-`TRADE_READY` signals; CAUTION actionability must report all three lenses every run; promotion requires avoid-buy or exit/sell to pass (short-like alone cannot promote, because NEPSE retail cannot short); kill-date conversation trigger noted (superseded)
- v3: 2026-04-19 second-round reviewer follow-up — quantified promotion margin (≥1σ of baseline month-to-month return distribution); precise `COST_NEGATIVE` vs `COST_MARGINAL` definitions via 1σ bound on post-cost EV; baseline pool P defined as the 3 active_shadow symbols (not all 26); Metric #7 exit/sell horizon locked to the same 10-trading-day window as production `success_10d`; forward-decay sensitivity check specified as 10-percentage-point hit-rate decay; per-case CSV schema switched to wide format with per-lens cost and net-value columns

---

## Why This Document Exists

The persistence shadow N=25 gate will land around late April / early May 2026. The current `run_batch_score.py` will return `PROMOTE` on forecast-validity alone: hit rate, clustering, sub-period stability, F.1 pre-registration artifact, structural checks. It does NOT require post-cost EV, positive mean return, or actionability vs a no-signal baseline.

A `PROMOTE` without those checks is cosmetic. A 72% hit rate can be negative-EV post-cost. A positive hit rate with negative payoff ratio can underperform "do nothing." A forecast-valid signal that fails cost realism is real research evidence but not a tradeable signal, and the two must not share a verdict.

This contract locks the interpretation before N=25 arrives so the logic cannot be tuned after seeing results.

---

## Current State (honest)

As of 2026-04-19, the batch-score-playbook enforces these PROMOTE conditions (from `README.md`):

- N ≥ 25 resolved `persistence_caution_only`
- Hit rate ≥ 65%
- Sample concentration: top-3 dates ≤ 40% of resolved
- Effective independent episodes ≥ 5
- Sub-period stability across ≥ 2 sub-periods
- F.1 pre-registration artifact present
- No A.1–A.3 code-structural failure

It does NOT enforce:

- Post-cost expected value (EV) above a no-signal baseline
- Mean return strictly > 0
- Bootstrap confidence interval excluding zero
- Payoff ratio sanity (avg win vs avg loss)
- Avoid-buy value vs no-signal baseline
- Exit / sell value after realistic Nepal equity costs
- Any actionability interpretation

The hardened gate defined below adds these without modifying the existing forecast-validity checks.

---

## What Is In Scope For This Contract

**In scope (future work authorized only after Romeo signs off on this doc):**
- Extending `run_batch_score.py` (or adding a sibling module inside `experiments/batch-score-playbook/`) to compute the Gate 2 metrics and apply the verdict logic below
- Writing the per-case CSV and per-group JSON with the expanded metrics
- Returning the new v2 verdicts (`FORECAST_UNVALIDATED`, `FORECAST_VALID_COST_UNMEASURED`, `FORECAST_VALID_COST_NEGATIVE`, `FORECAST_VALID_COST_MARGINAL`, `TRADE_READY`) alongside the existing `BELOW_GATE` and `HOLD`

**Out of scope (this contract explicitly forbids):**
- Modifying `market-gist/automation/score_persistence_shadow_reports.py` (production scorer stays untouched; hit-rate history stays comparable)
- Modifying the live signal, the frozen policy, the daily runner, or any `market-gist/**` file
- Modifying `persistence_shadow_reports/**` outputs
- Retro-adjusting any prior hit-rate claim or L-entry
- Expanding to universe v2 symbols
- Computing signals, hit rates, or EV during this contract step — this document is specification only

---

## Gate 1 — Forecast Validity (existing checks, kept as-is)

Unchanged from the current playbook. All of the following must pass for Gate 1:

| Check | Threshold | Source |
|---|---|---|
| N resolved in `persistence_caution_only` | ≥ 25 | current playbook |
| Hit rate | ≥ 65% | current playbook |
| Sample concentration (top-3 dates share) | ≤ 40% | current playbook |
| Effective independent episodes | ≥ 5 | current playbook |
| Sub-period stability | holds across ≥ 2 sub-periods | current playbook |
| F.1 pre-registration artifact | present, timestamped ≤ 2026-04-05 | current playbook |
| A.1–A.3 structural checks | no failure | current playbook |

If any Gate 1 check fails → verdict is `KILL` or `BELOW_GATE` per existing rules (no change).

---

## Gate 2 — Actionability (new)

Introduced by this contract. Evaluated only if Gate 1 passes.

### Signal-direction-aware win/loss convention

**Because CAUTION is a negative-direction signal, "win" and "loss" are defined relative to the signal's predicted direction, not positive/negative return in isolation.**

For the CAUTION signal under evaluation:
- **Forecast win** = 10d return < 0 (signal predicted down and price went down)
- **Forecast loss** = 10d return ≥ 0 (signal predicted down but price did not fall)
- **Avg forecast-win move** = mean return among forecast wins — typically a negative number
- **Avg forecast-loss move** = mean return among forecast losses — typically a positive number

Payoff and asymmetry metrics below are defined from **decision value**, not raw sign alone. A "win" is not "return was positive"; it is "the signal's predicted direction was realized."

For signals in the lab that predict UP (none currently, but documented for generality): forecast win = return > 0, forecast loss = return ≤ 0. Every future Gate 2 evaluation must state the signal's predicted direction before computing these metrics.

### Baseline pool P (locked)

**Baseline pool P = symbols in `experiments/shared/universe_v1_frozen.csv` where `v1_role == active_shadow`, currently {NABIL, EBL, SANIMA}.** Comparison = equal-weight buy-and-hold over the same 10-trading-day horizon with the same cost tier applied from `market-gist/automation/replay_cost_realism_study.py`.

**Important:** do NOT accidentally use all 26 v1 symbols or any v2 symbols as the baseline unless separately authorized by Romeo with a new pre-registration. The baseline pool is narrow on purpose: the persistence-shadow v1 policy fires only on the active_shadow tier, so the counterfactual "what would I have done instead" is also scoped to the active_shadow tier.

### Promotion margin (locked)

**Promotion margin = post-cost EV must exceed the no-signal baseline by at least 1σ of the month-to-month baseline-sample return distribution, with σ computed on the same resolved-case window.**

Concretely: bucket the baseline-pool no-signal cases by calendar month across the resolved-case window, compute each month's mean post-cost return, take the standard deviation of those monthly means → this is σ. The signal's post-cost EV must exceed baseline post-cost EV by at least this σ for `TRADE_READY`.

### Metrics required

| # | Metric | Definition (for CAUTION — negative-direction signal) |
|---|---|---|
| 1 | Avg forecast-win move | Mean 10d return among resolved cases where return < 0 (typically negative number) |
| 2 | Avg forecast-loss move | Mean 10d return among resolved cases where return ≥ 0 (typically positive number) |
| 3 | Payoff ratio | \|avg forecast-win move\| ÷ \|avg forecast-loss move\|. Asymmetry favoring the signal's predicted direction implies payoff > 1. |
| 4 | Pre-cost mean return | Mean 10d return across all resolved cases. For CAUTION, this should be negative if the signal's forecast content is real. |
| 5 | Post-cost EV estimate | The lens-appropriate decision value, minus realistic Nepal cost per `replay_cost_realism_study.py` cost tiers. For CAUTION under the avoid-buy lens, decision value = "avoided a losing buy" — see Metric #6. For exit/sell lens, decision value = return differential between exit-and-reenter vs hold — see Metric #7. |
| 6 | Avoid-buy value vs no-signal baseline | Post-cost value of "not buying into a CAUTION-firing stock" minus post-cost value of "buying from pool P (see Baseline pool above) over a 10-trading-day horizon, equal-weight, same cost tier". Expected to be positive if CAUTION's forecast content is economically meaningful. |
| 7 | Exit / sell value after realistic costs | Post-cost value if the signal is acted on as an exit trigger (sell on CAUTION and re-enter later) vs holding through **the same 10-trading-day horizon as `success_10d` in the production scorer**. Requires explicit round-trip cost model. Typically the hardest lens to clear because of round-trip friction. |
| 8 | Actionability label | Derived flag: `actionable` / `not_actionable` / `inconclusive` (see actionability pass conditions below). |

### Actionability pass conditions (all required)

- Metric #4 (pre-cost mean return) has the sign consistent with the signal's predicted direction — for CAUTION, strictly negative.
- Metric #3 (payoff ratio) is > 1, AND passes the **forward-decay sensitivity check**: recompute payoff ratio and post-cost EV under a 10-percentage-point hit-rate decay (e.g., if observed hit rate is 65%, stress case uses 55%). Pass only if EV remains positive under the decay.
- Metric #6 (avoid-buy value vs no-signal baseline) exceeds the baseline post-cost EV by **at least the promotion margin** (≥ 1σ of baseline month-to-month return distribution, σ computed on the same resolved-case window) — OR — Metric #7 (exit/sell value) is positive after round-trip costs by at least the same promotion margin.
- At least one of Metric #6 OR Metric #7 must pass its margin; Metric #4 alone (the short-like-forecast lens) is a diagnostic of forecast quality and cannot by itself authorize promotion to `TRADE_READY`. NEPSE retail cannot trade the short-like return stream.

### Actionability cannot be computed — explicit handling

If metric #5, #6, or #7 cannot be produced because the cost model is missing, divergent, or the baseline sample is too small:
- Verdict is `FORECAST_VALID_COST_UNMEASURED`
- Must NOT return `TRADE_READY` under any cost-incomputable condition
- Must NOT retry with relaxed cost assumptions unless Romeo re-authorizes

---

## Verdict Matrix (v2 — expanded state ladder)

| Gate 1 (forecast) | Gate 2 (actionability) | Verdict |
|---|---|---|
| N < 25 | not evaluated | `BELOW_GATE` (existing, pre-gate state) |
| pass but sub-period borderline | any | `HOLD` (existing, sub-period stability deferred) |
| fail | not evaluated | `FORECAST_UNVALIDATED` (replaces `KILL` at the forecast stage) |
| pass | cannot compute | `FORECAST_VALID_COST_UNMEASURED` |
| pass | post-cost EV point estimate ≤ 0 AND upper 1σ bound ≤ 0 | `FORECAST_VALID_COST_NEGATIVE` |
| pass | post-cost EV > 0 but < promotion margin, OR 1σ interval crosses zero | `FORECAST_VALID_COST_MARGINAL` |
| pass | post-cost EV exceeds baseline by ≥ promotion margin (≥ 1σ of baseline month-to-month return distribution) | `TRADE_READY` (replaces `PROMOTE`) |

Only the four `FORECAST_VALID_COST_*` states and `TRADE_READY` are new in v2; `BELOW_GATE` and `HOLD` carry over from the existing playbook unchanged.

### State ladder and re-entry paths

| Verdict | Meaning | Re-entry path |
|---|---|---|
| `BELOW_GATE` | N < 25 resolved; forecast gate not yet evaluable | Wait; accumulate forward evidence |
| `FORECAST_UNVALIDATED` | N ≥ 25 but forecast gate (hit rate, clustering, effective episodes, sub-period stability, F.1 pre-reg, A.1–A.3 structural) failed | N-expansion (if universe v2 or longer window is justified via new pre-reg) or kill outright; no quiet retry |
| `FORECAST_VALID_COST_UNMEASURED` | Forecast gate passed; Gate 2 inputs (cost model wiring, baseline sample) not ready to evaluate | Resolve Gate 2 inputs, re-run the playbook. Subject to the expiry rule below. |
| `FORECAST_VALID_COST_NEGATIVE` | Forecast gate passed; post-cost EV point estimate ≤ 0 AND upper 1σ bound ≤ 0 | **Fixed label, no drift.** Permanently not a trade rule unless the cost structure itself changes materially (not the signal). Document in LEARNINGS. |
| `FORECAST_VALID_COST_MARGINAL` | Forecast gate passed; post-cost EV > 0 but below promotion margin, OR 1σ interval crosses zero | Extend N, improve execution assumptions, or revisit after more forward evidence. Subject to expiry rule. |
| `TRADE_READY` | Forecast gate passed AND post-cost EV exceeds baseline by ≥ promotion margin (≥ 1σ of baseline month-to-month return distribution) | Active lane candidate. Still requires Romeo sign-off per existing `README.md` PROMOTE flow before any real-money action. |

### Splitting rationale

The single `FORECAST_VALID_CONTEXT_ONLY` bucket in v1 (superseded) conflated three distinct failure modes with different next steps:
- **Cost not yet measured** → the fix is computation, not re-research
- **Cost measured, clearly negative** → the signal is structurally un-tradeable and the label should stick
- **Cost measured, borderline** → more N or cheaper execution could flip it

Compressing those into one label creates drift risk: a signal that's actually `COST_NEGATIVE` (permanent) could get re-examined repeatedly as if it were `COST_UNMEASURED` (temporary). The four-state split locks each signal's interpretation to its specific failure mode.

### Expiry rule for `FORECAST_VALID_COST_UNMEASURED`

A verdict of `FORECAST_VALID_COST_UNMEASURED` cannot sit forever. Without an expiry clock, "context only" becomes a permanent parking lot where signals accumulate with no resolution.

**Rule:** if Gate 2 (actionability) cannot be computed at the first N≥25 run, the playbook produces the `FORECAST_VALID_COST_UNMEASURED` verdict and records a deadline of **the next gate review** (whenever the playbook runs again at N≥25 with additional resolved cases). If Gate 2 still cannot be computed at that next review, the verdict **remains `FORECAST_VALID_COST_UNMEASURED`**, stays blocked from any trade-ready promotion, and requires Romeo review before any further re-interpretation.

**No auto-demotion to `FORECAST_VALID_COST_NEGATIVE`.** Missing cost computation is a computation-pipeline problem, not evidence of negative EV. Treating "we couldn't measure it" as "it's bad" would bake a pipeline gap into the signal's permanent label. The correct response is to unblock the cost computation, not to demote the signal.

No silent re-runs. No indefinite parking. No drift of `UNMEASURED` into `NEGATIVE` without actually measuring.

### Influence rule (all non-`TRADE_READY` verdicts)

The single failure mode the v1 contract did not guard against: psychological bleed-through. A human who sees "the signal predicts direction, even if post-cost EV is negative" may use it discretionarily in position sizing, trade direction, or stock selection — despite being told it's context only.

**Rule:** a signal with any verdict other than `TRADE_READY` may appear in shadow-report narrative commentary and risk-context discussion, but may NOT:
- Influence position sizing (no "bigger bet because signal agrees")
- Influence the direction of an active trade (no "exit because signal caution-fires")
- Influence stock selection (no "prefer this over that because signal quiet")
- Be cited as part of any real-money decision rationale

If the signal does not have `TRADE_READY` status, its forecast content is not permission to trade. This rule is written explicitly so the boundary exists on paper, not just in memory.

---

## `TRADE_READY` Requires Both Gates

`TRADE_READY` is AND-gated. Forecast validity alone is not sufficient. Actionability alone is not sufficient. Both must pass within the same playbook run, on the same N=25+ resolved sample, with the same frozen policy version `v1_frozen_2026-04-05`.

No partial-promotion, no conditional promotion, no "`TRADE_READY` with caveats." The verdict is exactly one of: `BELOW_GATE`, `HOLD`, `FORECAST_UNVALIDATED`, `FORECAST_VALID_COST_UNMEASURED`, `FORECAST_VALID_COST_NEGATIVE`, `FORECAST_VALID_COST_MARGINAL`, `TRADE_READY`.

---

## CAUTION — Three Interpretation Lenses (all three measured every run)

The `persistence_caution_only` signal fires as a CAUTION flag on the live symbol. That flag does not itself specify a trading action. Three distinct readings are possible, each evaluating against a different counterfactual with different cost structures.

**v2 rule (reviewer follow-up): every playbook run must measure and report all three lenses side-by-side on the same window.** Reporting only one lens creates a version of the original hit-rate trap — the chosen lens can be tuned post-hoc to look best, and different users (buyer vs holder vs researcher) care about different measures.

| # | Lens | Counterfactual | Cost structure | NEPSE retail realism |
|---|---|---|---|---|
| 1 | **Avoid-buy** | "I would have bought from pool P; CAUTION trims the pool" | Medium — one-way friction avoided | **Highest.** Matches how retail actually uses a CAUTION flag. |
| 2 | **Exit / sell** | "Already holding; sell now vs. keep through the window" | Very high — round-trip cost + re-entry risk + cash drag | Low. Most NEPSE retail is buy-and-hold. Round-trip costs usually dominate the edge. |
| 3 | **Short-like forecast** | Synthetic short at mid, infinite liquidity | None — pure forecast-quality measure | Zero. NEPSE retail shorting is effectively unavailable at scale. |

### Primary lens and promotion rule

**Primary lens for promotion (`TRADE_READY`) evaluation: avoid-buy (#1).** Rationale: lowest cost burden, most direct match to the way retail actually uses a CAUTION signal, lowest execution friction.

**Promotion requires at least one of avoid-buy (#1) OR exit/sell (#2) to pass its benchmark after costs.** The short-like forecast lens (#3) is a forecast-quality diagnostic — it measures whether the signal's directional content is real, separate from whether it is personally actionable. **Lens #3 alone cannot promote a signal to `TRADE_READY`** because NEPSE retail cannot realize the short-like return stream.

### Reporting requirements (every run)

The playbook must produce, for every N≥25 run:
- All three lenses' post-cost EV values, side-by-side, same window
- Each lens's pass/fail against its own benchmark
- The explicit verdict mapping: short-like pass alone → `FORECAST_VALID_COST_NEGATIVE` or `FORECAST_VALID_COST_MARGINAL` (signal predicts but is not tradeable). Avoid-buy or exit/sell pass (with short-like) → `TRADE_READY`.

### Why lens #3 stays in the report even though it cannot promote

It separates directional quality (does the signal predict?) from executability (can retail trade it?). A signal that fails #3 is forecast-dead; a signal that passes #3 but fails #1 and #2 is forecast-valid but unexecutable — genuinely different scientific verdicts, and the `FORECAST_VALID_*` state ladder depends on the distinction.

---

## What This Document Does NOT Authorize

- Any code change to `run_batch_score.py`, `score_persistence_shadow_reports.py`, or anything in `market-gist/**`
- Any change to the frozen policy, the daily runner, the shadow report generator, or the scoring pipeline
- Any modification of historical hit-rate claims, LEARNINGS entries, or prior verdicts
- Any universe-v2 work or cross-symbol extension
- Any signal tuning, threshold adjustment, or lens reinterpretation after seeing the N=25 result

---

## Reporting Requirements (for the future coded run, when implemented)

When the hardened playbook runs at N≥25, the output memo must report:

1. Gate 1 result (pass / fail) with per-check values
2. Gate 2 result (pass / fail / cannot-compute) with all 8 metrics
3. The chosen CAUTION interpretation lens (default: avoid-buy)
4. Secondary views under the other two lenses, labeled as reference only
5. Per-case CSV in **wide format** so all three lenses can be reported from the same row. Required columns:
   - `report_date`
   - `symbol`
   - `pre_cost_return_10d`
   - `win_flag` (1 if return_10d < 0 for CAUTION, else 0)
   - `magnitude`
   - `group_key`
   - `cost_pct_avoid_buy`
   - `cost_pct_exit_sell`
   - `cost_pct_short_like`
   - `net_value_avoid_buy`
   - `net_value_exit_sell`
   - `net_value_short_like`
   
   Wide format is preferred so each lens's cost tier and net value is visible per row without joins. Long format is NOT allowed unless every downstream summary aggregator is also updated to expect it (a coordinated change, out of scope for this pre-code contract).
6. Final verdict from the matrix above

---

## Connection To The System-Level Kill Date

A system-level kill date for the whole systematic lane has been deferred for later decision (Ishwor picks date + threshold). This contract states the trigger for that conversation:

**Kill-date conversation trigger:** immediately after the persistence N=25 gate completes (whenever the playbook first produces a verdict other than `BELOW_GATE`). At that point, Ishwor picks:
1. The date by which the systematic lane must show at least one `TRADE_READY` signal
2. The success threshold (e.g., post-cost EV > NEPSE equal-weight-plus-dividend benchmark + margin)

The kill date is NOT set by this contract. It is scheduled by this contract to happen immediately after the first real gate evaluation.

## Sign-Off

This pre-code contract is committed BEFORE any implementation work. Any deviation requires a revision of this document, not an amendment to the code. Romeo review is required before:

- Any modification to `run_batch_score.py`
- Any new sibling module inside `experiments/batch-score-playbook/`
- Any exercise of the hardened verdict logic against actual N=25 data

No code changes are authorized by v1, v2, or v3 of this contract. After Romeo signs off on v3, a future revision may adjust thresholds, lens defaults, or metric definitions if justified. Only when Romeo signs off on a final revision does implementation begin.
