# Signal Decay Tracker

> First reference sandbox under `SANDBOX_PROTOCOL.md`. Layer 3 experiment.
> Monitors the persistence shadow signal's rolling hit rate and alerts on decay.

---

## Why This Exists

The persistence signal currently shows a hit rate of 72.7% on 11 resolved CAUTION cases (binomial p ≈ 0.11 — directionally suggestive, not statistically significant at this N; per `LEARNINGS.md` L-012 addendum 2026-04-18). The earlier 88.9%-on-9 headline is retired. The published broker-flow literature ceiling is ~53%; Nepal's data-quality advantage raises the plausible ceiling to ~55–58%. The current 72.7% is still above that range, but with the sample still clustered across a few report dates (L-012), the preliminary rate is expected to drift downward as more forward cases resolve. This tracker watches for that decay. Weekly. Without touching the production lane.

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
