#!/usr/bin/env python3
"""Debug script to test Google Trends API directly."""

import sys
from pathlib import Path

# Add project root to path (tests/momentum/ -> tests/ -> root/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_pytrends_basic():
    """Test pytrends library directly."""
    print("\n" + "="*60)
    print("Testing pytrends Library Directly")
    print("="*60)
    
    try:
        from pytrends.request import TrendReq
        print("✅ pytrends imported successfully")
        
        # Initialize
        print("\n1. Initializing TrendReq...")
        pytrends = TrendReq(
            hl='en-US',
            tz=360  # US timezone (simplified for compatibility)
        )
        print("✅ TrendReq initialized")
        
        # Test with a popular search term
        print("\n2. Testing with 'Tesla stock'...")
        try:
            pytrends.build_payload(['Tesla stock'], timeframe='now 7-d')
            print("✅ Payload built")
            
            data = pytrends.interest_over_time()
            print(f"✅ Data fetched: {type(data)}")
            
            if data is not None and not data.empty:
                print(f"\n📊 Data shape: {data.shape}")
                print(f"📊 Columns: {data.columns.tolist()}")
                print(f"\n📊 Last 5 rows:")
                print(data.tail())
                
                if 'Tesla stock' in data.columns:
                    values = data['Tesla stock'].values
                    print(f"\n✅ Interest values: min={values.min()}, max={values.max()}, mean={values.mean():.1f}")
                else:
                    print(f"⚠️  'Tesla stock' column not found")
            else:
                print("⚠️  Data is empty or None")
                print(f"   Data: {data}")
                
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            import traceback
            traceback.print_exc()
            
    except ImportError as e:
        print(f"❌ Failed to import pytrends: {e}")
        print("\nInstall with: pip install pytrends")
        return False
    
    return True


def test_multiple_symbols():
    """Test with multiple stock symbols."""
    print("\n\n" + "="*60)
    print("Testing Multiple Symbols")
    print("="*60)
    
    from pytrends.request import TrendReq
    pytrends = TrendReq(hl='en-US', tz=360)
    
    symbols = ["TSLA", "NVDA", "AAPL", "GME"]
    
    for symbol in symbols:
        try:
            print(f"\n{symbol}:")
            pytrends.build_payload([f"{symbol} stock"], timeframe='now 7-d')
            data = pytrends.interest_over_time()
            
            if data is not None and not data.empty:
                col = f"{symbol} stock"
                if col in data.columns:
                    values = data[col].values
                    print(f"  ✅ Interest: {values[-1]}/100 (avg: {values.mean():.1f})")
                else:
                    print(f"  ⚠️  No '{col}' column in data")
                    print(f"     Columns: {data.columns.tolist()}")
            else:
                print(f"  ⚠️  No data returned")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")


def test_timeframes():
    """Test different timeframes."""
    print("\n\n" + "="*60)
    print("Testing Different Timeframes")
    print("="*60)
    
    from pytrends.request import TrendReq
    pytrends = TrendReq(hl='en-US', tz=360)
    
    timeframes = [
        'now 1-d',
        'now 7-d',
        'today 1-m',
        'today 3-m'
    ]
    
    symbol = "TSLA"
    
    for tf in timeframes:
        try:
            print(f"\n{tf}:")
            pytrends.build_payload([f"{symbol} stock"], timeframe=tf)
            data = pytrends.interest_over_time()
            
            if data is not None and not data.empty:
                print(f"  ✅ Rows: {len(data)}, Latest: {data[f'{symbol} stock'].iloc[-1]}/100")
            else:
                print(f"  ⚠️  No data")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    print("\n🔍 Google Trends Debug Tool\n")
    
    # Test 1: Basic functionality
    if not test_pytrends_basic():
        sys.exit(1)
    
    # Test 2: Multiple symbols
    try:
        test_multiple_symbols()
    except Exception as e:
        print(f"\n❌ Multiple symbols test failed: {e}")
    
    # Test 3: Timeframes
    try:
        test_timeframes()
    except Exception as e:
        print(f"\n❌ Timeframes test failed: {e}")
    
    print("\n\n" + "="*60)
    print("✅ Debug tests completed!")
    print("="*60)
    print()

