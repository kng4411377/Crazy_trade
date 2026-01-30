#!/usr/bin/env python3
"""
Comprehensive Test Script for Crazy Trade Bot

Tests:
1. Configuration loading
2. Alpaca API connection
3. Gemini AI connection
4. Momentum providers (YFinance, Apewisdom)
5. Technical indicators
6. Paper trading order placement (optional)

Usage:
    python scripts/test_all.py                  # Run all tests
    python scripts/test_all.py --skip-order     # Skip order placement test
    python scripts/test_all.py --only alpaca    # Test only Alpaca
    python scripts/test_all.py --only gemini    # Test only Gemini
    python scripts/test_all.py --only momentum  # Test only momentum
    python scripts/test_all.py --only indicators # Test only indicators
"""

import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Colors:
    """Terminal colors."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"{Colors.BOLD}{title}{Colors.END}")
    print('='*60)


def print_pass(msg: str):
    """Print a pass message."""
    print(f"  {Colors.GREEN}✅ {msg}{Colors.END}")


def print_fail(msg: str):
    """Print a fail message."""
    print(f"  {Colors.RED}❌ {msg}{Colors.END}")


def print_warn(msg: str):
    """Print a warning message."""
    print(f"  {Colors.YELLOW}⚠️  {msg}{Colors.END}")


def print_info(msg: str):
    """Print an info message."""
    print(f"  {Colors.BLUE}ℹ️  {msg}{Colors.END}")


async def test_config() -> bool:
    """Test configuration loading."""
    print_header("1. CONFIGURATION TEST")
    
    try:
        print("\n  Loading config.yaml...")
        from src.config import BotConfig
        config = BotConfig.from_yaml('config.yaml')
        
        print_pass(f"Config loaded successfully")
        print_info(f"Mode: {config.mode}")
        print_info(f"Stock watchlist: {config.watchlist[:3]}..." if len(config.watchlist) > 3 else f"Stock watchlist: {config.watchlist}")
        print_info(f"Crypto watchlist: {config.crypto_watchlist}")
        
        # Check secrets
        print("\n  Checking secrets.yaml...")
        import yaml
        with open('secrets.yaml', 'r') as f:
            secrets = yaml.safe_load(f)
        
        alpaca_key = secrets.get('alpaca', {}).get('api_key', '')
        if alpaca_key and not alpaca_key.startswith('YOUR_'):
            print_pass("Alpaca API key found")
        else:
            print_warn("Alpaca API key not set (using placeholder)")
        
        gemini_key = secrets.get('gemini', {}).get('api_key', '')
        if gemini_key and not gemini_key.startswith('YOUR_'):
            print_pass("Gemini API key found")
        else:
            print_warn("Gemini API key not set (optional)")
        
        return True
        
    except FileNotFoundError as e:
        print_fail(f"Config file not found: {e}")
        print_info("Run: cp config.yaml.example config.yaml")
        return False
    except Exception as e:
        print_fail(f"Config error: {e}")
        return False


async def test_alpaca() -> bool:
    """Test Alpaca API connection."""
    print_header("2. ALPACA API TEST")
    
    try:
        print("\n  Connecting to Alpaca...")
        from src.config import BotConfig
        from src.alpaca_client import AlpacaClient
        
        config = BotConfig.from_yaml('config.yaml')
        client = AlpacaClient(config)
        await client.connect()
        print_pass("Connected to Alpaca")
        
        # Get account
        print("\n  Fetching account info...")
        account = await client.get_account()
        print_pass(f"Account value: ${float(account.equity):,.2f}")
        print_info(f"Buying power: ${float(account.buying_power):,.2f}")
        print_info(f"Cash: ${float(account.cash):,.2f}")
        
        # Get price
        print("\n  Testing market data...")
        price = await client.get_last_price('AAPL')
        if price:
            print_pass(f"AAPL price: ${price:.2f}")
        else:
            print_warn("Could not fetch AAPL price (market may be closed)")
        
        # Get positions
        print("\n  Checking positions...")
        positions = await client.get_positions()
        print_info(f"Open positions: {len(positions)}")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print_fail(f"Alpaca error: {e}")
        if 'api key' in str(e).lower() or 'unauthorized' in str(e).lower():
            print_info("Check your API keys in secrets.yaml")
            print_info("Make sure you're using Paper Trading keys")
        return False


async def test_gemini() -> bool:
    """Test Gemini AI connection."""
    print_header("3. GEMINI AI TEST")
    
    try:
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
            print_warn("Gemini API key not configured")
            print_info("Get a free key at: https://aistudio.google.com/app/apikey")
            print_info("Add to secrets.yaml under gemini.api_key")
            return True  # Not a failure, just skipped
        
        print("\n  Importing google-generativeai...")
        try:
            import google.generativeai as genai
        except ImportError:
            print_fail("google-generativeai not installed")
            print_info("Run: pip install google-generativeai")
            return False
        
        print("\n  Configuring Gemini...")
        genai.configure(api_key=api_key)
        
        print("\n  Testing API connection...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'Hello, trading bot!' in one line.")
        
        if response and response.text:
            print_pass(f"Gemini response: {response.text.strip()[:50]}")
            return True
        else:
            print_fail("Empty response from Gemini")
            return False
            
    except Exception as e:
        print_fail(f"Gemini error: {e}")
        if 'api key' in str(e).lower():
            print_info("Check your Gemini API key")
        return False


async def test_momentum() -> bool:
    """Test momentum providers."""
    print_header("4. MOMENTUM PROVIDERS TEST")
    
    try:
        # Test YFinance
        print("\n  Testing YFinance provider...")
        from src.momentum.providers.yfinance_provider import YFinanceProvider
        
        yf_provider = YFinanceProvider({})
        await yf_provider.initialize()
        
        if yf_provider.is_available():
            print_pass("YFinance provider available")
            
            # Test data fetch
            metrics = await yf_provider.calculate_volume_metrics('AAPL')
            if metrics:
                print_pass(f"AAPL RVOL: {metrics.get('rvol', 0):.2f}x")
            else:
                print_warn("Could not fetch volume metrics")
        else:
            print_fail("YFinance provider not available")
        
        await yf_provider.close()
        
        # Test Apewisdom
        print("\n  Testing Apewisdom provider (Reddit sentiment)...")
        from src.momentum.providers.apewisdom import ApewisdomProvider
        
        ape_provider = ApewisdomProvider({})
        await ape_provider.initialize()
        
        if ape_provider.is_available():
            print_pass("Apewisdom provider available")
            
            # Get trending
            trending = await ape_provider.get_trending_stocks(limit=5)
            if trending:
                print_pass(f"Found {len(trending)} trending stocks")
                top = trending[0] if trending else {}
                print_info(f"Top stock: {top.get('symbol', 'N/A')} ({top.get('mentions', 0)} mentions)")
            else:
                print_warn("No trending stocks found")
        else:
            print_warn("Apewisdom provider not available (may be rate limited)")
        
        await ape_provider.close()
        
        return True
        
    except Exception as e:
        print_fail(f"Momentum error: {e}")
        return False


async def test_indicators() -> bool:
    """Test technical indicators."""
    print_header("5. TECHNICAL INDICATORS TEST")
    
    try:
        print("\n  Testing indicator calculations...")
        from src.analysis.indicators import TechnicalIndicators
        
        config = {
            'rsi': {'enabled': True, 'period': 14},
            'macd': {'enabled': True},
            'bollinger': {'enabled': True},
            'sma': {'enabled': True, 'periods': [20, 50]},
            'volume': {'enabled': True}
        }
        
        indicators = TechnicalIndicators(config)
        
        # Calculate for AAPL
        print("\n  Calculating indicators for AAPL...")
        result = await indicators.calculate_for_symbol('AAPL')
        
        if result:
            print_pass(f"Price: ${result.price:.2f}")
            
            if result.rsi:
                status = "oversold" if result.rsi < 30 else "overbought" if result.rsi > 70 else "neutral"
                print_pass(f"RSI(14): {result.rsi:.1f} ({status})")
            
            if result.macd is not None:
                trend = "bullish" if result.macd > (result.macd_signal or 0) else "bearish"
                print_pass(f"MACD: {result.macd:.4f} ({trend})")
            
            if result.bb_percent is not None:
                print_pass(f"Bollinger %B: {result.bb_percent:.2%}")
            
            if result.sma_20:
                print_pass(f"SMA(20): ${result.sma_20:.2f}")
            
            if result.relative_volume:
                print_pass(f"Relative Volume: {result.relative_volume:.2f}x")
            
            return True
        else:
            print_fail("Could not calculate indicators")
            return False
            
    except ImportError as e:
        print_fail(f"Import error: {e}")
        print_info("Make sure pandas and numpy are installed")
        return False
    except Exception as e:
        print_fail(f"Indicator error: {e}")
        return False


async def test_paper_order(skip: bool = False) -> bool:
    """Test paper trading order placement."""
    print_header("6. PAPER ORDER TEST")
    
    if skip:
        print_warn("Order test skipped (use --test-order to enable)")
        return True
    
    try:
        from src.config import BotConfig
        config = BotConfig.from_yaml('config.yaml')
        
        if config.mode != 'paper':
            print_warn("Not in paper mode - skipping order test for safety")
            print_info("Set mode: 'paper' in config.yaml to test orders")
            return True
        
        print("\n  Testing paper order placement...")
        print_warn("This will place a REAL order in your PAPER account")
        
        confirm = input("  Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print_info("Order test skipped by user")
            return True
        
        from src.alpaca_client import AlpacaClient
        client = AlpacaClient(config)
        await client.connect()
        
        # Place a small limit order that won't fill
        print("\n  Placing test order (small limit order)...")
        
        # Get current price
        price = await client.get_last_price('AAPL')
        if not price:
            print_fail("Could not get price for test order")
            return False
        
        # Place limit order well below market (won't fill)
        test_price = round(price * 0.5, 2)  # 50% below market
        
        order = await client.place_limit_order(
            symbol='AAPL',
            qty=1,
            side='buy',
            limit_price=test_price,
            tif='DAY'
        )
        
        if order:
            print_pass(f"Order placed: {order.id}")
            print_info(f"Symbol: AAPL, Qty: 1, Limit: ${test_price}")
            
            # Cancel it immediately
            print("\n  Cancelling test order...")
            await client.cancel_order(str(order.id))
            print_pass("Order cancelled")
        else:
            print_fail("Failed to place order")
            return False
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print_fail(f"Order test error: {e}")
        return False


async def run_all_tests(args):
    """Run all tests."""
    print(f"\n{Colors.BOLD}🧪 CRAZY TRADE BOT - COMPREHENSIVE TEST{Colors.END}")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Determine which tests to run
    run_all = args.only is None
    
    # Test 1: Config
    if run_all or args.only == 'config':
        results['config'] = await test_config()
    
    # Test 2: Alpaca
    if run_all or args.only == 'alpaca':
        results['alpaca'] = await test_alpaca()
    
    # Test 3: Gemini
    if run_all or args.only == 'gemini':
        results['gemini'] = await test_gemini()
    
    # Test 4: Momentum
    if run_all or args.only == 'momentum':
        results['momentum'] = await test_momentum()
    
    # Test 5: Indicators
    if run_all or args.only == 'indicators':
        results['indicators'] = await test_indicators()
    
    # Test 6: Paper Order
    if run_all or args.only == 'order':
        results['order'] = await test_paper_order(skip=not args.test_order)
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print()
    for name, passed_test in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if passed_test else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {name.upper():15} {status}")
    
    print()
    if passed == total:
        print(f"  {Colors.GREEN}{Colors.BOLD}All {total} tests passed! ✅{Colors.END}")
        print(f"\n  Your bot is ready to run: ./run.sh")
    else:
        print(f"  {Colors.YELLOW}{passed}/{total} tests passed{Colors.END}")
        print(f"\n  Fix the failing tests before running the bot.")
    
    print()
    return passed == total


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Test Crazy Trade Bot features')
    parser.add_argument('--only', choices=['config', 'alpaca', 'gemini', 'momentum', 'indicators', 'order'],
                        help='Run only specific test')
    parser.add_argument('--test-order', action='store_true',
                        help='Include paper order placement test')
    parser.add_argument('--skip-order', action='store_true',
                        help='Skip order test (deprecated, orders skip by default)')
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(run_all_tests(args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
