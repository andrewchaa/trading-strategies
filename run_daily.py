#!/usr/bin/env python3
"""
Daily runner for Donchian Breakout live trading.

Detects signals on the daily close and places a market order on OANDA
with attached SL and TP. Risk is fixed at 1% of account equity per trade.

Usage:
    python run_daily.py [--instruments EUR_USD GBP_USD ...] [--practice|--live] [--dry-run]
"""

import argparse
import logging
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

MAJORS = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'USD_CAD', 'NZD_USD']


def parse_args():
    parser = argparse.ArgumentParser(description='Daily Donchian Breakout signal runner')
    parser.add_argument('--instruments', nargs='+', default=MAJORS, metavar='INSTRUMENT',
                        help='Instruments to trade (default: all 7 majors)')
    env_group = parser.add_mutually_exclusive_group()
    env_group.add_argument('--practice', action='store_true', default=True)
    env_group.add_argument('--live', action='store_true')
    parser.add_argument('--dry-run', action='store_true', help='Print order details without placing order')
    return parser.parse_args()


def run_instrument(instrument, client, retriever, balance, dry_run):
    price_fmt = '.3f' if 'JPY' in instrument else '.5f'

    today = datetime.now(pytz.UTC)
    from_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')

    df = retriever.fetch_historical_data(instrument, 'D', from_date)
    if df.empty:
        logger.warning(f"{instrument}: no data retrieved, skipping")
        return

    df = df[df['complete'] == True].copy()
    if len(df) < 50:
        logger.warning(f"{instrument}: only {len(df)} complete candles, skipping")
        return

    signal = detect_signal(df)
    if signal is None:
        logger.info(f"{instrument}: no signal")
        return

    side = signal['side']
    sl_dist = signal['sl_dist']
    entry = signal['entry_price']

    risk_amount = balance * 0.01
    units = int(risk_amount / sl_dist)
    if side == 'sell':
        units = -units

    sl = (entry - sl_dist) if side == 'buy' else (entry + sl_dist)
    tp = (entry + sl_dist * 2.0) if side == 'buy' else (entry - sl_dist * 2.0)

    logger.info(
        f"{instrument}: {side.upper()} {units} units | "
        f"entry~{entry:{price_fmt}} | sl={sl:{price_fmt}} | tp={tp:{price_fmt}}"
    )

    if dry_run:
        logger.info(f"{instrument}: [DRY RUN] order not placed")
        return

    response = client.place_market_order(instrument, units, sl, tp)
    logger.info(f"{instrument}: order placed — {response}")


def main():
    args = parse_args()
    environment = 'live' if args.live else 'practice'

    logger.info(f"Starting daily runner | environment={environment} | dry_run={args.dry_run}")
    logger.info(f"Instruments: {args.instruments}")

    client = OandaClient(environment=environment, config_path='config/oanda_config.ini')
    retriever = HistoricalDataRetriever(client)

    account = client.get_account_info()
    balance = float(account['balance'])
    logger.info(f"Account balance: {balance}")

    for instrument in args.instruments:
        try:
            run_instrument(instrument, client, retriever, balance, args.dry_run)
        except Exception as e:
            logger.error(f"{instrument}: error — {e}")


if __name__ == '__main__':
    main()
