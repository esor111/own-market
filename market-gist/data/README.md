# Data Layout Guide

This folder stores the full reliability-first analysis pipeline.

## Layers

- `raw/`: direct evidence captured from Playwright MCP runs
- `normalized/`: structured records used for scoring and decisions
- `features/`: derived scoring inputs and model-ready fields
- `outcomes/`: later result labels for calibration and learning

## Raw

- `raw/sessions/`: session metadata or raw run logs
- `raw/screenshots/`: clean and annotated chart images
- `raw/snapshots/`: page snapshot text or extracted DOM state
- `raw/tables/`: extracted screener or tabular page data

## Normalized

- `normalized/sessions/`: one record per analysis session
- `normalized/market/`: NEPSE market context
- `normalized/sectors/`: sector context
- `normalized/candidates/`: screener-selected stocks
- `normalized/stocks/`: stock chart structure and price-location records
- `normalized/indicators/`: indicator values like EMA, RSI, MACD
- `normalized/events/`: catalysts such as bonus, rights, AGM, book closure
- `normalized/broker_flow/`: floorsheet or broker behavior records
- `normalized/relative_strength/`: stock vs market and sector strength
- `normalized/decisions/`: final actionable setup records

## Features

- `features/setup_scores/`: interpretable scoring buckets
- `features/model_inputs/`: compact prediction-ready feature sets

## Outcomes

- `outcomes/realized_results/`: what happened after the call

## Templates

Starter JSON templates live in [`templates/`](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/templates). Use them as the base contract for new runs.

## Naming

Use this file naming pattern whenever possible:

```text
YYYY-MM-DD__SYMBOL__TIMEFRAME__record_type.json
YYYY-MM-DD__SYMBOL__TIMEFRAME__clean.png
YYYY-MM-DD__SYMBOL__TIMEFRAME__annotated.png
```

Example:

```text
2026-03-16__SMHL__1W__stock_chart.json
2026-03-16__SMHL__1W__clean.png
2026-03-16__SMHL__1W__annotated.png
```

## Rule

Every reliable run should produce:

1. raw evidence
2. normalized records
3. decision output
4. later outcome label
