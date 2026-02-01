#!/usr/bin/env python3
"""
Test script to verify notebook data loading logic works correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from src.data_storage import DataStorage

# Configuration (matching notebook)
INSTRUMENT = "EUR_USD"
GRANULARITY = "M15"
FROM_DATE = "20240101"
TO_DATE = "20241231"

DATA_DIR = Path("data/historical")
DATA_PATH = (
    DATA_DIR / INSTRUMENT / f"{INSTRUMENT}_{GRANULARITY}_{FROM_DATE}_{TO_DATE}.csv"
)

print("=" * 60)
print("TESTING NOTEBOOK DATA LOADING LOGIC")
print("=" * 60)

# Test 1: Check if file exists
print(f"\n1. Checking if data file exists...")
print(f"   Path: {DATA_PATH}")
print(f"   Exists: {DATA_PATH.exists()}")

if not DATA_PATH.exists():
    print("   ✗ FAIL: Expected data file does not exist!")
    sys.exit(1)

print("   ✓ PASS: Data file found")

# Test 2: Load data using comment='#' (new approach)
print(f"\n2. Testing data loading with comment='#' parameter...")
try:
    df = pd.read_csv(DATA_PATH, comment="#", parse_dates=["time"], index_col="time")
    print(f"   ✓ PASS: Loaded {len(df):,} rows")
    print(f"   Columns: {list(df.columns)}")
except Exception as e:
    print(f"   ✗ FAIL: {e}")
    sys.exit(1)

# Test 3: Verify column capitalization works
print(f"\n3. Testing column capitalization...")
df.columns = [col.capitalize() for col in df.columns]
print(f"   Capitalized columns: {list(df.columns)}")

required_cols = ["Open", "High", "Low", "Close", "Volume"]
missing = [col for col in required_cols if col not in df.columns]

if missing:
    print(f"   ✗ FAIL: Missing columns: {missing}")
    sys.exit(1)

print(f"   ✓ PASS: All required columns present")

# Test 4: Verify data format
print(f"\n4. Verifying data format...")
df_final = df[[col for col in required_cols if col in df.columns]]

print(f"   Shape: {df_final.shape}")
print(f"   Index type: {type(df_final.index)}")
print(f"   Date range: {df_final.index.min()} to {df_final.index.max()}")
print(f"   Duration: {(df_final.index.max() - df_final.index.min()).days} days")

# Show sample
print(f"\n   First 5 rows:")
print(df_final.head())

print(f"\n   Price statistics:")
print(df_final.describe())

# Final summary
print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED")
print("=" * 60)
print("\nThe notebook data loading logic should work correctly!")
print(f"Expected candles: ~{len(df_final):,} (M15 for full year 2024)")
