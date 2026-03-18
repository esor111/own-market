# Web-Validated Reliability Requirements

**Date:** March 18, 2026  
**Purpose:** Define the minimum additional work required to make the current system meaningfully more reliable, using both the current codebase and outside validation sources  
**Rule:** This is not a feature wishlist. It is the smallest serious list that moves the project toward high reliability.

---

## 1. Honest Framing

No market prediction system becomes "100% certain."

What we can do is move toward:

- high extraction reliability
- high traceability
- high decision consistency
- calibrated confidence
- lower odds of false confidence

That is the right target.

---

## 2. What Outside Sources Confirm

### A. Technical analysis needs systematization

Lo, Mamaysky, and Wang showed that technical analysis can have practical value, but one of the main problems is its subjectivity. Their conclusion supports turning chart reading into a systematic process instead of ad hoc human interpretation.

Implication for this project:

- support/resistance cannot stay vague
- setup rules must be explicit
- chart interpretation must be reproducible

### B. Time-ordered validation is mandatory

Scikit-learn's `TimeSeriesSplit` documentation explicitly warns that ordinary cross-validation is inappropriate for time-ordered data because it can train on future data and evaluate on past data.

Implication for this project:

- any scoring or predictive model must be validated in time order
- random train/test splitting is not acceptable
- outcome tracking must preserve chronology

### C. Confidence must be calibrated, not guessed

Scikit-learn's calibration guidance explains that model probabilities can be badly estimated even when predictions look reasonable.

Implication for this project:

- a confidence score like `70%` cannot remain a hand-crafted number forever
- confidence must eventually be compared against real outcomes
- predicted confidence and realized hit rate must be measured together

### D. Backtests are easy to overfit

Bailey, Borwein, Lopez de Prado, and Zhu show that backtests can overfit easily, and that in-sample selection often fails out of sample.

Implication for this project:

- we cannot trust good-looking historical logic by itself
- each added rule or filter increases overfitting risk
- symbol-wide and date-wide validation is required before stronger claims

### E. Reliability requires governance, measurement, and monitoring

The NIST AI RMF emphasizes that trustworthy systems must be valid and reliable, documented, measured, monitored in production-like settings, and regularly reviewed.

Implication for this project:

- every run needs evidence and documentation
- every decision needs QC
- every deployed rule needs review against later results

---

## 3. Exact Required Work From Here

These are the smallest serious requirements that remain.

### 1. Extract multi-bar structure inputs, not just current chart state

Current limitation:

- the system mostly relies on the current candle, current OHLC, and current indicator values

Required result:

- store recent visible swing highs
- store recent visible swing lows
- store local range boundaries
- store whether the structure is compression, range, trend continuation, or trend break

Reason:

- without multi-bar structure, support/resistance is too naive
- this is the main blocker to trustworthy setup levels

### 2. Upgrade structure logic from "nearest level" to "validated structure"

Current limitation:

- levels can still be too close to price
- one-candle logic can still produce weak entries and targets

Required result:

- derive support/resistance from repeated reactions, not one reading
- derive breakout levels from visible range boundaries
- derive invalidation from structure failure, not a generic percent offset
- emit `structure_confidence = low` when the chart does not provide enough evidence

Reason:

- this is how we reduce subjectivity without pretending certainty

### 3. Add a hard QC gate before decision output

Current limitation:

- a run can succeed technically while the trade plan is still weak

Required result:

- reject or downgrade outputs when structure is weak
- reject or downgrade outputs when `risk_reward_ratio < 1`
- reject or downgrade outputs when entry and target are trivial
- reject or downgrade outputs when evidence is incomplete or contradictory

Reason:

- runtime success is not analysis quality

### 4. Build time-ordered outcome tracking

Current limitation:

- the system stores decisions, but not enough realized follow-up for validation

Required result:

- for each run, later store:
  - whether invalidation was hit
  - whether target 1, 2, or 3 was hit
  - how long it took
  - what the max favorable and adverse excursion looked like

Reason:

- without this, confidence remains opinion
- this is required for walk-forward validation

### 5. Calibrate confidence against realized outcomes

Current limitation:

- current confidence is still hand-built

Required result:

- compare predicted confidence buckets against actual hit rates
- adjust scoring so `70%` means something close to observed reality
- treat confidence as a monitored metric, not a presentation field

Reason:

- this is the step that turns "looks sensible" into "measured reliability"

### 6. Replace hard-coded symbol-to-sector assumptions

Current limitation:

- sector lookup is still hard-coded in the script

Required result:

- move sector lookup into a maintained data file
- make missing-sector cases explicit instead of silently defaulting

Reason:

- silent defaults weaken reliability and generality

### 7. Run repeated cross-symbol validation before stronger claims

Current limitation:

- we have individual verified runs, but not broad validation

Required result:

- test the same workflow across many symbols
- compare whether the outputs remain symbol-specific and sensible
- review failure patterns by setup type, sector, and timeframe

Reason:

- a system that works on one symbol is still unproven

---

## 4. What Is Not Required Yet

These are still not required for the next reliability stage:

- full drawing-tool automation
- Fibonacci automation
- pattern libraries
- broker-flow intelligence
- OCR
- machine learning models
- dashboards
- notifications
- advanced forecasting tools

These can help later, but they are not the current bottleneck.

---

## 5. Exact Next Build Order

If we stay disciplined, the next build order should be:

1. extract multi-bar structure inputs
2. upgrade structure-derived levels
3. add a hard QC gate
4. replace sector hard-coding
5. start outcome tracking
6. calibrate confidence after enough outcomes exist
7. validate across many symbols and dates

---

## 6. What "10/10" Means Here

For this project, "10/10" does **not** mean perfect prediction.

It means:

- the system extracts evidence consistently
- decisions are traceable
- weak setups are filtered out
- confidence is measured against actual outcomes
- rules survive time-ordered validation

That is the highest honest target.

---

## 7. Sources

1. Andrew W. Lo, Harry Mamaysky, and Jiang Wang, *Foundations of Technical Analysis: Computational Algorithms, Statistical Inference, and Empirical Implementation*  
   [https://business.columbia.edu/sites/default/files-efs/pubfiles/19268/Lo-Mamaysky_wang_foundations.pdf](https://business.columbia.edu/sites/default/files-efs/pubfiles/19268/Lo-Mamaysky_wang_foundations.pdf)

2. scikit-learn, `TimeSeriesSplit` documentation  
   [https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)

3. scikit-learn, probability calibration documentation  
   [https://scikit-learn.org/stable/modules/calibration.html](https://scikit-learn.org/stable/modules/calibration.html)

4. David H. Bailey, Jonathan M. Borwein, Marcos Lopez de Prado, and Qiji Jim Zhu, *The Probability of Backtest Overfitting*  
   [https://carmamaths.org/jon/backtest2.pdf](https://carmamaths.org/jon/backtest2.pdf)

5. NIST AI RMF 1.0  
   [https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf)
