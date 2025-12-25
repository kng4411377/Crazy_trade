#!/usr/bin/env python3
"""Test script for momentum filter integration."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.momentum.filter import MomentumFilter


async def test_filter():
    """Test the momentum filter."""
    print("\n" + "="*70)
    print("🧪 TESTING MOMENTUM FILTER")
    print("="*70)
    
    # Test configuration
    config = {
        'enabled': True,
        'min_score': 0.4,
        'volume_weight': 0.7,
        'reddit_weight': 0.3,
        'cache_duration': 3600,
        'require_volume': True,
        'require_reddit': False,
        'fail_open': True
    }
    
    # Test symbols
    test_symbols = [
        "TSLA", "AAPL", "NVDA", "AMD", "MSFT",
        "GOOGL", "META", "AMZN", "GME", "AMC"
    ]
    
    print("\n1. Initializing filter...")
    print(f"   Config: {config}")
    
    filter = MomentumFilter(config)
    success = await filter.initialize()
    
    if not success:
        print("   ❌ Filter initialization failed!")
        return False
    
    print("   ✅ Filter initialized successfully!")
    
    print(f"\n2. Filtering {len(test_symbols)} symbols...")
    print(f"   Input: {test_symbols}")
    
    filtered = await filter.filter_symbols(test_symbols)
    
    print(f"\n3. Results:")
    print(f"   Input symbols:    {len(test_symbols)}")
    print(f"   Filtered symbols: {len(filtered)}")
    print(f"   Passed:           {filtered}")
    print(f"   Rejected:         {[s for s in test_symbols if s not in filtered]}")
    
    print(f"\n4. Filter statistics:")
    stats = await filter.get_filter_stats()
    print(f"   YFinance available: {stats['yfinance_available']}")
    print(f"   Apewisdom available: {stats['apewisdom_available']}")
    print(f"   Cache size: {stats['cache_size']}")
    
    await filter.close()
    
    print("\n✅ Test completed!")
    return True


async def main():
    """Run the test."""
    try:
        success = await test_filter()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

