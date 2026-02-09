# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a forex trading strategy development and backtesting system using OANDA's v20 REST API. The project focuses on algorithmic trading strategy development with proper multi-timeframe analysis and backtesting capabilities.

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks (CRITICAL - prevents committing sensitive data)
pre-commit install

# Configure OANDA credentials
cp config/oanda_config.ini.example config/oanda_config.ini
# Edit config/oanda_config.ini with your API credentials
```

## Common Commands

### Running Backtests
```bash
# Run strategy backtest scripts directly
python test_mtf_strategy.py
python src/backtest_rsi.py

# Or use Jupyter notebooks (recommended for interactive analysis)
jupyter notebook notebooks/02_rsi_mean_reversion_backtest.ipynb
jupyter notebook notebooks/03_vwap_hma_crossover_backtest.ipynb
```

### Data Retrieval
```bash
# Fetch historical data using scripts
python fetch_m15_eur_usd.py

# Or use the interactive notebook
jupyter notebook notebooks/01_retrieve_historical_data.ipynb
```

### Running Tests
```bash
# Run specific test file
python test_mtf_strategy.py
python test_notebook_data_loading.py

# Note: There is no pytest setup yet - tests are standalone Python scripts
```

## Architecture

### Core Components

1. **OANDA API Layer** (`src/oanda_client.py`)
   - Handles authentication and connection to OANDA v20 REST API
   - Provides persistent HTTP session management
   - Supports both practice and live environments
   - All API communication goes through this client

2. **Data Retrieval** (`src/data_retriever.py`)
   - Fetches historical candlestick data with automatic pagination
   - Handles OANDA's 5000 candle-per-request limit transparently
   - Supports all OANDA granularities (S5 to M - seconds to monthly)
   - Converts API responses to pandas DataFrames

3. **Data Storage** (`src/data_storage.py`)
   - Saves data to CSV files with structured directory organization
   - Handles data appending and duplicate detection
   - Metadata tracking in CSV headers
   - Directory structure: `data/historical/{instrument}/{instrument}_{granularity}_{dates}.csv`

4. **Trading Strategies** (`src/strategies/`)
   - **RSI Mean Reversion** (`rsi_mean_reversion.py`): Multi-timeframe strategy using H1 EMA200 for trend + M15 for entries
   - **VWAP HMA Crossover** (`vwap_hma_crossover.py`): Intraday trend following with institutional bias
   - All strategies inherit from `backtesting.Strategy` base class
   - Strategies include both standard and optimized variants

### Multi-Timeframe Architecture

The project implements proper multi-timeframe analysis:
- Higher timeframe (H1) provides trend direction via EMA200
- Lower timeframe (M15) provides entry signals via RSI/BB or VWAP/HMA
- Pre-calculation and forward-filling approach: calculate H1 indicators, then forward-fill to M15 frequency
- Example: `RSIMeanReversionMTF` expects `H1_EMA200` column pre-calculated in the M15 DataFrame

### Data Flow

1. Data Retrieval: OANDA API → `OandaClient` → `HistoricalDataRetriever` → pandas DataFrame
2. Data Storage: DataFrame → `DataStorage` → CSV files in `data/historical/`
3. Backtesting: CSV → pandas DataFrame → Strategy indicators → `backtesting.py` engine → Results
4. Multi-timeframe: Fetch both H1 and M15 → Calculate H1 indicators → Forward-fill to M15 → Backtest on M15

## Important Patterns

### Configuration Management
- OANDA credentials stored in `config/oanda_config.ini` (NEVER commit this file)
- Config file contains practice and live account credentials
- Client validates credentials are not placeholders on initialization
- Use `environment='practice'` for development, `environment='live'` for production

### Rate Limit Handling
- OANDA limits: 2 new connections/sec, 100 requests/sec, 5000 candles/request
- System uses persistent HTTP sessions (requests.Session)
- Automatic pagination with 0.01s sleep between requests
- Smart time-based iteration to handle large date ranges

### Multi-Timeframe Strategy Implementation
When implementing multi-timeframe strategies:
1. Fetch both timeframes separately (e.g., H1 and M15)
2. Calculate higher timeframe indicators (e.g., H1 EMA200)
3. Forward-fill higher timeframe data to lower timeframe frequency
4. Add as column to lower timeframe DataFrame (e.g., `df['H1_EMA200']`)
5. Strategy reads pre-calculated column, not real-time calculation

### Bollinger Bands Helper Pattern
The pandas_ta Bollinger Bands function returns a DataFrame, so strategies use helper functions to extract individual bands:
```python
def bb_upper(s, length, std):
    bb = ta.bbands(s, length=length, std=std, mamode="sma")
    col_name = f"BBU_{length}_{std}_2.0"
    return bb[col_name].values if col_name in bb.columns else bb.iloc[:, 2].values
```

## Security & Pre-commit Hooks

This project has pre-commit hooks that strip Jupyter notebook outputs before commits. This prevents accidentally committing:
- API tokens
- Account IDs
- Balance information
- Personal trading data

Always ensure pre-commit hooks are installed. The hook runs automatically on `git commit`.

## Data Conventions

- All timestamps in UTC
- CSV columns: `time`, `open`, `high`, `low`, `close`, `volume`, `complete`
- Instrument names use OANDA format: `EUR_USD`, `GBP_USD` (underscore separator)
- Granularity codes: `S5/S10/S15/S30` (seconds), `M1/M5/M15/M30` (minutes), `H1/H4/H12` (hours), `D/W/M` (daily+)

## Strategy Parameter Guidelines

### RSI Mean Reversion
- RSI 30/70: Standard thresholds (~10-15% market exposure)
- RSI 20/80: Conservative thresholds (~1-2% market exposure)
- Risk/Reward: Default 2.0, adjust based on backtest results
- Multi-timeframe version (MTF) is recommended over single-timeframe

### VWAP HMA Crossover
- HMA Period: 21 (balance between responsiveness and noise)
- ATR Multiplier: 1.5x for stop loss
- Intraday only - closes positions 30 mins before EOD
- Best on high liquidity pairs (EUR_USD, GBP_USD)

## Testing Strategy Changes

When modifying strategies:
1. Test with small date ranges first (1-2 months)
2. Verify indicator calculations match expectations
3. Check entry/exit logic with print statements or breakpoints
4. Run full backtest on longer period (6-12 months minimum)
5. Validate results using notebooks for visualization

## File Naming Conventions

- Strategy files: lowercase with underscores (`rsi_mean_reversion.py`)
- Test files: prefix with `test_` (`test_mtf_strategy.py`)
- Notebooks: numbered with descriptive names (`01_retrieve_historical_data.ipynb`)
- Data files: `{instrument}_{granularity}_{from_date}_{to_date}.csv`
