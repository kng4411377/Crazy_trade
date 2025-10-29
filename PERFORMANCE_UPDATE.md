# Performance Tracking - NEW FEATURE ✨

## What's Been Added

Your bot now has comprehensive P&L statistics and performance tracking!

### 🎯 New Capabilities

1. **Real-Time Account P&L** from IBKR
   - Net liquidation value
   - Cash and position values
   - Unrealized and realized P&L
   - Buying power

2. **Trade-Level Analytics**
   - Automatic P&L calculation from fills
   - Win rate, profit factor, Sharpe ratio
   - Max drawdown tracking
   - Average win/loss analysis
   - Per-symbol performance breakdown

3. **Historical Tracking**
   - Daily performance snapshots
   - 30-day P&L trends
   - Trade history with duration
   - Account value over time

4. **Export & Analysis**
   - CSV export of all trades
   - Import to Excel/Google Sheets
   - Programmatic API access
   - Custom analysis queries

---

## 📦 New Files Added

### Core Module
- **`src/performance.py`** (508 lines)
  - `PerformanceTracker` class
  - Account summary from IBKR
  - Trade P&L calculation
  - Statistical analysis
  - CSV export functionality

### Scripts
- **`scripts/show_performance.py`**
  - Display comprehensive performance report
  - Command: `python scripts/show_performance.py`

- **`scripts/export_trades.py`**
  - Export trades to CSV
  - Command: `python scripts/export_trades.py`

### Tests
- **`tests/test_performance.py`** (266 lines)
  - Full test coverage for performance module
  - Trade calculation tests
  - Statistics validation
  - Export functionality tests

### Documentation
- **`PERFORMANCE_GUIDE.md`** (Complete guide)
  - Metrics explained
  - Usage examples
  - Best practices
  - Troubleshooting

### Database
- **New table**: `performance_snapshots`
  - Daily account snapshots
  - Historical performance tracking
  - Automatic capture by bot

---

## 🚀 Quick Start

### View Your Performance

```bash
python scripts/show_performance.py
```

**Sample Output:**
```
======================================================================
PERFORMANCE REPORT
======================================================================

📊 ACCOUNT SUMMARY
----------------------------------------------------------------------
Net Liquidation: $52,350.00
Cash: $22,150.00
Position Value: $30,200.00
Unrealized P&L: $1,200.00
Realized P&L: $850.00

📈 OVERALL STATISTICS
----------------------------------------------------------------------
Total Trades: 15
Win Rate: 60.0% (9W / 6L)
Total P&L: $1,250.00
Average P&L per Trade: $83.33
Profit Factor: 1.77
Sharpe Ratio: 1.24
Max Drawdown: $425.00

🎯 PERFORMANCE BY SYMBOL
----------------------------------------------------------------------
TSLA:
  Trades: 6 | Win Rate: 66.67%
  Total P&L: $850.00 | Avg: $141.67

NVDA:
  Trades: 5 | Win Rate: 60.0%
  Total P&L: $325.00 | Avg: $65.00
```

### Export Trades

```bash
python scripts/export_trades.py
```

Creates: `trades_20241024_143000.csv`

---

## 📊 Key Metrics Explained

### Win Rate
Percentage of profitable trades. Good: >50% for momentum strategies.

### Profit Factor
Ratio of gross profit to gross loss. >1.0 = profitable, >2.0 = excellent.

### Sharpe Ratio
Risk-adjusted return measure. >1.0 = good, >2.0 = excellent.

### Max Drawdown
Largest peak-to-trough decline in cumulative P&L. Shows worst-case risk.

### Expectancy
Expected profit per trade. Positive = long-term edge.

---

## 🔧 Integration

The bot automatically:
- ✅ Captures daily snapshots of account value
- ✅ Calculates P&L from all fills
- ✅ Tracks per-symbol performance
- ✅ Stores historical data in database

No configuration needed - it just works!

---

## 💡 Usage Examples

### Monitor Daily Performance

```bash
# Morning: check yesterday's results
python scripts/show_performance.py

# Evening: review today's trades
python scripts/show_performance.py
```

### Weekly Analysis

```bash
# Export all trades
python scripts/export_trades.py

# Analyze in Excel/Sheets
# - Calculate weekly returns
# - Identify best/worst symbols
# - Review stopped-out trades
```

### Programmatic Access

```python
from src.database import DatabaseManager
from src.performance import PerformanceTracker

db = DatabaseManager("sqlite:///bot.db")
tracker = PerformanceTracker(db, ibkr_client)

with db.get_session() as session:
    # Get statistics
    stats = tracker.calculate_trade_statistics(session)
    print(f"Win Rate: {stats['win_rate']}%")
    print(f"Profit Factor: {stats['profit_factor']}")
    
    # By symbol
    by_symbol = tracker.get_performance_by_symbol(session)
    for symbol, perf in by_symbol.items():
        print(f"{symbol}: ${perf['total_pnl']:,.2f}")
    
    # Daily P&L
    daily = tracker.get_daily_pnl(session, days=30)
    for day in daily:
        print(f"{day['date']}: ${day['pnl']:,.2f}")
```

---

## 📈 Database Updates

New table `performance_snapshots`:
```sql
CREATE TABLE performance_snapshots (
    id INTEGER PRIMARY KEY,
    date DATETIME,
    account_value FLOAT,
    cash_value FLOAT,
    position_value FLOAT,
    unrealized_pnl FLOAT,
    realized_pnl FLOAT,
    daily_pnl FLOAT,
    num_positions INTEGER,
    num_trades INTEGER,
    created_at DATETIME
);
```

Query snapshots:
```bash
sqlite3 bot.db "SELECT * FROM performance_snapshots ORDER BY date DESC"
```

---

## 🎯 What to Monitor

### Daily
- **Total P&L**: Am I profitable?
- **Win Rate**: Trending up or down?
- **Today's Trades**: Any patterns?

### Weekly  
- **Best/Worst Symbols**: Allocate more to winners
- **Max Drawdown**: Adjust sizes if too high
- **Profit Factor**: Should be >1.5

### Monthly
- **Sharpe Ratio**: Is it consistent?
- **Monthly Return %**: Calculate from snapshots
- **Strategy Refinement**: Optimize parameters

---

## 🔍 Troubleshooting

### "No closed trades yet"
Bot needs at least one buy-sell cycle. Keep trading!

### Account data missing
- Check IBKR connection
- Verify API permissions in IB Gateway

### Inaccurate P&L
- Review fills: `sqlite3 bot.db "SELECT * FROM fills"`
- Ensure complete buy/sell pairs

---

## 📚 Full Documentation

See **`PERFORMANCE_GUIDE.md`** for:
- Complete metric explanations
- Best practices
- Advanced queries
- Optimization strategies
- External analysis workflows

---

## ✅ Code Statistics

**Added:**
- 1 new module: `performance.py` (508 lines)
- 2 new scripts: `show_performance.py`, `export_trades.py`
- 1 test file: `test_performance.py` (266 lines)
- 1 database table: `performance_snapshots`
- Performance tracking integrated into main bot loop

**Total Impact:**
- +508 lines of production code
- +266 lines of test code
- +100% performance visibility
- Zero configuration required

---

## 🎉 Summary

You asked: **"Can it get the relevant data from the account and calculate the performance?"**

Answer: **Yes! Completely implemented.**

The bot now:
✅ Pulls real-time P&L from IBKR account  
✅ Calculates trade-level statistics  
✅ Tracks win rate, Sharpe ratio, max drawdown  
✅ Provides per-symbol performance breakdown  
✅ Exports to CSV for external analysis  
✅ Stores daily snapshots automatically  
✅ Offers programmatic API access  

**Try it now:**
```bash
python scripts/show_performance.py
```

🚀 **Your bot now has institutional-grade performance tracking!**

