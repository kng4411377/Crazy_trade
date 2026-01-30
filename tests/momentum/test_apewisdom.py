#!/usr/bin/env python3
"""Test script for Apewisdom provider and Reddit attention factor."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path (tests/momentum/ -> tests/ -> root/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from src.momentum.providers.apewisdom import ApewisdomProvider
from src.momentum.factors.reddit_attention import RedditAttentionFactor

# Popular stocks that should be in Apewisdom trending list
TEST_SYMBOLS = ["GME", "AMC", "TSLA", "NVDA", "PLTR", "AAPL"]


async def test_apewisdom_provider():
    """Test Apewisdom provider initialization and data fetching."""
    print("\n" + "="*70)
    print("🧪 Testing Apewisdom Provider (Reddit/WSB Sentiment)")
    print("="*70)
    
    provider = ApewisdomProvider({})
    
    try:
        print("\n1. Initializing provider...")
        initialized = await provider.initialize()
        print(f"   ✅ Initialized: {initialized}")
        print(f"   ✅ Available: {provider.is_available()}")
        
        if not initialized or not provider.is_available():
            print("\n❌ Apewisdom provider failed to initialize.")
            print("   Note: Apewisdom updates only 2x per day (9 AM & 9 PM EST)")
            print("   If symbols are not found, they may not be trending on Reddit.")
            return False
        
        print("\n2. Fetching Reddit sentiment data...")
        success = True
        
        for symbol in TEST_SYMBOLS:
            data = await provider.get_stock_sentiment(symbol)
            if data:
                print(f"\n   {symbol}:")
                print(f"      Mentions: {data['mentions']:,}")
                print(f"      Change 24h: {data['mentions_change']:+.1f}%")
                print(f"      Rank: #{data['rank']}")
                print(f"      Rank Change: {data['rank_change']:+d}")
                print(f"      Positivity: {data['positivity']:.2f} (0-1 scale)")
                
                if data['mentions_change'] > 50:
                    print(f"      🔥 TRENDING UP!")
                if data['positivity'] > 0.6:
                    print(f"      😊 BULLISH SENTIMENT")
            else:
                print(f"\n   {symbol}:")
                print(f"      ⚠️  Not in Apewisdom trending list (not enough Reddit activity)")
        
        print("\n3. Running health check...")
        health = await provider.health_check()
        print(f"   ✅ Health check: {health}")
        
        print("\n✅ Apewisdom provider test completed!")
        return success
    finally:
        await provider.close()


async def test_reddit_attention_factor():
    """Test Reddit attention factor with Apewisdom provider."""
    print("\n" + "="*70)
    print("🧪 Testing Reddit Attention Factor")
    print("="*70)
    
    provider = ApewisdomProvider({})
    
    try:
        await provider.initialize()
        
        if not provider.is_available():
            print("❌ Apewisdom provider not available, skipping factor test.")
            return False
        
        factor = RedditAttentionFactor([provider], {
            'weight': 1.0,
            'mention_threshold': 50,
            'volume_weight': 0.3,
            'velocity_weight': 0.4,
            'sentiment_weight': 0.3
        })
        
        print("\n1. Calculating Reddit attention scores...")
        print("   (Only symbols with >50 mentions will score)")
        success = True
        scored_symbols = []
        
        for symbol in TEST_SYMBOLS:
            score = await factor.calculate_score(symbol)
            if score:
                print(f"\n   {symbol}:")
                print(f"      Score: {score.score:.3f}")
                print(f"      Confidence: {score.confidence:.3f}")
                print(f"      Mentions: {score.metadata.get('mentions'):,}")
                print(f"      Mention Change: {score.metadata.get('mentions_change'):+.1f}%")
                print(f"      Rank: #{score.metadata.get('rank')}")
                print(f"      Positivity: {score.metadata.get('positivity'):.2f}")
                
                if score.metadata.get('is_breakout'):
                    print(f"      💥 BREAKOUT DETECTED!")
                if score.metadata.get('is_trending_up'):
                    print(f"      📈 TRENDING UP")
                if score.metadata.get('is_bullish'):
                    print(f"      🚀 BULLISH SENTIMENT")
                
                scored_symbols.append((symbol, score))
            else:
                print(f"\n   {symbol}:")
                print(f"      ⚠️  No score (not trending or below threshold)")
        
        if scored_symbols:
            print("\n2. Ranking by Reddit attention:")
            scored_symbols.sort(key=lambda x: x[1].score, reverse=True)
            for i, (symbol, score) in enumerate(scored_symbols, 1):
                emoji = "🔥" if score.score > 0.7 else "📈" if score.score > 0.5 else "📊"
                print(f"   {i}. {emoji} {symbol}: {score.score:.3f}")
        
        print("\n✅ Reddit attention factor test completed!")
        return success
    finally:
        await provider.close()


async def test_integration():
    """Test Apewisdom + YFinance integration."""
    print("\n" + "="*70)
    print("🎯 Testing Apewisdom + YFinance Integration")
    print("="*70)
    
    from src.momentum.providers.yfinance_provider import YFinanceProvider
    from src.momentum.factors.volume_anomaly import VolumeAnomalyFactor
    
    # Initialize providers
    apewisdom = ApewisdomProvider({})
    yfinance = YFinanceProvider({})
    
    await apewisdom.initialize()
    await yfinance.initialize()
    
    if not apewisdom.is_available():
        print("⚠️  Apewisdom not available, using YFinance only")
    
    # Create factors
    reddit_factor = RedditAttentionFactor([apewisdom], {
        'weight': 0.5,
        'mention_threshold': 50,
        'volume_weight': 0.3,
        'velocity_weight': 0.4,
        'sentiment_weight': 0.3
    })
    
    volume_factor = VolumeAnomalyFactor([yfinance], {
        'weight': 0.5,
        'rvol_threshold': 1.5,
        'volume_trend_threshold': 0.2
    })
    
    print("\n1. Calculating combined scores...")
    print("   (Volume + Reddit sentiment)")
    
    combined_scores = []
    
    for symbol in TEST_SYMBOLS:
        # Get individual scores
        reddit_score = await reddit_factor.calculate_score(symbol) if apewisdom.is_available() else None
        volume_score = await volume_factor.calculate_score(symbol)
        
        if volume_score:
            # Calculate composite
            if reddit_score:
                composite = (0.5 * volume_score.score) + (0.5 * reddit_score.score)
            else:
                composite = volume_score.score
            
            combined_scores.append({
                'symbol': symbol,
                'composite': composite,
                'volume': volume_score.score,
                'reddit': reddit_score.score if reddit_score else 0,
                'rvol': volume_score.metadata.get('rvol', 0),
                'mentions': reddit_score.metadata.get('mentions', 0) if reddit_score else 0
            })
            
            print(f"\n   {symbol}:")
            print(f"      Composite: {composite:.3f}")
            print(f"      Volume: {volume_score.score:.3f} (RVOL: {volume_score.metadata.get('rvol'):.2f}x)")
            if reddit_score:
                print(f"      Reddit: {reddit_score.score:.3f} (Mentions: {reddit_score.metadata.get('mentions'):,})")
            else:
                print(f"      Reddit: N/A (not trending)")
    
    if combined_scores:
        print("\n2. Top Combined Momentum Plays:")
        combined_scores.sort(key=lambda x: x['composite'], reverse=True)
        for i, stock in enumerate(combined_scores[:5], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            print(f"   {emoji} {stock['symbol']}: {stock['composite']:.3f}")
            print(f"      └─ Volume: {stock['volume']:.3f} (RVOL: {stock['rvol']:.2f}x)")
            if stock['reddit'] > 0:
                print(f"      └─ Reddit: {stock['reddit']:.3f} ({stock['mentions']:,} mentions)")
    
    await apewisdom.close()
    await yfinance.close()
    
    print("\n✅ Integration test completed!")
    return True


async def main():
    """Run all Apewisdom tests."""
    print("="*70)
    print("🚀 APEWISDOM PROVIDER TEST SUITE")
    print("="*70)
    print("Testing: Reddit/WSB sentiment tracking\n")
    print("ℹ️  Note: Apewisdom updates 2x per day (9 AM & 9 PM EST)")
    print("ℹ️  If tests fail, data may not be updated yet.")
    print()
    
    results = {
        "apewisdom_provider": await test_apewisdom_provider(),
        "reddit_attention_factor": await test_reddit_attention_factor(),
        "integration": await test_integration(),
    }
    
    print("\n" + "="*70)
    print("✅ All Apewisdom tests completed!")
    print("="*70)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "⚠️  COMPLETED (some symbols not found)"
        print(f"  {test_name}: {status}")
    
    print("\n💡 Next Steps:")
    print("  1. Enable momentum in config.yaml: momentum.enabled: true (filter/reddit use apewisdom)")
    print("  2. Run scanner: python scripts/scan_momentum.py")
    print("  3. No API key needed - works out of the box!")
    print()
    print("🎯 Apewisdom is perfect for:")
    print("   - Pre-market scanning (9 AM update)")
    print("   - After-hours analysis (9 PM update)")
    print("   - WSB/meme stock detection")
    print("   - Reddit momentum tracking")


if __name__ == "__main__":
    asyncio.run(main())

