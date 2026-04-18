# Signal Decay Tracker

> First reference sandbox under `SANDBOX_PROTOCOL.md`. Layer 3 experiment.
> Monitors the persistence shadow signal's rolling hit rate and alerts on decay.

---

## Why This Exists

The persistence signal currently shows 88.9% hit rate on 9 resolved CAUTION cases. The published broker-flow literature ceiling is ~53%. Nepal's data-quality advantage gets us maybe to ~58% theoretical. Our 88.9% is 30+ pp above the most generous ceiling — which means either (a) the signal is genuinely novel, (b) it's clustered/overfit (L-012 suggests this), or (c) it will decay as more forward cases arrive.

This tracker watches for (c). Weekly. Without touching the production lane.

---

## What It Does

1. Reads the scorecard cases CSV (all verdicts + forward outcomes to date).
2. Filters to resolved cases only, grouped by `group_key`.
3. For each group:
   - Computes overall hit rate (baseline)
   - Computes rolling hit rate over last 5, 10, 20 cases
   - Measures sample concentration (how many unique report dates, Gini coefficient)
4. Flags decay when rolling-window hit rate drops materially below baseline.
5. Writes a markdown report and (if breached) an alert file.

---

## Severity Tiers

| Severity | Trigger |
|---|---|
| **YELLOW** | Rolling-5 hit rate drops >10pp below all-time baseline OR rolling-5 falls below 65% |
| **ORANGE** | Rolling-5 drops >20pp below baseline OR rolling-5 falls below 55% |
| **RED** | Rolling-5 drops >30pp below baseline OR rolling-5 falls below 50% (coin flip) |

Thresholds are intentionally conservative. At N < 20 resolved cases, tracker reports descriptive stats only and does not fire alerts.

---

## How To Run

```
python experiments/signal-decay-tracker/run.py
```

Produces:
- `results/decay_<date>.json` + `.md`
- `results/latest.json` + `.md` (same content, latest overwrite)
- `alerts/<date>_<severity>.md` (only if a tier is breached)

---

## What To Do With The Output

Read `results/latest.md` weekly. If nothing is flagged, close the file and move on.

If an alert fires:
- **YELLOW:** log it, monitor the next week. No action.
- **ORANGE:** review the specific cases that dropped hit rate. Flag to Romeo.
- **RED:** pause any new promotion discussion. Open a formal audit.

---

## Kill Condition

Delete this folder. Nothing else breaks. See `CONTRACT.md`.

---

## Future Extensions (Not Built)

- Track multiple signals beyond persistence (dividend annotation, future Tier 1 signals)
- Decay-aware Bayesian prior updating
- Cross-signal correlation decay (do our signals start agreeing more as the market adapts?)

None of these are built yet. Keep the first version simple.
