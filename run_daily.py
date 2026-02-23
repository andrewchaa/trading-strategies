#!/usr/bin/env python3
"""
Daily runner for Donchian Breakout live trading.

Detects signals on the daily close and places a market order on OANDA
with attached SL and TP. Risk is fixed at 1% of account equity per trade.

Usage:
    python run_daily.py [--instrument GBP_USD] [--practice|--live] [--dry-run]
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta

import pytz

from src.oanda_client import OandaClient
from src.data_retriever import HistoricalDataRetriever
from src.signal_detector import detect_signal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Daily Donchian Breakout signal runner')
    parser.add_argument('--instrument', default='GBP_USD', help='Instrument to trade (default: GBP_USD)')
    env_group = parser.add_mutually_exclusive_group()
    env_group.add_argument('--practice', action='store_true', default=True, help='Use practice account (default)')
    env_group.add_argument('--live', action='store_true', help='Use live account')
    parser.add_argument('--dry-run', action='store_true', help='Print order details without placing order')
    return parser.parse_args()


def main():
    args = parse_args()
    environment = 'live' if args.live else 'practice'
    instrument = args.instrument

    logger.info(f"Starting daily runner: {instrument} | environment={environment} | dry_run={args.dry_run}")

    client = OandaClient(environment=environment, config_path='config/oanda_config.ini')
    retriever = HistoricalDataRetriever(client)

    # Fetch last 90 daily candles (well under OANDA's 5000-candle limit)
    today = datetime.now(pytz.UTC)
    from_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')

    logger.info(f"Fetching daily candles from {from_date}")
    df = retriever.fetch_historical_data(instrument, 'D', from_date)

    if df.empty:
        logger.error("No data retrieved, exiting")
        sys.exit(1)

    # Only use complete candles
    df = df[df['complete'] == True].copy()

    if len(df) < 50:
        logger.error(f"Insufficient complete candles ({len(df)}), need at least 50")
        sys.exit(1)

    signal = detect_signal(df)

    if signal is None:
        logger.info("No signal detected, exiting cleanly")
        return

    logger.info(f"Signal detected: side={signal['side']} entry~{signal['entry_price']:.5f} sl_dist={signal['sl_dist']:.5f}")

    account = client.get_account_info()
    balance = float(account['balance'])
    logger.info(f"Account balance: {balance}")

    side = signal['side']
    sl_dist = signal['sl_dist']
    entry = signal['entry_price']

    risk_amount = balance * 0.01
    units = int(risk_amount / sl_dist)
    if side == 'sell':
        units = -units

    if side == 'buy':
        sl = entry - sl_dist
        tp = entry + sl_dist * 2.0
    else:
        sl = entry + sl_dist
        tp = entry - sl_dist * 2.0

    logger.info(
        f"Order: {instrument} {side.upper()} {units} units | "
        f"entry~{entry:.5f} | sl={sl:.5f} | tp={tp:.5f}"
    )

    if args.dry_run:
        logger.info("[DRY RUN] Order not placed")
        return

    response = client.place_market_order(instrument, units, sl, tp)
    logger.info(f"Order placed successfully: {response}")


if __name__ == '__main__':
    main()
