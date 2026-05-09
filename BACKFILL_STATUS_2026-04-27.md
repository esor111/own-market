# Broker Flow Backfill Status — 2026-04-27

## Goal

Backfill historical broker-flow data for AHPC, RADHI, and RHPL from 2023-01-01 to 2025-12-31 to bring them in line with UPPER/AKPL/API coverage.

## Target Coverage

- **Before**: 70 files per symbol (Jan-Apr 2026 only, ~4 months)
- **Target**: ~470 files per symbol (2023-2026, ~3 years)
- **Benchmark**: UPPER has 328 files, AKPL has 388 files

## Current Status

### AHPC ✅ COMPLETE
- **Before**: 70 files (2026-01-01 to 2026-04-24)
- **After**: 467 files (2023-01-01 to 2026-04-24)
- **Added**: 397 files
- **Coverage**: ~3 years of broker-flow data

### RADHI ✅ COMPLETE
- **Before**: 70 files (2026-01-01 to 2026-04-24)
- **After**: 376 files (2023-01-01 to 2026-04-24)
- **Added**: 306 files
- **Coverage**: ~3 years of broker-flow data

### RHPL ⏳ IN PROGRESS
- **Current**: 110+ files (was 70)
- **Status**: Backfill process running (Terminal ID 3), adding ~3-5 files per minute
- **Target**: ~400 files (2023-2026)
- **ETA**: 1-2 hours

## Process Details

**Command**:
```bash
python backfill_merolagani_floorsheet.py \
  --symbol AHPC --symbol RADHI --symbol RHPL \
  --start-date 2023-01-01 --end-date 2025-12-31
```

**Background Process**: Terminal ID 5 (running)

**Log File**: `backfill_ahpc_radhi_rhpl_2023-2025.log`

## What This Unlocks

Once complete, all three symbols will have:
- **~400 trading days** of broker-flow history
- **Trustworthy avoid/buy signals** based on multi-year patterns instead of 4-month coincidences
- **Comparable coverage** to UPPER/AKPL/API for cross-symbol analysis

## Next Steps

1. Monitor RADHI/RHPL backfill completion (process still running)
2. Verify final file counts match target (~470 files per symbol)
3. Run coverage report to confirm data quality
4. Update psychology engine with expanded broker-flow data

## Technical Notes

- Script creates raw files first in `raw_merolagani/` folder, then converts to ledger files
- Without `--force` flag, existing ledger files are not overwritten
- Browser-based scraping is slow (~1-2 seconds per trading day per symbol)
- Expected total runtime: 2-4 hours for 3 symbols × ~400 days each
