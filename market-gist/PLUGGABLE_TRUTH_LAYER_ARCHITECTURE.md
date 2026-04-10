# Pluggable Truth Layer Architecture

## Rule

External repos are never the core of the project.

They are only providers.

This project owns:

- the interface
- the registry
- the schema mapping
- the comparison logic
- the downstream analysis pipeline

## Structure

- `automation/data_sources/base.py`
  - provider interface
- `automation/data_sources/registry.py`
  - provider lookup / instantiation
- `automation/data_sources/nepse_scraper_source.py`
  - wrapper around the external `nepse_scraper` repo
- `automation/compare_nepse_truth.py`
  - compare provider truth vs browser truth

## Why This Matters

This makes the system:

- extendable
- replaceable
- safer to maintain
- less dependent on any one external repo

## Intended Use

- Playwright remains the chart/portal layer
- truth providers supply raw market data
- comparisons reveal drift or extraction errors
- the main analysis pipeline can later consume whichever provider proves reliable

## Future Providers

Possible later providers:

- `nepse_api`
- `openbb_custom_provider`
- `official_disclosure_provider`
- `floorsheet_provider`

The main pipeline should not need to know which one is active.
