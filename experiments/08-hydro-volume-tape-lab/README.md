# Experiment 08 — Hydropower Volume / Tape Microstructure Lab

> Status: scaffold. Scraper is wired, first builder runs against any raw volume files already present.
> This lane is separate from the live prediction lane, the persistence shadow lane, and experiment 07 (broker-flow lab).

## Core Question

What does minute/hourly/daily volume behavior say on its own, and does it agree or disagree
with the broker-flow labels from experiment 07?

## What This Uses

- **Existing Nepse Alpha volume scraper** (do NOT reinvent):
  - `scripts/refresh_nepse_symbol.js`
  - `scripts/render_volume_chart.py`
  - `refresh_upper_data.ps1` (already parametric on `-Symbol`)
- **Raw volume captures** per symbol:
  - `experiments/08-hydro-volume-tape-lab/raw/<SYMBOL>/<SYMBOL>_volume_1min.csv`
  - `experiments/08-hydro-volume-tape-lab/raw/<SYMBOL>/<SYMBOL>_volume_hourly.csv`
  - `experiments/08-hydro-volume-tape-lab/raw/<SYMBOL>/<SYMBOL>_volume_daily.csv`
  - `experiments/08-hydro-volume-tape-lab/raw/<SYMBOL>/<SYMBOL>_volume_last_month_full.json`
  - `experiments/08-hydro-volume-tape-lab/raw/<SYMBOL>/<SYMBOL>_volume_last_month_summary.json`
  - `experiments/08-hydro-volume-tape-lab/raw/<SYMBOL>/<SYMBOL>_volume_daily_chart.png`

## What This Does Not Touch

- Does not modify live prediction prompts.
- Does not update the persistence shadow policy.
- Does not reimplement the existing Node/Playwright scraper. We wrap it.

## First-Pass Symbols

The default universe matches experiment 07:

- `UPPER`, `API`, `AKPL`, `AHPC`, `BHCL`, `RADHI`, `RHPL`

## How To Refresh Raw Data

The refresh script requires a live Chrome instance with remote debugging on port 9222
and the Playwright skill present at `~/.agents/skills/playwright`. The wrapper will
start Chrome for you if it is missing, but the Playwright skill must already be installed.

```powershell
# refresh a single symbol
powershell -NoProfile -ExecutionPolicy Bypass -File .\experiments\08-hydro-volume-tape-lab\refresh_hydro_volumes.ps1 -Symbol AKPL

# refresh multiple symbols
powershell -NoProfile -ExecutionPolicy Bypass -File .\experiments\08-hydro-volume-tape-lab\refresh_hydro_volumes.ps1 -Symbols UPPER,AKPL,API

# refresh all configured hydro symbols
powershell -NoProfile -ExecutionPolicy Bypass -File .\experiments\08-hydro-volume-tape-lab\refresh_hydro_volumes.ps1 -All
```

The wrapper calls the existing `refresh_upper_data.ps1` for each symbol, then relocates the
output files into `experiments/08-hydro-volume-tape-lab/raw/<SYMBOL>/`.

## How To Build

Once raw data is present, run the builder to produce per-symbol and cross-symbol volume summaries:

```powershell
python .\experiments\08-hydro-volume-tape-lab\build_volume_dataset.py
```

Optional focus mode (matches experiment 07 convention):

```powershell
python .\experiments\08-hydro-volume-tape-lab\build_volume_dataset.py --focus AKPL
```

## Outputs

Produced by `build_volume_dataset.py`:

- `data/volume_daily.csv` — multi-symbol daily volume dataset with derived labels
- `data/volume_events.csv` — spike days, high-volume-down, failed rallies, absorption candles
- `data/volume_summary.json` — per-symbol rollups
- `results/volume_findings.md` — cross-symbol summary
- `results/<focus_lower>_volume_read.md` (when `--focus` given) — focus-symbol volume narrative

## Volume Labels (first-pass)

Research labels, not signals:

- `volume_spike` — daily volume ≥ 2.0× the 20-day average
- `volume_drought` — daily volume ≤ 0.5× the 20-day average
- `high_volume_up` — volume ≥ 1.5× 20-day avg AND close > open
- `high_volume_down` — volume ≥ 1.5× 20-day avg AND close < open
- `failed_rally` — intraday range ≥ 5% AND close in lower 40% of range on above-avg volume
- `absorption_candle` — intraday range ≥ 5% AND close in upper 60% of range on above-avg volume

These labels will be cross-referenced against experiment 07's broker-flow labels in a follow-up pass.

## Open Questions / Next Steps

- Seed raw/UPPER/ from the existing root-directory `upper_volume_*` files to avoid a fresh scrape.
- Once broker-flow labels and volume labels are both present for the same date, build a "labels agreement matrix" — that's where this experiment earns its keep.
- Expand to all listed hydropower symbols only after confirming scraper coverage.
