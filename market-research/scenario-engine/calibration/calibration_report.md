# Calibration Report — NEPSE Scenario Engine

Fill this in quarterly. Pull numbers from `brier_log.csv`. Goal: check whether our stated probabilities match our actual hit rates over time.

---

## Q2 2026 (May 8 → Jul 31)

**Predictions resolved this quarter:** 0 (too early — earliest resolution Jun 4)
**Predictions active:** 6

*Fill in after Jun 4 when PRED-004 (Chachan arrest) resolves.*

---

## Template for each quarterly entry

```
## Q[N] [Year] ([start date] → [end date])

**Predictions resolved:** N
**Aggregate Brier score:** X.XX (lower = better; random baseline = 0.25)

### Calibration by bucket

| Forecast bucket | Predictions | Resolved YES | Expected rate | Actual rate | Error |
|---|---:|---:|---:|---:|---:|
| 0–20% | N | N | 10% | X% | +/-X% |
| 20–40% | N | N | 30% | X% | +/-X% |
| 40–60% | N | N | 50% | X% | +/-X% |
| 60–80% | N | N | 70% | X% | +/-X% |
| 80–100% | N | N | 90% | X% | +/-X% |

### Findings
- Strength: [bucket where calibration is good]
- Weakness: [bucket where we are over/underconfident]
- Systematic bias: [e.g., "overconfident on enforcement predictions"]

### Action
- [specific adjustment to future forecasts in the weak bucket]
- [any category where base rates need rechecking]

### Post-mortem on resolved predictions
[For each PRED that resolved this quarter: was the reasoning right, or was the outcome lucky?]
```

---

## Running calibration manually

From `brier_log.csv`:
1. Filter rows where `outcome` is not null
2. Group by `forecast_prob` into buckets (0-.2, .2-.4, .4-.6, .6-.8, .8-1)
3. For each bucket: `actual_rate = count(outcome=1) / count(all in bucket)`
4. `calibration_error = actual_rate - bucket_midpoint`
5. `aggregate_brier = mean(brier_score) for all resolved rows`

If calibration_error is positive → underconfident in that bucket (events happen more than we think)
If calibration_error is negative → overconfident in that bucket (events happen less than we think)
