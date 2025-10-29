# Performance Tracking & P&L Analytics Guide

## Overview

The bot now includes comprehensive performance tracking that:
- **Pulls real-time P&L** from your IBKR account
- **Calculates trade-level P&L** from fill records
- **Tracks performance metrics** (win rate, Sharpe ratio, max drawdown, etc.)
- **Stores daily snapshots** for historical analysis
- **Exports trades** to CSV for external analysis

---

## Quick Start

### View Current Performance

```bash
# Show comprehensive performance report
python scripts/show_performance.py
```

**Output includes:**
- Account summary (from IBKR)
- Overall trade statistics
- Performance by symbol
- Daily P&L breakdown

### Export Trades for Analysis

```bash
# Export all trades to CSV
python scripts/export_trades.py
```

Creates a timestamped CSV file: `trades_20241024_143000.csv`

---

## Performance Metrics Explained

### Account-Level (from IBKR)

```
Net Liquidation: $52,350.00    ← Total account value
Cash: $22,150.00                ← Available cash
Position Value: $30,200.00      ← Current positions value
Unrealized P&L: $1,200.00       ← Open position profit
Realized P&L: $850.00           ← Closed trade profit
```

### Trade Statistics

**Total Trades**: Count of completed round trips (buy → sell)

**Win Rate**: Percentage of winning trades
- Formula: `(Winning Trades / Total Trades) × 100`
- Good: >50% for momentum strategies

**Total P&L**: Sum of all closed trade profits/losses

**Average P&L per Trade**: Total P&L ÷ Total Trades
- Positive = profitable system overall

**Profit Factor**: Ratio of gross profit to gross loss
- Formula: `Gross Profit / Gross Loss`
- >1.0 = profitable, >2.0 = excellent

**Expectancy**: Expected profit per trade
- Formula: `(Win Rate × Avg Win) - (Loss Rate × Avg Loss)`
- Positive = edge over time

**Sharpe Ratio**: Risk-adjusted return measure
- Higher = better (>1.0 is good, >2.0 is excellent)
- Measures return consistency

**Max Drawdown**: Largest peak-to-trough decline
- Formula: `Peak - Trough` in cumulative P&L
- Shows worst-case scenario risk

---

## Sample Performance Report

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
Average Win: $245.56
Average Loss: $-125.00
Largest Win: $550.00
Largest Loss: $-275.00
Profit Factor: 1.77
Expectancy: $72.33
Sharpe Ratio: 1.24
Max Drawdown: $425.00
Avg Trade Duration: 3.45 hours

🎯 PERFORMANCE BY SYMBOL
----------------------------------------------------------------------
TSLA:
  Trades: 6 | Win Rate: 66.67%
  Total P&L: $850.00 | Avg: $141.67
  Best: $550.00 | Worst: $-150.00

NVDA:
  Trades: 5 | Win Rate: 60.0%
  Total P&L: $325.00 | Avg: $65.00
  Best: $275.00 | Worst: $-125.00

META:
  Trades: 4 | Win Rate: 50.0%
  Total P&L: $75.00 | Avg: $18.75
  Best: $200.00 | Worst: $-275.00

📅 DAILY P&L (Last 10 Days)
----------------------------------------------------------------------
2024-10-15 | 🟢  $  325.00 | 3 trades
2024-10-16 | 🔴  $ -150.00 | 2 trades
2024-10-17 | 🟢  $  550.00 | 1 trades
2024-10-18 | 🟢  $  125.00 | 4 trades
2024-10-21 | 🔴  $ -275.00 | 2 trades
2024-10-22 | 🟢  $  425.00 | 2 trades
2024-10-23 | 🟢  $  175.00 | 1 trades

======================================================================
```

---

## Programmatic Access

### In Your Code

```python
from src.database import DatabaseManager
from src.performance import PerformanceTracker

# Initialize
db = DatabaseManager("sqlite:///bot.db")
tracker = PerformanceTracker(db, ibkr_client)

with db.get_session() as session:
    # Get statistics
    stats = tracker.calculate_trade_statistics(session)
    print(f"Win Rate: {stats['win_rate']}%")
    print(f"Total P&L: ${stats['total_pnl']:,.2f}")
    
    # Get account summary
    account = tracker.get_account_summary()
    print(f"Account Value: ${account['NetLiquidation']:,.2f}")
    
    # Get by-symbol performance
    by_symbol = tracker.get_performance_by_symbol(session)
    for symbol, perf in by_symbol.items():
        print(f"{symbol}: {perf['win_rate']}% win rate")
    
    # Get daily P&L
    daily = tracker.get_daily_pnl(session, days=30)
    for day in daily:
        print(f"{day['date']}: ${day['pnl']:,.2f}")
    
    # Export to CSV
    tracker.export_trades_to_csv(session, "my_trades.csv")
```

---

## Database Queries

### Direct SQL Access

```bash
# View performance snapshots
sqlite3 bot.db "SELECT * FROM performance_snapshots ORDER BY date DESC LIMIT 10"

# Get total P&L by symbol
sqlite3 bot.db "
SELECT 
    symbol,
    COUNT(*) as trades,
    SUM(CASE WHEN side='SELL' THEN price * qty ELSE -price * qty END) as pnl
FROM fills 
GROUP BY symbol
"

# View trade history
sqlite3 bot.db "
SELECT 
    f1.symbol,
    f1.price as entry_price,
    f2.price as exit_price,
    f1.qty,
    (f2.price - f1.price) * f1.qty as pnl
FROM fills f1
JOIN fills f2 ON f1.symbol = f2.symbol 
WHERE f1.side = 'BUY' AND f2.side = 'SELL'
  AND f2.ts > f1.ts
"
```

---

## Performance Monitoring Best Practices

### Daily Review

1. **Check Performance Report**
   ```bash
   python scripts/show_performance.py
   ```

2. **Key Metrics to Watch**
   - Win rate trending down? → Review entry criteria
   - Profit factor < 1.0? → System losing money
   - Large drawdown? → Reduce position sizes
   - Sharpe < 1.0? → High volatility, inconsistent returns

3. **Symbol-Specific Review**
   - Identify best/worst performers
   - Adjust allocations accordingly
   - Consider removing consistently losing symbols

### Weekly Analysis

1. **Export Trades**
   ```bash
   python scripts/export_trades.py
   ```

2. **Analyze in Spreadsheet**
   - Calculate average holding time
   - Identify time-of-day patterns
   - Review stopped-out trades
   - Look for setup patterns

3. **Optimization**
   - Adjust `buy_stop_pct_above_last` if too many false breakouts
   - Modify `trailing_stop_pct` based on volatility
   - Fine-tune `after_stopout_minutes` cooldown

### Monthly Deep Dive

1. **Performance Trends**
   - Compare month-over-month
   - Calculate monthly return %
   - Review max drawdown recovery

2. **Risk Analysis**
   - Sharpe ratio trends
   - Win rate consistency
   - Position sizing effectiveness

3. **Strategy Refinement**
   - Test different entry percentages
   - Experiment with trailing stop levels
   - Evaluate cooldown periods

---

## Key Performance Indicators (KPIs)

### Profitability
- ✅ **Positive Total P&L**: System is profitable
- ✅ **Profit Factor > 1.5**: Strong edge
- ✅ **Positive Expectancy**: Long-term edge

### Consistency
- ✅ **Win Rate 50-70%**: Balanced for momentum
- ✅ **Sharpe Ratio > 1.0**: Good risk-adjusted returns
- ✅ **Max Drawdown < 20%**: Controlled risk

### Efficiency
- ✅ **Average Trade Duration < 6 hours**: Quick in/out
- ✅ **Profit Factor > 2.0**: Excellent efficiency
- ✅ **Win/Loss Ratio > 2:1**: Wins bigger than losses

---

## Automated Performance Tracking

The bot automatically:
- **Captures daily snapshots** of account value
- **Records all fills** for P&L calculation
- **Logs performance events** to database
- **Tracks per-symbol metrics**

### Daily Snapshot Contents

```python
{
    'date': '2024-10-24',
    'account_value': 52350.00,
    'cash_value': 22150.00,
    'position_value': 30200.00,
    'unrealized_pnl': 1200.00,
    'realized_pnl': 850.00,
    'num_positions': 3,
    'num_trades': 5
}
```

Snapshots are stored in `performance_snapshots` table for historical tracking.

---

## Exporting & External Analysis

### CSV Export Format

```csv
symbol,entry_ts,exit_ts,duration,entry_price,exit_price,qty,pnl,pnl_pct,trade_type
TSLA,2024-10-24 10:30:00,2024-10-24 14:15:00,3.75,252.50,265.00,10,125.00,4.95,long
NVDA,2024-10-24 11:00:00,2024-10-24 15:30:00,4.50,518.00,535.50,5,87.50,3.38,long
```

### Import to Excel/Google Sheets

1. Export: `python scripts/export_trades.py`
2. Open in Excel/Sheets
3. Create pivot tables for analysis
4. Build custom charts

### Python Data Analysis

```python
import pandas as pd

# Load trades
df = pd.read_csv('trades_20241024_143000.csv')

# Calculate metrics
print(f"Average P&L: ${df['pnl'].mean():.2f}")
print(f"Win Rate: {(df['pnl'] > 0).mean() * 100:.1f}%")
print(f"Best Day: {df.groupby('exit_ts')['pnl'].sum().max():.2f}")

# Plot equity curve
df['cumulative_pnl'] = df['pnl'].cumsum()
df.plot(x='exit_ts', y='cumulative_pnl')
```

---

## Alerts & Notifications

### Set Up Performance Alerts

Add to your config for webhook alerts on key events:

```yaml
alerts:
  webhook: "https://your-webhook-url"  # Slack, Discord, etc.
```

The bot can send alerts for:
- New trade fills
- Daily P&L summary
- Drawdown warnings
- Performance milestones

---

## Troubleshooting

### "No closed trades yet"
- Bot needs to complete at least one buy-sell cycle
- Check fills table: `sqlite3 bot.db "SELECT * FROM fills"`

### Missing account data
- Ensure IBKR connection is active
- Verify API permissions in IB Gateway
- Check `ibkr.connected` status

### Inaccurate P&L calculations
- Review fills for incomplete data
- Ensure fills are properly matched (buy/sell pairs)
- Check for manual trades not tracked by bot

---

## Tips for Better Performance

1. **Track Everything**: Don't delete old trades, use them for analysis
2. **Regular Reviews**: Check performance weekly minimum
3. **Document Changes**: Note config changes and their impact
4. **Compare Periods**: Use snapshots to compare performance over time
5. **Risk Management**: Use P&L to adjust position sizes

---

## Summary

Performance tracking gives you:
- ✅ Real-time account P&L from IBKR
- ✅ Complete trade history analysis
- ✅ Win rate, profit factor, Sharpe ratio
- ✅ Per-symbol performance breakdown
- ✅ Daily P&L tracking
- ✅ CSV export for external analysis
- ✅ Automated daily snapshots

**Check your performance daily. Optimize weekly. Refine monthly.** 📈

---

**Next**: Review `COMMANDS.md` for quick command reference.

