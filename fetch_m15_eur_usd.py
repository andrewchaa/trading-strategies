#!/usr/bin/env python3
"""
Fetch M15 historical data for all major currency pairs for 2025
"""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.oanda_client import OandaClient
from src.data_retriever import HistoricalDataRetriever
from src.data_storage import DataStorage

MAJOR_PAIRS = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'USD_CAD', 'AUD_USD', 'NZD_USD']
FROM_DATE = '2025-01-01'
TO_DATE = '2025-12-31'
GRANULARITY = 'M15'


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )


def main():
    """Fetch M15 data for all major pairs for 2025."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Starting {GRANULARITY} data retrieval for {len(MAJOR_PAIRS)} major pairs ({FROM_DATE} to {TO_DATE})")

    config_path = Path(__file__).parent / "config" / "oanda_config.ini"
    client = OandaClient(environment="practice", config_path=str(config_path))
    retriever = HistoricalDataRetriever(client)
    storage = DataStorage()

    results = []
    for i, pair in enumerate(MAJOR_PAIRS, 1):
        logger.info(f"[{i}/{len(MAJOR_PAIRS)}] Fetching {pair} {GRANULARITY}...")
        try:
            df = retriever.fetch_historical_data(
                instrument=pair,
                granularity=GRANULARITY,
                from_date=FROM_DATE,
                to_date=TO_DATE,
            )
            file_path = storage.save_to_csv(
                df=df,
                instrument=pair,
                granularity=GRANULARITY,
                from_date=FROM_DATE,
                to_date=TO_DATE,
            )
            logger.info(f"  ✓ Saved {len(df):,} candles to {file_path}")
            results.append((pair, len(df), str(file_path), None))
        except Exception as e:
            logger.error(f"  ✗ Error: {e}")
            results.append((pair, 0, None, str(e)))

    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    for pair, count, path, error in results:
        if error:
            logger.info(f"  {pair}: FAILED - {error}")
        else:
            logger.info(f"  {pair}: {count:,} candles -> {path}")
    logger.info("=" * 60)

    failed = [r for r in results if r[3]]
    return len(failed) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
