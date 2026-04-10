# NEPSE Scraper Evaluation

## What I Did

- cloned the repo into:
  - `C:\Users\ishwor\Music\own-organize\own-market\external\nepse_scraper`
- read the README, `pyproject.toml`, `client.py`, and `endpoints.py`
- installed the declared runtime dependency `wasmtime`
- ran live probes against the NEPSE endpoints

## Important Finding

The cloned repo did not import cleanly as-is.

It had a syntax typo in:

- `external/nepse_scraper/nepse_scraper/auth.py`

I fixed that locally in the clone only so I could continue evaluation.

## What Worked

The client returned real NEPSE data successfully with:

- `NepseScraper(verify_ssl=False)`

Verified working methods:

- `is_market_open()`
- `get_today_price()`
- `get_market_summary()`
- `get_sectorwise_summary()`
- `get_ticker_info('NABIL')`
- `get_ticker_price_history('NABIL', '2025-01-01', '2026-03-18')`
- `get_brokers()`
- `get_supply_demand()`

Observed live results during testing:

- `get_today_price()` returned `340` records
- `get_sectorwise_summary()` returned `16` records
- `get_brokers()` returned `92` records
- `get_ticker_price_history('NABIL', ...)` returned paginated history with `222` records in the payload

## What Looks Strong

This repo is strong for:

- raw daily OHLCV-style data
- symbol/security metadata
- company and capital structure details
- market summary
- sector summary
- broker directory data
- basic supply/demand snapshots

This is exactly the kind of truth-layer data your current browser-first system is missing.

## What Looks Weak

- the package had a real syntax error in the clone
- it requires `verify_ssl=False` because the NEPSE server certificate chain is incomplete
- `get_company_disclosures()` returned `0` records in my test
- `get_live_trades()` returned `0` because the market was closed at test time
- there is no first-class `floorsheet` method exposed in `client.py`
- for floorsheet-like needs, we may need either:
  - a custom endpoint via `register_endpoint(...)`, or
  - a second NEPSE source later

## My Recommendation

Yes, this repo is worth using.

But not as a blind drop-in dependency.

Use it as a wrapped raw-data adapter for:

- market summary
- sector summary
- ticker/company metadata
- price history
- broker directory
- supply/demand snapshots

Do not use it for:

- chart screenshots
- TradingView/NepseAlpha chart state
- drawing tools
- portal-only UI features

That should stay in your Playwright system.

## Best Fit In Your Architecture

Use this split:

- `nepse_scraper` = raw market truth
- Playwright MCP = chart evidence and NepseAlpha-only interactions
- your pipeline = normalization, QC, scoring, storage
- stronger model = final reasoning over structured inputs

## Best Next Integration Move

If we continue with this repo, the smartest next step is:

1. build a thin adapter inside `market-gist/automation`
2. map a few methods into your schema first:
   - `get_today_price`
   - `get_ticker_info`
   - `get_ticker_price_history`
   - `get_market_summary`
   - `get_sectorwise_summary`
3. compare those outputs against your current Playwright captures
4. only then decide whether to rely on it for more than the truth layer

## Bottom Line

This repo is good enough to be useful.

It is not clean enough to trust blindly.

It should be wrapped, tested, and used selectively.
