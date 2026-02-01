# RSI Mean Reversion Strategy - Diagnostic Analysis

## Problem Identified

Your backtest showed **0% exposure time** and **0 trades** because the strategy conditions are too strict.

### Root Cause: Extreme RSI Thresholds

The default parameters require:
- **RSI < 20** for longs (only ~2-5% of candles)
- **RSI > 80** for shorts (only ~2-5% of candles)

Combined with requiring:
- Price above/below EMA(200) 
- Price touching Bollinger Bands

These conditions **almost never occur together**.

---

## Quick Fixes

### Option 1: Relax RSI Thresholds (Recommended)

Run the backtest with more reasonable RSI levels:

```python
# In the backtest cell, add parameters:
stats = bt.run(
    rsi_oversold=30,    # Changed from 20
    rsi_overbought=70   # Changed from 80
)
```

### Option 2: Use the Optimization Cell

The notebook already includes parameter optimization (Cell 8). This will automatically find better RSI thresholds:

```python
stats_opt = bt.optimize(
    rsi_period=range(10, 21, 2),
    rsi_oversold=range(15, 31, 5),     # Tests: 15, 20, 25, 30
    rsi_overbought=range(70, 86, 5),   # Tests: 70, 75, 80, 85
    bb_period=range(15, 26, 5),
    maximize='Sharpe Ratio'
)
```

### Option 3: Create Custom Parameters Cell

Add this cell before running the backtest:

```python
# Custom strategy parameters
custom_params = {
    'rsi_period': 14,
    'rsi_oversold': 30,      # More lenient
    'rsi_overbought': 70,    # More lenient
    'bb_period': 20,
    'bb_std': 2.0,
    'ema_period': 200,
    'risk_reward': 2.0
}

# Run with custom params
stats = bt.run(**custom_params)
```

---

## Diagnostic Cells

Add these cells to your notebook to diagnose the issue:

### Cell A: Check RSI Distribution

```python
# Calculate RSI on your data
import pandas_ta as ta

rsi = ta.rsi(df['Close'], length=14)

print("RSI Statistics:")
print(f"  Mean: {rsi.mean():.2f}")
print(f"  Std: {rsi.std():.2f}")
print(f"  Min: {rsi.min():.2f}")
print(f"  Max: {rsi.max():.2f}")
print(f"\nRSI < 20: {(rsi < 20).sum()} candles ({(rsi < 20).sum() / len(rsi) * 100:.2f}%)")
print(f"RSI > 80: {(rsi > 80).sum()} candles ({(rsi > 80).sum() / len(rsi) * 100:.2f}%)")
print(f"RSI < 30: {(rsi < 30).sum()} candles ({(rsi < 30).sum() / len(rsi) * 100:.2f}%)")
print(f"RSI > 70: {(rsi > 70).sum()} candles ({(rsi > 70).sum() / len(rsi) * 100:.2f}%)")

# Plot RSI distribution
import matplotlib.pyplot as plt
plt.figure(figsize=(14, 5))
plt.subplot(1, 2, 1)
plt.hist(rsi.dropna(), bins=50, edgecolor='black', alpha=0.7)
plt.axvline(20, color='red', linestyle='--', linewidth=2, label='Oversold (20)')
plt.axvline(80, color='red', linestyle='--', linewidth=2, label='Overbought (80)')
plt.axvline(30, color='orange', linestyle='--', linewidth=1, label='Relaxed Oversold (30)')
plt.axvline(70, color='orange', linestyle='--', linewidth=1, label='Relaxed Overbought (70)')
plt.xlabel('RSI')
plt.ylabel('Frequency')
plt.title('RSI Distribution - Full Dataset')
plt.legend()
plt.grid(alpha=0.3)

plt.subplot(1, 2, 2)
plt.plot(df.index, rsi, linewidth=0.5, alpha=0.7)
plt.axhline(20, color='red', linestyle='--', linewidth=2, label='Oversold (20)')
plt.axhline(80, color='red', linestyle='--', linewidth=2, label='Overbought (80)')
plt.axhline(30, color='orange', linestyle='--', linewidth=1, label='Relaxed (30)')
plt.axhline(70, color='orange', linestyle='--', linewidth=1, label='Relaxed (70)')
plt.xlabel('Date')
plt.ylabel('RSI')
plt.title('RSI Time Series')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
```

### Cell B: Check Combined Conditions

```python
# Calculate all indicators
rsi = ta.rsi(df['Close'], length=14)
bb = ta.bbands(df['Close'], length=20, std=2.0)
ema200 = ta.ema(df['Close'], length=200)

# Extract BB columns
bb_upper = bb[bb.columns[2]]  # Upper band
bb_lower = bb[bb.columns[0]]  # Lower band

# Check conditions
above_ema = df['Close'] > ema200
below_ema = df['Close'] < ema200
touches_lower = df['Close'] <= bb_lower * 1.001
touches_upper = df['Close'] >= bb_upper * 0.999
rsi_below_20 = rsi < 20
rsi_above_80 = rsi > 80
rsi_below_30 = rsi < 30
rsi_above_70 = rsi > 70

# Count potential signals
print("Condition Analysis (after EMA200 warm-up period):")
print("=" * 60)

valid_idx = ~ema200.isna()

print(f"\nTrend Filters:")
print(f"  Price > EMA200: {above_ema[valid_idx].sum():,} candles ({above_ema[valid_idx].sum() / valid_idx.sum() * 100:.1f}%)")
print(f"  Price < EMA200: {below_ema[valid_idx].sum():,} candles ({below_ema[valid_idx].sum() / valid_idx.sum() * 100:.1f}%)")

print(f"\nBollinger Band Touches:")
print(f"  Touches Lower BB: {touches_lower[valid_idx].sum():,} candles ({touches_lower[valid_idx].sum() / valid_idx.sum() * 100:.1f}%)")
print(f"  Touches Upper BB: {touches_upper[valid_idx].sum():,} candles ({touches_upper[valid_idx].sum() / valid_idx.sum() * 100:.1f}%)")

print(f"\nRSI Extremes (Current thresholds):")
print(f"  RSI < 20: {rsi_below_20[valid_idx].sum():,} candles ({rsi_below_20[valid_idx].sum() / valid_idx.sum() * 100:.1f}%)")
print(f"  RSI > 80: {rsi_above_80[valid_idx].sum():,} candles ({rsi_above_80[valid_idx].sum() / valid_idx.sum() * 100:.1f}%)")

print(f"\nRSI Extremes (Relaxed thresholds):")
print(f"  RSI < 30: {rsi_below_30[valid_idx].sum():,} candles ({rsi_below_30[valid_idx].sum() / valid_idx.sum() * 100:.1f}%)")
print(f"  RSI > 70: {rsi_above_70[valid_idx].sum():,} candles ({rsi_above_70[valid_idx].sum() / valid_idx.sum() * 100:.1f}%)")

print(f"\n" + "=" * 60)
print("COMBINED CONDITIONS (Long Entry Signals):")
print("=" * 60)

long_strict = above_ema & touches_lower & rsi_below_20
long_relaxed = above_ema & touches_lower & rsi_below_30

print(f"\nStrict (RSI < 20):")
print(f"  Signals: {long_strict[valid_idx].sum():,}")
print(f"  Expected trades/year: ~{long_strict[valid_idx].sum()}")

print(f"\nRelaxed (RSI < 30):")
print(f"  Signals: {long_relaxed[valid_idx].sum():,}")
print(f"  Expected trades/year: ~{long_relaxed[valid_idx].sum()}")

print(f"\n" + "=" * 60)
print("COMBINED CONDITIONS (Short Entry Signals):")
print("=" * 60)

short_strict = below_ema & touches_upper & rsi_above_80
short_relaxed = below_ema & touches_upper & rsi_above_70

print(f"\nStrict (RSI > 80):")
print(f"  Signals: {short_strict[valid_idx].sum():,}")
print(f"  Expected trades/year: ~{short_strict[valid_idx].sum()}")

print(f"\nRelaxed (RSI > 70):")
print(f"  Signals: {short_relaxed[valid_idx].sum():,}")
print(f"  Expected trades/year: ~{short_relaxed[valid_idx].sum()}")

print(f"\n" + "=" * 60)
print("RECOMMENDATION:")
print("=" * 60)

total_strict = long_strict[valid_idx].sum() + short_strict[valid_idx].sum()
total_relaxed = long_relaxed[valid_idx].sum() + short_relaxed[valid_idx].sum()

if total_strict == 0:
    print("❌ Current parameters (RSI 20/80) generate ZERO trade signals.")
    print(f"✅ Relaxed parameters (RSI 30/70) would generate {total_relaxed} trade signals.")
    print("\nRECOMMENDATION: Use RSI thresholds of 30/70 instead of 20/80")
else:
    print(f"Current parameters would generate {total_strict} trades")
    print(f"Relaxed parameters would generate {total_relaxed} trades")
```

---

## Expected Results After Fix

With **RSI 30/70** thresholds, you should see:
- **Exposure Time**: 5-15%
- **# Trades**: 20-100 trades per year
- **Win Rate**: 50-65% (if strategy is profitable)

---

## Implementation Steps

1. **Add diagnostic cells** above to understand the issue
2. **Modify Cell 4** (Run Basic Backtest) to use relaxed parameters:
   ```python
   stats = bt.run(rsi_oversold=30, rsi_overbought=70)
   ```
3. **Re-run the backtest**
4. **Analyze results** - you should now see trades!

---

## Why This Happens

This is a common issue with mean reversion strategies:

1. **Over-optimization on specific market conditions**: RSI 20/80 might work in highly volatile markets but fail in normal conditions
2. **Survivorship bias**: Published strategies often show parameters that worked on specific datasets
3. **Multiple filter effect**: Each filter (EMA200, BB, RSI) reduces the opportunity set. Combined, they can eliminate all signals.

**Best practice**: Always run diagnostics before backtesting to ensure your strategy generates signals!
