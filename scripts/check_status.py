#!/usr/bin/env python3
"""Check bot status from database."""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager


def format_timestamp(ts):
    """Format timestamp for display."""
    if ts is None:
        return "None"
    if isinstance(ts, str):
        return ts
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Display bot status."""
    db = DatabaseManager("sqlite:///bot.db")
    
    print("=" * 60)
    print("CRAZY TRADE BOT - STATUS REPORT")
    print("=" * 60)
    print()
    
    with db.get_session() as session:
        # Symbol states
        print("📊 SYMBOL STATES")
        print("-" * 60)
        states = session.query(db.SymbolState).all()
        if states:
            for state in states:
                cooldown_str = format_timestamp(state.cooldown_until_ts)
                in_cooldown = state.cooldown_until_ts and state.cooldown_until_ts > datetime.utcnow()
                status = "🔴 COOLDOWN" if in_cooldown else "🟢 ACTIVE"
                print(f"{state.symbol:6s} | {status} | Cooldown until: {cooldown_str}")
        else:
            print("No symbol states found")
        print()
        
        # Active orders
        print("📋 ACTIVE ORDERS")
        print("-" * 60)
        active_orders = db.get_active_orders(session)
        if active_orders:
            for order in active_orders[:10]:  # Show last 10
                print(f"Order {order.order_id} | {order.symbol:6s} | {order.side:4s} | "
                      f"{order.order_type:8s} | Qty: {order.qty} | Status: {order.status}")
        else:
            print("No active orders")
        print()
        
        # Recent fills
        print("💰 RECENT FILLS (Last 10)")
        print("-" * 60)
        from src.database import FillRecord
        recent_fills = (
            session.query(FillRecord)
            .order_by(FillRecord.ts.desc())
            .limit(10)
            .all()
        )
        if recent_fills:
            for fill in recent_fills:
                print(f"{format_timestamp(fill.ts)} | {fill.symbol:6s} | {fill.side:4s} | "
                      f"Qty: {fill.qty} @ ${fill.price:.2f}")
        else:
            print("No fills yet")
        print()
        
        # Recent events
        print("📝 RECENT EVENTS (Last 10)")
        print("-" * 60)
        from src.database import EventRecord
        recent_events = (
            session.query(EventRecord)
            .order_by(EventRecord.ts.desc())
            .limit(10)
            .all()
        )
        if recent_events:
            for event in recent_events:
                symbol_str = event.symbol if event.symbol else "SYSTEM"
                print(f"{format_timestamp(event.ts)} | {symbol_str:6s} | {event.event_type}")
        else:
            print("No events logged")
        print()
    
    print("=" * 60)
    print("To view full database: sqlite3 bot.db")
    print("=" * 60)


if __name__ == "__main__":
    main()

