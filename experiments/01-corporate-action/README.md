# Corporate Action Timing

## Hypothesis

Corporate action event dates in NEPSE stocks create measurable price moves.
Information leakage means prices may move before the official announcement date,
so we should test pre-event, reaction, and post-event windows separately.

## Seed Universe

This experiment starts with 14 seed symbols:

- Banks: `NABIL`, `NBL`, `EBL`, `HBL`, `KBL`, `SANIMA`, `PRVU`, `NIMB`
- Hydropower: `SMHL`, `HIDCL`, `NGPL`, `API`, `AKPL`, `UPPER`

## Sources

- ShareSansar company pages: `https://www.sharesansar.com/company/SYMBOL`
- ShareSansar structured company endpoints discovered from the live page:
  - `company-dividend`
  - `company-rightshare`
  - `company-agm`
  - `company-announcements`
  - `company-events`

## What Gets Built

- `scrape_sharesansar_history.py`
  - downloads raw company pages
  - fetches structured corporate-action feeds for each symbol
  - stores raw JSON/HTML under `data/raw/`
- `build_event_table.py`
  - converts the raw feeds into a single standardized event table
  - preserves structured dates like announcement, AGM meeting, book close, and listing
- `run_event_study.py`
  - measures return windows around each event-date type
  - writes event-level returns and grouped summary stats to `results/`

## Success Criteria

Find at least one event type with more than `60%` directional hit rate in a
specific window, with enough cases to be worth following up.

## Event Windows

- `pre_-10_-1`
- `reaction_0_1`
- `drift_2_10`

## Current Reality

This experiment is viable as a standalone build. The ShareSansar structured
feeds do work when requested with the correct company session and token, so we
do not need to depend on `market-gist/` for the historical event timeline.
