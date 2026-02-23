#!/usr/bin/env python3
"""
EOD position closer.

Closes any open positions before the OANDA daily candle closes
(21:00 UTC summer EDT / 22:00 UTC winter EST). Run via GitHub Actions
at 20:55 UTC Mon–Thu.

Usage:
    python close_position.py [--instruments EUR_USD GBP_USD ...] [--practice|--live] [--dry-run]
"""

import argparse
import logging

from src.oanda_client import OandaClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

MAJORS = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'USD_CAD', 'NZD_USD']


def parse_args():
    parser = argparse.ArgumentParser(description='Close open OANDA positions before daily close')
    parser.add_argument('--instruments', nargs='+', default=MAJORS, metavar='INSTRUMENT',
                        help='Instruments to close (default: all 7 majors)')
    env = parser.add_mutually_exclusive_group()
    env.add_argument('--practice', action='store_true', default=True)
    env.add_argument('--live', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    environment = 'live' if args.live else 'practice'

    logger.info(f"EOD close | environment={environment} | dry_run={args.dry_run}")

    client = OandaClient(environment=environment, config_path='config/oanda_config.ini')

    positions = client.get_open_positions()
    open_instruments = {p['instrument']: p for p in positions}

    for instrument in args.instruments:
        if instrument not in open_instruments:
            logger.info(f"{instrument}: no open position")
            continue

        pos = open_instruments[instrument]
        logger.info(f"{instrument}: open — long={pos['long_units']} short={pos['short_units']}")

        if args.dry_run:
            logger.info(f"{instrument}: [DRY RUN] position not closed")
            continue

        try:
            result = client.close_position(instrument)
            logger.info(f"{instrument}: closed — {result}")
        except Exception as e:
            logger.error(f"{instrument}: failed to close — {e}")


if __name__ == '__main__':
    main()
