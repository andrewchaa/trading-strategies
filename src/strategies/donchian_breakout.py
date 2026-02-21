"""
Donchian Channel Breakout Strategy

Two implementations:

1. DonchianBreakout (Single-Timeframe)
   - Upper band = highest high over previous N bars
   - Lower band = lowest low over previous N bars
   - Entry LONG: close breaks above upper band
   - Entry SHORT: close breaks below lower band
   - Stop Loss: ATR-based

2. DonchianBreakoutMTF (Multi-Timeframe - Recommended)
   - Same breakout logic on M15
   - H1 Donchian middle band as trend filter
   - LONG only when M15 close > H1 middle band
   - SHORT only when M15 close < H1 middle band
   - Requires H1_DC_Mid column pre-calculated and forward-filled
"""

from backtesting import Strategy
import pandas_ta as ta
import pandas as pd
import numpy as np


def rolling_high(series, period):
    """Highest high over previous N bars (excludes current bar)."""
    return pd.Series(series).shift(1).rolling(period).max().values


def rolling_low(series, period):
    """Lowest low over previous N bars (excludes current bar)."""
    return pd.Series(series).shift(1).rolling(period).min().values


def rolling_mid(high, low, period):
    """Middle of Donchian channel over previous N bars."""
    upper = pd.Series(high).shift(1).rolling(period).max()
    lower = pd.Series(low).shift(1).rolling(period).min()
    return ((upper + lower) / 2).values


class DonchianBreakout(Strategy):
    """
    Donchian Channel Breakout Strategy (Single-Timeframe)

    Parameters:
        dc_period: Donchian channel lookback period (default: 40)
        atr_period: ATR period for stop loss (default: 14)
        sl_atr_mult: Stop loss ATR multiplier (default: 2.0)
        risk_reward: Risk to reward ratio (default: 2.0)
        min_channel_pct: Minimum channel width as fraction of price (default: 0.002)
    """

    dc_period = 40
    atr_period = 14
    sl_atr_mult = 2.0
    risk_reward = 2.0
    min_channel_pct = 0.002

    def init(self):
        high = self.data.High
        low = self.data.Low
        close = self.data.Close

        self.dc_upper = self.I(rolling_high, pd.Series(high), self.dc_period)
        self.dc_lower = self.I(rolling_low, pd.Series(low), self.dc_period)
        self.dc_mid = self.I(rolling_mid, pd.Series(high), pd.Series(low), self.dc_period)

        self.atr = self.I(
            ta.atr,
            pd.Series(high),
            pd.Series(low),
            pd.Series(close),
            length=self.atr_period,
        )

    def next(self):
        price = self.data.Close[-1]

        if np.isnan(self.dc_upper[-1]) or np.isnan(self.atr[-1]):
            return

        if self.position:
            return

        # Volatility filter: skip breakouts in narrow channels (consolidation/noise)
        if (self.dc_upper[-1] - self.dc_lower[-1]) / price < self.min_channel_pct:
            return

        sl_dist = self.atr[-1] * self.sl_atr_mult

        if price > self.dc_upper[-1]:
            stop_loss = price - sl_dist
            take_profit = price + sl_dist * self.risk_reward
            self.buy(sl=stop_loss, tp=take_profit)

        elif price < self.dc_lower[-1]:
            stop_loss = price + sl_dist
            take_profit = price - sl_dist * self.risk_reward
            self.sell(sl=stop_loss, tp=take_profit)


class DonchianBreakoutMTF(Strategy):
    """
    Multi-Timeframe Donchian Channel Breakout Strategy

    Uses H1 Donchian middle band as trend filter and M15 for entries.
    Expects DataFrame with H1_DC_Mid column pre-calculated and forward-filled.

    Parameters:
        dc_period: Donchian channel lookback period (default: 40)
        atr_period: ATR period for stop loss (default: 14)
        sl_atr_mult: Stop loss ATR multiplier (default: 2.0)
        risk_reward: Risk to reward ratio (default: 2.0)
        min_channel_pct: Minimum channel width as fraction of price (default: 0.002)

    Data Requirements:
        - M15 OHLCV columns (Open, High, Low, Close, Volume)
        - H1_DC_Mid column: Pre-calculated H1 Donchian middle band, forward-filled to M15
    """

    dc_period = 40
    atr_period = 14
    sl_atr_mult = 2.0
    risk_reward = 2.0
    min_channel_pct = 0.002

    def init(self):
        if "H1_DC_Mid" not in self.data.df.columns:
            raise ValueError(
                "H1_DC_Mid column not found in data. "
                "Please calculate H1 Donchian middle band and forward-fill to M15 before backtesting."
            )

        high = self.data.High
        low = self.data.Low
        close = self.data.Close

        self.dc_upper = self.I(rolling_high, pd.Series(high), self.dc_period)
        self.dc_lower = self.I(rolling_low, pd.Series(low), self.dc_period)

        self.atr = self.I(
            ta.atr,
            pd.Series(high),
            pd.Series(low),
            pd.Series(close),
            length=self.atr_period,
        )

    def next(self):
        price = self.data.Close[-1]

        if np.isnan(self.dc_upper[-1]) or np.isnan(self.atr[-1]):
            return

        if self.position:
            return

        h1_dc_mid = self.data.H1_DC_Mid[-1]
        if pd.isna(h1_dc_mid):
            return

        # Volatility filter: skip breakouts in narrow channels (consolidation/noise)
        if (self.dc_upper[-1] - self.dc_lower[-1]) / price < self.min_channel_pct:
            return

        sl_dist = self.atr[-1] * self.sl_atr_mult

        if price > h1_dc_mid and price > self.dc_upper[-1]:
            stop_loss = price - sl_dist
            take_profit = price + sl_dist * self.risk_reward
            self.buy(sl=stop_loss, tp=take_profit)

        elif price < h1_dc_mid and price < self.dc_lower[-1]:
            stop_loss = price + sl_dist
            take_profit = price - sl_dist * self.risk_reward
            self.sell(sl=stop_loss, tp=take_profit)
