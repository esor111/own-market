# Scenario Engine — NEPSE Research Lab

A structured prediction tracking system with calibration feedback. Combines superforecasting discipline (Brier scores, calibration buckets), pre-registration principles (reason before you see the outcome), and scenario tree logic (conditional chains, not isolated guesses).

---

## Why this exists

The `probability_stack.md` holds current beliefs. This folder answers a different question: **were those beliefs right, and are we getting better over time?**

Without this, we can always explain away being wrong. With this, we can see it.

---

## System Principles

1. **Pre/Post separation** — all reasoning written BEFORE outcome. OBSERVED section filled AFTER. Never touch the PREDICTED section after the prediction is made.
2. **Falsifiability first** — every prediction must have a specific resolution criteria, a data source to verify it, and a hard deadline.
3. **Brier score as feedback** — not just right/wrong, but were we *appropriately confident*? A 70% prediction that resolves YES is good. A 90% prediction that resolves YES barely scores better.
4. **Scenario trees over point estimates** — complex market views live in `scenarios/`, capturing the conditional chain. Individual falsifiable claims live in `predictions/`.
5. **Luck vs skill audit** — post-mortem asks: was the reasoning sound or was the outcome lucky?

---

## Folder structure

```
scenario-engine/
├── README.md                          ← this file
├── INDEX.md                           ← master table of all scenarios + predictions
├── calibration/
│   ├── brier_log.csv                  ← machine-readable per-prediction scores
│   └── calibration_report.md         ← quarterly human-readable calibration review
├── scenarios/
│   └── 2026-05-08__nepse-cleanup-cycle.md    ← conditional scenario trees
└── predictions/
    └── PRED-NNN__slug.md              ← individual falsifiable predictions
```

---

## How to add a prediction

1. Create `predictions/PRED-NNN__slug.md` using the template in any existing PRED file
2. Fill in the PREDICTED section fully — question, resolution criteria, data source, deadline, probability, reasoning
3. Add a row to `calibration/brier_log.csv` with `outcome=null` and `brier_score=null`
4. Add a row to `INDEX.md`

## How to resolve a prediction

1. Open the PRED file
2. Fill in the OBSERVED section — actual outcome, date observed, source
3. Update `brier_log.csv`: set `outcome=0` or `outcome=1`, compute `brier_score = (forecast_prob - outcome)²`
4. Update `INDEX.md` row: change status to `resolved`
5. Write a post-mortem note in the PRED file

## How to run calibration

Quarterly — open `calibration/calibration_report.md` and fill in the table from `brier_log.csv`. Group by probability bucket (0-20%, 20-40%, etc.) and check if the resolution rates match the bucket midpoints. If 60-80% bucket resolves at 90%, we're overconfident there.

## How to add a scenario tree

1. Create `scenarios/YYYY-MM-DD__slug.md`
2. Define 3-6 scenarios with probabilities summing to ~100%
3. Each scenario: trigger chain, discriminating watch signal, portfolio response, timeline
4. Add to INDEX.md scenarios table
5. Reference related PRED IDs in the scenario file

---

## Brier score quick reference

`brier_score = (forecast_prob - outcome)²`

| Forecast | Outcome | Brier |
|---:|---:|---:|
| 0.90 | 1 (correct) | 0.01 |
| 0.70 | 1 (correct) | 0.09 |
| 0.50 | 1 (correct) | 0.25 |
| 0.70 | 0 (wrong) | 0.49 |
| 0.90 | 0 (wrong) | 0.81 |

Lower = better. A random forecaster (50% on everything) averages 0.25.

---

## Connection to the rest of the research system

- `probability_stack.md` — live beliefs; source for new PRED entries
- `watch_signals.md` — each watch signal maps to a scenario discriminator
- `dossiers/` — source of reasoning; cite the dossier slug in PREDICTED section
- When a scenario fires → write a new dossier documenting the event
