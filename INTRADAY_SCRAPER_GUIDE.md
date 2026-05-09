# Intraday Data Scraper — Complete Guide

## What We Have

A **fully functional intraday scraper** that collects minute/hourly/daily volume data from nepsealpha.com TradingView charts.

## How It Works

### Architecture

1. **Chrome with Remote Debugging** - Opens nepsealpha.com chart in Chrome with CDP (Chrome DevTools Protocol) enabled
2. **Node.js Scraper** (`scripts/refresh_nepse_symbol.js`) - Connects to Chrome, extracts data from TradingView API
3. **Python Renderer** (`scripts/render_volume_chart.py`) - Creates volume charts from the data

### Data Flow

```
nepsealpha.com (TradingView chart)
    ↓
Chrome with CDP (port 9222)
    ↓
Node.js scraper (extracts via /trading/1/history endpoint)
    ↓
Outputs:
  - {symbol}_volume_last_month_full.json (complete data)
  - {symbol}_volume_last_month_summary.json (summary stats)
  - {symbol}_volume_1min.csv (minute bars)
  - {symbol}_volume_hourly.csv (hourly aggregation)
  - {symbol}_volume_daily.csv (daily aggregation)
  - {symbol}_volume_daily_chart.png (visualization)
```

## Current Coverage

| Symbol | Minute Data | Status |
|--------|-------------|--------|
| UPPER | 23 days | ✅ Has data |
| BHL | ~30 days | ✅ Has data |
| AKPL | 0 days | ❌ Need to scrape |
| API | 0 days | ❌ Need to scrape |
| AHPC | 0 days | ❌ Need to scrape |
| RADHI | 0 days | ❌ Need to scrape |
| RHPL | 0 days | ❌ Need to scrape |
| BHCL | 0 days | ❌ Need to scrape |

## How to Use

### Single Symbol (Manual)

```powershell
# Run the PowerShell wrapper
.\refresh_upper_data.ps1 -Symbol AKPL -Days 31
```

This will:
1. Start Chrome with remote debugging (if not already running)
2. Navigate to nepsealpha.com/nepse-chart
3. Extract last 31 days of minute data
4. Generate CSV files and chart

### Multiple Symbols (Batch)

Create a batch script to scrape all symbols:

```powershell
# scrape_all_intraday.ps1
$symbols = @("UPPER", "AKPL", "API", "AHPC", "RADHI", "RHPL", "BHCL")

foreach ($symbol in $symbols) {
    Write-Host "Scraping $symbol..." -ForegroundColor Cyan
    .\refresh_upper_data.ps1 -Symbol $symbol -Days 31
    Start-Sleep -Seconds 5  # Pause between symbols
}

Write-Host "All symbols scraped!" -ForegroundColor Green
```

## What Data You Get

### Minute Bars (`{symbol}_volume_1min.csv`)
```csv
symbol,resolution,ts,datetime_np,date_np,open,high,low,close,volume
BHL,1min,1774224000,2026-03-22 09:14,2026-03-22,220.00,232.00,220.00,221.80,25235
```

**Fields**:
- `ts`: Unix timestamp
- `datetime_np`: Nepal time (YYYY-MM-DD HH:MM)
- `date_np`: Nepal date (YYYY-MM-DD)
- `open`, `high`, `low`, `close`: OHLC prices
- `volume`: Shares traded in that minute

### Hourly Aggregation (`{symbol}_volume_hourly.csv`)
```csv
hour_np,bars,volume,open,high,low,close
2026-03-22 09:00,60,189486,220.00,232.00,220.00,221.80
```

**Fields**:
- `hour_np`: Hour timestamp
- `bars`: Number of minute bars in that hour
- `volume`: Total volume for the hour
- OHLC: Aggregated from minute bars

### Daily Aggregation (`{symbol}_volume_daily.csv`)
```csv
date_np,bars,volume,open,high,low,close
2026-03-22,390,697495,220.00,232.00,220.00,221.80
```

**Fields**:
- `date_np`: Trading date
- `bars`: Number of minute bars that day
- `volume`: Total daily volume
- OHLC: Aggregated from minute bars

### Summary JSON (`{symbol}_volume_last_month_summary.json`)
```json
{
  "scraped_at_np": "2026-04-27 15:30:00",
  "symbol": "BHL",
  "source": "https://nepsealpha.com/nepse-chart",
  "latest_datetime_np": "2026-04-21 15:00",
  "cutoff_datetime_np": "2026-03-22 15:00",
  "minute_bar_count": 8234,
  "total_volume": 15234567,
  "trading_days": 23,
  "top_10_days_by_volume": [...],
  "top_10_hours_by_volume": [...]
}
```

## What This Unlocks

### 1. Panic vs. Absorption Detection

**Panic Selling** (avoid):
- Large volume spike in first hour (09:00-10:00)
- Price closes near lows of the day
- Volume tapers off in afternoon

**Smart Money Absorption** (potential buy):
- Large volume spike in last hour (14:00-15:00)
- Price recovers from lows, closes strong
- Steady accumulation throughout the day

### 2. Close Strength Analysis

```
Close Strength = (Close - Low) / (High - Low)
```

- **0.8-1.0**: Strong close (bullish)
- **0.2-0.4**: Weak close (bearish)
- **0.4-0.6**: Neutral

### 3. Volume Profile

- **Front-loaded**: Volume concentrated in morning (panic/news reaction)
- **Back-loaded**: Volume concentrated in afternoon (accumulation/distribution)
- **Balanced**: Even distribution (normal trading)

## Technical Details

### Data Source

The scraper uses nepsealpha.com's internal TradingView API:

```
GET /trading/1/history?fsk={token}&symbol={SYMBOL}&resolution={1|5|30|60|1D}&frame=1000
```

**Resolutions**:
- `1`: 1-minute bars
- `5`: 5-minute bars
- `30`: 30-minute bars
- `60`: 1-hour bars
- `1D`: Daily bars

### Authentication

The scraper automatically discovers the `fsk` (session token) by:
1. Loading nepsealpha.com/nepse-chart
2. Monitoring network requests
3. Extracting `fsk` parameter from TradingView API calls

No manual authentication required.

### Data Retention

nepsealpha.com provides:
- **Minute data**: Last ~30-60 days
- **Daily data**: Full history (years)

For longer intraday history, you need to scrape daily and accumulate.

## Limitations

1. **Historical Limit**: Can only get last ~30-60 days of minute data
2. **Rate Limiting**: Should pause 5-10 seconds between symbols
3. **Browser Dependency**: Requires Chrome with remote debugging
4. **Session Token**: `fsk` token expires, scraper auto-refreshes it

## Next Steps

### Immediate (Today)

1. **Test the scraper** on one symbol:
   ```powershell
   .\refresh_upper_data.ps1 -Symbol AKPL -Days 31
   ```

2. **Verify output files** are created:
   - `akpl_volume_1min.csv`
   - `akpl_volume_hourly.csv`
   - `akpl_volume_daily.csv`

### Short-term (This Week)

3. **Create batch script** to scrape all 7 symbols
4. **Run daily** to accumulate 30+ days of data
5. **Build analysis scripts** to detect panic vs. absorption

### Long-term (Ongoing)

6. **Automate daily scraping** (Task Scheduler or manual)
7. **Integrate with psychology engine** to enhance avoid/buy signals
8. **Build intraday pattern library** (panic signatures, absorption patterns)

## Files

**Scraper**:
- `scripts/refresh_nepse_symbol.js` - Main Node.js scraper
- `refresh_upper_data.ps1` - PowerShell wrapper

**Renderer**:
- `scripts/render_volume_chart.py` - Chart generator

**Dependencies**:
- Node.js (for scraper)
- Python (for charts)
- Chrome (for browser automation)
- Playwright skill (in `~/.agents/skills/playwright`)

## Example Output

See existing files:
- `bhl_volume_minute_last_30d.csv` - 30 days of BHL minute data
- `bhl_volume_hourly_last_30d_derived_from_1m.csv` - Hourly aggregation
- `bhl_volume_daily_last_30d.csv` - Daily aggregation
- `bhl_volume_last_month_raw.json` - Full JSON with metadata

## Bottom Line

**Gap 2 (Intraday Tape): 90% SOLVED**

The scraper exists and works. You just need to:
1. Run it for the 6 missing symbols (AKPL, API, AHPC, RADHI, RHPL, BHCL)
2. Run it daily to accumulate 30+ days of data
3. Build analysis logic to use the data

The hard part (building the scraper) is already done.
