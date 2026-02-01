# Plan: Fix RSI Backtest Notebook Data Dates

## Context
The notebook `notebooks/02_rsi_mean_reversion_backtest.ipynb` is configured to load data for 2025, but only 2024 data exists.

**Current state:**
- Notebook expects: `data/historical/EUR_USD/EUR_USD_M15_20250101_20251231.csv`
- Existing file: `data/historical/EUR_USD/EUR_USD_M15_20240101_20241231.csv` (1.6MB, exists)

## Tasks

### Task 1: Update Notebook Date Configuration
**File:** `notebooks/02_rsi_mean_reversion_backtest.ipynb`

In the Configuration cell (cell 2), change:
```python
# FROM:
FROM_DATE = '20250101'
TO_DATE = '20251231'

# TO:
FROM_DATE = '20240101'
TO_DATE = '20241231'
```

### Task 2: Update Dynamic Title Reference
**File:** `notebooks/02_rsi_mean_reversion_backtest.ipynb`

In the candlestick chart cell, the title is hardcoded. Change:
```python
# FROM:
title=f'{INSTRUMENT} {GRANULARITY} - Full 2024',

# TO:
title=f'{INSTRUMENT} {GRANULARITY} - Full {FROM_DATE[:4]}',
```

This makes the title dynamic based on the FROM_DATE year.

## Verification
After changes, the notebook should:
1. Successfully load the CSV from `data/historical/EUR_USD/EUR_USD_M15_20240101_20241231.csv`
2. Display ~35,000 M15 candles for EUR_USD (2024 full year)
3. Run backtest successfully

## Alternative Option
If user wants 2025 data instead, create a new fetch script to download available 2025 data (partial year, Jan-present). This would require running the OANDA API fetcher.
