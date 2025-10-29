#!/usr/bin/env python3
"""Display performance and P&L statistics."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager
from src.performance import PerformanceTracker


def main():
    """Display performance report."""
    db = DatabaseManager("sqlite:///bot.db")
    tracker = PerformanceTracker(db)
    
    with db.get_session() as session:
        # Generate and print report
        report = tracker.generate_performance_report(session)
        print(report)
        
        # Also show recent daily P&L
        print("\n📅 DAILY P&L (Last 10 Days)")
        print("-" * 70)
        daily = tracker.get_daily_pnl(session, days=10)
        
        if daily:
            for day in daily:
                pnl_indicator = "🟢" if day['pnl'] > 0 else "🔴" if day['pnl'] < 0 else "⚪"
                print(f"{day['date']} | {pnl_indicator} ${day['pnl']:>8,.2f} | {day['trades']} trades")
        else:
            print("No closed trades yet")
        
        print()
        
        # Export option
        print("💾 Export trades to CSV: python scripts/export_trades.py")


if __name__ == "__main__":
    main()

