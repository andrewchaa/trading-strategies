#!/usr/bin/env python
"""
Quick test script to verify multi-timeframe strategy implementation.
Tests that RSIMeanReversionMTF can be instantiated and run on sample data.
"""

import sys
import pandas as pd
import numpy as np
import pandas_ta as ta
from pathlib import Path
from backtesting import Backtest
from src.strategies.rsi_mean_reversion import RSIMeanReversionMTF


def create_sample_data(n_bars=1000):
    """Create synthetic M15 data with H1_EMA200 column."""
    dates = pd.date_range("2025-01-01", periods=n_bars, freq="15min")

    np.random.seed(42)
    close_prices = 1.0500 + np.cumsum(np.random.randn(n_bars) * 0.0001)

    df = pd.DataFrame(
        {
            "Open": close_prices + np.random.randn(n_bars) * 0.0001,
            "High": close_prices + np.abs(np.random.randn(n_bars) * 0.0002),
            "Low": close_prices - np.abs(np.random.randn(n_bars) * 0.0002),
            "Close": close_prices,
            "Volume": np.random.randint(100, 1000, n_bars),
        },
        index=dates,
    )

    df["High"] = df[["Open", "High", "Close"]].max(axis=1)
    df["Low"] = df[["Open", "Low", "Close"]].min(axis=1)

    h1_ema200 = ta.ema(df["Close"].resample("1h").last().ffill(), length=200)
    df["H1_EMA200"] = h1_ema200.reindex(df.index, method="ffill")

    return df


def main():
    print("=" * 60)
    print("TESTING MULTI-TIMEFRAME STRATEGY IMPLEMENTATION")
    print("=" * 60)

    print("\n[1/4] Creating sample data with H1_EMA200 column...")
    df = create_sample_data(n_bars=5000)
    print(f"✓ Created {len(df)} M15 bars")
    print(f"  Columns: {list(df.columns)}")
    print(f"  H1_EMA200 non-null: {df['H1_EMA200'].notna().sum()}/{len(df)}")

    print("\n[2/4] Verifying RSIMeanReversionMTF class...")
    print(f"✓ Default parameters:")
    print(f"  rsi_oversold: {RSIMeanReversionMTF.rsi_oversold}")
    print(f"  rsi_overbought: {RSIMeanReversionMTF.rsi_overbought}")
    print(f"  bb_period: {RSIMeanReversionMTF.bb_period}")
    print(f"  risk_reward: {RSIMeanReversionMTF.risk_reward}")

    print("\n[3/4] Running backtest with RSIMeanReversionMTF...")
    try:
        bt = Backtest(df, RSIMeanReversionMTF, cash=10000, commission=0.0001)
        stats = bt.run()
        print("✓ Backtest completed successfully")
        print(f"\nResults:")
        print(f"  # Trades: {stats['# Trades']}")
        print(f"  Exposure Time [%]: {stats['Exposure Time [%]']:.2f}%")
        print(f"  Return [%]: {stats['Return [%]']:.2f}%")
        if stats["# Trades"] > 0:
            print(f"  Win Rate [%]: {stats['Win Rate [%]']:.2f}%")
    except Exception as e:
        print(f"✗ Backtest failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    print("\n[4/4] Verifying H1_EMA200 requirement...")
    try:
        df_no_h1 = df.drop(columns=["H1_EMA200"])
        bt_fail = Backtest(df_no_h1, RSIMeanReversionMTF, cash=10000, commission=0.0001)
        bt_fail.run()
        print("✗ ERROR: Strategy should have raised ValueError for missing H1_EMA200")
        return 1
    except ValueError as e:
        print(f"✓ Correctly raised ValueError for missing H1_EMA200:")
        print(f"  {str(e)}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)
    print("\nMulti-timeframe strategy implementation is working correctly.")
    print(
        "You can now run the notebook: notebooks/02_rsi_mean_reversion_backtest.ipynb"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
