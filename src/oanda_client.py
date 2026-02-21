"""
OANDA API Client Wrapper

This module provides a wrapper around OANDA's v20 REST API for easy authentication
and connection management using standard HTTP requests.
"""

import configparser
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import requests


class OandaClient:
    """
    OANDA API client wrapper for managing connections and authentication.

    Uses OANDA's REST API directly via HTTP requests for maximum compatibility
    and control.

    Attributes:
        environment (str): The trading environment ('practice' or 'live')
        api_url (str): Base URL for API requests
        account_id (str): The OANDA account ID
        session (requests.Session): Persistent HTTP session
    """

    def __init__(self, environment: str = 'practice', config_path: str = '../config/oanda_config.ini'):
        """
        Initialize the OANDA client.

        Args:
            environment: Trading environment ('practice' or 'live')
            config_path: Path to the configuration file

        Raises:
            ValueError: If environment is not 'practice' or 'live'
            FileNotFoundError: If config file doesn't exist
            KeyError: If required configuration keys are missing
        """
        self.logger = logging.getLogger(__name__)

        if environment not in ['practice', 'live']:
            raise ValueError("Environment must be 'practice' or 'live'")

        self.environment = environment
        self.config_path = config_path

        # Load configuration
        self._load_config()

        # Create persistent session with authentication
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept-Datetime-Format': 'RFC3339'
        })

        self.logger.info(f"OANDA client initialized for {environment} environment")

    def _load_config(self) -> None:
        """
        Load configuration from INI file.

        Raises:
            FileNotFoundError: If config file doesn't exist
            KeyError: If required configuration keys are missing
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n"
                f"Please copy config/oanda_config.ini.example to config/oanda_config.ini "
                f"and fill in your credentials."
            )

        config = configparser.ConfigParser()
        config.read(self.config_path)

        try:
            self.api_token = config[self.environment]['api_token']
            self.account_id = config[self.environment]['account_id']
            self.api_url = config['settings'][f'base_url_{self.environment}']
        except KeyError as e:
            raise KeyError(
                f"Missing configuration key: {e}\n"
                f"Please check your config file at {self.config_path}"
            )

        # Validate that credentials are not placeholder values
        if 'YOUR_' in self.api_token or 'YOUR_' in self.account_id:
            raise ValueError(
                "Please update config/oanda_config.ini with your actual OANDA credentials.\n"
                "Current values appear to be placeholders."
            )

        self.logger.debug(f"Configuration loaded from {self.config_path}")

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict:
        """
        Make a request to OANDA API.

        Args:
            method: HTTP method ('GET', 'POST', etc.)
            endpoint: API endpoint (e.g., '/accounts/{accountID}')
            params: Query parameters
            json: JSON body for POST requests

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.api_url}{endpoint}"

        response = None
        try:
            response = self.session.request(method, url, params=params, json=json, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error: {e}")
            if response is not None:
                self.logger.error(f"Response: {response.text}")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {e}")
            raise

    def validate_connection(self) -> bool:
        """
        Validate the connection to OANDA API by fetching account details.

        Returns:
            True if connection is successful

        Raises:
            Exception: If connection fails
        """
        try:
            response = self._request('GET', f'/v3/accounts/{self.account_id}')
            account = response['account']

            account_currency = account['currency']
            account_balance = account['balance']

            self.logger.info(
                f"Connection validated successfully. "
                f"Account: {self.account_id}, "
                f"Currency: {account_currency}, "
                f"Balance: {account_balance}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Connection validation failed: {str(e)}")
            raise

    def get_account_info(self) -> Dict:
        """
        Get detailed account information.

        Returns:
            Dictionary containing account details

        Raises:
            Exception: If API request fails
        """
        try:
            response = self._request('GET', f'/v3/accounts/{self.account_id}')
            return response['account']
        except Exception as e:
            self.logger.error(f"Failed to fetch account info: {str(e)}")
            raise

    def get_instruments(self) -> List[str]:
        """
        Get list of available tradeable instruments.

        Returns:
            List of instrument names (e.g., ['EUR_USD', 'GBP_USD', ...])

        Raises:
            Exception: If API request fails
        """
        try:
            response = self._request('GET', f'/v3/accounts/{self.account_id}/instruments')

            instruments = [instrument['name'] for instrument in response['instruments']]

            self.logger.info(f"Retrieved {len(instruments)} available instruments")
            return instruments
        except Exception as e:
            self.logger.error(f"Failed to fetch instruments: {str(e)}")
            raise

    def get_instrument_details(self, instrument: str) -> Dict:
        """
        Get detailed information about a specific instrument.

        Args:
            instrument: Instrument name (e.g., 'EUR_USD')

        Returns:
            Dictionary containing instrument details

        Raises:
            ValueError: If instrument not found
            Exception: If API request fails
        """
        try:
            response = self._request('GET', f'/v3/accounts/{self.account_id}/instruments')

            for instr in response['instruments']:
                if instr['name'] == instrument:
                    return instr

            raise ValueError(f"Instrument {instrument} not found")
        except Exception as e:
            self.logger.error(f"Failed to fetch instrument details: {str(e)}")
            raise

    def get_candles(
        self,
        instrument: str,
        params: Dict
    ) -> Dict:
        """
        Get candle data for an instrument.

        Args:
            instrument: Instrument name (e.g., 'EUR_USD')
            params: Query parameters for candle request
                - granularity: Candle granularity (e.g., 'H1', 'D')
                - from: Start time (RFC3339 format)
                - to: End time (RFC3339 format)
                - count: Number of candles (max 5000)
                - price: Price type ('M', 'B', 'A', 'BA', 'MBA')

        Returns:
            Dictionary with candle data

        Raises:
            Exception: If API request fails
        """
        try:
            endpoint = f'/v3/instruments/{instrument}/candles'
            return self._request('GET', endpoint, params=params)
        except Exception as e:
            self.logger.error(f"Failed to fetch candles: {str(e)}")
            raise

    def get_open_positions(self) -> List[Dict]:
        """
        Get all open positions for the account.

        Returns:
            List of dicts with 'instrument', 'long_units', 'short_units'

        Raises:
            Exception: If API request fails
        """
        try:
            response = self._request('GET', f'/v3/accounts/{self.account_id}/openPositions')
            positions = []
            for pos in response.get('positions', []):
                positions.append({
                    'instrument': pos['instrument'],
                    'long_units': int(pos['long']['units']),
                    'short_units': int(pos['short']['units']),
                })
            return positions
        except Exception as e:
            self.logger.error(f"Failed to fetch open positions: {str(e)}")
            raise

    def place_market_order(
        self,
        instrument: str,
        units: int,
        sl_price: float,
        tp_price: float,
    ) -> Dict:
        """
        Place a market order with attached stop loss and take profit.

        Args:
            instrument: Instrument name (e.g., 'GBP_USD')
            units: Position size — positive = buy, negative = sell
            sl_price: Stop loss price
            tp_price: Take profit price

        Returns:
            Order response dictionary

        Raises:
            Exception: If API request fails
        """
        body = {
            "order": {
                "type": "MARKET",
                "instrument": instrument,
                "units": str(units),
                "timeInForce": "FOK",
                "stopLossOnFill": {"price": f"{sl_price:.5f}", "timeInForce": "GTC"},
                "takeProfitOnFill": {"price": f"{tp_price:.5f}", "timeInForce": "GTC"},
            }
        }
        try:
            response = self._request('POST', f'/v3/accounts/{self.account_id}/orders', json=body)
            self.logger.info(f"Market order placed: {instrument} {units} units")
            return response
        except Exception as e:
            self.logger.error(f"Failed to place market order: {str(e)}")
            raise


# Configure logging
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'data_retrieval.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
