"""
Donchian Breakout Signal Detector

Replicates the DonchianBreakout.next() logic for live signal detection.
"""

import pandas as pd
import pandas_ta as ta


def detect_signal(
    df,
    dc_period=40,
    atr_period=14,
    sl_atr_mult=2.0,
    min_channel_pct=0.002,
):
    """
    Detect a Donchian breakout signal from a DataFrame of candles.

    Args:
        df: DataFrame with 'high', 'low', 'close' columns (lowercase).
            Only complete candles should be passed in.
        dc_period: Donchian channel lookback period (default 40).
        atr_period: ATR period for stop loss (default 14).
        sl_atr_mult: ATR multiplier for stop loss distance (default 2.0).
        min_channel_pct: Minimum channel width as fraction of price (default 0.002).

    Returns:
        dict with keys 'side' ('buy'|'sell'), 'sl_dist' (float), 'entry_price' (float)
        or None if no signal.
    """
    high = df['high']
    low = df['low']
    close = df['close']

    upper = high.shift(1).rolling(dc_period).max()
    lower = low.shift(1).rolling(dc_period).min()
    atr = ta.atr(high, low, close, length=atr_period)

    last_upper = upper.iloc[-1]
    last_lower = lower.iloc[-1]
    last_atr = atr.iloc[-1]
    last_close = close.iloc[-1]

    if pd.isna(last_upper) or pd.isna(last_atr):
        return None

    if (last_upper - last_lower) / last_close < min_channel_pct:
        return None

    sl_dist = last_atr * sl_atr_mult

    if last_close > last_upper:
        return {'side': 'buy', 'sl_dist': sl_dist, 'entry_price': last_close}
    elif last_close < last_lower:
        return {'side': 'sell', 'sl_dist': sl_dist, 'entry_price': last_close}

    return None
