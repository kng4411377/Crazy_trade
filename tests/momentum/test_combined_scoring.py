#!/usr/bin/env python3
"""Comprehensive test for both YFinance and Google Trends providers with combined scoring."""

import asyncio
import sys
from pathlib import Path

# Add project root to path (tests/momentum/ -> tests/ -> root/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.momentum.providers.yfinance_provider import YFinanceProvider
from src.momentum.providers.google_trends import GoogleTrendsProvider
from src.momentum.factors.volume_anomaly import VolumeAnomalyFactor
from src.momentum.factors.retail_attention import RetailAttentionFactor


async def test_yfinance():
    """Test YFinance provider."""
    print("\n" + "="*70)
    print("🧪 Testing YFinance Provider (Volume Data)")
    print("="*70)
    
    provider = YFinanceProvider({})
    
    print("\n1. Initializing provider...")
    success = await provider.initialize()
    print(f"   {'✅' if success else '❌'} Initialized: {success}")
    print(f"   {'✅' if provider.is_available() else '❌'} Available: {provider.is_available()}")
    
    if not success:
        print("\n❌ YFinance provider failed to initialize")
        return False
    
    # Test with symbols
    test_symbols = ["TSLA", "NVDA", "GME", "AAPL"]
    
    print("\n2. Fetching volume metrics...")
    for symbol in test_symbols:
        print(f"\n   {symbol}:")
        try:
            metrics = await provider.calculate_volume_metrics(symbol)
            
            if metrics:
                print(f"      Current Volume: {metrics.get('current_volume', 0):,.0f}")
                print(f"      Average Volume: {metrics.get('avg_volume_20', 0):,.0f}")
                print(f"      RVOL: {metrics.get('rvol', 0):.2f}x")
                print(f"      Volume Trend: {metrics.get('volume_trend', 0):+.2%}")
            else:
                print(f"      ⚠️  No data available")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    await provider.close()
    print("\n✅ YFinance test completed!")
    return True


async def test_google_trends():
    """Test Google Trends provider."""
    print("\n" + "="*70)
    print("🧪 Testing Google Trends Provider (Retail Attention)")
    print("="*70)
    
    provider = GoogleTrendsProvider({})
    
    print("\n1. Initializing provider...")
    success = await provider.initialize()
    print(f"   {'✅' if success else '❌'} Initialized: {success}")
    print(f"   {'✅' if provider.is_available() else '❌'} Available: {provider.is_available()}")
    
    if not success:
        print("\n❌ Google Trends provider failed to initialize")
        return False
    
    # Test with symbols
    test_symbols = ["TSLA", "NVDA", "GME", "AAPL"]
    
    print("\n2. Fetching search interest...")
    for symbol in test_symbols:
        print(f"\n   {symbol}:")
        try:
            data = await provider.get_search_interest(symbol, timeframe='now 7-d')
            
            if data:
                print(f"      Current Interest: {data['current_interest']:.1f}/100")
                print(f"      Average Interest: {data['average_interest']:.1f}/100")
                print(f"      Velocity: {data['velocity']:+.1f}")
                print(f"      Breakout: {'🔥 YES' if data['is_breakout'] else 'No'}")
            else:
                print(f"      ⚠️  No data available")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    await provider.close()
    print("\n✅ Google Trends test completed!")
    return True


async def test_volume_anomaly_factor():
    """Test Volume Anomaly factor."""
    print("\n" + "="*70)
    print("🧪 Testing Volume Anomaly Factor")
    print("="*70)
    
    # Initialize provider
    provider = YFinanceProvider({})
    await provider.initialize()
    
    if not provider.is_available():
        print("\n❌ YFinance provider not available")
        return False
    
    # Create factor
    factor = VolumeAnomalyFactor([provider], {'weight': 0.5})
    
    # Test symbols
    test_symbols = ["TSLA", "NVDA", "GME", "AMC", "AAPL"]
    
    print("\n1. Calculating volume anomaly scores...")
    scores = []
    
    for symbol in test_symbols:
        print(f"\n   {symbol}:")
        try:
            score = await factor.calculate_score(symbol)
            
            if score:
                scores.append((symbol, score))
                print(f"      Score: {score.score:.3f}")
                print(f"      Confidence: {score.confidence:.3f}")
                if 'rvol' in score.metadata:
                    print(f"      RVOL: {score.metadata['rvol']:.2f}x")
            else:
                print(f"      ⚠️  No score available")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    # Rank by score
    if scores:
        print("\n2. Ranking by volume anomaly:")
        scores.sort(key=lambda x: x[1].score, reverse=True)
        
        for i, (symbol, score) in enumerate(scores, 1):
            emoji = "🔥" if score.score > 0.7 else "📈" if score.score > 0.5 else "📊"
            print(f"   {i}. {emoji} {symbol}: {score.score:.3f}")
    
    await provider.close()
    print("\n✅ Volume Anomaly factor test completed!")
    return True


async def test_retail_attention_factor():
    """Test Retail Attention factor."""
    print("\n" + "="*70)
    print("🧪 Testing Retail Attention Factor")
    print("="*70)
    
    # Initialize provider
    provider = GoogleTrendsProvider({})
    await provider.initialize()
    
    if not provider.is_available():
        print("\n❌ Google Trends provider not available")
        return False
    
    # Create factor
    factor = RetailAttentionFactor([provider], {
        'weight': 0.5,
        'timeframe': 'now 7-d',
        'breakout_weight': 0.4,
        'velocity_weight': 0.4,
        'interest_weight': 0.2
    })
    
    # Test symbols
    test_symbols = ["TSLA", "NVDA", "GME", "AMC", "AAPL"]
    
    print("\n1. Calculating retail attention scores...")
    scores = []
    
    for symbol in test_symbols:
        print(f"\n   {symbol}:")
        try:
            score = await factor.calculate_score(symbol)
            
            if score:
                scores.append((symbol, score))
                print(f"      Score: {score.score:.3f}")
                print(f"      Confidence: {score.confidence:.3f}")
                if score.metadata:
                    print(f"      Interest: {score.metadata.get('current_interest', 0):.1f}/100")
                    if score.metadata.get('is_breakout'):
                        print(f"      🔥 BREAKOUT DETECTED!")
            else:
                print(f"      ⚠️  No score available")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    # Rank by score
    if scores:
        print("\n2. Ranking by retail attention:")
        scores.sort(key=lambda x: x[1].score, reverse=True)
        
        for i, (symbol, score) in enumerate(scores, 1):
            emoji = "🔥" if score.score > 0.7 else "📈" if score.score > 0.5 else "📊"
            print(f"   {i}. {emoji} {symbol}: {score.score:.3f}")
    
    await provider.close()
    print("\n✅ Retail Attention factor test completed!")
    return True


async def test_combined_scoring():
    """Test combined multi-factor scoring."""
    print("\n" + "="*70)
    print("🎯 Testing Combined Multi-Factor Scoring")
    print("="*70)
    print("Combining: Volume Anomaly (50%) + Retail Attention (50%)")
    print()
    
    # Initialize providers
    yf_provider = YFinanceProvider({})
    gt_provider = GoogleTrendsProvider({})
    
    await yf_provider.initialize()
    await gt_provider.initialize()
    
    if not yf_provider.is_available():
        print("❌ YFinance provider not available")
        return False
    
    if not gt_provider.is_available():
        print("❌ Google Trends provider not available")
        return False
    
    # Create factors
    volume_factor = VolumeAnomalyFactor([yf_provider], {'weight': 0.5})
    retail_factor = RetailAttentionFactor([gt_provider], {'weight': 0.5})
    
    # Test symbols
    test_symbols = ["TSLA", "NVDA", "GME", "AMC", "AAPL", "PLTR"]
    
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
            
            print(f"  Volume Score:  {volume_score.score:.3f} 📊")
            print(f"  Retail Score:  {retail_score.score:.3f} 🔍")
            print(f"  Composite:     {composite:.3f} {get_emoji(composite)}")
            
            # Show signals
            signals = []
            if volume_score.score > 0.7:
                signals.append("High Volume")
            if retail_score.score > 0.7:
                signals.append("High Retail Interest")
            if retail_score.metadata and retail_score.metadata.get('is_breakout'):
                signals.append("🔥 Breakout")
            if signals:
                print(f"  Signals: {', '.join(signals)}")
        else:
            missing = []
            if not volume_score:
                missing.append("volume")
            if not retail_score:
                missing.append("retail")
            print(f"  ⚠️  Incomplete data (missing: {', '.join(missing)})")
        
        print()
    
    # Rank by composite score
    if composite_scores:
        print("\n🏆 Final Rankings (Volume + Retail Attention):")
        print("="*70)
        composite_scores.sort(key=lambda x: x[1], reverse=True)
        
        for i, (symbol, composite, vol, retail) in enumerate(composite_scores, 1):
            emoji = get_emoji(composite)
            print(f"\n  {i}. {emoji} {symbol}: {composite:.3f}")
            print(f"       Volume: {vol.score:.3f}, Retail: {retail.score:.3f}")
            
            # Show why it's ranked here
            if composite > 0.7:
                print(f"       💡 Strong signal - both factors agree!")
            elif vol.score > 0.7 and retail.score < 0.5:
                print(f"       💡 Volume confirmed, retail building")
            elif retail.score > 0.7 and vol.score < 0.5:
                print(f"       💡 Retail interest high, volume may follow")
    
    await yf_provider.close()
    await gt_provider.close()
    
    print("\n\n✅ Combined scoring test completed!")
    return True


def get_emoji(score):
    """Get emoji based on score."""
    if score > 0.8:
        return "🔥🔥🔥"
    elif score > 0.7:
        return "🔥🔥"
    elif score > 0.6:
        return "🔥"
    elif score > 0.5:
        return "📈"
    else:
        return "📊"


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🚀 COMPREHENSIVE MOMENTUM LAYER TEST SUITE")
    print("="*70)
    print("Testing: YFinance + Google Trends + Combined Scoring")
    print()
    
    all_passed = True
    
    try:
        # Test 1: YFinance Provider
        if not await test_yfinance():
            all_passed = False
        
        # Test 2: Google Trends Provider
        if not await test_google_trends():
            all_passed = False
        
        # Test 3: Volume Anomaly Factor
        if not await test_volume_anomaly_factor():
            all_passed = False
        
        # Test 4: Retail Attention Factor
        if not await test_retail_attention_factor():
            all_passed = False
        
        # Test 5: Combined Scoring
        if not await test_combined_scoring():
            all_passed = False
        
        print("\n\n" + "="*70)
        if all_passed:
            print("✅ ALL TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED")
        print("="*70)
        
        print("\n💡 Next Steps:")
        print("  1. Enable momentum layer in momentum_config.yaml")
        print("  2. Adjust factor weights (volume vs retail)")
        print("  3. Run: python examples/momentum_example.py")
        print("  4. Integrate with main bot")
        print()
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

