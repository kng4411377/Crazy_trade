#!/usr/bin/env python3
"""Test which crypto symbols are available in Alpaca."""

import asyncio
from src.config import BotConfig
from alpaca.trading.client import TradingClient
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

def main():
    # Load config
    config = BotConfig.from_yaml('config.yaml')
    
    print("🔍 Testing Alpaca Crypto Availability\n")
    print(f"Mode: {config.mode}")
    print(f"Paper Trading: {'Yes' if config.mode == 'paper' else 'No'}\n")
    
    # Initialize client
    if config.mode == "paper":
        trading_client = TradingClient(
            api_key=config.alpaca.api_key,
            secret_key=config.alpaca.secret_key,
            paper=True
        )
    else:
        trading_client = TradingClient(
            api_key=config.alpaca.api_key,
            secret_key=config.alpaca.secret_key,
            paper=False
        )
    
    # Test 1: Get all crypto assets
    print("=" * 60)
    print("TEST 1: Available Crypto Assets")
    print("=" * 60)
    try:
        from alpaca.trading.requests import GetAssetsRequest
        from alpaca.trading.enums import AssetClass
        
        request = GetAssetsRequest(asset_class=AssetClass.CRYPTO)
        assets = trading_client.get_all_assets(request)
        
        print(f"✅ Found {len(assets)} crypto assets\n")
        
        # Show first 20
        print("Available crypto symbols:")
        for i, asset in enumerate(assets[:20]):
            tradable = "✅" if asset.tradable else "❌"
            print(f"  {tradable} {asset.symbol:15s} - {asset.name}")
        
        if len(assets) > 20:
            print(f"\n  ... and {len(assets) - 20} more")
            
        # Check specific symbols
        print("\n" + "=" * 60)
        print("Your Requested Symbols:")
        print("=" * 60)
        test_symbols = ['BTC/USD', 'BTCUSD', 'BTC-USD', 'ETH/USD', 'ETHUSD', 'ETH-USD']
        for symbol in test_symbols:
            found = any(a.symbol == symbol and a.tradable for a in assets)
            status = "✅ FOUND" if found else "❌ NOT FOUND"
            print(f"  {status}: {symbol}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Try fetching crypto data
    print("\n" + "=" * 60)
    print("TEST 2: Crypto Data API")
    print("=" * 60)
    
    try:
        data_client = CryptoHistoricalDataClient()
        
        test_symbols = ['BTC/USD', 'BTCUSD', 'ETH/USD', 'ETHUSD']
        
        for symbol in test_symbols:
            try:
                request = CryptoBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Hour,
                    start=datetime.now() - timedelta(hours=2)
                )
                bars = data_client.get_crypto_bars(request)
                print(f"  ✅ {symbol:10s} - Data available")
            except Exception as e:
                print(f"  ❌ {symbol:10s} - {str(e)[:50]}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Paper trading crypto support
    print("\n" + "=" * 60)
    print("TEST 3: Paper Trading Crypto Support")
    print("=" * 60)
    
    if config.mode == "paper":
        print("ℹ️  Important Note:")
        print("   Alpaca Paper Trading has LIMITED crypto support")
        print("   Most crypto pairs only work in LIVE trading\n")
        
        print("📚 Recommendation:")
        print("   1. For testing: Use STOCK symbols in paper mode")
        print("   2. For crypto: Switch to LIVE mode (real money!)")
        print("   3. Alternative: Remove crypto from paper trading config")
    else:
        print("✅ You're in LIVE mode - full crypto support available")

if __name__ == '__main__':
    main()

