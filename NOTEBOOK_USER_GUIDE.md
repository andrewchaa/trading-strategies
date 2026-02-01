# Using the Updated RSI Backtest Notebook

## What Changed?

The notebook now **automatically downloads missing historical data** from OANDA API. No more manual data retrieval!

---

## Quick Start

### Option 1: Use Existing 2024 Data (Default)

Just open and run the notebook:

```bash
jupyter notebook notebooks/02_rsi_mean_reversion_backtest.ipynb
```

The notebook is pre-configured to use cached 2024 data:
- ✓ Data file exists: `EUR_USD_M15_20240101_20241231.csv`
- ✓ 24,861 candles ready to use
- ✓ No API call needed

### Option 2: Download Different Data

Change the configuration in **Cell 2**:

```python
# Example: Get 2023 data
FROM_DATE = '20230101'
TO_DATE = '20231231'

# Example: Get different instrument
INSTRUMENT = 'GBP_USD'
GRANULARITY = 'H1'
```

Then run the notebook. It will:
1. Check if data file exists
2. If not → Download from OANDA API
3. Save to CSV for future use
4. Load and run backtest

---

## Cell-by-Cell Guide

### Cell 1: Imports
**New imports added:**
- `OandaClient` - connects to OANDA API
- `HistoricalDataRetriever` - fetches historical data
- `DataStorage` - saves/loads CSV files

### Cell 2: Configuration
**What to change:**
```python
INSTRUMENT = 'EUR_USD'      # Change to any forex pair
GRANULARITY = 'M15'         # Change to M1, H1, H4, D, etc.
FROM_DATE = '20240101'      # Start date (YYYYMMDD)
TO_DATE = '20241231'        # End date (YYYYMMDD)
```

**What you'll see:**
```
Configuration:
  Instrument: EUR_USD
  Timeframe: M15
  Period: 20240101 to 20241231
  Initial Capital: $10,000.00
  Commission: 0.01%
  Data Path: ../data/historical/EUR_USD/EUR_USD_M15_20240101_20241231.csv
  Data Exists: True  ← Shows if data is cached
```

### Cell 3: Load Historical Data
**Automatic logic:**

**If data exists:**
```
✓ Data file found: ../data/historical/EUR_USD/...
Loading data from: ...
✓ Loaded 24,861 candles
```

**If data missing:**
```
✗ Data file not found: ...
  Downloading from OANDA API...

Fetching EUR_USD M15 data from OANDA API...
✓ OANDA client initialized
✓ Retrieved 24,861 candles
✓ Saved to: data/historical/EUR_USD/...
✓ Loaded 24,861 candles
```

### Cell 4+: Rest of Notebook
No changes needed. Backtest runs as before.

---

## Common Use Cases

### 1. Backtest on Different Year
```python
FROM_DATE = '20230101'
TO_DATE = '20231231'
```
→ Downloads 2023 data if not cached

### 2. Backtest on Different Instrument
```python
INSTRUMENT = 'GBP_USD'
```
→ Downloads GBP_USD data if not cached

### 3. Backtest on Different Timeframe
```python
GRANULARITY = 'H1'  # 1-hour candles
```
→ Downloads H1 data if not cached

### 4. Backtest on Current Year (Partial)
```python
FROM_DATE = '20250101'
TO_DATE = '20251231'
```
→ Downloads available 2025 data (Jan to present)

---

## Requirements

### 1. OANDA API Credentials

If downloading new data, you need OANDA credentials in `config/oanda_config.ini`:

```ini
[practice]
api_token = your_practice_token_here
account_id = your_practice_account_id

[live]
api_token = your_live_token_here
account_id = your_live_account_id
```

**Don't have this?** Copy from example:
```bash
cp config/oanda_config.ini.example config/oanda_config.ini
# Then edit with your credentials
```

**Get credentials:** [OANDA Demo Account](https://www.oanda.com/demo-account/)

### 2. Python Packages

All required packages should already be installed:
- pandas, numpy, matplotlib, plotly
- backtesting
- requests, pytz (for OANDA API)

---

## Troubleshooting

### Error: "File not found: config/oanda_config.ini"
**Solution:** Create config file with your OANDA credentials (see Requirements above)

### Error: "Invalid credentials"
**Solution:** Check your API token and account ID in `config/oanda_config.ini`

### Error: "No data retrieved for EUR_USD"
**Solution:** 
- Check date range is valid (not in the future)
- Verify OANDA API is accessible
- Try shorter date range (e.g., 1 month instead of 1 year)

### Notebook takes long time on first run
**Normal:** Downloading 1 year of M15 data takes 2-5 minutes (25,000+ candles)
- Future runs will be instant (data is cached)
- Try shorter date range for faster testing

### Downloaded wrong data / want to re-download
**Solution:** Delete the CSV file and re-run:
```bash
rm data/historical/EUR_USD/EUR_USD_M15_20240101_20241231.csv
# Then re-run Cell 3
```

---

## Tips

1. **Cache is your friend:** Once data is downloaded, it's saved. Future runs are instant.

2. **Start small:** Test with 1 month of data first, then expand to full year:
   ```python
   FROM_DATE = '20240101'
   TO_DATE = '20240131'  # Just January
   ```

3. **Multiple instruments:** Change `INSTRUMENT` and re-run to compare different pairs

4. **Different timeframes:** Try M15, H1, H4, D to see how strategy performs on different timeframes

5. **Organized storage:** Data is saved in:
   ```
   data/historical/
   ├── EUR_USD/
   │   ├── EUR_USD_M15_20240101_20241231.csv
   │   └── EUR_USD_H1_20240101_20241231.csv
   ├── GBP_USD/
   │   └── GBP_USD_M15_20240101_20241231.csv
   └── ...
   ```

---

## What's Next?

After running the basic backtest:

1. **Try optimized strategy** (Cell 7) - uses additional filters
2. **Run parameter optimization** (Cell 8) - finds best RSI/BB settings
3. **Compare different instruments** - change `INSTRUMENT` and compare results
4. **Test different timeframes** - change `GRANULARITY` to see what works best
5. **Analyze trade distribution** - review winning/losing trade patterns

---

## Support

- **Project README:** `README.md` - full documentation
- **Plan document:** `.sisyphus/plan-auto-download-historical-data.md`
- **Implementation summary:** `IMPLEMENTATION_SUMMARY.md`
- **Test script:** `test_notebook_data_loading.py` - verify setup

Happy backtesting! 📈
