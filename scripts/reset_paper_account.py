#!/usr/bin/env python3
"""
Reset paper trading account by closing all positions and canceling all orders.

IMPORTANT: This script only works with paper trading accounts.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.alpaca_client import AlpacaClient
from src.config import BotConfig
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


async def main():
    """Reset paper trading account."""
    print("=" * 60)
    print("RESET PAPER TRADING ACCOUNT")
    print("=" * 60)
    print()
    
    # Load config
    try:
        config = BotConfig.from_yaml("config.yaml")
    except Exception as e:
        print(f"❌ Failed to load config.yaml: {e}")
        sys.exit(1)
    
    # Safety check - only allow paper trading
    if config.mode != "paper":
        print("❌ ERROR: This script only works in paper trading mode!")
        print(f"   Current mode: {config.mode}")
        print()
        print("⚠️  For safety, we don't allow resetting live accounts via script.")
        print("   If you need to close live positions, use the Alpaca dashboard.")
        sys.exit(1)
    
    print(f"✅ Mode: {config.mode} (paper trading)")
    print()
    
    # Confirm with user
    print("⚠️  WARNING: This will close ALL positions and cancel ALL orders!")
    print()
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Aborted. No changes made.")
        sys.exit(0)
    
    print()
    print("Connecting to Alpaca...")
    
    # Connect to Alpaca
    client = AlpacaClient(config)
    try:
        await client.connect()
        print("✅ Connected!")
        print()
        
        # Get current state
        print("📊 Current Account State:")
        positions = client.get_positions()
        print(f"   Open Positions: {len(positions)}")
        for symbol, pos in positions.items():
            print(f"      - {symbol}: {pos['quantity']} shares")
        
        orders = client.get_open_orders()
        print(f"   Open Orders: {len(orders)}")
        for order_wrapper in orders:
            print(f"      - {order_wrapper.contract.symbol}: {order_wrapper.order.side.value} {order_wrapper.order.type.value}")
        
        print()
        
        # Reset account
        if len(positions) > 0 or len(orders) > 0:
            print("🔄 Resetting account...")
            result = client.reset_paper_account()
            
            if result:
                print("✅ Account reset successful!")
                print()
                print("   - All positions closed")
                print("   - All orders cancelled")
                print()
                
                # Verify
                await asyncio.sleep(2)  # Give API time to process
                positions_after = client.get_positions()
                orders_after = client.get_open_orders()
                
                print("📊 Account State After Reset:")
                print(f"   Open Positions: {len(positions_after)}")
                print(f"   Open Orders: {len(orders_after)}")
                
                if len(positions_after) == 0 and len(orders_after) == 0:
                    print()
                    print("✅ Account successfully reset to starting state!")
                else:
                    print()
                    print("⚠️  Some positions or orders may still be open.")
                    print("   Check Alpaca dashboard if needed.")
            else:
                print("❌ Reset failed. Check logs for details.")
                sys.exit(1)
        else:
            print("✅ Account is already clean (no positions or orders).")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error("reset_failed", error=str(e))
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("RESET COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

