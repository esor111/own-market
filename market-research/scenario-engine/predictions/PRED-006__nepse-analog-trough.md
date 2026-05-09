---
id: PRED-006
status: active
created: 2026-05-08
resolution_date: 2028-12-31
forecast_prob: 0.40
outcome: null
brier_score: null
category: market_structure
source_dossier: seventh-dossier
---

# PRED-006 — NEPSE reaches analog mean trough zone (~1,720-1,800)

## PREDICTED (2026-05-08)

### Question
Will NEPSE close at or below 1,800 at any point before Dec 31, 2028?

### Resolution criteria
- **YES (outcome=1):** NEPSE daily close ≤ 1,800 at any point before Dec 31, 2028
- **NO (outcome=0):** NEPSE never closes ≤ 1,800 by Dec 31, 2028
- **Data source:** ShareSansar, HimalPress — daily NEPSE index close
- **Ambiguity:** Intraday lows don't count. Close-only. 1,800 is used rather than 1,720 to give a 4.7% buffer around the analog mean (2,960 × 0.58 = 1,717; rounded to 1,720).

### Probability: 40%

### Reasoning at prediction time

**Analog mean says 42% drawdown from 2,960 peak → trough ~1,720.**

But:
- The analog mean includes some severe outliers (Bangladesh −49.5%)
- Nepal's cleanup may be shallower: broker-side only so far (Bhrikuti), not sovereign default (Sri Lanka) or full political revolution (Bangladesh/Vietnam)
- Domestic support factors: NRB can cut rates, SEBON can ease margin rules → policy tools exist
- Retail investor base is sticky (Nepal equity culture post-lockdown) — may provide support floors above analog mean

**The 40% vs 60% split:**
- 40% = full analog mean plays out (Scenario B)
- 60% = correction stays shallower than analog mean (Scenarios A, C, D)

This is the most extreme falsifiable claim in the system. If it resolves YES, it means Scenario B fully played out and we were right not to deploy early. If NO, it means our defensive positioning was slightly too conservative.

**Historical base rate:**
- 2 of 4 analogs (Bangladesh, Sri Lanka) had drawdowns >42%
- 2 of 4 analogs (Vietnam, NEPSE 2016-18) were close to 42% but not deeper
- So roughly 2-4 of 4 analogs support a 1,720 zone touch — base rate is 50-100%
- I'm using 40% because Nepal's current cycle has mitigating factors (no sovereign crisis)

**What it means for the portfolio:**
- If NEPSE approaches 2,000-2,200, re-evaluate whether Scenario B is unfolding
- If NEPSE hits 1,900 with no deployment trigger, write a new dossier — the setup has changed

---

## OBSERVED (fill in after Dec 31, 2028 or earlier if resolves)

**Resolution date:**
**Date recorded:**
**Lowest NEPSE close recorded (2026-2028):**
**Actual outcome:** YES (touched ≤1,800) / NO (stayed above 1,800)
**Date of lowest close:**
**Brier score:** ( [forecast_prob] - [outcome] )² =

### Post-mortem

**What drove the trough level — shallower or deeper than analog mean?**

**Which mitigating factors mattered most?**

**Update base rate for future analog-mean trough predictions:**
