#!/usr/bin/env python3
"""
EOD position closer.

Closes any open position for the given instrument before the OANDA daily
candle closes (21:00 UTC summer / 22:00 UTC winter). Run via GitHub Actions
at 20:55 UTC Mon–Thu.

Usage:
    python close_position.py [--instrument GBP_USD] [--practice|--live] [--dry-run]
"""

import argparse
import logging
import sys

from src.oanda_client import OandaClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Close open OANDA position before daily close')
    parser.add_argument('--instrument', default='GBP_USD')
    env = parser.add_mutually_exclusive_group()
    env.add_argument('--practice', action='store_true', default=True)
    env.add_argument('--live', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    environment = 'live' if args.live else 'practice'
    instrument = args.instrument

    logger.info(f"EOD close: {instrument} | environment={environment} | dry_run={args.dry_run}")

    client = OandaClient(environment=environment, config_path='config/oanda_config.ini')

    positions = client.get_open_positions()
    target = next((p for p in positions if p['instrument'] == instrument), None)

    if target is None:
        logger.info(f"No open position for {instrument}")
        return

    logger.info(f"Open position: long={target['long_units']} short={target['short_units']}")

    if args.dry_run:
        logger.info("[DRY RUN] Position not closed")
        return

    result = client.close_position(instrument)
    logger.info(f"Position closed: {result}")


if __name__ == '__main__':
    main()
