#!/usr/bin/env python3
"""
Donchian Channel Breakout Strategy Backtesting Script

Usage:
    # Single-timeframe backtest
    python src/backtest_donchian.py --instrument GBP_USD --granularity M15 \\
      --from-date 20250101 --to-date 20251231

    # Multi-timeframe backtest (H1 trend filter)
    python src/backtest_donchian.py --instrument GBP_USD --granularity M15 \\
      --from-date 20250101 --to-date 20251231 --mtf
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from backtesting import Backtest

sys.path.insert(0, str(Path(__file__).parent))

from strategies.donchian_breakout import DonchianBreakout, DonchianBreakoutMTF


def load_data(instrument: str, granularity: str, from_date: str, to_date: str) -> pd.DataFrame:
    data_dir = Path(__file__).parent.parent / "data" / "historical" / instrument
    filename = f"{instrument}_{granularity}_{from_date}_{to_date}.csv"
    filepath = data_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"Data file not found: {filepath}\n"
            f"Please ensure historical data is available for the specified period."
        )

    df = pd.read_csv(
        filepath,
        skiprows=6,
        parse_dates=["time"],
        index_col="time",
    )

    required_cols = ["open", "high", "low", "close", "volume"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})

    if "complete" in df.columns:
        df = df.drop(columns=["complete"])

    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

    if len(df) == 0:
        raise ValueError("DataFrame is empty after loading and cleaning")

    print(f"Loaded {len(df):,} candles from {filepath.name}")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")

    return df


def add_h1_dc_mid(df_m15: pd.DataFrame, instrument: str, from_date: str, to_date: str, dc_period: int = 20) -> pd.DataFrame:
    """Load H1 data, compute Donchian middle band, forward-fill to M15 index."""
    h1_df = load_data(instrument, "H1", from_date, to_date)

    h1_upper = h1_df["High"].shift(1).rolling(dc_period).max()
    h1_lower = h1_df["Low"].shift(1).rolling(dc_period).min()
    h1_mid = (h1_upper + h1_lower) / 2

    # Forward-fill H1 middle band onto M15 index
    h1_mid_reindexed = h1_mid.reindex(df_m15.index.union(h1_mid.index)).ffill()
    df_m15 = df_m15.copy()
    df_m15["H1_DC_Mid"] = h1_mid_reindexed.reindex(df_m15.index)

    filled = df_m15["H1_DC_Mid"].notna().sum()
    print(f"H1_DC_Mid: {filled:,}/{len(df_m15):,} bars filled")

    return df_m15


def print_key_metrics(stats) -> None:
    trades = stats["_trades"]
    print(f"\n{'=' * 60}")
    print("KEY METRICS")
    print(f"{'=' * 60}")
    print(f"# Trades:        {stats['# Trades']}")
    print(f"Return [%]:      {stats['Return [%]']:.2f}%")
    print(f"Win Rate [%]:    {stats['Win Rate [%]']:.2f}%")
    print(f"Max Drawdown:    {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Sharpe Ratio:    {stats['Sharpe Ratio']:.2f}")
    print(f"Exposure Time:   {stats['Exposure Time [%]']:.2f}%")

    if len(trades) > 0:
        long_trades = trades[trades["Size"] > 0]
        short_trades = trades[trades["Size"] < 0]
        print(f"Long / Short:    {len(long_trades)} / {len(short_trades)}")


def run_backtest(
    instrument: str,
    granularity: str,
    from_date: str,
    to_date: str,
    mtf: bool,
    cash: float,
    commission: float,
) -> None:
    print(f"\n{'=' * 60}")
    print("DONCHIAN CHANNEL BREAKOUT BACKTEST")
    print(f"{'=' * 60}")
    print(f"Instrument:  {instrument}")
    print(f"Granularity: {granularity}")
    print(f"Period:      {from_date} to {to_date}")
    print(f"Mode:        {'MTF (H1 trend filter)' if mtf else 'Single-timeframe'}")
    print(f"Capital:     ${cash:,.2f}")
    print(f"Commission:  {commission * 10000:.1f} pips\n")

    df = load_data(instrument, granularity, from_date, to_date)

    if mtf:
        df = add_h1_dc_mid(df, instrument, from_date, to_date)
        StrategyClass = DonchianBreakoutMTF
    else:
        StrategyClass = DonchianBreakout

    bt = Backtest(
        df,
        StrategyClass,
        cash=cash,
        commission=commission,
        margin=1.0,
        trade_on_close=False,
        hedging=False,
        exclusive_orders=True,
    )

    stats = bt.run()

    print(f"\n{'=' * 60}")
    print("BACKTEST RESULTS")
    print(f"{'=' * 60}")
    print(stats)

    print_key_metrics(stats)

    print(f"\n{'=' * 60}")
    print("BACKTEST COMPLETE")
    print(f"{'=' * 60}\n")

    return stats


def parse_date(date_str: str) -> str:
    if "-" in date_str:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")
    datetime.strptime(date_str, "%Y%m%d")  # validate
    return date_str


def main():
    parser = argparse.ArgumentParser(description="Backtest Donchian Channel Breakout strategy")

    parser.add_argument("--instrument", type=str, default="GBP_USD")
    parser.add_argument("--granularity", type=str, default="M15")
    parser.add_argument("--from-date", type=str, default="20250101")
    parser.add_argument("--to-date", type=str, default="20251231")
    parser.add_argument("--cash", type=float, default=10000)
    parser.add_argument("--commission", type=float, default=0.0001)
    parser.add_argument("--mtf", action="store_true", help="Use H1 Donchian middle band as trend filter")

    args = parser.parse_args()

    try:
        from_date = parse_date(args.from_date)
        to_date = parse_date(args.to_date)
    except ValueError as e:
        print(f"Date error: {e}")
        sys.exit(1)

    try:
        run_backtest(
            instrument=args.instrument,
            granularity=args.granularity,
            from_date=from_date,
            to_date=to_date,
            mtf=args.mtf,
            cash=args.cash,
            commission=args.commission,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
