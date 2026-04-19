# Broker Data Enrichment

> Layer 3 research infrastructure. This does not touch production scoring and does not create a trading signal.

## What this is

The broker-flow fact table already tells us:

- which broker bought
- which broker sold
- how much quantity and rupee amount changed hands
- whether the broker was net buyer or net seller on that symbol-day

This sandbox adds the missing context:

- broker name/contact mapping where a public mapping is available
- nearby corporate-action events from the existing L-001 event table
- contamination flags for book-close, dividend/bonus, right-share, AGM, and listing windows

## Why this helps

Raw statement:

`Broker 58 sold NABIL heavily for 7 sessions.`

Richer statement:

`Broker 58 sold NABIL heavily for 7 sessions, and there was no nearby book-close/dividend/right-share/AGM event in the L-001 event table. This is cleaner broker-flow evidence.`

Or:

`Broker 58 sold NABIL heavily, but a book-close/dividend event was nearby. Treat as contaminated context, not clean alpha.`

That is the point. This sandbox makes future broker-flow research harder to fool.

## Current scope

- Reads the existing broker-flow fact table.
- Reads the existing L-001 corporate-action event table.
- Builds an enriched table with event-context columns.
- Does not modify the daily persistence shadow policy.
- Does not change any CAUTION / NO_SIGNAL verdict.

## Outputs

After running:

- `data/broker_master.csv` — observed broker IDs plus public-name mapping where available.
- `data/event_calendar.csv` — one row per symbol/event/date-role from L-001.
- `data/symbol_day_event_context.csv` — compact event context per symbol-date.
- `data/broker_flow_fact_table_enriched.csv` — broker-flow fact rows plus broker/event context.
- `data/enrichment_summary.md` — human-readable summary.

## Known limitations

- Broker-name mapping is not fully official for all 90+ observed broker IDs yet.
- The current event context comes from the L-001 ShareSansar-derived table, not a complete NEPSE/SEBON filing archive.
- A symbol with `0` nearby events may simply have no L-001 event-table coverage yet. That means unknown, not necessarily clean.
- Event windows use calendar days for context labeling, not trading-day tests. This is acceptable for contamination notes, but not for a pre-registered return test.
- Unmapped broker IDs are retained as numeric IDs instead of being guessed.
