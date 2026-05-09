# Experiment Contract: signal-decay-tracker

## Purpose

Monitor the persistence shadow signal's hit rate over rolling windows and alert when recent performance materially decays from the all-time baseline. Protects against silent signal degradation between batch-score gates.

---

## Inputs (read-only paths)

- `market-gist/data/validation/persistence_shadow_reviews/latest__shadow_batch_cases_v1.csv`
- `market-gist/data/validation/persistence_shadow_reviews/latest__shadow_batch_scorecard_v1.json`

Reads nothing outside Layers 1 and 2.

---

## Outputs (paths this experiment writes to)

- `experiments/signal-decay-tracker/results/decay_<YYYY-MM-DD>.json` — structured snapshot
- `experiments/signal-decay-tracker/results/decay_<YYYY-MM-DD>.md` — human-readable report
- `experiments/signal-decay-tracker/results/latest.json` — most recent snapshot (convenience)
- `experiments/signal-decay-tracker/results/latest.md` — most recent report (convenience)
- `experiments/signal-decay-tracker/alerts/<YYYY-MM-DD>_<severity>.md` — only if thresholds breached

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

Delete `experiments/signal-decay-tracker/`. Nothing else breaks.

**What depends on this:** nothing. The tracker is read-only; no production or experimental code imports it.

---

## Runnable As

```
python experiments/signal-decay-tracker/run.py
```

No required flags. Optional flags:
- `--window N` — rolling window size (default 5, also reports 10 and 20)
- `--dry-run` — print report but do not write files

NOT invoked by the production daily routine. Run weekly or after each batch-score update.

---

## Forward Evidence Gate

Decay detection becomes statistically meaningful at N ≥ 20 resolved cases. Below that, the tracker reports descriptive statistics only and flags "insufficient sample for decay inference."

Current resolved case count: 20 total across all groups, 11 in `persistence_caution_only` (as of 2026-04-19, per `latest__shadow_batch_scorecard_v1.json`). Below the gate (N≥25 in `persistence_caution_only` per `batch-score-playbook/INTERPRETATION_GATE.md` v3).

---

## Naming

All alerts output by this experiment use the prefix `x-decay-`:
- `x-decay-persistence-caution-yellow` — 10pp rolling drop
- `x-decay-persistence-caution-orange` — 20pp drop OR hit rate falls below 60%
- `x-decay-persistence-caution-red` — 30pp drop OR hit rate near 50% coin-flip

---

## Output File Header

Every output markdown and JSON file begins with:

```
⚠️ EXPERIMENTAL SIGNAL — shadow only, not a trading decision.
Experiment: signal-decay-tracker
Forward evidence: N=<current> / required=20
Layer: 3 (research)
```

---

## Romeo / Benvolio Verification Status

- **Designed by:** Juliet, 2026-04-13
- **Reviewed by Romeo:** pending
- **Reviewed by Benvolio:** pending
- **Promotion path status:** pre-evidence (tracker does not itself predict; it monitors another signal's decay)

Note: this experiment's verdict is its own output's reliability, not a tradeable signal. It does not need the full 6-step promotion path; it needs Romeo to confirm the decay thresholds are sensible.
