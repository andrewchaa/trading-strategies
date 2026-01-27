# Quick Start Guide

Get started with OANDA historical data retrieval in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Credentials

1. Copy the config template:
```bash
cp config/oanda_config.ini.example config/oanda_config.ini
```

2. Get your OANDA API credentials:
   - Go to https://www.oanda.com/demo-account/tpa/personal_info
   - Sign up for a practice account
   - Navigate to: Account → Manage API Access → Generate Token

3. Edit `config/oanda_config.ini` with your credentials:
```ini
[practice]
api_token = your_token_here
account_id = your_account_id
```

## Step 3: Test Connection

Create a test script `test_connection.py`:

```python
from src.oanda_client import OandaClient

# Initialize client
client = OandaClient(environment='practice')

# Test connection
try:
    client.validate_connection()
    print("✓ Successfully connected to OANDA!")
    
    # Show available instruments
    instruments = client.get_instruments()
    print(f"✓ {len(instruments)} instruments available")
    print(f"  Examples: {instruments[:5]}")
    
except Exception as e:
    print(f"✗ Connection failed: {str(e)}")
```

Run it:
```bash
python test_connection.py
```

Expected output:
```
✓ Successfully connected to OANDA!
✓ 68 instruments available
  Examples: ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']
```

## Step 4: Fetch Your First Data

Create `fetch_data.py`:

```python
from src.oanda_client import OandaClient
from src.data_retriever import HistoricalDataRetriever
from src.data_storage import DataStorage

# Initialize
client = OandaClient(environment='practice')
retriever = HistoricalDataRetriever(client)
storage = DataStorage()

# Fetch EUR/USD hourly data for last 30 days
print("Fetching EUR/USD hourly data...")
df = retriever.fetch_historical_data(
    instrument='EUR_USD',
    granularity='H1',
    from_date='2024-01-01'
)

print(f"✓ Retrieved {len(df)} candles")
print(f"  Date range: {df['time'].min()} to {df['time'].max()}")
print("\nFirst 5 rows:")
print(df.head())

# Save to CSV
file_path = storage.save_to_csv(
    df=df,
    instrument='EUR_USD',
    granularity='H1',
    from_date='2024-01-01',
    to_date='2024-12-31'
)

print(f"\n✓ Saved to: {file_path}")
```

Run it:
```bash
python fetch_data.py
```

## Step 5: Use Jupyter Notebook (Recommended)

```bash
jupyter notebook notebooks/01_retrieve_historical_data.ipynb
```

The notebook includes:
- ✓ Interactive data retrieval
- ✓ Visualization examples
- ✓ Bulk download templates
- ✓ Data analysis samples

## Common Issues

### Issue: "Config file not found"
**Solution**: Make sure you copied `config/oanda_config.ini.example` to `config/oanda_config.ini`

### Issue: "Invalid credentials"
**Solution**: Check that you:
1. Generated an API token in your OANDA account
2. Copied the token and account ID correctly
3. Removed any extra spaces in the config file

### Issue: "Import requests could not be resolved"
**Solution**: Install dependencies: `pip install -r requirements.txt`

## Next Steps

✅ You're all set! Now you can:
1. Explore the Jupyter notebook for interactive usage
2. Check `EXAMPLES.md` for code examples
3. Read `README.md` for detailed documentation
4. Start building your trading strategies!

## Need Help?

- **Examples**: See `EXAMPLES.md`
- **Full Documentation**: See `README.md`
- **OANDA API Docs**: https://developer.oanda.com/rest-live-v20/introduction/

Happy Trading! 📈
