#!/usr/bin/env python3
"""Example usage of Momentum Intelligence Layer."""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.momentum.engine import MomentumEngine
from src.momentum.providers.yfinance_provider import YFinanceProvider
from src.momentum.providers.google_trends import GoogleTrendsProvider
from src.momentum.factors.volume_anomaly import VolumeAnomalyFactor
from src.momentum.factors.retail_attention import RetailAttentionFactor


async def example_basic_usage():
    """Basic example: Score a single symbol using FREE providers (YFinance + Google Trends)."""
    print("Example 1: Score a Single Symbol")
    print("=" * 50)
    print("Using FREE Providers:")
    print("  ✅ YFinance - Volume data")
    print("  ✅ Google Trends - Retail attention")
    print("  🎉 NO API KEYS NEEDED!")
    print()
    
    # Create momentum engine
    config = {
        'enabled': True,
        'factor_weights': {
            'VolumeAnomalyFactor': 0.5,
            'RetailAttentionFactor': 0.5,
        },
        'min_score': 0.5,
        'min_confidence': 0.4
    }
    
    engine = MomentumEngine(config)
    
    # Initialize providers (both FREE!)
    yf_provider = YFinanceProvider({})
    gt_provider = GoogleTrendsProvider({})
    
    await yf_provider.initialize()
    await gt_provider.initialize()
    
    # Register providers
    engine.provider_registry.register(yf_provider)
    engine.provider_registry.register(gt_provider)
    
    # Create and register factors
    volume_factor = VolumeAnomalyFactor([yf_provider], {'weight': 0.5})
    retail_factor = RetailAttentionFactor([gt_provider], {'weight': 0.5})
    
    engine.register_factor(volume_factor)
    engine.register_factor(retail_factor)
    
    # Initialize engine
    await engine.initialize()
    
    # Score a symbol
    symbol = "GME"  # Good test for retail attention!
    print(f"Scoring {symbol}...")
    score = await engine.calculate_score(symbol)
    
    if score:
        print(f"\n✅ Results for {symbol}:")
        print(f"  Composite Score: {score.composite_score:.3f}")
        print(f"  Confidence: {score.confidence:.3f}")
        print(f"  Factors Used: {score.factors_used}/{score.factors_available}")
        print(f"  Is Strong Signal: {score.is_strong_signal()}")
        print(f"\n  Factor Breakdown:")
        for name, factor_score in score.factor_scores.items():
            print(f"    {name}: {factor_score.score:.3f} (confidence: {factor_score.confidence:.3f})")
            if name == "RetailAttentionFactor" and factor_score.metadata:
                print(f"      → Google Interest: {factor_score.metadata.get('current_interest', 0):.1f}/100")
                print(f"      → Breakout: {'🔥 YES' if factor_score.metadata.get('is_breakout') else 'No'}")
    else:
        print(f"❌ Failed to score {symbol}")
    
    # Cleanup
    await yf_provider.close()
    await gt_provider.close()


async def example_universe_scoring():
    """Example: Score multiple symbols and rank them using multi-factor analysis."""
    print("\n\nExample 2: Score Universe and Generate Watchlist")
    print("=" * 50)
    print("Multi-Factor Analysis:")
    print("  📊 Volume Anomaly (YFinance)")
    print("  🔍 Retail Attention (Google Trends)")
    print("  🎉 100% FREE!")
    print()
    
    # Create momentum engine
    config = {
        'enabled': True,
        'factor_weights': {
            'VolumeAnomalyFactor': 0.5,
            'RetailAttentionFactor': 0.5,
        },
        'min_score': 0.4,
        'min_confidence': 0.3
    }
    
    engine = MomentumEngine(config)
    
    # Initialize providers (both free!)
    yf_provider = YFinanceProvider({})
    gt_provider = GoogleTrendsProvider({})
    
    await yf_provider.initialize()
    await gt_provider.initialize()
    
    engine.provider_registry.register(yf_provider)
    engine.provider_registry.register(gt_provider)
    
    # Create and register factors
    volume_factor = VolumeAnomalyFactor([yf_provider], {'weight': 0.5})
    retail_factor = RetailAttentionFactor([gt_provider], {'weight': 0.5})
    
    engine.register_factor(volume_factor)
    engine.register_factor(retail_factor)
    
    await engine.initialize()
    
    # Define universe (meme stocks + tech)
    universe = ["GME", "AMC", "TSLA", "NVDA", "AMD", "PLTR", "SOFI", "AAPL"]
    
    print(f"Scoring universe: {', '.join(universe)}")
    print("(Combining volume + retail attention for best signals)\n")
    
    # Generate dynamic watchlist
    watchlist = await engine.generate_watchlist(universe, max_symbols=3)
    
    print("\n🎯 Top Momentum Symbols:")
    for i, symbol in enumerate(watchlist, 1):
        print(f"  {i}. {symbol}")
    
    if not watchlist:
        print("  (No symbols met minimum thresholds)")
    
    # Get detailed scores for top symbols
    if watchlist:
        print("\n📊 Detailed Scores:")
        top_scores = await engine.get_top_momentum(watchlist, top_n=3)
        
        for score in top_scores:
            print(f"\n  {score.symbol}:")
            print(f"    Composite: {score.composite_score:.3f}")
            print(f"    Confidence: {score.confidence:.3f}")
            for name, factor_score in score.factor_scores.items():
                print(f"      {name}: {factor_score.score:.3f}")
    
    # Cleanup
    await yf_provider.close()
    await gt_provider.close()


async def example_health_check():
    """Example: Check momentum engine health."""
    print("\n\nExample 3: Health Check")
    print("=" * 50)
    
    config = {'enabled': True}
    engine = MomentumEngine(config)
    
    # Initialize providers (both free!)
    yf_provider = YFinanceProvider({})
    gt_provider = GoogleTrendsProvider({})
    
    await yf_provider.initialize()
    await gt_provider.initialize()
    
    engine.provider_registry.register(yf_provider)
    engine.provider_registry.register(gt_provider)
    
    # Register factors
    volume_factor = VolumeAnomalyFactor([yf_provider], {'weight': 0.5})
    retail_factor = RetailAttentionFactor([gt_provider], {'weight': 0.5})
    
    engine.register_factor(volume_factor)
    engine.register_factor(retail_factor)
    
    await engine.initialize()
    
    # Get health status
    health = await engine.health_check()
    
    print("\n🏥 Momentum Engine Health:")
    print(f"  Enabled: {health['enabled']}")
    print(f"\n  Providers: {health['providers']['available']}/{health['providers']['total']} available")
    
    for name, details in health['providers']['details'].items():
        status = "✅" if details['available'] else "❌"
        print(f"    {status} {name}")
        if details['error']:
            print(f"       Error: {details['error']}")
        if details['rate_limited']:
            print(f"       ⚠️  Rate limited")
    
    print(f"\n  Factors: {health['factors']['enabled']}/{health['factors']['total']} enabled")
    for name in health['factors']['names']:
        print(f"    ✅ {name}")
    
    # Cleanup
    await yf_provider.close()
    await gt_provider.close()


async def main():
    """Run all examples."""
    print("\n🚀 Momentum Intelligence Layer - Usage Examples")
    print("=" * 60)
    print("Multi-Factor Analysis with FREE Providers:")
    print("  ✅ YFinance - Volume & price data")
    print("  ✅ Google Trends - Retail attention")
    print("  🎉 100% FREE - No API keys needed!")
    print("  ⚡ UNLIMITED - No rate limits!")
    print("=" * 60)
    print()
    
    try:
        # Example 1: Basic scoring
        await example_basic_usage()
        
        # Example 2: Universe scoring
        await example_universe_scoring()
        
        # Example 3: Health check
        await example_health_check()
        
        print("\n\n✅ Examples completed!")
        print("\n💡 Next Steps:")
        print("  1. Install: pip install yfinance pytrends")
        print("  2. Enable momentum in momentum_config.yaml")
        print("  3. Adjust factor weights (volume vs retail)")
        print("  4. Run the bot with dynamic watchlist generation!")
        print("\n📚 Documentation:")
        print("  - docs/MOMENTUM_LAYER_REQUIREMENTS.md")
        print("  - MOMENTUM_QUICKSTART.md")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("\nMake sure dependencies are installed:")
        print("  pip install yfinance pytrends")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

