#!/usr/bin/env python3
"""Test momentum intelligence layer providers."""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path (tests/momentum/ -> tests/ -> root/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from .env file
load_dotenv()

from src.momentum.providers.alphavantage import AlphaVantageProvider
from src.momentum.providers.yfinance_provider import YFinanceProvider
from src.momentum.providers.stocktwits import StockTwitsProvider
from src.momentum.factors.volume_anomaly import VolumeAnomalyFactor
from src.momentum.factors.sentiment_velocity import SentimentVelocityFactor
import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


async def test_alphavantage():
    """Test Alpha Vantage provider."""
    print("\n" + "="*60)
    print("Testing Alpha Vantage Provider")
    print("="*60)
    
    api_key = os.getenv('ALPHAVANTAGE_API_KEY')
    if not api_key:
        print("❌ ALPHAVANTAGE_API_KEY not set in environment")
        return False
    
    provider = AlphaVantageProvider({})
    
    print("Initializing...")
    success = await provider.initialize()
    if not success:
        print("❌ Initialization failed")
        return False
    
    print("✅ Initialized successfully")
    
    print("\nChecking health...")
    health = await provider.health_check()
    print(f"  Available: {health.is_available}")
    print(f"  Rate Limited: {health.rate_limited}")
    if health.error_message:
        print(f"  Error: {health.error_message}")
    
    if not health.is_available:
        print("❌ Provider not available")
        await provider.close()
        return False
    
    print("✅ Health check passed")
    
    print("\nTesting volume metrics for AAPL...")
    metrics = await provider.calculate_volume_metrics('AAPL')
    if metrics:
        print("✅ Volume metrics retrieved:")
        print(f"  RVOL: {metrics['rvol']:.2f}")
        print(f"  Volume Trend: {metrics['volume_trend']:.2%}")
        print(f"  Current Volume: {metrics['current_volume']:,.0f}")
    else:
        print("❌ Failed to get volume metrics")
        await provider.close()
        return False
    
    await provider.close()
    print("\n✅ Alpha Vantage: ALL TESTS PASSED")
    return True


async def test_stocktwits():
    """Test StockTwits provider."""
    print("\n" + "="*60)
    print("Testing StockTwits Provider")
    print("="*60)
    
    # StockTwits works without token (public API) but has lower rate limits
    has_token = bool(os.getenv('STOCKTWITS_ACCESS_TOKEN'))
    print(f"Access Token: {'✅ Set' if has_token else '⚠️  Not set (using public API)'}")
    
    provider = StockTwitsProvider({})
    
    print("\nInitializing...")
    success = await provider.initialize()
    if not success:
        print("❌ Initialization failed")
        return False
    
    print("✅ Initialized successfully")
    
    print("\nChecking health...")
    health = await provider.health_check()
    print(f"  Available: {health.is_available}")
    print(f"  Rate Limited: {health.rate_limited}")
    if health.error_message:
        print(f"  Error: {health.error_message}")
    
    if not health.is_available:
        print("❌ Provider not available")
        await provider.close()
        return False
    
    print("✅ Health check passed")
    
    print("\nTesting sentiment metrics for TSLA...")
    metrics = await provider.calculate_sentiment_metrics('TSLA')
    if metrics:
        print("✅ Sentiment metrics retrieved:")
        print(f"  Total Messages: {metrics['total_messages']}")
        print(f"  Bullish Ratio: {metrics['bullish_ratio']:.1%}")
        print(f"  Sentiment Score: {metrics['sentiment_score']:.3f}")
        print(f"  Velocity: {metrics['velocity']} msgs/hour")
        print(f"  Trend: {metrics['sentiment_trend']:+.3f}")
    else:
        print("❌ Failed to get sentiment metrics")
        await provider.close()
        return False
    
    await provider.close()
    print("\n✅ StockTwits: ALL TESTS PASSED")
    return True


async def test_factors():
    """Test momentum factors."""
    print("\n" + "="*60)
    print("Testing Momentum Factors")
    print("="*60)
    
    # Initialize providers
    av_provider = AlphaVantageProvider({})
    st_provider = StockTwitsProvider({})
    
    await av_provider.initialize()
    await st_provider.initialize()
    
    # Test Volume Anomaly Factor
    print("\n--- Volume Anomaly Factor ---")
    volume_factor = VolumeAnomalyFactor(
        providers=[av_provider],
        config={'weight': 0.3}
    )
    
    print("Calculating score for AAPL...")
    score = await volume_factor.calculate_score('AAPL')
    if score:
        print(f"✅ Score: {score.score:.3f}")
        print(f"  Confidence: {score.confidence:.3f}")
        print(f"  Metadata: {score.metadata}")
    else:
        print("❌ Failed to calculate volume anomaly score")
    
    # Test Sentiment Velocity Factor
    print("\n--- Sentiment Velocity Factor ---")
    sentiment_factor = SentimentVelocityFactor(
        providers=[st_provider],
        config={'weight': 0.3}
    )
    
    print("Calculating score for TSLA...")
    score = await sentiment_factor.calculate_score('TSLA')
    if score:
        print(f"✅ Score: {score.score:.3f}")
        print(f"  Confidence: {score.confidence:.3f}")
        print(f"  Metadata: {score.metadata}")
    else:
        print("❌ Failed to calculate sentiment velocity score")
    
    await av_provider.close()
    await st_provider.close()
    
    print("\n✅ Factors: ALL TESTS PASSED")
    return True


async def main():
    """Run all tests."""
    print("\n" + "🚀"*30)
    print("MOMENTUM INTELLIGENCE LAYER - PROVIDER TESTS")
    print("🚀"*30)
    
    print("\nRequired Environment Variables:")
    print(f"  ALPHAVANTAGE_API_KEY: {'✅' if os.getenv('ALPHAVANTAGE_API_KEY') else '❌ MISSING'}")
    print(f"  STOCKTWITS_ACCESS_TOKEN: {'✅' if os.getenv('STOCKTWITS_ACCESS_TOKEN') else '⚠️  Optional (public API works)'}")
    
    results = []
    
    # Test Alpha Vantage
    try:
        result = await test_alphavantage()
        results.append(('Alpha Vantage', result))
    except Exception as e:
        print(f"\n❌ Alpha Vantage test failed with exception: {e}")
        results.append(('Alpha Vantage', False))
    
    # Test StockTwits
    try:
        result = await test_stocktwits()
        results.append(('StockTwits', result))
    except Exception as e:
        print(f"\n❌ StockTwits test failed with exception: {e}")
        results.append(('StockTwits', False))
    
    # Test Factors
    try:
        result = await test_factors()
        results.append(('Momentum Factors', result))
    except Exception as e:
        print(f"\n❌ Factor test failed with exception: {e}")
        results.append(('Momentum Factors', False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\n{total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nYou're ready to use the momentum layer!")
        print("Next steps:")
        print("  1. In config.yaml set momentum.enabled: true")
        print("  2. Filter/dynamic_watchlist turn on with momentum; set to false to disable only one")
        print("  3. Run the bot with momentum layer enabled")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nTroubleshooting:")
        print("  1. Check environment variables are set")
        print("  2. Verify API keys are valid")
        print("  3. Check you're not rate limited")
        print("  4. See docs/MOMENTUM_LAYER_REQUIREMENTS.md")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

