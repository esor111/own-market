# Reversal Specialist

> Tier 1 sandbox under `SANDBOX_PROTOCOL.md`. Layer 3 experiment.
> Tests whether NEPSE stocks mean-revert after sharp single-day price moves.

---

## Status

**Lane CLOSED (2026-04-19) — Gate 1 failed on primary direction. No H1 will be run.**

Timeline:
- 2026-04-18 morning: scaffold + revision 1 drafted.
- 2026-04-18 afternoon: Romeo first review → revision 2 (5 methodology findings).
- 2026-04-18 late afternoon: Romeo second review → revision 3 (2 measurement fixes).
- 2026-04-18 evening: Romeo third review → revision 4 (4 consistency items).
- 2026-04-19 morning: Romeo APPROVED revision 4. Gate 1 run authorized.
- 2026-04-19: `build_trigger_events.py` produced 1,098 raw trigger candidates across 26 symbols. `check_gate1.py` verdict = **FAIL** on primary direction (N=66 < 80). Per pre-reg, lane closed.

## Gate 1 Outcome

| Direction | N (h1-eligible) | Required | Verdict |
|---|---:|---:|---|
| Sharp-down (primary H1) | **66** | ≥ 80 | **FAIL** |
| Sharp-up (secondary H1b) | 258 | ≥ 80 | PASS (but non-promotion) |

**Every other Gate 1 criterion passed comfortably** for the primary direction:
- Unique trigger dates: 62 (need ≥30) — 2x the gate
- Top-3 concentration: 9.1% (need ≤30%) — excellent dispersion
- Symbol spread: 17 (need ≥5)

The failure is purely sample-size. The mechanism may be real; the data doesn't support properly-powered inference on NEPSE's banks + hydros + allied sectors in 2021-2026.

## What The Funnel Tells Us About NEPSE Microstructure

```
Raw sharp-down candidates:      333
Volume-threshold failures:      134  (thin-market artifacts)
Near-price-limit / circuit:      64  (circuit-breaker adjacent)
Layer B market-wide shock:      178  (53% were regime events, not idiosyncratic)
Layer A regime date:              2
Corporate-action overlap:        16
Passed filters:                  68
Forward-window / baseline gap:    2 + 50
H1-eligible:                     66   ← below the 80 threshold
```

The dominant cut is Layer B: over half of "raw" sharp-down days were market-wide, not idiosyncratic. The rest of the funnel (volume, price-limit, corp-action) removed thin-market and mechanical-adjustment noise. After all filters, NEPSE's true idiosyncratic sharp-down event rate is ~13 per year per symbol-set combined. That's not enough for a properly-powered reversal test with N≥80 requirement.

## What's Preserved

- Full research foundation in `PRE_REGISTRATION.md` revision 4
- Event table at `data/trigger_events.csv` (1,098 rows)
- Gate 1 decision memo at `data/gate1_decision.md`
- Gate-drift diagnostic (2.7% drift — small)
- All code and configuration

If in the future (a) the NEPSE universe expands to more symbols, (b) the pre-registered threshold is explicitly revised via a new pre-registration (NOT a post-hoc relax), or (c) an alternative trigger definition is tried, the infrastructure is here and ready. The decision to run H1 again would require a NEW pre-registration going through the same Romeo-review cycle.

## What's NOT Preserved (Explicitly)

- H1 historical test did not run and will not run from revision 4.
- H1b sharp-up secondary is not run — pre-reg made it non-promotion-grade from the start, and Romeo authorized only Gate 1, not H1b.

The experiment did its job: pre-registration + strict gating caught an under-powered test in 1 session of code.

Once signed off, the flow is: build_trigger_events → check_gate1 → H1 (only if Gate 1 passes).

---

## Why This Exists

The lab needed a Tier 1 signal that is **structurally independent** of existing work:
- Persistence signal is about broker flow.
- Dividend-microstructure (now closed) was about corporate-action events.
- Hydro-intelligence pilot is about symbol-specific observations.
- **Reversal specialist uses only price data and no event anchoring.** Guaranteed independent.

Academic foundation: Lo-MacKinlay variance-ratio family, Jegadeesh 1990, De Bondt-Thaler 1985, plus emerging-market extensions showing **stronger reversion in small / illiquid / volatile stocks** — NEPSE's exact structural profile.

This is the experiment we pivoted to after dividend-microstructure's Gate 1 failure (see its `README.md` for context).

---

## The Core Idea In One Sentence

After a stock falls sharply in a single day (≤ −5%), it often bounces back partially over the next 5 trading days — enough to generate positive baseline-adjusted excess returns if the effect is real.

---

## Primary Hypothesis (H1)

See `PRE_REGISTRATION.md` for the exact locked statement. Informally: NEPSE symbols that have a sharp-down day (−5% or worse) tend to show **positive** baseline-adjusted excess return over [T+1, T+5], with hit rate ≥ 60%, mean excess return ≥ +1.0%, and block-bootstrap CI excluding zero.

Secondary hypothesis (H1b): same test mirrored for sharp-up days (≥ +5%) expecting **negative** excess return. Reported alongside H1 but H1 is the promotion-grade test.

---

## Gate Structure

```
Gate 0: Pre-registration (revision 4 pending final sign-off)
  Lock hypothesis + thresholds.
  Romeo rounds: round 1 done (5 findings), round 2 done (2 measurement findings), round 3 done (4 consistency items), round 4 pending — sign-off imminent.
  No code runs until sign-off.

Gate 1: Sample adequacy (per-direction)
  - N ≥ 80 trigger events
  - Unique trigger dates ≥ 30
  - Top-3 date concentration ≤ 30%
  - ≥ 5 symbols contributing ≥ 1 event each
  If any fails → lane closed.

Gate 2: H1 historical pass (all 3 required)
  - Mean excess return ≥ +1.0%
  - Hit rate ≥ 60%
  - Bootstrap 95% CI excludes zero (positive side)
  "Historical pass" is not promotion — still needs forward evidence.

Gate 3: Forward evidence
  N ≥ 25 post-pre-registration triggers with completed [T+1, T+5].
  Must satisfy the same success criteria on forward data.

Gate 4: Audit + Romeo re-review
  6-class audit before any canonical integration.
```

No gate can be skipped. No gate can be softened mid-flight.

---

## What NOT To Do

- Do NOT run Gate 1 code before Romeo signs off on pre-registration revision 4.
- Do NOT change the −5% threshold after seeing trigger counts.
- Do NOT pick the diagnostic window that looked best.
- Do NOT merge Cohort A and Cohort B style (there is no such split here; the dividend-micro failure mode doesn't apply because this signal doesn't depend on other lab signals).
- Do NOT expand symbol universe post-hoc.
- Do NOT drop the bear-market-contamination sensitivity check.

All of these would violate the pre-registration.

---

## Folder Layout

```
experiments/reversal-specialist/
├── README.md                        ← this file
├── CONTRACT.md                      ← sandbox protocol compliance
├── PRE_REGISTRATION.md              ← locked hypothesis (revision 4, awaiting Romeo final sign-off)
├── build_trigger_events.py          ← Step 1: detect sharp-move events
├── check_gate1.py                   ← Step 2: Gate 1 sample-adequacy decision
├── data/                            ← trigger event table + Gate 1 output (created on first run)
└── results/                         ← H1 output (created only if Gate 1 passes)
```

---

## Kill Condition

Delete this folder. Nothing else breaks. See `CONTRACT.md`.

---

## Next Step

Send `PRE_REGISTRATION.md` revision 4 to Romeo for final sign-off. Revision 4 integrates Romeo's third-review findings (Layer B wording consistency, stale revision 1 text in check_gate1.py, gate-drift diagnostic, baseline-method alignment with H1). Romeo said "Revise small items, then sign off" — sign-off is imminent. On sign-off, run `build_trigger_events.py` then `check_gate1.py`, then make the Gate 1 decision.
