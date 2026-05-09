# Scenario Engine — Master Index

---

## Active Scenario Trees

| File | Created | Context | Scenarios | Status |
|---|---|---|---|---|
| [2026-05-08__nepse-cleanup-cycle](scenarios/2026-05-08__nepse-cleanup-cycle.md) | 2026-05-08 | Day 33 of structural cleanup; NEPSE 2,712 | A(40%) B(25%) C(12%) D(8%) E(5%) F(10%) | ACTIVE |

---

## Predictions

| ID | Question (short) | P | Created | Resolves | Status | Outcome | Brier |
|---|---|---:|---|---|---|---|---:|
| [PRED-001](predictions/PRED-001__nepse-retest-2511.md) | NEPSE retests 2,511-2,620 before 2,900 | 65% | 2026-05-08 | 2026-12-31 | active | — | — |
| [PRED-002](predictions/PRED-002__second-arrest-fires.md) | Second major arrest by Nov 8 | 70% | 2026-05-08 | 2026-11-08 | active | — | — |
| [PRED-003](predictions/PRED-003__nabil-595-610.md) | NABIL ≥ Rs 595 by Aug 5 | 60% | 2026-05-08 | 2026-08-05 | active | — | — |
| [PRED-004](predictions/PRED-004__chachan-arrest-jun4.md) | Chachan arrested by Jun 4 | 80% | 2026-05-08 | 2026-06-04 | active | — | — |
| [PRED-005](predictions/PRED-005__nepse-recovery-24m.md) | NEPSE recovery takes >24 months | 70% | 2026-05-08 | 2028-03-24 | active | — | — |
| [PRED-006](predictions/PRED-006__nepse-analog-trough.md) | NEPSE closes ≤ 1,800 by Dec 2028 | 40% | 2026-05-08 | 2028-12-31 | active | — | — |

---

## Calibration summary

| Quarter | Predictions resolved | Aggregate Brier | Notes |
|---|---:|---:|---|
| Q2 2026 (May–Jul) | 0 | — | PRED-004 resolves Jun 4 |
| Q3 2026 (Aug–Oct) | 0 | — | PRED-003 resolves Aug 5 |

*Update this table as predictions resolve. Full calibration analysis in [calibration/calibration_report.md](calibration/calibration_report.md).*

---

## How to add a new prediction

1. Copy any existing PRED file as template
2. Assign next ID (PRED-007, etc.)
3. Fill PREDICTED section fully — do not leave reasoning blank
4. Add row to the Predictions table above
5. Add row to `calibration/brier_log.csv`

## How to resolve a prediction

1. Open the PRED file, fill OBSERVED section
2. Update status in Predictions table: `active → resolved`
3. Fill Outcome (YES/NO) and Brier score columns
4. Update `brier_log.csv`
5. Add to Calibration summary table if that quarter hasn't been totaled yet

## How to add a new scenario tree

1. Create `scenarios/YYYY-MM-DD__slug.md`
2. Add row to Active Scenario Trees table above
3. List related PRED IDs in the scenario file
