---
id: PRED-001
status: active
created: 2026-05-08
resolution_date: 2026-12-31
forecast_prob: 0.65
outcome: null
brier_score: null
category: market_structure
source_dossier: seventh-dossier
---

# PRED-001 — NEPSE retests 2,511-2,620 zone before any recovery above 2,900

## PREDICTED (2026-05-08)

### Question
Will NEPSE close at or below 2,620 at least once before closing at or above 2,900 — all within 2026?

### Resolution criteria
- **YES (outcome=1):** NEPSE daily close ≤ 2,620 occurs BEFORE any daily close ≥ 2,900, by Dec 31, 2026
- **NO (outcome=0):** NEPSE closes ≥ 2,900 before ever touching ≤ 2,620, OR year ends without either event
- **Data source:** ShareSansar daily or HimalPress end-of-day NEPSE index figure
- **Ambiguity:** If both happen on the same session (impossible given the gap), use intraday sequence. If Dec 31 passes with neither, outcome = 0.

### Probability: 65%

### Reasoning at prediction time

NEPSE is at 2,712 on May 8, 2026. The 2,511-2,620 zone is the Sep-2025 structural support — the trough from the prior Gen-Z protest correction.

Arguments FOR (YES, 65%):
- Analog mean drawdown is −42% from peak (2,960). That implies a trough around 1,720. Even if Nepal's cleanup is shallower, touching 2,511-2,620 is implied by any analog that goes deeper than −9%.
- We are only 8.5% off peak. Vietnam and Bangladesh both went significantly further. The analog says we're early.
- Vietnam clock: second arrest in next 4-6 months (Scenario A) would accelerate selling. That would easily push NEPSE through 2,620.
- Current breadth: A/D 0.11. Extreme one-sidedness typically precedes further deterioration, not reversal.
- Deployment trigger not close to firing: turnover Rs 4.26B vs Rs 6B required. No bottom signal.

Arguments AGAINST (NO, 35%):
- Scenario C (quick resolution, 12%): clean chairman + no second arrest → breadth recovers fast → 2,900 before 2,511
- NEPSE has historically had strong retail buying on dips; 2,511-2,620 might attract buyers before we touch it
- If Bhrikuti resolution is fast and structured (W4 fires positively), forced selling ends sooner than expected

**Base rate:** 4 of 4 matched analogs saw the index go well below their equivalent "prior correction trough" before recovery. This prediction requires only that NEPSE touches 2,511-2,620 — not that it goes to 1,720. The base rate supports YES strongly.

---

## OBSERVED (fill in after Dec 31, 2026 or earlier if resolves)

**Resolution date:**
**Date recorded:**
**Actual outcome:** YES / NO
**Evidence:** [ShareSansar date + NEPSE close figure]
**Brier score:** ( [forecast_prob] - [outcome] )² =

### Post-mortem

**Was the reasoning right?**

**Luck vs skill:**
- Skill (reasoning quality):
- Luck (factors I couldn't control):

**What to update for future predictions:**
