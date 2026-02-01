#!/usr/bin/env python3
"""
Fetch M15 EUR_USD historical data for 2024
"""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.oanda_client import OandaClient
from src.data_retriever import HistoricalDataRetriever
from src.data_storage import DataStorage


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )


def main():
    """Fetch M15 EUR_USD data for 2024."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting M15 EUR_USD data retrieval for 2024")

    try:
        # Initialize client
        logger.info("Initializing OANDA client...")
        config_path = Path(__file__).parent / "config" / "oanda_config.ini"
        client = OandaClient(environment="practice", config_path=str(config_path))
        logger.info("✓ OANDA client initialized")

        # Initialize retriever
        retriever = HistoricalDataRetriever(client)

        # Fetch data
        logger.info("Fetching EUR_USD M15 data from 2024-01-01 to 2024-12-31...")
        df = retriever.fetch_historical_data(
            instrument="EUR_USD",
            granularity="M15",
            from_date="2024-01-01",
            to_date="2024-12-31",
        )

        if df.empty:
            logger.error("✗ No data retrieved!")
            return False

        logger.info(f"✓ Retrieved {len(df)} candles")
        logger.info(f"  Date range: {df['time'].min()} to {df['time'].max()}")
        logger.info(f"  Price range: {df['low'].min():.5f} to {df['high'].max():.5f}")

        # Save to CSV
        logger.info("Saving data to CSV...")
        storage = DataStorage()
        file_path = storage.save_to_csv(
            df=df,
            instrument="EUR_USD",
            granularity="M15",
            from_date="2024-01-01",
            to_date="2024-12-31",
        )
        logger.info(f"✓ Data saved to: {file_path}")

        # Verify file
        logger.info("Verifying file...")
        file_size = Path(file_path).stat().st_size / 1024 / 1024
        logger.info(f"✓ File size: {file_size:.2f} MB")

        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Instrument:     EUR_USD")
        logger.info(f"Granularity:    M15")
        logger.info(f"Date Range:     2024-01-01 to 2024-12-31")
        logger.info(f"Candles:        {len(df):,}")
        logger.info(f"Start Price:    {df['open'].iloc[0]:.5f}")
        logger.info(f"End Price:      {df['close'].iloc[-1]:.5f}")
        logger.info(f"Min Price:      {df['low'].min():.5f}")
        logger.info(f"Max Price:      {df['high'].max():.5f}")
        logger.info(f"Avg Volume:     {df['volume'].mean():.0f}")
        logger.info(f"File Path:      {file_path}")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"✗ Error: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
