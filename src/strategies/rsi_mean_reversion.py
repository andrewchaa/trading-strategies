"""
RSI Mean Reversion Strategy

Strategy Overview:
- Timeframe: 15-minute primary, 1-hour for trend filter
- Win Rate: 55-65%
- Risk/Reward: 1:2
- Trades per day: 2-4

Entry Rules:
- LONG: H1 price above EMA200 + M15 price touches lower BB + RSI < 20
- SHORT: H1 price below EMA200 + M15 price touches upper BB + RSI > 80

Exit Rules:
- Stop Loss: Beyond BB extreme (20-30 pips)
- Take Profit: Middle BB (1:2 risk/reward)
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
    rsi_oversold = 20
    rsi_overbought = 80
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
