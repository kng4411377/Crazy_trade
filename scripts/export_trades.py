#!/usr/bin/env python3
"""Export trades to CSV for analysis."""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager
from src.performance import PerformanceTracker


def main():
    """Export trades to CSV."""
    db = DatabaseManager("sqlite:///bot.db")
    tracker = PerformanceTracker(db)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trades_{timestamp}.csv"
    
    with db.get_session() as session:
        tracker.export_trades_to_csv(session, filename)
        
        # Count trades
        trades = tracker.calculate_closed_trades(session)
        print(f"✅ Exported {len(trades)} trades to {filename}")
        
        if trades:
            print(f"\nFirst trade: {trades[0]['entry_ts']}")
            print(f"Last trade: {trades[-1]['exit_ts']}")
            print(f"\nTotal P&L: ${sum(t['pnl'] for t in trades):,.2f}")


if __name__ == "__main__":
    main()

