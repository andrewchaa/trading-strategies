# OANDA Data Retrieval - Usage Examples

This document provides practical examples for retrieving historical forex data using the OANDA API wrapper.

## Table of Contents
1. [Basic Setup](#basic-setup)
2. [Single Instrument Retrieval](#single-instrument-retrieval)
3. [Multiple Instruments](#multiple-instruments)
4. [Different Timeframes](#different-timeframes)
5. [Date Range Specifications](#date-range-specifications)
6. [Working with Saved Data](#working-with-saved-data)
7. [Bulk Downloads](#bulk-downloads)
8. [Data Analysis Examples](#data-analysis-examples)

---

## Basic Setup

```python
from src.oanda_client import OandaClient
from src.data_retriever import HistoricalDataRetriever
from src.data_storage import DataStorage
import pandas as pd
from datetime import datetime, timedelta

# Initialize components
client = OandaClient(environment='practice')
retriever = HistoricalDataRetriever(client)
storage = DataStorage()

# Validate connection
client.validate_connection()
print("✓ Connected to OANDA")
```

---

## Single Instrument Retrieval

### Example 1: EUR/USD Hourly Data

```python
# Fetch EUR/USD hourly candles for 2024
df = retriever.fetch_historical_data(
    instrument='EUR_USD',
    granularity='H1',
    from_date='2024-01-01',
    to_date='2024-12-31'
)

# Display summary
print(f"Retrieved {len(df)} candles")
print(f"Date range: {df['time'].min()} to {df['time'].max()}")
print(f"Price range: {df['low'].min():.5f} to {df['high'].max():.5f}")

# Preview data
print(df.head())

# Save to CSV
file_path = storage.save_to_csv(
    df=df,
    instrument='EUR_USD',
    granularity='H1',
    from_date='2024-01-01',
    to_date='2024-12-31'
)
print(f"Saved to: {file_path}")
```

### Example 2: GBP/USD with Auto End Date

```python
# Fetch GBP/USD from specific date to now
df = retriever.fetch_historical_data(
    instrument='GBP_USD',
    granularity='H4',
    from_date='2024-06-01'
    # to_date is optional - defaults to now
)

print(f"Retrieved {len(df)} 4-hour candles")
```

---

## Multiple Instruments

### Example 3: Major Forex Pairs

```python
# Define major pairs
major_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF']

# Fetch all at once
data_dict = retriever.fetch_multiple_instruments(
    instruments=major_pairs,
    granularity='H1',
    from_date='2024-01-01'
)

# Process results
for instrument, df in data_dict.items():
    print(f"\n{instrument}:")
    print(f"  Candles: {len(df)}")
    print(f"  Date range: {df['time'].min()} to {df['time'].max()}")
    
    # Save each
    storage.save_to_csv(
        df=df,
        instrument=instrument,
        granularity='H1',
        from_date='2024-01-01',
        to_date=datetime.now().strftime('%Y-%m-%d')
    )

print("\n✓ All instruments saved")
```

### Example 4: Cross Pairs

```python
# Fetch cross pairs (non-USD pairs)
cross_pairs = ['EUR_GBP', 'EUR_JPY', 'GBP_JPY']

data_dict = retriever.fetch_multiple_instruments(
    instruments=cross_pairs,
    granularity='D',  # Daily data
    from_date='2023-01-01'
)

print(f"Retrieved data for {len(data_dict)} cross pairs")
```

---

## Different Timeframes

### Example 5: Multiple Timeframes for Same Instrument

```python
instrument = 'EUR_USD'
granularities = ['M15', 'H1', 'H4', 'D']
from_date = '2024-01-01'

results = {}
for gran in granularities:
    print(f"Fetching {instrument} {gran}...")
    
    df = retriever.fetch_historical_data(
        instrument=instrument,
        granularity=gran,
        from_date=from_date
    )
    
    results[gran] = df
    
    # Save
    storage.save_to_csv(
        df=df,
        instrument=instrument,
        granularity=gran,
        from_date=from_date,
        to_date=datetime.now().strftime('%Y-%m-%d')
    )
    
    print(f"  ✓ {len(df)} candles saved")

# Compare candle counts
print("\nCandle counts by timeframe:")
for gran, df in results.items():
    print(f"  {gran}: {len(df):,} candles")
```

### Example 6: High-Frequency Data

```python
# Fetch 5-second candles for recent data
df = retriever.fetch_historical_data(
    instrument='EUR_USD',
    granularity='S5',
    from_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
)

print(f"Retrieved {len(df):,} 5-second candles")
print(f"Data covers: {(df['time'].max() - df['time'].min()).total_seconds() / 3600:.1f} hours")
```

---

## Date Range Specifications

### Example 7: Different Date Formats

```python
instrument = 'USD_JPY'
granularity = 'H1'

# Format 1: Simple date
df1 = retriever.fetch_historical_data(
    instrument=instrument,
    granularity=granularity,
    from_date='2024-01-01',
    to_date='2024-06-30'
)

# Format 2: ISO 8601 with time
df2 = retriever.fetch_historical_data(
    instrument=instrument,
    granularity=granularity,
    from_date='2024-07-01T00:00:00Z',
    to_date='2024-12-31T23:59:59Z'
)

print(f"Q1-Q2: {len(df1)} candles")
print(f"Q3-Q4: {len(df2)} candles")
```

### Example 8: Relative Date Ranges

```python
from datetime import datetime, timedelta

# Last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

df = retriever.fetch_historical_data(
    instrument='EUR_USD',
    granularity='H1',
    from_date=start_date.strftime('%Y-%m-%d'),
    to_date=end_date.strftime('%Y-%m-%d')
)

print(f"Last 30 days: {len(df)} hourly candles")

# Last 3 months of daily data
start_date = end_date - timedelta(days=90)

df = retriever.fetch_historical_data(
    instrument='EUR_USD',
    granularity='D',
    from_date=start_date.strftime('%Y-%m-%d')
)

print(f"Last 90 days: {len(df)} daily candles")
```

---

## Working with Saved Data

### Example 9: Load and Analyze

```python
# Load previously saved data
file_path = 'data/historical/EUR_USD/EUR_USD_H1_20240101_20241231.csv'
df = storage.load_from_csv(file_path)

print(f"Loaded {len(df)} candles")

# Basic statistics
print("\nPrice Statistics:")
print(df[['open', 'high', 'low', 'close']].describe())

# Calculate returns
df['returns'] = df['close'].pct_change()
print(f"\nAverage return: {df['returns'].mean():.6f}")
print(f"Volatility (std): {df['returns'].std():.6f}")
```

### Example 10: List Available Data

```python
# List all saved data files
available = storage.list_available_data()

print(f"Total data files: {len(available)}")
print("\nAvailable data:")
print(available[['instrument', 'granularity', 'record_count', 'from_date']])

# Filter for specific instrument
eur_usd_data = storage.list_available_data(instrument='EUR_USD')
print(f"\nEUR_USD files: {len(eur_usd_data)}")
```

### Example 11: Append New Data

```python
# Load existing data
file_path = 'data/historical/EUR_USD/EUR_USD_H1_20240101_20241231.csv'
existing_df = storage.load_from_csv(file_path)
print(f"Existing data: {len(existing_df)} candles")
print(f"Last date: {existing_df['time'].max()}")

# Fetch new data since last date
last_date = existing_df['time'].max()
new_df = retriever.fetch_historical_data(
    instrument='EUR_USD',
    granularity='H1',
    from_date=last_date.strftime('%Y-%m-%d')
)

print(f"New data: {len(new_df)} candles")

# Append to existing file
updated_path = storage.append_to_existing(
    df=new_df,
    file_path=file_path,
    remove_duplicates=True
)

print(f"✓ Updated file: {updated_path}")
```

---

## Bulk Downloads

### Example 12: Complete Historical Dataset

```python
# Configuration for comprehensive data collection
configs = [
    # EUR/USD - Multiple timeframes
    {'instrument': 'EUR_USD', 'granularity': 'M1', 'from': '2024-12-01'},
    {'instrument': 'EUR_USD', 'granularity': 'M15', 'from': '2024-01-01'},
    {'instrument': 'EUR_USD', 'granularity': 'H1', 'from': '2023-01-01'},
    {'instrument': 'EUR_USD', 'granularity': 'H4', 'from': '2022-01-01'},
    {'instrument': 'EUR_USD', 'granularity': 'D', 'from': '2020-01-01'},
    
    # Major pairs - Daily
    {'instrument': 'GBP_USD', 'granularity': 'D', 'from': '2020-01-01'},
    {'instrument': 'USD_JPY', 'granularity': 'D', 'from': '2020-01-01'},
    {'instrument': 'USD_CHF', 'granularity': 'D', 'from': '2020-01-01'},
    
    # Cross pairs - Daily
    {'instrument': 'EUR_GBP', 'granularity': 'D', 'from': '2020-01-01'},
    {'instrument': 'EUR_JPY', 'granularity': 'D', 'from': '2020-01-01'},
]

print(f"Starting bulk download: {len(configs)} datasets\n")

results = []
for i, config in enumerate(configs, 1):
    print(f"[{i}/{len(configs)}] {config['instrument']} {config['granularity']}...")
    
    try:
        # Fetch
        df = retriever.fetch_historical_data(**config)
        
        # Save
        file_path = storage.save_to_csv(
            df=df,
            instrument=config['instrument'],
            granularity=config['granularity'],
            from_date=config['from'],
            to_date=datetime.now().strftime('%Y-%m-%d')
        )
        
        results.append({
            'instrument': config['instrument'],
            'granularity': config['granularity'],
            'candles': len(df),
            'status': '✓'
        })
        
        print(f"  ✓ {len(df):,} candles\n")
        
    except Exception as e:
        results.append({
            'instrument': config['instrument'],
            'granularity': config['granularity'],
            'candles': 0,
            'status': f'✗ {str(e)}'
        })
        print(f"  ✗ Error: {str(e)}\n")

# Summary
results_df = pd.DataFrame(results)
print("\n" + "="*60)
print("BULK DOWNLOAD COMPLETE")
print("="*60)
print(results_df)
print(f"\nTotal candles downloaded: {results_df['candles'].sum():,}")
```

---

## Data Analysis Examples

### Example 13: Calculate Technical Indicators

```python
# Load data
df = storage.load_from_csv('data/historical/EUR_USD/EUR_USD_H1_20240101_20241231.csv')

# Simple Moving Averages
df['SMA_20'] = df['close'].rolling(window=20).mean()
df['SMA_50'] = df['close'].rolling(window=50).mean()
df['SMA_200'] = df['close'].rolling(window=200).mean()

# Relative Strength Index (RSI)
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# Bollinger Bands
df['BB_middle'] = df['close'].rolling(window=20).mean()
df['BB_std'] = df['close'].rolling(window=20).std()
df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)

print("Technical indicators calculated:")
print(df[['time', 'close', 'SMA_20', 'SMA_50', 'RSI']].tail())
```

### Example 14: Volatility Analysis

```python
# Load data
df = storage.load_from_csv('data/historical/EUR_USD/EUR_USD_D_20200101_20241231.csv')

# Calculate returns
df['returns'] = df['close'].pct_change()

# Rolling volatility (20-day)
df['volatility_20'] = df['returns'].rolling(window=20).std() * (252 ** 0.5)  # Annualized

# True Range
df['TR'] = df[['high', 'close']].max(axis=1) - df[['low', 'close']].min(axis=1)
df['ATR_14'] = df['TR'].rolling(window=14).mean()

print("Volatility metrics:")
print(df[['time', 'close', 'volatility_20', 'ATR_14']].tail(10))

# Plot
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

ax1.plot(df['time'], df['close'])
ax1.set_title('EUR/USD Daily Close Price')
ax1.set_ylabel('Price')
ax1.grid(True, alpha=0.3)

ax2.plot(df['time'], df['volatility_20'])
ax2.set_title('20-Day Rolling Volatility (Annualized)')
ax2.set_ylabel('Volatility')
ax2.set_xlabel('Date')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
```

### Example 15: Correlation Analysis

```python
# Load multiple instruments
instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'EUR_GBP']
dfs = {}

for instrument in instruments:
    file_path = f'data/historical/{instrument}/{instrument}_D_20200101_20241231.csv'
    df = storage.load_from_csv(file_path)
    dfs[instrument] = df[['time', 'close']].set_index('time')

# Combine into single DataFrame
combined = pd.DataFrame({
    instr: df['close'] for instr, df in dfs.items()
})

# Calculate returns
returns = combined.pct_change()

# Correlation matrix
correlation = returns.corr()
print("Correlation Matrix:")
print(correlation)

# Visualize
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 8))
sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0, 
            square=True, linewidths=1, cbar_kws={"shrink": 0.8})
plt.title('Forex Pairs Correlation Matrix (Daily Returns)')
plt.tight_layout()
plt.show()
```

---

## Advanced Usage

### Example 16: Custom Price Types

```python
# Fetch bid, mid, and ask prices
df = retriever.fetch_historical_data(
    instrument='EUR_USD',
    granularity='H1',
    from_date='2024-01-01',
    price_type='MBA'  # Mid, Bid, Ask (default)
)

# Calculate bid-ask spread (if using multiple price types)
# Note: Default implementation uses 'mid' price
# For actual bid-ask spread, you'd need to parse the raw API response

print(df.head())
```

### Example 17: Error Handling

```python
instruments = ['EUR_USD', 'INVALID_PAIR', 'GBP_USD']

for instrument in instruments:
    try:
        df = retriever.fetch_historical_data(
            instrument=instrument,
            granularity='H1',
            from_date='2024-01-01'
        )
        print(f"✓ {instrument}: {len(df)} candles")
        
    except ValueError as e:
        print(f"✗ {instrument}: {str(e)}")
        
    except Exception as e:
        print(f"✗ {instrument}: Unexpected error - {str(e)}")
```

---

## Tips & Best Practices

1. **Start with Daily Data**: Test your setup with daily or 4-hour data before downloading large minute-level datasets

2. **Use Appropriate Timeframes**: 
   - Intraday strategies → M1, M5, M15, H1
   - Swing trading → H4, D
   - Position trading → D, W

3. **Incremental Updates**: Use `append_to_existing()` to add new data without re-downloading everything

4. **Rate Limiting**: The system handles OANDA rate limits automatically, but be patient with large downloads

5. **Storage**: Daily data for 5 years ≈ 1-2 MB. Hourly data ≈ 10-20 MB. Plan storage accordingly.

6. **Validation**: Always check date ranges and candle counts after download to ensure completeness

---

For more examples, see the Jupyter notebook: `notebooks/01_retrieve_historical_data.ipynb`
