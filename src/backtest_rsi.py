#!/usr/bin/env python3
"""
RSI Mean Reversion Strategy Backtesting Script

This script runs backtests on the RSI Mean Reversion strategy using historical forex data.
It supports parameter optimization, detailed performance statistics, and equity curve visualization.

Usage:
    # Basic backtest with default parameters
    python src/backtest_rsi.py

    # Specify date range
    python src/backtest_rsi.py --from-date 2024-01-01 --to-date 2024-06-30

    # Run parameter optimization
    python src/backtest_rsi.py --optimize

    # Use optimized strategy variant
    python src/backtest_rsi.py --strategy optimized

    # Custom instrument and granularity
    python src/backtest_rsi.py --instrument EUR_USD --granularity M15

    # Show help
    python src/backtest_rsi.py --help

Requirements:
    - Historical data in CSV format at data/historical/{INSTRUMENT}/{INSTRUMENT}_{GRANULARITY}_{FROMDATE}_{TODATE}.csv
    - RSI Mean Reversion strategy at src/strategies/rsi_mean_reversion.py
    - backtesting library: pip install backtesting

Output:
    - Console: Detailed performance statistics
    - File: Equity curve plot saved to results/equity_curves/
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from backtesting import Backtest

# Add src to path for strategy imports
sys.path.insert(0, str(Path(__file__).parent))

from strategies.rsi_mean_reversion import RSIMeanReversion, RSIMeanReversionOptimized


def load_data(
    instrument: str, granularity: str, from_date: str, to_date: str
) -> pd.DataFrame:
    """
    Load historical forex data from CSV file.

    Args:
        instrument: Trading instrument (e.g., 'EUR_USD')
        granularity: Timeframe (e.g., 'M15', 'H1', 'H4')
        from_date: Start date in format YYYYMMDD
        to_date: End date in format YYYYMMDD

    Returns:
        DataFrame with OHLCV data, indexed by datetime

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If data cannot be parsed or is empty
    """
    # Construct file path
    data_dir = Path(__file__).parent.parent / "data" / "historical" / instrument
    filename = f"{instrument}_{granularity}_{from_date}_{to_date}.csv"
    filepath = data_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"Data file not found: {filepath}\n"
            f"Expected format: data/historical/{instrument}/{filename}\n"
            f"Please ensure historical data is available for the specified period."
        )

    try:
        # Read CSV, skipping metadata header rows
        df = pd.read_csv(
            filepath,
            skiprows=6,  # Skip metadata header lines
            parse_dates=["time"],
            index_col="time",
        )

        # Validate required columns
        required_cols = ["open", "high", "low", "close", "volume"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Rename columns to backtesting.py expected format (capitalized)
        df = df.rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
        )

        # Drop the 'complete' column if present
        if "complete" in df.columns:
            df = df.drop(columns=["complete"])

        # Keep only OHLCV columns
        df = df[["Open", "High", "Low", "Close", "Volume"]]

        # Remove any rows with NaN values
        df = df.dropna()

        if len(df) == 0:
            raise ValueError("DataFrame is empty after loading and cleaning")

        print(f"\nLoaded {len(df):,} candles from {filepath.name}")
        print(f"Date range: {df.index[0]} to {df.index[-1]}")
        print(f"Duration: {(df.index[-1] - df.index[0]).days} days")

        return df

    except Exception as e:
        raise ValueError(f"Error parsing data file {filepath}: {str(e)}")


def validate_data_for_strategy(df: pd.DataFrame, ema_period: int = 200) -> None:
    """
    Validate that data has sufficient candles for the strategy.

    Args:
        df: OHLCV DataFrame
        ema_period: EMA period required by strategy (default: 200)

    Raises:
        ValueError: If insufficient data for strategy indicators
    """
    if len(df) < ema_period:
        raise ValueError(
            f"Insufficient data for strategy. Need at least {ema_period} candles "
            f"for EMA{ema_period}, but only {len(df)} available."
        )


def print_trade_summary(stats, num_trades: int = 10) -> None:
    """
    Print summary of first and last trades.

    Args:
        stats: Backtest statistics object
        num_trades: Number of trades to show from start/end
    """
    trades = stats["_trades"]

    if len(trades) == 0:
        print("\n⚠️  No trades executed during backtest period")
        return

    print(f"\n{'=' * 80}")
    print(f"TRADE SUMMARY (Total: {len(trades)} trades)")
    print(f"{'=' * 80}")

    # Display settings for pandas
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", 20)

    # Show first N trades
    n_show = min(num_trades, len(trades))
    print(f"\n▼ First {n_show} trades:")
    print(trades.head(n_show).to_string())

    # Show last N trades if there are more than 2*num_trades
    if len(trades) > 2 * num_trades:
        print(f"\n▲ Last {n_show} trades:")
        print(trades.tail(n_show).to_string())

    # Trade statistics
    winning_trades = trades[trades["PnL"] > 0]
    losing_trades = trades[trades["PnL"] <= 0]
    long_trades = trades[trades["Size"] > 0]
    short_trades = trades[trades["Size"] < 0]

    print(f"\n{'=' * 80}")
    print("TRADE BREAKDOWN")
    print(f"{'=' * 80}")
    print(
        f"Winning trades: {len(winning_trades)} ({len(winning_trades) / len(trades) * 100:.1f}%)"
    )
    print(
        f"Losing trades:  {len(losing_trades)} ({len(losing_trades) / len(trades) * 100:.1f}%)"
    )
    print(
        f"Long trades:    {len(long_trades)} ({len(long_trades) / len(trades) * 100:.1f}%)"
    )
    print(
        f"Short trades:   {len(short_trades)} ({len(short_trades) / len(trades) * 100:.1f}%)"
    )

    if len(winning_trades) > 0:
        print(f"\nAverage winning trade: ${winning_trades['PnL'].mean():.2f}")
        print(f"Best trade: ${winning_trades['PnL'].max():.2f}")

    if len(losing_trades) > 0:
        print(f"Average losing trade: ${losing_trades['PnL'].mean():.2f}")
        print(f"Worst trade: ${losing_trades['PnL'].min():.2f}")


def save_equity_curve(stats, output_path: Path) -> None:
    """
    Save equity curve plot to file.

    Args:
        stats: Backtest statistics object
        output_path: Path to save the plot
    """
    try:
        import matplotlib

        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt

        equity_curve = stats["_equity_curve"]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # Equity curve
        ax1.plot(
            equity_curve.index, equity_curve["Equity"], linewidth=1.5, color="#2E86AB"
        )
        ax1.set_ylabel("Portfolio Value ($)", fontsize=11)
        ax1.set_title(
            "Equity Curve - RSI Mean Reversion Strategy", fontsize=14, fontweight="bold"
        )
        ax1.grid(True, alpha=0.3)
        ax1.fill_between(
            equity_curve.index,
            equity_curve["Equity"],
            stats["_equity_curve"]["Equity"].iloc[0],
            alpha=0.2,
            color="#2E86AB",
        )

        # Drawdown
        ax2.fill_between(
            equity_curve.index,
            0,
            equity_curve["DrawdownPct"] * 100,
            color="#A23B72",
            alpha=0.6,
        )
        ax2.set_ylabel("Drawdown (%)", fontsize=11)
        ax2.set_xlabel("Date", fontsize=11)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        print(f"\n✓ Equity curve saved to: {output_path}")

    except Exception as e:
        print(f"\n⚠️  Failed to save equity curve: {str(e)}")


def run_backtest(
    instrument: str = "EUR_USD",
    granularity: str = "M15",
    from_date: str = "20240101",
    to_date: str = "20241231",
    strategy_type: str = "base",
    cash: float = 10000,
    commission: float = 0.0001,
    optimize: bool = False,
) -> None:
    """
    Run backtest on RSI Mean Reversion strategy.

    Args:
        instrument: Trading instrument (e.g., 'EUR_USD')
        granularity: Timeframe (e.g., 'M15', 'H1')
        from_date: Start date in format YYYYMMDD
        to_date: End date in format YYYYMMDD
        strategy_type: 'base' or 'optimized'
        cash: Initial capital
        commission: Commission per trade (1 pip = 0.0001 for forex)
        optimize: Whether to run parameter optimization
    """
    print(f"\n{'=' * 80}")
    print("RSI MEAN REVERSION STRATEGY BACKTEST")
    print(f"{'=' * 80}")
    print(f"Instrument:  {instrument}")
    print(f"Granularity: {granularity}")
    print(f"Period:      {from_date} to {to_date}")
    print(f"Strategy:    {strategy_type.upper()}")
    print(f"Capital:     ${cash:,.2f}")
    print(f"Commission:  {commission * 100:.2f}% ({commission * 10000:.1f} pips)")

    try:
        # Load data
        df = load_data(instrument, granularity, from_date, to_date)

        # Validate sufficient data
        validate_data_for_strategy(df)

        # Select strategy class
        StrategyClass = (
            RSIMeanReversionOptimized
            if strategy_type == "optimized"
            else RSIMeanReversion
        )

        # Initialize backtest
        bt = Backtest(
            df,
            StrategyClass,
            cash=cash,
            commission=commission,
            margin=1.0,  # No leverage for forex
            trade_on_close=False,
            hedging=False,
            exclusive_orders=True,
        )

        # Run optimization or regular backtest
        if optimize:
            print(f"\n{'=' * 80}")
            print("RUNNING PARAMETER OPTIMIZATION")
            print(f"{'=' * 80}")
            print("This may take several minutes...")

            # Define parameter ranges for optimization
            if strategy_type == "optimized":
                # Optimized strategy has additional parameters
                stats = bt.optimize(
                    rsi_period=range(10, 21, 2),
                    rsi_oversold=range(15, 31, 5),
                    rsi_overbought=range(70, 86, 5),
                    bb_period=range(15, 31, 5),
                    bb_std=[1.5, 2.0, 2.5],
                    risk_reward=[1.5, 2.0, 2.5, 3.0],
                    min_bb_width=[0.0005, 0.0010, 0.0015],
                    max_bb_width=[0.0040, 0.0050, 0.0060],
                    maximize="Sharpe Ratio",
                    constraint=lambda p: p.rsi_oversold < 50 and p.rsi_overbought > 50,
                )
            else:
                # Base strategy parameters
                stats = bt.optimize(
                    rsi_period=range(10, 21, 2),
                    rsi_oversold=range(15, 31, 5),
                    rsi_overbought=range(70, 86, 5),
                    bb_period=range(15, 31, 5),
                    bb_std=[1.5, 2.0, 2.5],
                    risk_reward=[1.5, 2.0, 2.5, 3.0],
                    maximize="Sharpe Ratio",
                    constraint=lambda p: p.rsi_oversold < 50 and p.rsi_overbought > 50,
                )

            print("\n✓ Optimization complete!")
            print(f"\n{'=' * 80}")
            print("OPTIMAL PARAMETERS")
            print(f"{'=' * 80}")
            print(f"RSI Period:      {stats._strategy.rsi_period}")
            print(f"RSI Oversold:    {stats._strategy.rsi_oversold}")
            print(f"RSI Overbought:  {stats._strategy.rsi_overbought}")
            print(f"BB Period:       {stats._strategy.bb_period}")
            print(f"BB Std Dev:      {stats._strategy.bb_std}")
            print(f"Risk/Reward:     {stats._strategy.risk_reward}")
            if strategy_type == "optimized":
                print(f"Min BB Width:    {stats._strategy.min_bb_width}")
                print(f"Max BB Width:    {stats._strategy.max_bb_width}")

        else:
            # Run regular backtest with default parameters
            stats = bt.run()

        # Print detailed statistics
        print(f"\n{'=' * 80}")
        print("BACKTEST RESULTS")
        print(f"{'=' * 80}")
        print(stats)

        # Print trade summary
        print_trade_summary(stats, num_trades=10)

        # Create results directory if needed
        results_dir = Path(__file__).parent.parent / "results" / "equity_curves"
        results_dir.mkdir(parents=True, exist_ok=True)

        # Save equity curve
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_suffix = "_opt" if optimize else ""
        filename = f"{instrument}_{granularity}_{from_date}_{to_date}_{strategy_type}{strategy_suffix}_{timestamp}.png"
        output_path = results_dir / filename

        save_equity_curve(stats, output_path)

        # Print key metrics summary
        print(f"\n{'=' * 80}")
        print("KEY METRICS SUMMARY")
        print(f"{'=' * 80}")
        print(f"Total Return:       {stats['Return [%]']:.2f}%")
        print(f"Sharpe Ratio:       {stats['Sharpe Ratio']:.2f}")
        print(f"Max Drawdown:       {stats['Max. Drawdown [%]']:.2f}%")
        print(f"Win Rate:           {stats['Win Rate [%]']:.2f}%")
        print(f"Number of Trades:   {stats['# Trades']}")
        print(f"Exposure Time:      {stats['Exposure Time [%]']:.2f}%")

        if stats["# Trades"] > 0:
            print(f"Avg Trade:          ${stats['Avg. Trade [%]']:.2f}%")
            print(f"Best Trade:         {stats['Best Trade [%]']:.2f}%")
            print(f"Worst Trade:        {stats['Worst Trade [%]']:.2f}%")

        print(f"\n{'=' * 80}")
        print("BACKTEST COMPLETE")
        print(f"{'=' * 80}\n")

        return stats

    except FileNotFoundError as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def parse_date(date_str: str) -> str:
    """
    Parse and validate date string.

    Args:
        date_str: Date in format YYYY-MM-DD or YYYYMMDD

    Returns:
        Date in format YYYYMMDD

    Raises:
        ValueError: If date format is invalid
    """
    try:
        # Try parsing with hyphen
        if "-" in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y%m%d")
        else:
            # Validate YYYYMMDD format
            dt = datetime.strptime(date_str, "%Y%m%d")
            return date_str
    except ValueError:
        raise ValueError(
            f"Invalid date format: {date_str}\n"
            f"Expected format: YYYY-MM-DD or YYYYMMDD\n"
            f"Example: 2024-01-01 or 20240101"
        )


def main():
    """Main entry point for the backtesting script."""
    parser = argparse.ArgumentParser(
        description="Backtest RSI Mean Reversion strategy on historical forex data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run backtest with default settings (EUR_USD M15, full 2024)
  python src/backtest_rsi.py

  # Specify custom date range
  python src/backtest_rsi.py --from-date 2024-01-01 --to-date 2024-06-30

  # Run parameter optimization
  python src/backtest_rsi.py --optimize

  # Use optimized strategy variant with additional filters
  python src/backtest_rsi.py --strategy optimized

  # Custom instrument and timeframe
  python src/backtest_rsi.py --instrument GBP_USD --granularity H1

  # Full example with all options
  python src/backtest_rsi.py --instrument EUR_USD --granularity M15 \\
                             --from-date 2024-01-01 --to-date 2024-12-31 \\
                             --strategy optimized --optimize --cash 50000 \\
                             --commission 0.0002

Output:
  - Console: Detailed performance statistics and trade summary
  - File: Equity curve plot saved to results/equity_curves/
        """,
    )

    parser.add_argument(
        "--instrument",
        type=str,
        default="EUR_USD",
        help="Trading instrument (e.g., EUR_USD, GBP_USD). Default: EUR_USD",
    )

    parser.add_argument(
        "--granularity",
        type=str,
        default="M15",
        help="Timeframe granularity (e.g., M15, H1, H4, D). Default: M15",
    )

    parser.add_argument(
        "--from-date",
        type=str,
        default="20240101",
        help="Start date in YYYY-MM-DD or YYYYMMDD format. Default: 20240101",
    )

    parser.add_argument(
        "--to-date",
        type=str,
        default="20241231",
        help="End date in YYYY-MM-DD or YYYYMMDD format. Default: 20241231",
    )

    parser.add_argument(
        "--strategy",
        type=str,
        choices=["base", "optimized"],
        default="base",
        help="Strategy variant: base (RSIMeanReversion) or optimized (RSIMeanReversionOptimized with filters). Default: base",
    )

    parser.add_argument(
        "--cash",
        type=float,
        default=10000,
        help="Initial capital in dollars. Default: 10000",
    )

    parser.add_argument(
        "--commission",
        type=float,
        default=0.0001,
        help="Commission per trade as decimal (0.0001 = 1 pip for forex). Default: 0.0001",
    )

    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Run parameter optimization to find best strategy parameters",
    )

    args = parser.parse_args()

    # Parse and validate dates
    try:
        from_date = parse_date(args.from_date)
        to_date = parse_date(args.to_date)

        # Validate date range
        from_dt = datetime.strptime(from_date, "%Y%m%d")
        to_dt = datetime.strptime(to_date, "%Y%m%d")

        if from_dt >= to_dt:
            print(f"\n❌ Error: from-date must be before to-date")
            print(f"   from-date: {from_date}")
            print(f"   to-date:   {to_date}")
            sys.exit(1)

    except ValueError as e:
        print(f"\n❌ Date error: {str(e)}")
        sys.exit(1)

    # Run backtest
    run_backtest(
        instrument=args.instrument,
        granularity=args.granularity,
        from_date=from_date,
        to_date=to_date,
        strategy_type=args.strategy,
        cash=args.cash,
        commission=args.commission,
        optimize=args.optimize,
    )


if __name__ == "__main__":
    main()
