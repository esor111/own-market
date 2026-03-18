# Stock Analysis Automation

Automated stock analysis using Playwright browser automation.

## Setup

1. Install Python dependencies:
```bash
cd market-gist/automation
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

### Basic Analysis
```bash
python analyze_stock.py SMHL 1W
```

### Parameters
- `SYMBOL`: Stock symbol (e.g., SMHL, NABIL)
- `TIMEFRAME`: Chart timeframe (1D, 1W, 1M) - default is 1W

### Examples
```bash
# Analyze SMHL on weekly chart
python analyze_stock.py SMHL 1W

# Analyze NABIL on daily chart
python analyze_stock.py NABIL 1D

# Batch analyze a saved list
python batch_analyze.py 1W @core_reliability

# Run the full reliability cycle for a saved list
python run_reliability_cycle.py 1W @core_reliability

# Check which symbols in a list have sector mappings
python symbol_coverage.py @core_reliability

# Re-evaluate only pending outcomes for an existing run
python reevaluate_pending_outcomes.py 2026-03-18 1W @expanded_reliability

# Build a simple follow-up queue from the latest cycle
python followup_queue.py 2026-03-18 1W

# Run the full daily follow-up in one command
python daily_followup.py 2026-03-18 1W @expanded_reliability
```

## Output

The script generates:

### Raw Evidence Files
- `data/raw/screenshots/` - Chart screenshots
- `data/raw/snapshots/` - Page snapshots
- `data/raw/tables/` - Extracted data JSON

### Normalized Records
- `data/normalized/sessions/` - Session metadata
- `data/normalized/market/` - Market context
- `data/normalized/sectors/` - Sector data
- `data/normalized/stocks/` - Stock chart data
- `data/normalized/indicators/` - Technical indicators
- `data/normalized/relative_strength/` - RS analysis
- `data/normalized/decisions/` - Trading decisions
- `data/normalized/events/` - Corporate events
- `data/normalized/broker_flow/` - Broker flow data

### Feature Scores
- `data/features/setup_scores/` - Setup quality scores

## Configuration

Edit `config.py` to customize:
- Browser settings (headless mode, timeouts)
- Indicator configuration
- Scoring rules
- Decision thresholds

Maintain reusable symbols in `symbol_lists.json`.
Maintain symbol-to-sector coverage in `sector_map.json`.

## Architecture

- `analyze_stock.py` - Main automation script
- `browser_actions.py` - Playwright browser automation
- `data_extractor.py` - Data extraction and parsing
- `analyzer.py` - Scoring and decision logic
- `file_generator.py` - JSON file generation
- `config.py` - Configuration settings

## Troubleshooting

### Browser not found
```bash
playwright install chromium
```

### Timeout errors
Increase `BROWSER_TIMEOUT` in `config.py`

### Element not found
The script may need adjustments if NEPSE Alpha UI changes

## Limitations

- Data extraction is partially automated (some values are placeholders)
- Pattern recognition for support/resistance is simplified
- Broker flow data requires login (not automated)
- OCR not implemented for text extraction from charts

## Future Improvements

- [ ] Full OCR integration for data extraction
- [ ] Advanced pattern recognition
- [ ] Historical data comparison
- [ ] Multi-symbol batch processing
- [ ] Email/Slack notifications
- [ ] Database storage
- [ ] REST API wrapper
