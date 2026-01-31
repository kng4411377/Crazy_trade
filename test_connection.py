#!/usr/bin/env python3
"""Quick diagnostic script to test Alpaca API connection."""

import sys
import asyncio


async def test():
    """Test Alpaca API connection and configuration."""
    print("=" * 60)
    print("ALPACA API CONNECTION TEST")
    print("=" * 60)
    
    try:
        # Load config
        print("\n1️⃣  Loading configuration...")
        from src.config import BotConfig
        config = BotConfig.from_yaml('config.yaml')
        print(f"   Mode: {config.mode}")
        
        # Test connection
        print("\n2️⃣  Connecting to Alpaca API...")
        from src.alpaca_client import AlpacaClient
        client = AlpacaClient(config)
        await client.connect()
        print("   ✅ Connected!")
        
        # Get account info
        print("\n3️⃣  Getting account info...")
        account_summary = client.get_account_summary()
        print(f"   Account Value: ${account_summary.get('NetLiquidation', 0):,.2f}")
        print(f"   Cash: ${account_summary.get('TotalCashValue', 0):,.2f}")
        print(f"   Buying Power: ${account_summary.get('BuyingPower', 0):,.2f}")
        
        # Get positions
        print("\n4️⃣  Getting positions...")
        positions = client.get_positions()
        print(f"   Open positions: {len(positions)}")
        for symbol, pos in list(positions.items())[:3]:  # Show first 3
            print(f"      - {symbol}: {pos['quantity']} shares @ ${pos['avg_cost']:.2f}")
        
        # Test market data request
        print("\n5️⃣  Testing market data request...")
        price = await client.get_last_price('AAPL')
        if price:
            print(f"   ✅ AAPL last price: ${price:.2f}")
        else:
            print(f"   ⚠️  Could not fetch price")
        
        # Optional: Test Tavily (Deep Research fallback) if API key is set
        import os
        if os.environ.get("TAVILY_API_KEY"):
            print("\n6️⃣  Testing Tavily API (Deep Research fallback)...")
            try:
                from src.analysis.tavily_research import get_tavily_context
                summary = get_tavily_context("AAPL")
                if summary:
                    print(f"   ✅ Tavily connected. Sample: {summary[:120]}...")
                else:
                    print("   ⚠️  Tavily returned no answer (check key or try another ticker)")
            except Exception as e:
                print(f"   ⚠️  Tavily test failed: {e}")
        else:
            print("\n6️⃣  Tavily API: skipped (no TAVILY_API_KEY in env or secrets.yaml env section)")
        
        # Optional: Test Gemini (AI analysis) if API key is set
        import yaml
        gemini_key = None
        try:
            with open("secrets.yaml", "r") as sf:
                secrets = yaml.safe_load(sf) or {}
            gemini_key = (secrets.get("gemini") or {}).get("api_key")
        except Exception:
            pass
        if not gemini_key:
            gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key and str(gemini_key).strip() and "YOUR_" not in str(gemini_key).upper():
            print("\n7️⃣  Testing Gemini API (AI analysis)...")
            try:
                with open("config.yaml", "r") as f:
                    cfg = yaml.safe_load(f) or {}
                gemini_cfg = (cfg.get("gemini") or {}).copy()
                gemini_cfg["enabled"] = True
                from src.analysis.gemini_analyzer import GeminiAnalyzer
                analyzer = GeminiAnalyzer(gemini_cfg)
                ok = await analyzer.initialize()
                if ok:
                    print("   ✅ Gemini connected.")
                else:
                    print("   ⚠️  Gemini init returned False (check key or model)")
            except Exception as e:
                print(f"   ⚠️  Gemini test failed: {e}")
        else:
            print("\n7️⃣  Gemini API: skipped (no gemini.api_key in secrets.yaml or GEMINI_API_KEY)")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYour Alpaca API is configured correctly.")
        print("The bot should work now. Try: ./run.sh")
        
        await client.disconnect()
        return 0
        
    except FileNotFoundError as e:
        print("\n" + "=" * 60)
        print("❌ CONFIG FILE NOT FOUND")
        print("=" * 60)
        print("\nCannot find config.yaml")
        print("\n📋 SOLUTION:")
        print("1. Make sure config.yaml exists in the current directory")
        print("2. Copy from example if needed")
        return 1
        
    except Exception as e:
        error_msg = str(e).lower()
        print("\n" + "=" * 60)
        print(f"❌ ERROR: {type(e).__name__}")
        print("=" * 60)
        print(f"\n{e}")
        
        if 'api key' in error_msg or 'unauthorized' in error_msg or 'forbidden' in error_msg:
            print("\n📋 LIKELY CAUSE: Invalid API Keys")
            print("\n✅ SOLUTION:")
            print("1. Go to https://app.alpaca.markets/")
            print("2. Navigate to Paper Trading section")
            print("3. Generate new API keys")
            print("4. Update config.yaml with correct keys:")
            print("   alpaca:")
            print("     api_key: 'YOUR_API_KEY'")
            print("     secret_key: 'YOUR_SECRET_KEY'")
            print("\n⚠️  Make sure you're using Paper Trading keys if mode is 'paper'")
        
        elif 'connection' in error_msg or 'network' in error_msg:
            print("\n📋 LIKELY CAUSE: Network/Connection Issue")
            print("\n✅ SOLUTION:")
            print("1. Check your internet connection")
            print("2. Verify Alpaca service status: https://status.alpaca.markets")
            print("3. Check if firewall is blocking connections")
        
        else:
            print("\n📖 See ALPACA_MIGRATION.md for more help")
        
        return 1


def main():
    """Run the test."""
    print("\n🔍 Testing Alpaca API Connection...")
    print("This will help diagnose connection issues.\n")
    
    try:
        exit_code = asyncio.run(test())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
