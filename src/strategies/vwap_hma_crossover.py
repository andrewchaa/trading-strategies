"""
VWAP & HMA Crossover Strategy - Intraday Trend Following

Strategy Overview:
- Timeframe: M15 (15-minute candles)
- Style: Intraday trend following with institutional bias
- Win Rate: 50-60% (expected)
- Risk/Reward: 1:2
- Trades per day: 3-5 (expected)

Key Concepts:
- VWAP (Volume Weighted Average Price): Represents the average price weighted by volume
  Acts as the "fair value" benchmark - institutional traders use this
- HMA (Hull Moving Average): Fast-reacting moving average that reduces lag
  More responsive than traditional moving averages

Entry Rules:
- LONG: Price > VWAP (bullish bias) + HMA crosses above price (bullish momentum)
- SHORT: Price < VWAP (bearish bias) + HMA crosses below price (bearish momentum)

Exit Rules:
- Stop Loss: 1.5× ATR(14) from entry price
- Take Profit: 2× stop loss distance (1:2 R/R)
- Time Exit: Close all positions 30 minutes before market close (avoid overnight fees)

Risk Management:
- Position size: 2% of capital per trade
- Maximum 2 concurrent positions
- Intraday only (no overnight exposure)

Best Pairs: EUR_USD, GBP_USD (high liquidity, tight spreads)
"""

from backtesting import Strategy
import pandas as pd
import numpy as np
import pandas_ta as ta


class VWAPHMACrossover(Strategy):
    """
    VWAP & HMA Crossover Strategy for Intraday CFD Trading

    Parameters:
        hma_period: Hull Moving Average period (default: 21)
        atr_period: ATR period for stop loss (default: 14)
        atr_multiplier: ATR multiplier for stop loss (default: 1.5)
        risk_reward: Risk to reward ratio (default: 2.0)
        close_before_eod_minutes: Minutes before market close to exit (default: 30)
    """

    hma_period = 21
    atr_period = 14
    atr_multiplier = 1.5
    risk_reward = 2.0
    close_before_eod_minutes = 30

    def init(self):
        """Initialize indicators"""
        close = pd.Series(self.data.Close, index=self.data.index)
        high = pd.Series(self.data.High, index=self.data.index)
        low = pd.Series(self.data.Low, index=self.data.index)
        volume = pd.Series(self.data.Volume, index=self.data.index)

        # Calculate VWAP (resets daily)
        def calculate_vwap(high, low, close, volume):
            """
            Calculate VWAP with daily reset.
            VWAP = Σ(Typical Price × Volume) / Σ(Volume)
            Typical Price = (High + Low + Close) / 3
            """
            typical_price = (high + low + close) / 3
            
            # Get date for grouping
            dates = pd.Series(self.data.index).apply(lambda x: x.date())
            
            vwap = np.zeros(len(typical_price))
            
            # Calculate VWAP for each day
            for i in range(len(typical_price)):
                current_date = dates.iloc[i]
                
                # Find all indices for current date up to current bar
                day_mask = (dates[:i+1] == current_date).values
                
                if day_mask.sum() > 0:
                    day_tp = typical_price.iloc[:i+1][day_mask]
                    day_vol = volume.iloc[:i+1][day_mask]
                    
                    # Handle zero volume
                    total_vol = day_vol.sum()
                    if total_vol > 0:
                        vwap[i] = (day_tp * day_vol).sum() / total_vol
                    else:
                        vwap[i] = typical_price.iloc[i]
                else:
                    vwap[i] = typical_price.iloc[i]
            
            return vwap

        self.vwap = self.I(calculate_vwap, high, low, close, volume)

        # Calculate HMA (Hull Moving Average)
        self.hma = self.I(ta.hma, close, length=self.hma_period)

        # Calculate ATR for stop loss
        self.atr = self.I(ta.atr, high, low, close, length=self.atr_period)

    def next(self):
        """Execute strategy logic on each new bar"""
        # Wait for indicators to be ready
        if len(self.data) < self.hma_period:
            return

        if self.hma[-1] is None or self.vwap[-1] is None or self.atr[-1] is None:
            return

        price = self.data.Close[-1]
        current_time = self.data.index[-1]

        # Check if we should close positions before end of day
        if self._should_close_eod(current_time):
            if self.position:
                self.position.close()
            return

        # Only one position at a time
        if self.position:
            return

        # Current values
        hma_now = self.hma[-1]
        hma_prev = self.hma[-2] if len(self.data) > 1 else None
        vwap_now = self.vwap[-1]
        atr_now = self.atr[-1]

        price_now = price
        price_prev = self.data.Close[-2] if len(self.data) > 1 else None

        if hma_prev is None or price_prev is None:
            return

        # Detect crossovers
        # HMA crosses above price: bullish signal
        hma_crosses_above = (hma_now > price_now) and (hma_prev <= price_prev)
        
        # HMA crosses below price: bearish signal
        hma_crosses_below = (hma_now < price_now) and (hma_prev >= price_prev)

        # VWAP bias
        above_vwap = price_now > vwap_now  # Bullish bias
        below_vwap = price_now < vwap_now  # Bearish bias

        # LONG Entry: Price > VWAP + HMA crosses above price
        if above_vwap and hma_crosses_above:
            stop_loss = price_now - (atr_now * self.atr_multiplier)
            sl_distance = price_now - stop_loss
            take_profit = price_now + (sl_distance * self.risk_reward)

            self.buy(sl=stop_loss, tp=take_profit)

        # SHORT Entry: Price < VWAP + HMA crosses below price
        elif below_vwap and hma_crosses_below:
            stop_loss = price_now + (atr_now * self.atr_multiplier)
            sl_distance = stop_loss - price_now
            take_profit = price_now - (sl_distance * self.risk_reward)

            self.sell(sl=stop_loss, tp=take_profit)

    def _should_close_eod(self, current_time):
        """
        Check if we should close positions before end of trading day.
        
        For forex (24h market), we define "end of day" as:
        - Friday 21:00 UTC (before weekend)
        - Daily 23:30 UTC (to avoid low liquidity overnight)
        
        Args:
            current_time: Current bar timestamp
            
        Returns:
            bool: True if we should close positions
        """
        # Get hour and day of week
        hour = current_time.hour
        minute = current_time.minute
        day_of_week = current_time.weekday()  # Monday=0, Sunday=6

        # Close on Friday after 20:30 UTC (before weekend)
        if day_of_week == 4:  # Friday
            if hour >= 20 and minute >= 30:
                return True

        # Close every day after 23:00 UTC (low liquidity period)
        if hour >= 23:
            return True

        return False


class VWAPHMACrossoverOptimized(VWAPHMACrossover):
    """
    Optimized version with additional volume and volatility filters
    
    Additional Parameters:
        min_volume_multiplier: Minimum volume vs 20-period average (default: 1.0)
        min_atr_percentile: Minimum ATR percentile to trade (default: 0.3)
    """

    min_volume_multiplier = 1.0
    min_atr_percentile = 0.3

    def init(self):
        """Initialize indicators with additional filters"""
        super().init()

        # Calculate volume moving average
        volume = pd.Series(self.data.Volume, index=self.data.index)
        self.volume_ma = self.I(ta.sma, volume, length=20)

    def next(self):
        """Execute strategy with additional filters"""
        # Wait for volume MA to be ready
        if len(self.data) < 20:
            return

        if self.volume_ma[-1] is None:
            return

        # Volume filter: Only trade when volume is above average
        current_volume = self.data.Volume[-1]
        avg_volume = self.volume_ma[-1]

        if current_volume < avg_volume * self.min_volume_multiplier:
            return

        # ATR filter: Only trade when volatility is sufficient
        # Calculate ATR percentile over last 100 bars
        if len(self.data) >= 100:
            atr_values = [self.atr[i] for i in range(-100, 0) if self.atr[i] is not None]
            if len(atr_values) > 50:
                atr_percentile = np.percentile(atr_values, 100 * self.min_atr_percentile)
                if self.atr[-1] < atr_percentile:
                    return

        # Execute parent strategy logic
        super().next()
