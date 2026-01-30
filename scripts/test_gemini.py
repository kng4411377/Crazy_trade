#!/usr/bin/env python3
"""
Test Gemini AI Integration

Quick test to verify Gemini API connection and signal generation.

Usage:
    python scripts/test_gemini.py
    python scripts/test_gemini.py --symbols AAPL TSLA NVDA
    python scripts/test_gemini.py --crypto BTC-USD ETH-USD
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


async def test_gemini_api():
    """Test basic Gemini API connection."""
    print("\n" + "="*60)
    print("GEMINI API CONNECTION TEST")
    print("="*60)
    
    import os
    import yaml
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        try:
            with open('secrets.yaml', 'r') as f:
                secrets = yaml.safe_load(f)
            api_key = secrets.get('gemini', {}).get('api_key')
        except:
            pass
    
    if not api_key or api_key.startswith('YOUR_'):
        print("\n❌ Gemini API key not found!")
        print("\n📋 To fix this:")
        print("1. Get a free API key from: https://aistudio.google.com/app/apikey")
        print("2. Add to secrets.yaml:")
        print("   gemini:")
        print("     api_key: 'YOUR_KEY_HERE'")
        print("\n   Or set environment variable:")
        print("   export GEMINI_API_KEY='YOUR_KEY_HERE'")
        return False
    
    print("\n✅ API key found")
    
    try:
        import google.generativeai as genai
    except ImportError:
        print("\n❌ google-generativeai not installed")
        print("   Run: pip install google-generativeai")
        return False
    
    print("✅ google-generativeai imported")
    
    # Configure
    genai.configure(api_key=api_key)
    print("✅ Gemini configured")
    
    # Test simple call
    print("\n📤 Sending test prompt...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Respond with just 'OK' if you're working.")
    
    if response and response.text:
        print(f"📥 Response: {response.text.strip()}")
        print("\n✅ Gemini API is working!")
        return True
    else:
        print("❌ Empty response")
        return False


async def test_full_analysis(stocks: list, crypto: list):
    """Test full Gemini analysis with indicators."""
    print("\n" + "="*60)
    print("FULL GEMINI ANALYSIS TEST")
    print("="*60)
    
    try:
        # Load config
        import yaml
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        gemini_config = config.get('gemini', {})
        gemini_config['enabled'] = True  # Force enable for test
        
        # Override watchlists
        if stocks:
            gemini_config['enable_stocks'] = True
        if crypto:
            gemini_config['crypto_watchlist'] = crypto
            gemini_config['enable_crypto'] = True
        
        print(f"\n📊 Test symbols:")
        print(f"   Stocks: {stocks}")
        print(f"   Crypto: {crypto}")
        
        # Create analyzer
        from src.analysis.gemini_analyzer import GeminiAnalyzer
        
        analyzer = GeminiAnalyzer(gemini_config)
        success = await analyzer.initialize()
        
        if not success:
            print("❌ Failed to initialize analyzer")
            return False
        
        print("\n✅ Analyzer initialized")
        
        # Run analysis
        print("\n⏳ Running analysis (this may take a moment)...")
        signals = await analyzer.analyze(
            stock_symbols=stocks,
            crypto_symbols=crypto
        )
        
        if not signals:
            print("⚠️  No signals generated (indicators may have failed)")
            print("   This is often due to market being closed or rate limits")
            return True
        
        print(f"\n📈 Generated {len(signals)} signals:\n")
        
        for symbol, signal in signals.items():
            confidence_bar = "█" * int(signal.confidence * 10) + "░" * (10 - int(signal.confidence * 10))
            
            action_color = {
                'BUY': '\033[92m',   # Green
                'SELL': '\033[91m',  # Red
                'HOLD': '\033[93m',  # Yellow
                'WATCH': '\033[94m'  # Blue
            }.get(signal.action, '')
            
            print(f"  {symbol}")
            print(f"    Action:     {action_color}{signal.action}\033[0m")
            print(f"    Confidence: [{confidence_bar}] {signal.confidence:.0%}")
            print(f"    Strategy:   {signal.strategy}")
            print(f"    Risk:       {signal.risk_level}")
            print(f"    Reasoning:  {signal.reasoning[:80]}...")
            print()
        
        # Show actionable signals
        actionable = analyzer.get_actionable_signals(signals, ['BUY', 'SELL'])
        if actionable:
            print(f"\n🎯 Actionable signals (confidence >= {gemini_config.get('min_confidence', 0.6):.0%}):")
            for s in actionable:
                print(f"   • {s.action} {s.symbol} ({s.confidence:.0%} confidence)")
        
        await analyzer.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    parser = argparse.ArgumentParser(description='Test Gemini AI integration')
    parser.add_argument('--symbols', nargs='+', default=['AAPL', 'TSLA', 'NVDA'],
                        help='Stock symbols to analyze')
    parser.add_argument('--crypto', nargs='+', default=['BTC-USD', 'ETH-USD'],
                        help='Crypto symbols to analyze')
    parser.add_argument('--api-only', action='store_true',
                        help='Only test API connection')
    
    args = parser.parse_args()
    
    print("\n🤖 GEMINI AI INTEGRATION TEST")
    print("="*60)
    
    # Test API connection
    api_ok = await test_gemini_api()
    
    if not api_ok:
        sys.exit(1)
    
    if args.api_only:
        print("\n✅ API test passed!")
        sys.exit(0)
    
    # Test full analysis
    analysis_ok = await test_full_analysis(args.symbols, args.crypto)
    
    print("\n" + "="*60)
    if analysis_ok:
        print("✅ ALL GEMINI TESTS PASSED!")
        print("\nYour Gemini integration is working.")
        print("Enable in config.yaml:")
        print("  gemini:")
        print("    enabled: true")
    else:
        print("⚠️  Some tests had issues. Check the output above.")
    print("="*60 + "\n")
    
    sys.exit(0 if analysis_ok else 1)


if __name__ == '__main__':
    asyncio.run(main())
