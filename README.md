# Trading Strategies - OANDA Historical Data Retrieval

A modular Python system for retrieving and storing historical forex data from OANDA's v20 API. Built for algorithmic trading strategy development and backtesting.

## Features

✅ **Flexible Data Retrieval**
- Support for all OANDA instruments (forex, commodities, indices)
- Multiple timeframes from 5-second to monthly candles
- Automatic pagination for large date ranges
- Handles OANDA's 5000 candle-per-request limit automatically

✅ **Dual Account Support**
- Practice account for development and testing
- Live account for production trading
- Easy switching via configuration

✅ **Organized Data Storage**
- CSV format for easy analysis
- Structured directory organization by instrument
- Metadata tracking in file headers
- Duplicate detection and removal

✅ **Interactive Interface**
- Jupyter notebook for easy data exploration
- Built-in visualization tools
- Bulk download capabilities
- Progress tracking and logging

## Project Structure

```
trading-strategies/
├── config/
│   ├── __init__.py
│   └── oanda_config.ini.example    # Configuration template
├── src/
│   ├── __init__.py
│   ├── oanda_client.py             # OANDA API wrapper
│   ├── data_retriever.py           # Data fetching logic
│   └── data_storage.py             # CSV storage handler
├── data/
│   └── historical/                 # CSV data files
├── notebooks/
│   └── 01_retrieve_historical_data.ipynb
├── logs/
│   └── data_retrieval.log          # Operation logs
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone or Download

```bash
git clone <your-repo-url>
cd trading-strategies
```

### 2. Create Virtual Environment (Recommended)

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n trading python=3.11
conda activate trading
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

# Install pre-commit hooks (protects against committing sensitive data)
pre-commit install
```

### 4. Configure OANDA Credentials

1. Copy the example config file:
```bash
cp config/oanda_config.ini.example config/oanda_config.ini
```

2. Get your OANDA credentials:
   - **Practice Account**: Visit [OANDA Demo](https://www.oanda.com/demo-account/tpa/personal_info)
   - **Live Account**: Visit [OANDA Live](https://www.oanda.com/account/tpa/personal_info)
   - **API Token**: Account → Manage API Access → Generate Token

3. Edit `config/oanda_config.ini` with your credentials:
```ini
[practice]
api_token = your_practice_token_here
account_id = your_practice_account_id

[live]
api_token = your_live_token_here
account_id = your_live_account_id
```

⚠️ **Security Note**: Never commit `oanda_config.ini` to version control. It's already in `.gitignore`.

## Quick Start

### Using Jupyter Notebook (Recommended)

```bash
jupyter notebook notebooks/01_retrieve_historical_data.ipynb
```

The notebook provides:
- Step-by-step guided data retrieval
- Interactive visualizations
- Multiple usage examples
- Bulk download templates

### Using Python Script

```python
from src.oanda_client import OandaClient
from src.data_retriever import HistoricalDataRetriever
from src.data_storage import DataStorage

# Initialize
client = OandaClient(environment='practice')
retriever = HistoricalDataRetriever(client)
storage = DataStorage()

# Fetch data
df = retriever.fetch_historical_data(
    instrument='EUR_USD',
    granularity='H1',
    from_date='2024-01-01',
    to_date='2024-12-31'
)

# Save to CSV
file_path = storage.save_to_csv(
    df=df,
    instrument='EUR_USD',
    granularity='H1',
    from_date='2024-01-01',
    to_date='2024-12-31'
)

print(f"Saved {len(df)} candles to {file_path}")
```

## Usage Examples

### Example 1: Single Instrument

```python
# Fetch EUR/USD hourly data for 2024
df = retriever.fetch_historical_data(
    instrument='EUR_USD',
    granularity='H1',
    from_date='2024-01-01'
)

print(f"Retrieved {len(df)} candles")
print(df.head())
```

### Example 2: Multiple Instruments

```python
# Fetch multiple major pairs
instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY']
data_dict = retriever.fetch_multiple_instruments(
    instruments=instruments,
    granularity='H4',
    from_date='2024-01-01'
)

for instrument, df in data_dict.items():
    print(f"{instrument}: {len(df)} candles")
```

### Example 3: Different Timeframes

```python
# Available granularities
granularities = {
    'S5': '5 seconds',
    'M1': '1 minute',
    'M15': '15 minutes',
    'H1': '1 hour',
    'H4': '4 hours',
    'D': 'Daily',
    'W': 'Weekly',
    'M': 'Monthly'
}

# Fetch daily data for longer historical period
df_daily = retriever.fetch_historical_data(
    instrument='EUR_USD',
    granularity='D',
    from_date='2020-01-01'
)
```

### Example 4: Load Saved Data

```python
# Load previously saved CSV
df = storage.load_from_csv('data/historical/EUR_USD/EUR_USD_H1_20240101_20241231.csv')

# List all available data
available = storage.list_available_data()
print(available)
```

## Supported Granularities

| Category | Granularities |
|----------|--------------|
| **Seconds** | S5, S10, S15, S30 |
| **Minutes** | M1, M2, M4, M5, M10, M15, M30 |
| **Hours** | H1, H2, H3, H4, H6, H8, H12 |
| **Daily+** | D (Daily), W (Weekly), M (Monthly) |

## Data Format

CSV files include the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `time` | datetime | Candle timestamp (UTC) |
| `open` | float | Opening price |
| `high` | float | Highest price |
| `low` | float | Lowest price |
| `close` | float | Closing price |
| `volume` | int | Trading volume |
| `complete` | bool | Whether candle is finalized |

## Rate Limits

OANDA API has the following limits:
- **2 new connections per second**
- **100 requests per second** on persistent connection
- **5000 candles maximum per request**

The system automatically handles these limits through:
- Persistent HTTP connections (requests.Session)
- Request throttling
- Automatic pagination with smart time-based iteration

## Logging

All operations are logged to `logs/data_retrieval.log`:

```
2026-01-19 22:15:30 [INFO] Starting data retrieval for EUR_USD (H1)
2026-01-19 22:15:31 [INFO] Retrieved 5000 candles (Request 1)
2026-01-19 22:15:35 [INFO] Retrieved 5000 candles (Request 2)
...
2026-01-19 22:16:46 [INFO] Saved to: data/historical/EUR_USD/...
```

## Troubleshooting

### Connection Errors

```
Error: Invalid credentials
```
**Solution**: Check `config/oanda_config.ini` has correct API token and account ID

### Import Errors

```
ModuleNotFoundError: No module named 'requests'
```
**Solution**: Install dependencies: `pip install -r requirements.txt`

### No Data Retrieved

```
Warning: No data retrieved for EUR_USD
```
**Solution**: 
- Check date range is valid
- Verify instrument name is correct: use `client.get_instruments()`
- Ensure market was open during requested period

## Next Steps

Now that you have historical data, you can:

1. **Develop Trading Strategies**
   - Implement technical indicators
   - Create entry/exit rules
   - Define risk management

2. **Backtest Strategies**
   - Test strategy performance on historical data
   - Calculate metrics (Sharpe ratio, drawdown, etc.)
   - Optimize parameters

3. **Analyze Market Patterns**
   - Identify trends and patterns
   - Statistical analysis
   - Correlation studies

4. **Build ML Models**
   - Price prediction
   - Signal generation
   - Pattern recognition

## API Reference

### OandaClient

```python
client = OandaClient(environment='practice', config_path='config/oanda_config.ini')
client.validate_connection()                    # Test connection
client.get_account_info()                       # Get account details
client.get_instruments()                        # List available instruments
client.get_instrument_details('EUR_USD')        # Get instrument info
```

### HistoricalDataRetriever

```python
retriever = HistoricalDataRetriever(oanda_client)

df = retriever.fetch_historical_data(
    instrument='EUR_USD',
    granularity='H1',
    from_date='2024-01-01',
    to_date='2024-12-31',
    price_type='MBA'  # Mid, Bid, Ask
)

data_dict = retriever.fetch_multiple_instruments(
    instruments=['EUR_USD', 'GBP_USD'],
    granularity='H4',
    from_date='2024-01-01'
)
```

### DataStorage

```python
storage = DataStorage(base_path='data/historical')

file_path = storage.save_to_csv(df, 'EUR_USD', 'H1', '2024-01-01', '2024-12-31')
df = storage.load_from_csv(file_path)
storage.append_to_existing(new_df, file_path)
start, end = storage.get_existing_data_range(file_path)
available = storage.list_available_data(instrument='EUR_USD')
```

## Contributing

Contributions are welcome! Areas for improvement:
- Additional data sources
- More storage backends (database support)
- Advanced backtesting framework
- Technical indicator library
- Strategy templates

## License

[Your License Here]

## Disclaimer

**Trading forex involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results. This software is for educational and research purposes only. Use at your own risk.**

## Resources

- [OANDA API Documentation](https://developer.oanda.com/rest-live-v20/introduction/)
- [OANDA REST API Endpoints](https://developer.oanda.com/rest-live-v20/instrument-ep/)
- [Forex Trading Basics](https://www.oanda.com/forex-trading/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the example notebook for usage patterns
3. Consult OANDA API documentation
4. Open an issue in the repository

---

**Happy Trading! 📈**
