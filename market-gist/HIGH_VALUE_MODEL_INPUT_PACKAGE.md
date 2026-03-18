# High-Value Model Input Package

**Date:** March 18, 2026  
**Purpose:** Define the exact high-value feature package that should be fed into a stronger reasoning model for lower-entropy NEPSE prediction

---

## 1. What This Document Is

This is the bridge between:

- the current Playwright automation pipeline
- and a stronger reasoning model such as GPT or Claude

The purpose is not to send raw screenshots and ask a powerful model to "figure it out."

The purpose is to feed a stronger model:

- structured evidence
- multi-timeframe context
- event context
- quality flags
- a reduced-entropy decision package

This should improve reasoning quality without pretending that reasoning alone creates prediction accuracy.

---

## 2. First Principle

A stronger model is most useful when it receives:

- fewer but better features
- explicit confidence/quality flags
- clear market context
- clear invalidation
- clear event timing

It is least useful when it receives:

- messy screenshots without extracted state
- too many duplicated indicators
- decorative chart-tool output
- unsupported confidence claims

So the model-input package should be:

**small enough to reason over cleanly, rich enough to reduce ambiguity**

---

## 3. The 3 Most Important Additions

If we add only what truly matters, the next package should introduce:

### 1. Multi-timeframe context

At minimum:

- `1W`
- `1D`
- optional setup timeframe such as `4H` or `1H` later

Why:

- the same chart can look bullish on one timeframe and weak on another
- setup quality improves a lot when higher timeframe and setup timeframe align

### 2. Official event/corporate-action context

At minimum:

- rights issue
- bonus share
- book closure
- AGM
- major official company notice

Why:

- these events can distort or dominate technical interpretation in NEPSE

### 3. Better model-ready feature packaging

The stronger model should receive:

- normalized fields
- explicit quality flags
- ranked confluence
- explicit unanswered questions

Why:

- this reduces narrative drift
- this makes reasoning auditable

---

## 4. What The Stronger Model Should Actually Receive

The model-input package should be one record per symbol per run.

That record should have six sections:

1. Market context
2. Sector context
3. Multi-timeframe stock context
4. Event context
5. Quality and uncertainty flags
6. Decision-ready synthesis inputs

---

## 5. Market Context Section

These features are high value and should always be included:

```json
{
  "market": {
    "symbol": "NEPSE",
    "timeframe": "1D",
    "close": 2739.95,
    "change_pct": -0.65,
    "trend_label": "down",
    "market_phase": "pullback",
    "support_levels": [2700, 2650],
    "resistance_levels": [2770, 2820],
    "structure_confidence": "medium"
  }
}
```

Why this matters:

- many stock setups fail simply because the overall market is weak

---

## 6. Sector Context Section

These should also always be included:

```json
{
  "sector": {
    "name": "BANKING",
    "timeframe": "1D",
    "close": 1476.19,
    "change_pct": -0.56,
    "trend_label": "down",
    "relative_strength_vs_market": "slightly_stronger",
    "structure_confidence": "medium"
  }
}
```

Why this matters:

- stock strength is more meaningful when compared with its sector

---

## 7. Multi-Timeframe Stock Context

This is the most important new layer.

The stronger model should not receive only one timeframe.

It should receive a compact structure for each timeframe:

### Recommended minimum

- `1W`
- `1D`

### Optional later

- `4H` or `1H` for entry refinement

### Example structure

```json
{
  "timeframes": {
    "1W": {
      "close": 351.5,
      "trend_label": "bullish",
      "structure_label": "continuation",
      "support_zones": [[333, 341]],
      "resistance_zones": [[358, 368]],
      "breakout_level": 358.5,
      "invalidation_level": 333.0,
      "ema_20": 247.61,
      "ma_50": 244.24,
      "rsi": 54.05,
      "macd_histogram": -0.65,
      "volume_participation": "healthy",
      "structure_confidence": "medium"
    },
    "1D": {
      "close": 349.2,
      "trend_label": "bullish",
      "structure_label": "pullback_holding",
      "support_zones": [[343, 346]],
      "resistance_zones": [[352, 358]],
      "breakout_level": 352.0,
      "invalidation_level": 342.8,
      "ema_20": 346.1,
      "ma_50": 339.8,
      "rsi": 57.2,
      "macd_histogram": 1.2,
      "volume_participation": "average",
      "structure_confidence": "medium"
    }
  }
}
```

---

## 8. Multi-Timeframe Derived Features

We do not want the stronger model to infer everything from raw fields.

We should compute a few high-value derived features first.

These are the best ones:

### A. Higher timeframe alignment

```json
{
  "higher_timeframe_alignment": "aligned_bullish"
}
```

Allowed values:

- `aligned_bullish`
- `aligned_bearish`
- `mixed`
- `higher_tf_conflict`

### B. Structure agreement

```json
{
  "structure_agreement": "weekly_and_daily_supportive"
}
```

### C. Trigger readiness

```json
{
  "trigger_readiness": "near_breakout_but_not_confirmed"
}
```

### D. Invalidation quality

```json
{
  "invalidation_quality": "clear"
}
```

Allowed values:

- `clear`
- `acceptable`
- `weak`

### E. Trade quality summary

```json
{
  "trade_quality": "good_but_needs_confirmation"
}
```

These fields reduce model entropy a lot.

---

## 9. Event Layer

This is the second major addition that truly matters.

The event layer should use official or high-confidence sources only.

### High-value event fields

```json
{
  "event_context": {
    "has_active_event": true,
    "event_type": "rights_issue",
    "event_date": "2026-03-05",
    "days_since_event": 13,
    "event_sentiment": "mixed",
    "event_status": "active_window",
    "impact_window_days": 45,
    "corporate_action_flags": {
      "rights_issue": true,
      "bonus_share": false,
      "book_closure": true,
      "agm": false
    },
    "event_confidence": "high"
  }
}
```

### Why this is important

- event timing can change whether a breakout is meaningful or just event noise
- the stronger model should not have to guess whether price is reacting to a catalyst

---

## 10. Quality and Uncertainty Flags

This section is very important.

The stronger model should know what is strong and what is weak.

Example:

```json
{
  "quality_flags": {
    "market_data_quality": "high",
    "sector_data_quality": "high",
    "stock_structure_quality": "medium",
    "indicator_quality": "medium",
    "event_data_quality": "low",
    "outcome_history_quality": "low"
  },
  "uncertainties": [
    "event layer missing official notice for current run",
    "weekly resistance cluster is broad",
    "no calibrated hit-rate history yet"
  ]
}
```

This is essential because a strong model is better when uncertainty is explicit.

---

## 11. Decision-Ready Synthesis Fields

The stronger model should receive a final compact synthesis block too.

Example:

```json
{
  "decision_inputs": {
    "setup_type": "continuation",
    "score": 68,
    "confidence": 78,
    "action": "buy",
    "entry_zone": [343, 352],
    "stop_loss": 333,
    "targets": [368, 380, 391],
    "risk_reward_ratio": 2.4,
    "qc_status": "pass",
    "qc_findings": []
  }
}
```

This gives the stronger model a clean starting point for reasoning:

- agree
- disagree
- qualify
- rank
- produce a more thoughtful thesis

---

## 12. Exact Model-Input Package Shape

This is the recommended top-level package:

```json
{
  "session_id": "2026-03-18__EBL__v2",
  "run_date": "2026-03-18",
  "symbol": "EBL",
  "primary_horizon": "swing",
  "market": {},
  "sector": {},
  "timeframes": {
    "1W": {},
    "1D": {}
  },
  "derived_alignment": {},
  "event_context": {},
  "quality_flags": {},
  "uncertainties": [],
  "decision_inputs": {},
  "evidence_refs": []
}
```

This should be the package sent to the stronger reasoning model.

---

## 13. What We Should Not Feed The Stronger Model

Avoid feeding:

- every screenshot without structure
- decorative annotation data
- too many indicators
- duplicate momentum signals
- unsupported narratives
- giant raw DOM dumps

Those increase entropy instead of reducing it.

---

## 14. What We Have Right Now

Current project state:

- raw chart extraction exists
- market and sector capture exist
- single-timeframe structure and indicators exist
- decision and QC exist
- outcome and follow-up layers exist

Current missing pieces for this package:

- multi-timeframe stock records
- official event feature extraction
- dedicated model-input record generation

That means the current system is a good base, but this package is not fully produced yet.

---

## 15. What Matters Most For Prediction

If the question is:
"What should the stronger model rely on most?"

The answer is:

1. market regime
2. sector alignment
3. weekly structure
4. daily structure
5. event timing
6. invalidation quality
7. quality flags

Not:

- extra drawing tools
- too many indicators
- fancy chart annotations

---

## 16. Honest Expectation

This package will improve reasoning quality.

It will:

- reduce ambiguity
- reduce hallucinated chart stories
- make stronger-model output more consistent
- make later calibration easier

It will not magically create perfect prediction.

Prediction quality will still depend on:

- real outcome history
- calibrated scoring
- data quality

---

## 17. Smart Next Build Order

The smartest next implementation sequence is:

1. add multi-timeframe extraction and storage
2. add official event record extraction
3. add `model_input` record generation
4. feed that record to the stronger reasoning model
5. compare model judgment against later outcomes

That is the lowest-entropy path forward.

