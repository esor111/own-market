# Experiment Contract: broker-data-enrichment

## Purpose
Turn the raw broker-flow fact table into a richer research table by adding broker identity and nearby corporate-action context.

## Inputs (read-only paths)
- `market-gist/data/validation/broker_flow_fact_table/broker_flow_fact_table.csv`
- `experiments/01-corporate-action/data/events.csv`
- Public broker-contact pages, when reachable, for broker-name enrichment only.

## Outputs (only paths this experiment writes to)
- `experiments/broker-data-enrichment/data/broker_master.csv`
- `experiments/broker-data-enrichment/data/event_calendar.csv`
- `experiments/broker-data-enrichment/data/symbol_day_event_context.csv`
- `experiments/broker-data-enrichment/data/broker_flow_fact_table_enriched.csv`
- `experiments/broker-data-enrichment/data/enrichment_summary.json`
- `experiments/broker-data-enrichment/data/enrichment_summary.md`

## Never Touches
- `market-gist/automation/run_persistence_shadow_daily.py`
- `market-gist/automation/daily_persistence_shadow_report.py`
- `market-gist/automation/score_persistence_shadow_reports.py`
- `market-gist/data/validation/persistence_shadow_reports/`
- `market-gist/data/validation/persistence_shadow_reviews/`
- `experiments/LEARNINGS.md`, `BACKLOG.md`, `INDEX.md`, `MANIFESTO.md`

## Kill Condition
Delete `experiments/broker-data-enrichment/`. Nothing else breaks.

## Runnable As
```powershell
python experiments/broker-data-enrichment/build_enrichment_tables.py
```

## Forward Evidence Gate
None. This is not a trading signal and does not produce verdicts. It is research infrastructure that can later feed pre-registered experiments.

