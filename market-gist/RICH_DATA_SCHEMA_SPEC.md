# Rich Data Schema Specification

**Date:** March 16, 2026  
**Purpose:** Define the structured data contract for reliable Playwright-MCP-driven market analysis

---

## 1. Why This Schema Exists

This project cannot depend on markdown notes alone.

If we want reliable prediction, we need structured records that:

- preserve raw evidence
- store extracted values consistently
- support scoring
- support later backtesting
- support later outcome labeling

This schema is designed for that purpose.

---

## 2. Data Layers

The data model should use five layers:

### Layer 1: Raw Evidence
- screenshots
- page snapshots
- extracted text blocks
- tables

### Layer 2: Normalized State
- market state
- sector state
- stock state
- event state
- broker-flow state

### Layer 3: Derived Features
- trend score
- location score
- volume score
- momentum score
- relative strength score
- catalyst score

### Layer 4: Decision
- setup type
- confidence
- action
- entry
- stop
- targets

### Layer 5: Outcome
- what happened later
- target hit
- stop hit
- time to outcome

---

## 3. File and Folder Convention

Recommended folder structure:

```text
market-gist/
  data/
    raw/
      sessions/
      screenshots/
      snapshots/
      tables/
    normalized/
      sessions/
      market/
      sectors/
      candidates/
      stocks/
      indicators/
      events/
      broker_flow/
      relative_strength/
      decisions/
    features/
      setup_scores/
      model_inputs/
    outcomes/
      realized_results/
```

Recommended file naming:

```text
{run_date}__{symbol}__{timeframe}__{record_type}.json
{run_date}__{symbol}__{timeframe}__clean.png
{run_date}__{symbol}__{timeframe}__annotated.png
```

Example:

```text
2026-03-16__SMHL__1W__stock_chart.json
2026-03-16__SMHL__1W__clean.png
2026-03-16__SMHL__1W__annotated.png
```

---

## 4. Common Field Rules

Every record should use these common fields when applicable:

- `schema_version`
- `session_id`
- `run_date`
- `captured_at`
- `source`
- `symbol`
- `timeframe`
- `confidence_source`
- `evidence_refs`

### Confidence source values

Use one of:

- `direct_dom`
- `page_text`
- `table_extract`
- `visual_inference`
- `manual_note`

This helps us know which fields are strong and which are weaker.

---

## 5. Core Enumerations

### Trend labels
- `strong_bullish`
- `bullish`
- `neutral_to_bullish`
- `range`
- `neutral_to_bearish`
- `bearish`
- `strong_bearish`

### Setup types
- `breakout`
- `breakout_watch`
- `pullback`
- `reversal`
- `range_trade`
- `avoid`

### Action labels
- `buy_now`
- `wait_for_breakout`
- `wait_for_retest`
- `watch_only`
- `avoid`
- `reduce`
- `recheck_later`

### Outcome labels
- `target_1_hit`
- `target_2_hit`
- `target_3_hit`
- `stop_hit`
- `invalidated`
- `timed_out`
- `partial_success`

---

## 6. Session Record

Purpose:
- trace a complete automation run

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "captured_at": "2026-03-16T18:00:00+05:45",
  "source": "nepsealpha",
  "symbol": "SMHL",
  "status": "completed",
  "stages_completed": [
    "market_context",
    "sector_context",
    "candidate_discovery",
    "chart_capture",
    "enrichment",
    "decision"
  ],
  "stages_skipped": [],
  "notes": null
}
```

Required:
- `schema_version`
- `session_id`
- `run_date`
- `captured_at`
- `source`
- `symbol`
- `status`

---

## 7. Market Record

Purpose:
- store full-market context for the run

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "captured_at": "2026-03-16T18:02:00+05:45",
  "source": "nepsealpha",
  "symbol": "NEPSE",
  "timeframe": "1D",
  "close": 2824.90,
  "change_pct": 0.16,
  "trend_label": "neutral_to_bullish",
  "market_phase": "post_breakout_retest",
  "support_levels": [2800, 2750],
  "resistance_levels": [2900, 3000],
  "volume_visible": true,
  "confidence_source": "page_text",
  "evidence_refs": [
    "data/raw/screenshots/2026-03-16__NEPSE__1D__clean.png"
  ]
}
```

Required:
- `close`
- `trend_label`
- `support_levels`
- `resistance_levels`

---

## 8. Sector Record

Purpose:
- store sector-level context

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "captured_at": "2026-03-16T18:05:00+05:45",
  "source": "nepsealpha",
  "sector_name": "Hydropower",
  "timeframe": "1D",
  "trend_label": "bullish",
  "relative_strength_vs_market": "stronger",
  "notes": "Sector near resistance but still holding strength",
  "confidence_source": "visual_inference",
  "evidence_refs": [
    "data/raw/screenshots/2026-03-16__HYDRO__1D__clean.png"
  ]
}
```

Required:
- `sector_name`
- `trend_label`

---

## 9. Candidate Record

Purpose:
- store why a stock entered the analysis queue

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "source": "nepsealpha_screener",
  "symbol": "SMHL",
  "rank": 2,
  "selection_reasons": [
    "near breakout",
    "bullish momentum",
    "positive catalyst"
  ],
  "filter_values": {
    "rsi": 38.44,
    "macd_state": "turning_up",
    "price_vs_ema20": "above"
  },
  "confidence_source": "table_extract",
  "evidence_refs": [
    "data/raw/tables/2026-03-16__candidate_list.json"
  ]
}
```

Required:
- `symbol`
- `rank`
- `selection_reasons`

---

## 10. Stock Chart Record

Purpose:
- store structure and location on the chart

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "captured_at": "2026-03-16T18:10:00+05:45",
  "source": "nepsealpha_chart",
  "symbol": "SMHL",
  "timeframe": "1W",
  "close": 525.00,
  "open": null,
  "high": null,
  "low": null,
  "volume": 316929,
  "trend_label": "bullish",
  "structure_label": "base_forming",
  "swing_highs": [641.40, 742.90],
  "swing_lows": [477.50, 504.30],
  "support_zones": [[500, 515]],
  "resistance_zones": [[531, 545], [641, 650]],
  "breakout_level": 531.10,
  "breakdown_level": 500.00,
  "invalidation_level": 477.50,
  "location_label": "near_breakout_resistance",
  "confidence_source": "direct_dom",
  "evidence_refs": [
    "data/raw/screenshots/2026-03-16__SMHL__1W__clean.png",
    "data/raw/screenshots/2026-03-16__SMHL__1W__annotated.png"
  ]
}
```

Required:
- `symbol`
- `timeframe`
- `close`
- `trend_label`
- `support_zones`
- `resistance_zones`
- `invalidation_level`

---

## 11. Indicator Record

Purpose:
- store technical indicator values in structured form

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "captured_at": "2026-03-16T18:11:00+05:45",
  "source": "nepsealpha_chart",
  "symbol": "SMHL",
  "timeframe": "1W",
  "ema_20": 495.12,
  "ma_50": null,
  "ma_200": null,
  "rsi": 38.44,
  "macd_line": 3.25,
  "signal_line": -91.20,
  "histogram": -94.46,
  "price_above_ema_20": true,
  "price_above_ma_50": null,
  "price_above_ma_200": null,
  "momentum_label": "bullish_reversal_forming",
  "confidence_source": "page_text",
  "evidence_refs": [
    "data/raw/screenshots/2026-03-16__SMHL__1W__clean.png"
  ]
}
```

Required:
- at least one of `rsi` or `macd_line`
- `momentum_label`

---

## 12. Volume Record

Purpose:
- separate real moves from weak ones

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "symbol": "SMHL",
  "timeframe": "1W",
  "current_volume": 316929,
  "volume_vs_average": "average",
  "breakout_volume_signal": "not_triggered",
  "pullback_volume_signal": "healthy",
  "participation_label": "accumulation_possible",
  "confidence_source": "visual_inference",
  "evidence_refs": [
    "data/raw/screenshots/2026-03-16__SMHL__1W__clean.png"
  ]
}
```

Required:
- `current_volume`
- `participation_label`

---

## 13. Relative Strength Record

Purpose:
- compare stock strength to market and sector

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "symbol": "SMHL",
  "benchmark_market": "NEPSE",
  "benchmark_sector": "Hydropower",
  "rs_vs_market_label": "neutral",
  "rs_vs_sector_label": "stronger",
  "rs_notes": "Holding better than sector pullback",
  "confidence_source": "visual_inference",
  "evidence_refs": []
}
```

Required:
- `benchmark_market`
- `rs_vs_market_label`

---

## 14. Event Record

Purpose:
- store catalysts with timing and relevance

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "captured_at": "2026-03-16T18:20:00+05:45",
  "source": "company_announcement",
  "symbol": "SMHL",
  "event_date": "2026-01-04",
  "event_type": "bonus_and_rights_announcement",
  "sentiment": "positive",
  "impact_window_days": 90,
  "relevance_now": "active",
  "details": {
    "bonus_share_pct": 20,
    "rights_share_pct": 100
  },
  "confidence_source": "page_text",
  "evidence_refs": [
    "data/raw/snapshots/2026-03-16__SMHL__event_bonus_rights.txt"
  ]
}
```

Required:
- `event_date`
- `event_type`
- `sentiment`
- `relevance_now`

---

## 15. Broker Flow Record

Purpose:
- store floorsheet or broker behavior when relevant

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "source": "floorsheet_or_broker_view",
  "symbol": "SMHL",
  "activity_label": "neutral",
  "accumulation_signal": false,
  "distribution_signal": false,
  "notes": "No unusually strong broker concentration visible",
  "confidence_source": "visual_inference",
  "evidence_refs": []
}
```

Required:
- `activity_label`

---

## 16. Feature Score Record

Purpose:
- store interpretable scoring inputs

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "symbol": "SMHL",
  "scores": {
    "market_alignment": 1,
    "sector_alignment": 2,
    "structure_quality": 2,
    "location_quality": 2,
    "trend_filter_quality": 1,
    "volume_confirmation": 1,
    "momentum_confirmation": 2,
    "relative_strength": 1,
    "event_quality": 2,
    "risk_reward_quality": 2
  },
  "score_total": 14,
  "score_max": 20,
  "confidence_source": "derived",
  "evidence_refs": []
}
```

Required:
- `scores`
- `score_total`
- `score_max`

---

## 17. Decision Record

Purpose:
- store the actionable final output

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "run_date": "2026-03-16",
  "captured_at": "2026-03-16T18:25:00+05:45",
  "symbol": "SMHL",
  "setup_type": "breakout_watch",
  "score": 78,
  "confidence": 0.82,
  "action": "wait_for_breakout",
  "entry_zone": [535, 550],
  "stop_loss": 500,
  "invalidation_level": 477.50,
  "targets": [641, 742, 850],
  "risk_reward_ratio": 4.7,
  "why": [
    "weekly base forming",
    "positive event catalyst",
    "momentum improving",
    "market not broken"
  ],
  "evidence_refs": [
    "data/normalized/stocks/2026-03-16__SMHL__1W__stock_chart.json",
    "data/normalized/indicators/2026-03-16__SMHL__1W__indicator.json",
    "data/normalized/events/2026-03-16__SMHL__event_bonus_rights.json"
  ]
}
```

Required:
- `setup_type`
- `score`
- `action`
- `entry_zone`
- `stop_loss`
- `invalidation_level`
- `targets`

---

## 18. Outcome Record

Purpose:
- close the learning loop for prediction quality

Schema:

```json
{
  "schema_version": "1.0",
  "session_id": "2026-03-16T18-00-00-smhl",
  "decision_session_id": "2026-03-16T18-00-00-smhl",
  "symbol": "SMHL",
  "evaluation_date": "2026-04-16",
  "time_horizon": "1M",
  "outcome_label": "partial_success",
  "target_1_hit": true,
  "target_2_hit": false,
  "target_3_hit": false,
  "stop_hit": false,
  "max_favorable_excursion_pct": 18.2,
  "max_adverse_excursion_pct": -4.5,
  "notes": "Reached first target but failed to continue"
}
```

Required:
- `decision_session_id`
- `evaluation_date`
- `time_horizon`
- `outcome_label`

Without this record type, the system cannot learn.

---

## 19. Minimum Required Records for a Valid Prediction Run

For a run to count as valid, it must produce at least:

1. Session record
2. Market record
3. Stock chart record
4. Indicator record
5. Decision record

Recommended valid run:

1. Session record
2. Market record
3. Sector record
4. Candidate record
5. Stock chart record
6. Indicator record
7. Volume record
8. Event record
9. Feature score record
10. Decision record

---

## 20. Reliability Rule for Stored Data

Every final prediction must be reconstructable from stored records.

That means:

- if a score exists, its evidence must exist
- if a setup exists, its invalidation must exist
- if a decision exists, its entry and stop must exist
- if a prediction exists, an outcome record should later exist

This is how we move from opinion to reliable system.
