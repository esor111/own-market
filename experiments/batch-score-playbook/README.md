# Batch-Score Decision Playbook

> Layer 3 infrastructure tool under `SANDBOX_PROTOCOL.md`.
> Automates the batch-score gate decision at N≥25 persistence shadow cases.
> DEFENSIVE: built so the user can execute the decision without Claude available.

---

## Why This Exists

The persistence shadow signal will hit N=25 resolved cases around April 23-24, 2026. That is the first real promotion decision in the lab — promote to live trading, hold for more evidence, or kill outright.

This decision needs:
1. Clean audit results against the 6-class checklist (Benvolio's design, Romeo-reviewed)
2. Clear verdict thresholds that can't be argued with in the moment
3. Structured output the user can show Romeo for verification
4. Runnable in one command, without Claude needing to think through the logic live

This tool is that packaging. It does not introduce new research. It mechanizes the decision logic that already exists across `04_persistence_lookahead_audit.md`, L-012, L-013, and the signal decay tracker.

---

## What It Does

1. Loads the scorecard cases CSV and the scorecard JSON.
2. Checks whether N ≥ 25 resolved cases exist in `persistence_caution_only` group. If not → BELOW_GATE.
3. Runs the full 6-class audit on current data:
   - **F.1** pre-registration artifact: verify `PERSISTENCE_SHADOW_POLICY_V1_FROZEN.md` exists with a timestamp on or before 2026-04-05. Hash the current content for drift-check reference.
   - **F.2** search space documentation: descriptive only (cannot fully automate without a pre-registration file listing alternates tested).
   - **A.1-A.3** calendar/dedupe/regime: descriptive flags based on code introspection (reports whether `collapse_duplicate_sessions` is defined in the scorer).
   - **A.4** sub-period stability: split resolved cases by quarter and report hit rate per sub-period.
   - **B** frozen policy drift: check whether the policy file's content matches its state when the first shadow report was generated (best-effort via file timestamp).
   - **C** baseline adjustment: descriptive flag (no-signal baseline hit rate count, used as comparison).
   - **D** sample concentration: unique dates, top-3 share, Gini coefficient, by-symbol distribution.
   - **E** decay diagnostic: rolling-5 hit rate compared to all-time baseline.
4. Applies verdict thresholds → PROMOTE / HOLD / KILL.
5. Writes structured decision memo with verdict + reasoning + recommended next action.

---

## Verdict Thresholds

**PROMOTE** (all conditions required):
- N (resolved `persistence_caution_only`) ≥ 25
- Hit rate ≥ 65%
- Sample concentration: top-3 report dates ≤ 40% of resolved cases
- Effective independent episodes (unique report dates contributing wins) ≥ 5
- Sub-period stability: hit rate holds across at least 2 separate sub-periods (e.g. both Aug-Oct and Dec-Feb)
- F.1 pre-registration artifact present
- No A.1-A.3 code-structural failure

**KILL** (any triggers):
- Hit rate drops below 55%
- F.1 pre-registration check fails (no frozen policy file, or timestamp after first shadow report)
- Top-1 report date contains > 50% of resolved cases (extreme clustering)
- Effective independent episodes < 3

**HOLD** (everything in between):
- Some concerns but no hard failure
- Action: collect more forward evidence, re-run in 10-15 trading days

**BELOW_GATE** (default):
- N < 25 resolved cases
- Verdict deferred; descriptive stats reported but no action taken

---

## How To Use

### Day-to-day: do nothing

The daily routine produces shadow reports automatically. When the next report runs, case counts update. You don't need to run this tool until resolved count approaches 25.

### When to run

1. **Check readiness:** run at any time to see current resolved count and whether we're close.
2. **At the gate:** when resolved count hits 25+, run to produce the verdict.
3. **After verdict:** if HOLD, re-run every 5-10 new resolved cases until verdict stabilizes.

### Command

```
python experiments/batch-score-playbook/run_batch_score.py
```

Output: `results/latest.md` — read this file, follow the recommended next action.

### What to do with each verdict

**BELOW_GATE:** no action. Wait for more cases to resolve. Check in a week.

**PROMOTE:**
1. Read the memo fully.
2. Send it to Romeo for adversarial review (prompt template in the memo).
3. If Romeo agrees: follow the serial-promotion path in `PARALLEL_EXPLORATION_SERIAL_PROMOTION.md`.
4. Do not act on the verdict without Romeo sign-off, even if the tool says PROMOTE.

**KILL:**
1. Read the memo fully, especially which condition triggered the kill.
2. Document the failure in LEARNINGS.md (L-xxx entry).
3. Keep the persistence shadow running in shadow mode; the signal is not "broken" for monitoring purposes, just not promotable.
4. Redirect the lab's forward-evidence budget to other Tier 1 signals.

**HOLD:**
1. Read the memo to understand which conditions are borderline.
2. Continue the daily routine.
3. Re-run this tool after ~10 more trading days.

---

## Why This Doesn't Need Full Romeo Review Cycle

This tool packages already-validated methodology:
- 6-class audit: Benvolio-designed, Juliet-validated, Romeo-implicit via L-012 discovery
- Verdict thresholds: derived from L-013's ~50-52% implied ceiling + ~13-15pp needed to justify promotion
- Clustering rules: L-012 findings (7/8 from 2 dates = not independent)

Romeo's review is focused on the VERDICT THRESHOLD NUMBERS (65%, 55%, top-3 ≤ 40%, episodes ≥ 5). Not on the underlying methodology. That's a tighter review scope than the dividend-microstructure pre-registration required.

---

## Kill Condition

Delete this folder. Nothing else breaks.

---

## Relationship to Other Lab Tools

- **Signal Decay Tracker** (`experiments/signal-decay-tracker/`) runs weekly, watches for decay between gates. This playbook runs at the gate itself.
- **Persistence shadow** (`market-gist/automation/`) is the production signal being evaluated.
- **SANDBOX_PROTOCOL** governs this tool's layer boundaries.
