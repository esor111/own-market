# Template Guide

These files are starter contracts for the records described in [RICH_DATA_SCHEMA_SPEC.md](/C:/Users/ishwor/Music/own-organize/own-market/market-gist/RICH_DATA_SCHEMA_SPEC.md).

## How to Use

1. Copy the matching template for the record you are writing.
2. Fill all mandatory fields from the runbook.
3. Save the completed file into the correct symbol/date-scoped folder under `data/symbols/<SYMBOL>/<RUN_DATE>/...`.
4. Keep `evidence_refs` updated so every decision can be traced back to proof.

## Minimum Prediction Run

At minimum, a reliable run should fill:

- `session.template.json`
- `market.template.json`
- `stock_chart.template.json`
- `indicator.template.json`
- `decision.template.json`

For stronger runs, also fill:

- `sector.template.json`
- `candidate.template.json`
- `volume.template.json`
- `relative_strength.template.json`
- `event.template.json`
- `feature_score.template.json`
- `outcome.template.json` later

## Rule

Do not create ad hoc fields unless the schema has been updated first.
