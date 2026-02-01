# Plan: Auto-Download Missing Historical Data in RSI Backtest Notebook

## Objective
Update the notebook `notebooks/02_rsi_mean_reversion_backtest.ipynb` to automatically download missing historical data from OANDA API when the expected CSV file doesn't exist.

---

## Context

**Current Problem:**
- Notebook expects: `data/historical/EUR_USD/EUR_USD_M15_20250101_20251231.csv`
- This file does not exist
- Notebook fails at the "Load Historical Data" cell

**Existing Infrastructure:**
- `src/oanda_client.py` - OANDA API wrapper
- `src/data_retriever.py` - `HistoricalDataRetriever` class with `fetch_historical_data()` method
- `src/data_storage.py` - `DataStorage` class with `save_to_csv()` method
- `fetch_m15_eur_usd.py` - Example script showing usage pattern
- Config: `config/oanda_config.ini` - API credentials

**Existing Data Format (CSV with metadata comments):**
```
# Instrument: EUR_USD
# Granularity: M15
# Date Range: 2024-01-01 to 2024-12-31
# Records: 24861
# Retrieved: 2026-01-28 17:07:23 UTC
# Columns: time, open, high, low, close, volume, complete
time,open,high,low,close,volume,complete
2024-01-01 22:00:00+00:00,1.1044,1.10448,1.10438,1.10442,52,True
...
```

---

## Tasks

### Task 1: Update Imports Cell
**File:** `notebooks/02_rsi_mean_reversion_backtest.ipynb`
**Cell:** Cell 1 (Setup and Imports)

Add imports for data fetching capabilities:

```python
import sys
sys.path.append('..')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from backtesting import Backtest
from pathlib import Path
import os

# Import strategy classes
from src.strategies.rsi_mean_reversion import RSIMeanReversion, RSIMeanReversionOptimized

# Import data fetching classes (for auto-download)
from src.oanda_client import OandaClient
from src.data_retriever import HistoricalDataRetriever
from src.data_storage import DataStorage

# Configure pandas display
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_rows', 100)

# Set visualization style
plt.style.use('seaborn-v0_8-darkgrid')

print("✓ Imports successful")
```

**Changes:**
- Add `import os`
- Add imports for `OandaClient`, `HistoricalDataRetriever`, `DataStorage`

---

### Task 2: Update Configuration Cell
**File:** `notebooks/02_rsi_mean_reversion_backtest.ipynb`
**Cell:** Cell 2 (Configuration)

Update to use 2024 dates (we have this data, and 2025 is incomplete):

```python
# Data parameters
INSTRUMENT = 'EUR_USD'
GRANULARITY = 'M15'
FROM_DATE = '20240101'
TO_DATE = '20241231'

# Backtest parameters
INITIAL_CASH = 10000
COMMISSION = 0.0001  # 1 pip for forex

# File paths
DATA_DIR = Path('../data/historical')
DATA_PATH = DATA_DIR / INSTRUMENT / f'{INSTRUMENT}_{GRANULARITY}_{FROM_DATE}_{TO_DATE}.csv'

# API configuration path
CONFIG_PATH = Path('../config/oanda_config.ini')

print(f"Configuration:")
print(f"  Instrument: {INSTRUMENT}")
print(f"  Timeframe: {GRANULARITY}")
print(f"  Period: {FROM_DATE} to {TO_DATE}")
print(f"  Initial Capital: ${INITIAL_CASH:,.2f}")
print(f"  Commission: {COMMISSION*100:.2f}%")
print(f"  Data Path: {DATA_PATH}")
print(f"  Data Exists: {DATA_PATH.exists()}")
```

**Changes:**
- Change `FROM_DATE` from `'20250101'` to `'20240101'`
- Change `TO_DATE` from `'20251231'` to `'20241231'`
- Add `DATA_DIR` variable
- Add `CONFIG_PATH` variable
- Add print statement showing if data exists

---

### Task 3: Replace Data Loading Cell with Auto-Download Logic
**File:** `notebooks/02_rsi_mean_reversion_backtest.ipynb`
**Cell:** Cell 3 (Load Historical Data)

Replace the entire cell content with logic that checks for data and downloads if missing:

```python
def fetch_and_save_data(instrument: str, granularity: str, from_date: str, to_date: str) -> pd.DataFrame:
    """
    Fetch historical data from OANDA API and save to CSV.
    
    Args:
        instrument: Currency pair (e.g., 'EUR_USD')
        granularity: Timeframe (e.g., 'M15')
        from_date: Start date in YYYYMMDD format
        to_date: End date in YYYYMMDD format
        
    Returns:
        DataFrame with OHLCV data
    """
    print(f"Fetching {instrument} {granularity} data from OANDA API...")
    print(f"Date range: {from_date} to {to_date}")
    
    # Convert YYYYMMDD to YYYY-MM-DD for API
    from_date_api = f"{from_date[:4]}-{from_date[4:6]}-{from_date[6:8]}"
    to_date_api = f"{to_date[:4]}-{to_date[4:6]}-{to_date[6:8]}"
    
    # Initialize OANDA client
    client = OandaClient(environment='practice', config_path=str(CONFIG_PATH))
    print("✓ OANDA client initialized")
    
    # Initialize data retriever
    retriever = HistoricalDataRetriever(client)
    
    # Fetch data
    df = retriever.fetch_historical_data(
        instrument=instrument,
        granularity=granularity,
        from_date=from_date_api,
        to_date=to_date_api
    )
    
    if df.empty:
        raise ValueError(f"No data retrieved for {instrument}")
    
    print(f"✓ Retrieved {len(df):,} candles")
    
    # Save to CSV
    storage = DataStorage(base_path=str(DATA_DIR))
    file_path = storage.save_to_csv(
        df=df,
        instrument=instrument,
        granularity=granularity,
        from_date=from_date_api,
        to_date=to_date_api
    )
    print(f"✓ Saved to: {file_path}")
    
    return df


def load_data(data_path: Path) -> pd.DataFrame:
    """
    Load data from CSV file.
    
    Args:
        data_path: Path to CSV file
        
    Returns:
        DataFrame formatted for backtesting.py
    """
    print(f"Loading data from: {data_path}")
    
    # Read CSV, skipping header comments (lines starting with #)
    df = pd.read_csv(data_path, comment='#', parse_dates=['time'], index_col='time')
    
    # Rename columns to match backtesting.py expectations (capitalized)
    df.columns = [col.capitalize() for col in df.columns]
    
    # Keep only required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df[[col for col in required_cols if col in df.columns]]
    
    return df


# Main data loading logic
print("=" * 60)
print("LOADING HISTORICAL DATA")
print("=" * 60)

if DATA_PATH.exists():
    print(f"✓ Data file found: {DATA_PATH}")
    df = load_data(DATA_PATH)
else:
    print(f"✗ Data file not found: {DATA_PATH}")
    print(f"  Downloading from OANDA API...")
    print()
    
    # Fetch and save data
    raw_df = fetch_and_save_data(INSTRUMENT, GRANULARITY, FROM_DATE, TO_DATE)
    
    # Load the saved file (to ensure consistent formatting)
    df = load_data(DATA_PATH)

print(f"\n✓ Loaded {len(df):,} candles")
print(f"  Date range: {df.index.min()} to {df.index.max()}")
print(f"  Duration: {(df.index.max() - df.index.min()).days} days")
print(f"\nData sample:")
display(df.head())
print("\nPrice statistics:")
display(df.describe())
```

**Key Changes:**
1. Add `fetch_and_save_data()` function that uses OANDA API
2. Add `load_data()` helper function
3. Check if `DATA_PATH.exists()` before loading
4. If file doesn't exist, automatically fetch from API and save
5. Use `comment='#'` to skip metadata lines (cleaner than `skiprows=3`)
6. Dynamically capitalize column names instead of hardcoding

---

### Task 4: Update Candlestick Chart Title
**File:** `notebooks/02_rsi_mean_reversion_backtest.ipynb`  
**Cell:** Cell 4 (Visualize Price Data)

Make the title dynamic based on the configured year:

```python
# Create candlestick chart
fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name=INSTRUMENT
)])

fig.update_layout(
    title=f'{INSTRUMENT} {GRANULARITY} - {FROM_DATE[:4]}',
    yaxis_title='Price',
    xaxis_title='Date',
    height=600,
    xaxis_rangeslider_visible=False
)

fig.show()
```

**Changes:**
- Change `title=f'{INSTRUMENT} {GRANULARITY} - Full 2024'` to `title=f'{INSTRUMENT} {GRANULARITY} - {FROM_DATE[:4]}'`
- Change `name='EUR_USD'` to `name=INSTRUMENT`

---

## Verification Steps

After implementing these changes:

1. **Test with existing data (2024):**
   - Set `FROM_DATE = '20240101'` and `TO_DATE = '20241231'`
   - Run notebook - should load existing CSV without API call
   - Verify: "✓ Data file found" message appears

2. **Test with missing data:**
   - Change dates to a period without cached data (e.g., `FROM_DATE = '20230101'`)
   - Run notebook - should download from API and create new CSV
   - Verify: "✗ Data file not found" and "Downloading from OANDA API..." messages appear
   - Verify: New CSV file created in `data/historical/EUR_USD/`

3. **Test backtest execution:**
   - Run the full notebook through all cells
   - Verify: Backtest runs successfully with loaded data
   - Verify: Charts and statistics display correctly

---

## Error Handling Notes

The notebook should handle these error cases gracefully:

1. **Missing OANDA config:** If `config/oanda_config.ini` doesn't exist or has invalid credentials, the `OandaClient` will raise an informative error.

2. **API rate limits:** The `HistoricalDataRetriever` already handles pagination and rate limiting.

3. **Empty data:** If API returns no data (e.g., invalid date range), a `ValueError` is raised with a clear message.

4. **Partial year data:** For current year (2025), only available data up to current date will be fetched.

---

## Summary of File Changes

| File | Changes |
|------|---------|
| `notebooks/02_rsi_mean_reversion_backtest.ipynb` | Update 4 cells: imports, config, data loading, chart title |

Total: 1 file, 4 cell modifications
