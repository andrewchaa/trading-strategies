"""
Historical Data Retriever

This module provides functionality to retrieve historical candle data from OANDA
using the v20 REST API with automatic pagination for large date ranges.
"""

import logging
import math
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import pytz

from .oanda_client import OandaClient


class HistoricalDataRetriever:
    """
    Retrieve historical candle data from OANDA with flexible parameters.

    Handles automatic pagination for large date ranges and provides
    convenient data processing into pandas DataFrames.

    Attributes:
        client (OandaClient): The OANDA client instance
        logger (logging.Logger): Logger instance
    """

    # Supported granularities
    GRANULARITIES = [
        "S5",
        "S10",
        "S15",
        "S30",  # Seconds
        "M1",
        "M2",
        "M4",
        "M5",
        "M10",
        "M15",
        "M30",  # Minutes
        "H1",
        "H2",
        "H3",
        "H4",
        "H6",
        "H8",
        "H12",  # Hours
        "D",
        "W",
        "M",  # Daily, Weekly, Monthly
    ]

    # Granularity duration in seconds
    GRANULARITY_SECONDS = {
        "S5": 5,
        "S10": 10,
        "S15": 15,
        "S30": 30,
        "M1": 60,
        "M2": 120,
        "M4": 240,
        "M5": 300,
        "M10": 600,
        "M15": 900,
        "M30": 1800,
        "H1": 3600,
        "H2": 7200,
        "H3": 10800,
        "H4": 14400,
        "H6": 21600,
        "H8": 28800,
        "H12": 43200,
        "D": 86400,
        "W": 604800,
        "M": 2592000,  # Approximate for M
    }

    def __init__(self, oanda_client: OandaClient):
        """
        Initialize the data retriever.

        Args:
            oanda_client: An initialized OandaClient instance
        """
        self.client = oanda_client
        self.logger = logging.getLogger(__name__)

    def fetch_historical_data(
        self,
        instrument: str,
        granularity: str,
        from_date: str,
        to_date: Optional[str] = None,
        price_type: str = "M",
    ) -> pd.DataFrame:
        """
        Fetch historical candle data for a single instrument.

        Args:
            instrument: Instrument name (e.g., 'EUR_USD')
            granularity: Candle granularity (e.g., 'H1', 'D')
            from_date: Start date (ISO format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SSZ')
            to_date: End date (optional, defaults to now)
            price_type: Price type - 'M' (mid), 'B' (bid), 'A' (ask), 'BA', 'MBA'

        Returns:
            DataFrame with columns: time, open, high, low, close, volume, complete

        Raises:
            ValueError: If granularity is invalid or instrument is not available
        """
        # Validate granularity
        if granularity not in self.GRANULARITIES:
            raise ValueError(
                f"Invalid granularity: {granularity}. "
                f"Must be one of: {', '.join(self.GRANULARITIES)}"
            )

        # Validate instrument
        available_instruments = self.client.get_instruments()
        if instrument not in available_instruments:
            raise ValueError(
                f"Instrument {instrument} not available. "
                f"Check available instruments using client.get_instruments()"
            )

        # Format dates
        from_dt = self._parse_date(from_date)
        to_dt = self._parse_date(to_date) if to_date else datetime.now(pytz.UTC)

        self.logger.info(
            f"Fetching {instrument} data: {granularity} from {from_dt} to {to_dt}"
        )

        # Fetch data with pagination
        all_candles = self._fetch_with_pagination(
            instrument, granularity, from_dt, to_dt, price_type
        )

        if not all_candles:
            self.logger.warning(f"No data retrieved for {instrument}")
            return pd.DataFrame()

        # Convert to DataFrame
        df = self._candles_to_dataframe(all_candles, price_type)

        self.logger.info(
            f"Successfully retrieved {len(df)} candles for {instrument} "
            f"({df['time'].min()} to {df['time'].max()})"
        )

        return df

    def fetch_multiple_instruments(
        self,
        instruments: List[str],
        granularity: str,
        from_date: str,
        to_date: Optional[str] = None,
        price_type: str = "M",
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple instruments.

        Args:
            instruments: List of instrument names
            granularity: Candle granularity
            from_date: Start date
            to_date: End date (optional)
            price_type: Price type

        Returns:
            Dictionary mapping instrument names to DataFrames
        """
        results = {}

        for instrument in instruments:
            self.logger.info(f"Fetching data for {instrument}...")
            try:
                df = self.fetch_historical_data(
                    instrument=instrument,
                    granularity=granularity,
                    from_date=from_date,
                    to_date=to_date,
                    price_type=price_type,
                )
                results[instrument] = df

                # Small delay between instruments to respect rate limits
                time.sleep(0.5)
            except Exception as e:
                self.logger.error(f"Failed to fetch {instrument}: {str(e)}")
                continue

        return results

    def _fetch_with_pagination(
        self,
        instrument: str,
        granularity: str,
        from_dt: datetime,
        to_dt: datetime,
        price_type: str,
    ) -> List[Dict]:
        """
        Fetch candles with automatic pagination for large date ranges.

        OANDA limits to 5000 candles per request, so we need to paginate.
        """
        all_candles = []
        current_from = from_dt
        max_candles = 5000
        request_count = 0

        # Calculate expected number of candles to estimate requests
        duration_seconds = (to_dt - from_dt).total_seconds()
        candle_seconds = self.GRANULARITY_SECONDS.get(granularity, 3600)
        expected_candles = int(duration_seconds / candle_seconds)
        estimated_requests = math.ceil(expected_candles / max_candles)

        self.logger.info(
            f"Estimated {expected_candles:,} candles in {estimated_requests} requests"
        )

        while current_from < to_dt:
            # Respect rate limits: 100 requests per second max
            if request_count > 0:
                time.sleep(0.01)

            max_chunk_end = current_from + timedelta(
                seconds=candle_seconds * max_candles
            )
            chunk_end = min(max_chunk_end, to_dt)

            # Prepare request parameters
            params = {
                "granularity": granularity,
                "from": current_from.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"),
                "to": chunk_end.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"),
                "price": price_type,
            }

            try:
                response = self.client.get_candles(instrument, params)
                candles = response.get("candles", [])

                if not candles:
                    self.logger.debug("No more candles available")
                    break

                all_candles.extend(candles)
                request_count += 1

                self.logger.info(
                    f"Retrieved {len(candles)} candles (Request {request_count}/{estimated_requests or '?'}). "
                    f"Total: {len(all_candles):,}"
                )

                last_candle_time = candles[-1]["time"]
                current_from = datetime.fromisoformat(
                    last_candle_time.replace("Z", "+00:00")
                )
                current_from += timedelta(seconds=candle_seconds)

                if current_from >= to_dt:
                    self.logger.debug("Reached end date")
                    break

                if len(candles) < max_candles and chunk_end >= to_dt:
                    self.logger.debug("Received all available data")
                    break

            except Exception as e:
                self.logger.error(f"Error in pagination: {str(e)}")
                raise

        return all_candles

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string to datetime object.

        Args:
            date_str: Date string in format 'YYYY-MM-DD' or ISO 8601

        Returns:
            Timezone-aware datetime object (UTC)
        """
        # Try ISO 8601 format first
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            return dt
        except ValueError:
            pass

        # Try simple YYYY-MM-DD format
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return pytz.UTC.localize(dt)
        except ValueError:
            raise ValueError(
                f"Invalid date format: {date_str}. Use 'YYYY-MM-DD' or ISO 8601 format"
            )

    def _candles_to_dataframe(
        self, candles: List[Dict], price_type: str
    ) -> pd.DataFrame:
        """
        Convert candle data to pandas DataFrame.

        Args:
            candles: List of candle dictionaries from OANDA API
            price_type: Price type used in the request

        Returns:
            DataFrame with processed candle data
        """
        data = []

        for candle in candles:
            # Determine which price to use (mid, bid, or ask)
            if "M" in price_type and "mid" in candle:
                price_data = candle["mid"]
            elif "B" in price_type and "bid" in candle:
                price_data = candle["bid"]
            elif "A" in price_type and "ask" in candle:
                price_data = candle["ask"]
            else:
                # Default to mid if available
                price_data = candle.get("mid", candle.get("bid", candle.get("ask")))

            if price_data is None:
                continue

            data.append(
                {
                    "time": candle["time"],
                    "open": float(price_data["o"]),
                    "high": float(price_data["h"]),
                    "low": float(price_data["l"]),
                    "close": float(price_data["c"]),
                    "volume": int(candle["volume"]),
                    "complete": candle["complete"],
                }
            )

        df = pd.DataFrame(data)

        if df.empty:
            return df

        # Convert time to datetime
        df["time"] = pd.to_datetime(df["time"])

        df = df.sort_values("time").reset_index(drop=True)
        df = df.drop_duplicates(subset=["time"], keep="last")

        return df
