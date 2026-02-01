"""
RSI Mean Reversion Strategy - Multi-Timeframe Implementation

Strategy Overview:
- Timeframes: H1 (trend filter) + M15 (entry signals)
- Win Rate: 55-65% (expected)
- Risk/Reward: 1:2
- Trades per day: 2-4 (expected)

Two implementations available:

1. RSIMeanReversion (Single-Timeframe - Legacy)
   - Uses M15 data only
   - EMA200 calculated on M15 (not recommended for production)
   - Default RSI thresholds: 30/70

2. RSIMeanReversionMTF (Multi-Timeframe - Recommended)
   - Uses H1 EMA200 for trend filter + M15 for entries
   - Proper multi-timeframe approach
   - Default RSI thresholds: 30/70
   - Requires H1_EMA200 column pre-calculated and forward-filled

Entry Rules (Multi-Timeframe):
- LONG: H1 price > H1_EMA200 + M15 price touches lower BB + M15 RSI < 30
- SHORT: H1 price < H1_EMA200 + M15 price touches upper BB + M15 RSI > 70

Exit Rules:
- Stop Loss: 1.1x distance from BB extreme
- Take Profit: Stop loss distance * risk_reward ratio (default 2.0)

RSI Threshold Guidance:
- RSI 30/70: Standard mean reversion (recommended, ~10-15% exposure)
- RSI 20/80: Extreme mean reversion (very conservative, ~1-2% exposure)
- Adjust based on backtesting results for your instrument and timeframe
"""

from backtesting import Strategy
import pandas_ta as ta
import pandas as pd
import numpy as np


class RSIMeanReversion(Strategy):
    """
    RSI Mean Reversion Strategy

    Parameters:
        rsi_period: RSI calculation period (default: 14)
        rsi_oversold: RSI oversold threshold (default: 20)
        rsi_overbought: RSI overbought threshold (default: 80)
        bb_period: Bollinger Bands period (default: 20)
        bb_std: Bollinger Bands standard deviation (default: 2.0)
        ema_period: EMA trend filter period on H1 (default: 200)
        risk_reward: Risk to reward ratio (default: 2.0)
    """

    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    bb_period = 20
    bb_std = 2.0
    ema_period = 200
    risk_reward = 2.0

    def init(self):
        """Initialize indicators"""
        close = self.data.Close

        self.rsi = self.I(ta.rsi, pd.Series(close), length=self.rsi_period)

        # Calculate Bollinger Bands - pandas_ta returns DataFrame with multiple columns
        # We need to extract each band separately
        close_series = pd.Series(close)

        # Helper functions to extract individual BB columns
        def bb_upper(s, length, std):
            bb = ta.bbands(s, length=length, std=std, mamode="sma")
            col_name = f"BBU_{length}_{std}_2.0"
            return (
                bb[col_name].values if col_name in bb.columns else bb.iloc[:, 2].values
            )

        def bb_middle(s, length, std):
            bb = ta.bbands(s, length=length, std=std, mamode="sma")
            col_name = f"BBM_{length}_{std}_2.0"
            return (
                bb[col_name].values if col_name in bb.columns else bb.iloc[:, 1].values
            )

        def bb_lower(s, length, std):
            bb = ta.bbands(s, length=length, std=std, mamode="sma")
            col_name = f"BBL_{length}_{std}_2.0"
            return (
                bb[col_name].values if col_name in bb.columns else bb.iloc[:, 0].values
            )

        self.bb_upper = self.I(bb_upper, close_series, self.bb_period, self.bb_std)
        self.bb_middle = self.I(bb_middle, close_series, self.bb_period, self.bb_std)
        self.bb_lower = self.I(bb_lower, close_series, self.bb_period, self.bb_std)

        self.ema_200 = self.I(ta.ema, pd.Series(close), length=self.ema_period)

    def next(self):
        """Execute strategy logic on each new bar"""
        price = self.data.Close[-1]

        if len(self.data) < self.ema_period:
            return

        if self.rsi[-1] is None or self.bb_lower[-1] is None:
            return

        if self.position:
            return

        ema_trend_up = price > self.ema_200[-1]
        ema_trend_down = price < self.ema_200[-1]

        touches_lower_bb = price <= self.bb_lower[-1] * 1.001
        touches_upper_bb = price >= self.bb_upper[-1] * 0.999

        rsi_oversold = self.rsi[-1] < self.rsi_oversold
        rsi_overbought = self.rsi[-1] > self.rsi_overbought

        if ema_trend_up and touches_lower_bb and rsi_oversold:
            sl_distance = abs(price - self.bb_lower[-1])
            stop_loss = price - sl_distance * 1.1
            take_profit = price + (sl_distance * 1.1 * self.risk_reward)

            self.buy(sl=stop_loss, tp=take_profit)

        elif ema_trend_down and touches_upper_bb and rsi_overbought:
            sl_distance = abs(self.bb_upper[-1] - price)
            stop_loss = price + sl_distance * 1.1
            take_profit = price - (sl_distance * 1.1 * self.risk_reward)

            self.sell(sl=stop_loss, tp=take_profit)


class RSIMeanReversionOptimized(RSIMeanReversion):
    """
    Optimized version with additional filters and risk management
    """

    min_bb_width = 0.0010
    max_bb_width = 0.0050

    def init(self):
        """Initialize indicators with additional filters"""
        super().init()

        self.atr = self.I(
            ta.atr,
            pd.Series(self.data.High),
            pd.Series(self.data.Low),
            pd.Series(self.data.Close),
            length=14,
        )

    def next(self):
        """Execute strategy with additional filters"""
        if len(self.data) < self.ema_period:
            return

        if self.rsi[-1] is None or self.bb_lower[-1] is None:
            return

        bb_width = (self.bb_upper[-1] - self.bb_lower[-1]) / self.bb_middle[-1]

        if bb_width < self.min_bb_width or bb_width > self.max_bb_width:
            return

        super().next()


class RSIMeanReversionMTF(Strategy):
    """
    Multi-Timeframe RSI Mean Reversion Strategy

    Uses H1 data for trend filter (EMA200) and M15 data for entry signals.
    Expects DataFrame with H1_EMA200 column pre-calculated and forward-filled.

    Parameters:
        rsi_period: RSI calculation period (default: 14)
        rsi_oversold: RSI oversold threshold (default: 30)
        rsi_overbought: RSI overbought threshold (default: 70)
        bb_period: Bollinger Bands period (default: 20)
        bb_std: Bollinger Bands standard deviation (default: 2.0)
        risk_reward: Risk to reward ratio (default: 2.0)

    Data Requirements:
        - M15 OHLCV columns (Open, High, Low, Close, Volume)
        - H1_EMA200 column: Pre-calculated H1 EMA200, forward-filled to M15 frequency

    Entry Logic:
        LONG: M15 price > H1_EMA200 + M15 price touches lower BB + M15 RSI < 30
        SHORT: M15 price < H1_EMA200 + M15 price touches upper BB + M15 RSI > 70

    Exit Logic:
        - Stop Loss: 1.1x distance from Bollinger Band extreme
        - Take Profit: Stop loss distance * risk_reward ratio
    """

    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    bb_period = 20
    bb_std = 2.0
    risk_reward = 2.0

    def init(self):
        """Initialize indicators for M15 timeframe"""
        close = self.data.Close

        # RSI on M15
        self.rsi = self.I(ta.rsi, pd.Series(close), length=self.rsi_period)

        # Bollinger Bands on M15
        close_series = pd.Series(close)

        def bb_upper(s, length, std):
            bb = ta.bbands(s, length=length, std=std, mamode="sma")
            col_name = f"BBU_{length}_{std}_2.0"
            return (
                bb[col_name].values if col_name in bb.columns else bb.iloc[:, 2].values
            )

        def bb_middle(s, length, std):
            bb = ta.bbands(s, length=length, std=std, mamode="sma")
            col_name = f"BBM_{length}_{std}_2.0"
            return (
                bb[col_name].values if col_name in bb.columns else bb.iloc[:, 1].values
            )

        def bb_lower(s, length, std):
            bb = ta.bbands(s, length=length, std=std, mamode="sma")
            col_name = f"BBL_{length}_{std}_2.0"
            return (
                bb[col_name].values if col_name in bb.columns else bb.iloc[:, 0].values
            )

        self.bb_upper = self.I(bb_upper, close_series, self.bb_period, self.bb_std)
        self.bb_middle = self.I(bb_middle, close_series, self.bb_period, self.bb_std)
        self.bb_lower = self.I(bb_lower, close_series, self.bb_period, self.bb_std)

        # H1 EMA200 (pre-calculated, forward-filled from H1 to M15)
        # Access from self.data.H1_EMA200
        if "H1_EMA200" not in self.data.df.columns:
            raise ValueError(
                "H1_EMA200 column not found in data. "
                "Please calculate H1 EMA200 and forward-fill to M15 before backtesting."
            )

    def next(self):
        """Execute strategy logic on each M15 bar"""
        price = self.data.Close[-1]

        # Wait for indicators to be ready
        if self.rsi[-1] is None or self.bb_lower[-1] is None:
            return

        # Only one position at a time
        if self.position:
            return

        # Get H1 EMA200 value (pre-calculated and forward-filled)
        h1_ema200 = self.data.H1_EMA200[-1]

        if pd.isna(h1_ema200):
            return

        # Trend detection using H1 EMA200
        ema_trend_up = price > h1_ema200
        ema_trend_down = price < h1_ema200

        # M15 Bollinger Band touch detection (1% tolerance)
        touches_lower_bb = price <= self.bb_lower[-1] * 1.001
        touches_upper_bb = price >= self.bb_upper[-1] * 0.999

        # M15 RSI conditions
        rsi_oversold = self.rsi[-1] < self.rsi_oversold
        rsi_overbought = self.rsi[-1] > self.rsi_overbought

        # LONG Entry: H1 uptrend + M15 lower BB touch + M15 RSI oversold
        if ema_trend_up and touches_lower_bb and rsi_oversold:
            sl_distance = abs(price - self.bb_lower[-1])
            stop_loss = price - sl_distance * 1.1
            take_profit = price + (sl_distance * 1.1 * self.risk_reward)

            self.buy(sl=stop_loss, tp=take_profit)

        # SHORT Entry: H1 downtrend + M15 upper BB touch + M15 RSI overbought
        elif ema_trend_down and touches_upper_bb and rsi_overbought:
            sl_distance = abs(self.bb_upper[-1] - price)
            stop_loss = price + sl_distance * 1.1
            take_profit = price - (sl_distance * 1.1 * self.risk_reward)

            self.sell(sl=stop_loss, tp=take_profit)
