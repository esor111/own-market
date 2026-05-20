# UPPER Dossier — README (data sources & how to refresh)

This dossier reads from THREE independent data layers. They are independent
on purpose: any one going stale or breaking does not break the others.

## Layer 1 — Local EOD OHLCV (always fresh, no auth)

- **Path:** `../../sharesansar_datascrape/data/*.csv` (per-date files,
  `MM_DD_YYYY.csv`).
- **Coverage:** ~2021-09 → today (~1,615+ trading days for UPPER).
- **How refreshed:** the daily ShareSansar scrape (the `daily-flow` lab skill
  catches up any missing days).
- **NOT** corp-action adjusted.

## Layer 2 — Local broker flow (NEPSE floorsheet, fact table)

- **Raw:** `../../market-gist/broker_flow_ledger/raw_merolagani/UPPER/*.json`
- **Aggregated:** `../../market-gist/data/validation/broker_flow_fact_table/broker_flow_fact_table.csv`
- **Coverage:** ~2023-06 → ~2026-05 (336+ days, 92 brokers) for UPPER.
- **How refreshed:**
  1. Scrape new raw ledgers: `python market-gist/automation/backfill_merolagani_floorsheet.py --symbol UPPER --start-date YYYY-MM-DD --end-date YYYY-MM-DD --timeframe 1D`
  2. Rebuild the fact table: `python market-gist/automation/build_broker_flow_fact_table.py`
  3. Both scripts are read-only on shared artifacts (rebuilding the fact
     table does NOT disturb the persistence-shadow scorer; confirmed via
     `Grep broker_flow_fact_table own-market/` — only the dossier, an
     archived experiment, and the builder itself reference it).

## Layer 3 — nepsealpha minute / hourly / daily (intraday, gated)

**This is the layer I previously declared impossible. It works. See METHODOLOGY Rule 10.**

The site has bot detection that blocks fresh headless Playwright. The working approach (already implemented in the repo) is:

1. **CDP-attach to a real Chrome session** (not Playwright-launched Chromium)
   — bot detection sees a real human browser.
2. **Sniff the live `fsk` session token** from the page's own request to
   `/trading/1/search?...&fsk=XXX`.
3. **Call `/trading/1/history` from *inside* the TradingView iframe**
   (right origin) with that `fsk`.

The orchestration is one PowerShell + one Node script + the Playwright skill:

- **Run:** `./refresh_upper_data.ps1 -Symbol UPPER -Days 31` (from the
  `own-market/` root). The PowerShell wrapper:
  - Auto-launches real Chrome.exe at port 9222 if it isn't already up
    (visible window; uses a temp profile under `$env:TEMP\chrome-automation-nepse`).
  - Invokes `scripts/refresh_nepse_symbol.js` which connects over CDP,
    sniffs `fsk`, finds the TradingView iframe, calls the history API for
    1-min / 1-day / 5 / 30 / 60-min resolutions.
  - Writes 5 files to `own-market/` root: `upper_volume_last_month_full.json`,
    `upper_volume_last_month_summary.json`, `upper_volume_1min.csv`,
    `upper_volume_hourly.csv`, `upper_volume_daily.csv`.
  - Then renders a chart via `scripts/render_volume_chart.py`.

- **Programmatic access:** `dossier_data.intraday("UPPER")` returns the
  loaded JSON (falls back to `experiments/08-hydro-volume-tape-lab/raw/UPPER/`
  if the root-level file is missing). `assemble("UPPER").intraday` exposes it
  on the main dossier object.

- **Coverage on the existing snapshot (scraped 2026-04-27):** 37,347 minute
  bars · 1,652 daily bars · range 2023-10-29 → 2026-04-24.

## How to refresh everything in one pass (a typical session)

```powershell
# 1. EOD OHLCV (always free, no Chrome needed)
cd sharesansar_datascrape
python scrape_nepse.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD
cd ..
python market-gist/automation/price_data_integrity.py

# 2. Broker flow (Merolagani; no Chrome needed)
cd market-gist/automation
python backfill_merolagani_floorsheet.py --symbol UPPER --start-date YYYY-MM-DD --end-date YYYY-MM-DD --timeframe 1D
python build_broker_flow_fact_table.py
cd ../..

# 3. Intraday (nepsealpha; launches real Chrome visibly)
./refresh_upper_data.ps1 -Symbol UPPER -Days 31

# 4. Render today's read
python company_dossiers/UPPER/daily_read.py UPPER
```

## File map within the dossier

| File | Purpose |
|---|---|
| `DOSSIER_CONTRACT.md` | The frozen rulebook (sections, language, anti-self-deception rules). |
| `COMPANY_CONTEXT.md` | Curated company facts (business, debt, PPA, landslide, rights, AGM). Sourced lines + explicit `[unverified]` gaps. |
| `METHODOLOGY.md` | 10 transferable techniques for reading any case. |
| `cases/CASE_*.md` | Mechanically-selected historical event cases. |
| `daily_reads/UPPER_YYYY-MM-DD.md` | One file per trading day, auto sections + your immutable read + later review. |
| `analyze_event.py` | Focused per-date broker-flow analyzer (`python analyze_event.py YYYY-MM-DD UPPER`). |
| `render_chart.py` | Multi-zoom local chart renderer (full / 3y / 1y / 3m). |
| `daily_read.py` | Daily-read renderer (`python daily_read.py UPPER [DATE]`). |
| `charts/` | All rendered images + nepsealpha probe artifacts (proof of the auth gate). |
