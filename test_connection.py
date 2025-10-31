#!/usr/bin/env python3
"""Quick diagnostic script to test IB Gateway connection."""

import sys
from ib_insync import IB
import asyncio


async def test():
    """Test IB Gateway connection and configuration."""
    ib = IB()
    
    print("=" * 60)
    print("IB GATEWAY CONNECTION TEST")
    print("=" * 60)
    
    try:
        print("\n1️⃣  Attempting connection to localhost:5000...")
        print("   (timeout: 10 seconds)")
        
        await ib.connectAsync('127.0.0.1', 5000, clientId=999, timeout=10)
        
        print("   ✅ Connected!")
        
        print("\n2️⃣  Getting account info...")
        accounts = ib.managedAccounts()
        print(f"   Accounts: {accounts}")
        
        print("\n3️⃣  Getting positions...")
        positions = ib.positions()
        print(f"   Open positions: {len(positions)}")
        for pos in positions[:3]:  # Show first 3
            print(f"      - {pos.contract.symbol}: {pos.position} shares")
        
        print("\n4️⃣  Testing market data request...")
        contract = ib.Stock('AAPL', 'SMART', 'USD')
        ticker = ib.reqMktData(contract)
        await asyncio.sleep(2)
        
        if ticker.last and ticker.last > 0:
            print(f"   ✅ AAPL last price: ${ticker.last}")
        else:
            print(f"   ⚠️  No market data (may need subscription)")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYour IB Gateway is configured correctly.")
        print("The bot should work now. Try: ./run.sh")
        
    except asyncio.TimeoutError:
        print("\n" + "=" * 60)
        print("❌ TIMEOUT ERROR")
        print("=" * 60)
        print("\nThe connection times out during API handshake.")
        print("This is the SAME error your bot is getting.")
        print("\n📋 MOST LIKELY CAUSES (in order):")
        print("\n1. API not enabled in Gateway")
        print("   → IB Gateway → Configure → Settings → API → Settings")
        print("   → CHECK: 'Enable ActiveX and Socket Clients'")
        print("   → UNCHECK: 'Read-Only API'")
        print("   → Click OK, then RESTART Gateway")
        print("\n2. Client ID conflict")
        print("   → In Gateway API Settings, check 'Master API Client ID'")
        print("   → If it's 12, change your config.yaml client_id to 100")
        print("\n3. Gateway wasn't restarted after settings change")
        print("   → Must fully restart Gateway after changing API settings")
        print("\n4. Wrong port")
        print("   → Check Gateway's socket port matches 5000")
        print("   → Or try port 7497 for paper trading")
        print("\n📖 See TROUBLESHOOTING.md for detailed steps")
        return 1
        
    except ConnectionRefusedError:
        print("\n" + "=" * 60)
        print("❌ CONNECTION REFUSED")
        print("=" * 60)
        print("\nCannot connect to port 5000.")
        print("\n📋 POSSIBLE CAUSES:")
        print("\n1. IB Gateway is not running")
        print("   → Start IB Gateway first")
        print("\n2. Gateway is on different port")
        print("   → Check Gateway settings for socket port")
        print("   → Paper trading default: 7497")
        print("   → Live trading default: 7496")
        print("\n3. Firewall blocking connection")
        print("   → Check firewall allows localhost connections")
        print("\n💡 Quick check:")
        print("   Run: lsof -i :5000")
        print("   Should show Java process listening")
        return 1
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ ERROR: {type(e).__name__}")
        print("=" * 60)
        print(f"\n{e}")
        print("\n📖 See TROUBLESHOOTING.md for help")
        return 1
        
    finally:
        if ib.isConnected():
            ib.disconnect()
            print("\n✅ Disconnected cleanly")
    
    return 0


def main():
    """Run the test."""
    print("\n🔍 Testing IB Gateway Connection...")
    print("This will help diagnose connection issues.\n")
    
    try:
        exit_code = asyncio.run(test())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

