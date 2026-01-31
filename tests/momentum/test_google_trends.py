#!/usr/bin/env python3
"""Test script for Google Trends provider and Retail Attention factor."""

import asyncio
import sys
from pathlib import Path

# Add project root to path (tests/momentum/ -> tests/ -> root/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.momentum.providers.google_trends import GoogleTrendsProvider
from src.momentum.factors.retail_attention import RetailAttentionFactor


async def test_google_trends_provider():
    """Test Google Trends provider."""
    print("\n" + "="*60)
    print("Testing Google Trends Provider")
    print("="*60)
    
    provider = GoogleTrendsProvider({})
    
    # Initialize
    print("\n1. Initializing provider...")
    success = await provider.initialize()
    print(f"   ✅ Initialized: {success}")
    print(f"   Available: {provider.is_available()}")
    
    if not success:
        print("\n❌ Failed to initialize Google Trends provider")
        print("   Make sure pytrends is installed: pip install pytrends")
        return
    
    # Test with popular symbols
    test_symbols = ["TSLA", "NVDA", "GME", "AAPL"]
    
    print("\n2. Fetching search interest data...")
    for symbol in test_symbols:
        print(f"\n   {symbol}:")
        data = await provider.get_search_interest(symbol, timeframe='now 7-d')
        
        if data:
            print(f"      Current Interest: {data['current_interest']:.1f}/100")
            print(f"      Average Interest: {data['average_interest']:.1f}/100")
            print(f"      Velocity: {data['velocity']:+.1f}")
            print(f"      Breakout: {'🔥 YES' if data['is_breakout'] else 'No'}")
        else:
            print(f"      ⚠️  No data available")
    
    # Health check
    print("\n3. Running health check...")
    healthy = await provider.health_check()
    print(f"   {'✅' if healthy else '❌'} Health check: {healthy}")
    
    await provider.close()
    print("\n✅ Provider test completed!\n")


async def test_retail_attention_factor():
    """Test Retail Attention factor."""
    print("\n" + "="*60)
    print("Testing Retail Attention Factor")
    print("="*60)
    
    # Initialize provider
    provider = GoogleTrendsProvider({})
    await provider.initialize()
    
    if not provider.is_available():
        print("\n❌ Google Trends provider not available")
        return
    
    # Create factor
    factor_config = {
        'weight': 0.3,
        'timeframe': 'now 7-d',
        'breakout_weight': 0.4,
        'velocity_weight': 0.4,
        'interest_weight': 0.2,
    }
    
    factor = RetailAttentionFactor([provider], factor_config)
    
    # Test symbols
    test_symbols = ["TSLA", "NVDA", "GME", "AAPL", "SPY"]
    
    print("\n1. Calculating retail attention scores...")
    scores = []
    
    for symbol in test_symbols:
        print(f"\n   {symbol}:")
        score = await factor.calculate_score(symbol)
        
        if score:
            scores.append((symbol, score))
            print(f"      Score: {score.score:.3f}")
            print(f"      Confidence: {score.confidence:.3f}")
            print(f"      Interest: {score.metadata['current_interest']:.1f}/100")
            print(f"      Velocity: {score.metadata['velocity']:+.1f}")
            print(f"      Breakout: {'🔥' if score.metadata['is_breakout'] else '❌'}")
        else:
            print(f"      ⚠️  No score available")
    
    # Rank by score
    if scores:
        print("\n2. Ranking by retail attention:")
        scores.sort(key=lambda x: x[1].score, reverse=True)
        
        for i, (symbol, score) in enumerate(scores, 1):
            emoji = "🔥" if score.score > 0.7 else "📈" if score.score > 0.5 else "📊"
            print(f"   {i}. {emoji} {symbol}: {score.score:.3f}")
    
    await provider.close()
    print("\n✅ Factor test completed!\n")


async def test_combined():
    """Test combined scoring with multiple factors."""
    print("\n" + "="*60)
    print("Testing Combined Multi-Factor Scoring")
    print("="*60)
    print("Combining: Volume Anomaly + Retail Attention")
    print()
    
    # Import YFinance provider
    from src.momentum.providers.yfinance_provider import YFinanceProvider
    from src.momentum.factors.volume_anomaly import VolumeAnomalyFactor
    
    # Initialize providers
    yf_provider = YFinanceProvider({})
    gt_provider = GoogleTrendsProvider({})
    
    await yf_provider.initialize()
    await gt_provider.initialize()
    
    if not yf_provider.is_available():
        print("❌ YFinance provider not available")
        return
    
    if not gt_provider.is_available():
        print("❌ Google Trends provider not available")
        return
    
    # Create factors
    volume_factor = VolumeAnomalyFactor([yf_provider], {'weight': 0.5})
    retail_factor = RetailAttentionFactor([gt_provider], {'weight': 0.5})
    
    # Test symbols
    test_symbols = ["TSLA", "NVDA", "GME", "AMC", "AAPL"]
    
    print("Calculating composite scores...\n")
    
    composite_scores = []
    
    for symbol in test_symbols:
        print(f"{symbol}:")
        
        # Get both factor scores
        volume_score = await volume_factor.calculate_score(symbol)
        retail_score = await retail_factor.calculate_score(symbol)
        
        if volume_score and retail_score:
            # Calculate weighted composite
            composite = (
                0.5 * volume_score.score +
                0.5 * retail_score.score
            )
            
            composite_scores.append((symbol, composite, volume_score, retail_score))
            
            print(f"  Volume Score:  {volume_score.score:.3f}")
            print(f"  Retail Score:  {retail_score.score:.3f}")
            print(f"  Composite:     {composite:.3f} {'🔥' if composite > 0.7 else ''}")
        else:
            print(f"  ⚠️  Incomplete data")
        
        print()
    
    # Rank by composite score
    if composite_scores:
        print("\n🏆 Final Rankings (Volume + Retail Attention):")
        composite_scores.sort(key=lambda x: x[1], reverse=True)
        
        for i, (symbol, composite, vol, retail) in enumerate(composite_scores, 1):
            emoji = "🔥🔥🔥" if composite > 0.8 else "🔥🔥" if composite > 0.7 else "🔥" if composite > 0.6 else "📈"
            print(f"  {i}. {emoji} {symbol}: {composite:.3f}")
            print(f"       Volume: {vol.score:.3f}, Retail: {retail.score:.3f}")
    
    await yf_provider.close()
    await gt_provider.close()
    
    print("\n✅ Combined test completed!\n")


async def main():
    """Run all tests."""
    print("\n🚀 Google Trends & Retail Attention - Test Suite")
    print("="*60)
    print("Testing FREE momentum factors (no API keys needed!)")
    print()
    
    try:
        # Test 1: Provider
        await test_google_trends_provider()
        
        # Test 2: Factor
        await test_retail_attention_factor()
        
        # Test 3: Combined
        await test_combined()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        print("\n💡 Next Steps:")
        print("  1. Enable retail_attention in config.yaml under momentum.factors")
        print("  2. Adjust factor weights (volume vs retail)")
        print("  3. Run examples/momentum_example.py")
        print()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

