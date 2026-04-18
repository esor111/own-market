# Dividend Microstructure Signal

> Second reference sandbox under `SANDBOX_PROTOCOL.md`. Layer 3 experiment.
> Extends L-001 (book-closure notice drift) to the book-closure date event.

---

## Status

**Pre-code.** Research foundation documented (`RESEARCH_BRIEFING.md`). Pre-registration at **revision 3** (2026-04-17) after two Romeo adversarial passes. Awaiting final Romeo sign-off on revision 3. No code has been written. No returns computed. This state is deliberate.

Per the sandbox protocol: research before code, pre-registration before code, code before gate-check, gate-check before H1 test, H1 before promotion discussion. Historical pass before forward evidence. Forward evidence before canon integration.

---

## Why This Exists

L-001 found that book-closure **notices** on banks produce a negative post-notice drift at 71% hit rate with p=0.004. The academic literature on ex-dividend microstructure is not about notices — it is about the **book-closure date itself** (the "ex-date" equivalent in NEPSE's system).

The open question: **is the L-001 signal actually capturing the ex-date drift via its notice anchor, or are these two distinct signals?**

If notice drift is just "front-running the ex-date," they are the same signal measured twice. If they are distinct, we have a second independent signal that can be tracked forward alongside persistence.

This experiment answers that question.

---

## Research Foundation

See `RESEARCH_BRIEFING.md` for the full literature briefing. Key points:

- Best-supported mechanism for NEPSE: **dividend capture + shortage amplification**, not tax clientele (Nepal tax wedge is shallow)
- Closest emerging-market analog: **Pakistan PSX** (4.9% ex-day ARR, t=12.96, 2001-2020)
- Critical risk: overlap with L-001 notice events — must be measured BEFORE H1 test

**Priors kept out of decision language (per Romeo revision 2):**
Adjacent-market literature suggests NEPSE outcomes in some plausible range (smaller than Pakistan, given NEPSE lacks short-selling). This is briefing context only. It does **not** anchor the decision. The pass/fail criteria are pre-registered explicitly in `PRE_REGISTRATION.md`; no "expected outcome" number is permitted to soften a failed result.

---

## Primary Hypothesis (H1)

See `PRE_REGISTRATION.md` for the exact pre-registered statement.

Informally: banks + hydros that announce cash dividends should show a baseline-adjusted mean excess return ≤ −1.0% in **[T_ex + 1, T_ex + 5]** (where T_ex is the first non-entitled trading session), with directionally negative hit rate ≥ 60%, under date-cluster **block-bootstrap** inference where the 95% CI excludes zero on the negative side.

Decision statistic is block-bootstrap (10,000 iterations resampled by event date), not plain t-statistic. Plain t is descriptive only per Romeo revision 2.

---

## The Gate Structure (per PRE_REGISTRATION revision 2)

```
┌─────────────────────────────────────────────────────────┐
│ Gate 0: Pre-Registration (Romeo Review)                 │
│   Lock PRE_REGISTRATION.md to git.                      │
│   Romeo reviews hypothesis + thresholds + methodology.  │
│   REVISION 2 pending Romeo re-sign-off before code.     │
├─────────────────────────────────────────────────────────┤
│ Gate 1: Sample Adequacy (Cohort A only)                 │
│   - N ≥ 80 events                                       │
│   - Unique T_ex dates ≥ 30                              │
│   - Top-3 date concentration ≤ 30%                      │
│   - Notice→T_ex gap distribution documented             │
│   - Cohort B N ≥ 20 (attribution feasibility)           │
│   If fail → pause. Do not run H1.                       │
├─────────────────────────────────────────────────────────┤
│ Gate 2: Independence Documentation                      │
│   Compute Cohort B overlap rate.                        │
│   If ≥ 50%, banner H1 result: "structurally weak."      │
│   Not a kill condition; disclosure requirement.         │
├─────────────────────────────────────────────────────────┤
│ Gate 3: H1 Primary Test (Cohort A, block-bootstrap)     │
│   Success (ALL three required):                         │
│     - Mean excess return ≤ −1.0%                        │
│     - Hit rate ≥ 60%                                    │
│     - 95% bootstrap CI excludes zero (negative side)    │
│   Failure (ANY triggers): < 55% hit OR > −0.5% return   │
│     OR CI includes zero                                 │
│   Historical pass ≠ promotion. Still needs forward.     │
├─────────────────────────────────────────────────────────┤
│ Gate 4: Forward Evidence Gate                           │
│   Post-pre-registration N ≥ 25 forward-resolved cases.  │
│   Forward test must also pass success criteria.         │
├─────────────────────────────────────────────────────────┤
│ Gate 5: Audit + Romeo Review                            │
│   6-class audit (like persistence audit) before canon.  │
└─────────────────────────────────────────────────────────┘
```

No gate can be skipped. No gate can be softened mid-flight. "Historical pass" is not a trading signal — forward evidence is a separate gate.

---

## Folder Layout (Planned)

```
experiments/dividend-microstructure/
├── README.md                       ← this file
├── CONTRACT.md                     ← protocol contract
├── RESEARCH_BRIEFING.md            ← literature foundation
├── PRE_REGISTRATION.md             ← pinned hypothesis (pending)
├── build_event_table.py            ← Step 1 (pending)
├── check_gate1.py                  ← Gate 1 decision (pending)
├── run_h1.py                       ← Step 3 (pending, AFTER pre-reg)
├── run_diagnostic.py               ← secondary windows (pending)
├── data/                           ← pre-processed events
│   ├── event_table.csv
│   └── overlap_analysis.json
├── results/                        ← test outputs
└── alerts/                         ← only if thresholds breached
```

---

## What NOT To Do

- Do NOT run H1 before Gate 1 passes.
- Do NOT change the primary window after seeing results.
- Do NOT add H2/H3/H4 tests until H1 has been fully evaluated.
- Do NOT build the broker-flow layer yet.
- Do NOT update LEARNINGS.md from this experiment until Romeo review.
- Do NOT expand universe beyond banks + hydros.

All of these are failure modes documented in Section 5 of the research briefing.

---

## Kill Condition

Delete this folder. Nothing else breaks. See `CONTRACT.md`.

---

## Next Step

PRE_REGISTRATION revision 3 is written. Awaiting Romeo final sign-off. After sign-off:

1. Write `build_event_table.py` (Step 1, pulls L-001 corp action data + computes T_ex per event + applies hard drops).
2. Write `check_gate1.py` (Gate 1 sample-adequacy decision).
3. If Gate 1 passes: write `run_h1.py` (block-bootstrap H1 test on Cohort A + diagnostic windows).
4. H1 decision point: pass / intermediate / fail per pre-registered criteria.

Until Romeo signs off on revision 3, no code in this folder runs.
