# Crazy Trade Bot - IBKR Automated Trading System

A sophisticated, production-ready automated trading bot for Interactive Brokers (IBKR) that implements momentum-based entry strategies with trailing stop risk management.

## 🎯 Overview

This bot continuously monitors a watchlist of high-volatility stocks and automatically:
- Places **Buy Stop orders** at +5% above current price (entry trigger)
- Attaches **10% Trailing Stop** orders for risk management
- Enforces **cooldown periods** after stop-outs to prevent overtrading
- Operates strictly during **Regular Trading Hours (RTH)** for U.S. equities
- Manages position sizing based on dollar allocation and exposure limits

## 🏗️ Architecture

### Tech Stack
- **Language**: Python 3.11+
- **Broker API**: IBKR via `ib_insync` (IB Gateway on port 5000)
- **Data Processing**: pandas, numpy
- **Configuration**: pydantic, PyYAML
- **Market Hours**: pandas_market_calendars
- **Scheduling**: APScheduler
- **Database**: SQLAlchemy/sqlmodel (SQLite by default)
- **Logging**: structlog (structured JSON logging)

### Components

```
crazy_trade/
├── config.yaml              # Configuration file
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── src/
│   ├── __init__.py
│   ├── bot.py              # Main bot orchestrator
│   ├── config.py           # Configuration models
│   ├── database.py         # Database models and operations
│   ├── ibkr_client.py      # IBKR API wrapper
│   ├── market_hours.py     # RTH checking utilities
│   ├── sizing.py           # Position sizing logic
│   └── state_machine.py    # Per-symbol state machine
└── tests/
    ├── test_config.py
    ├── test_database.py
    ├── test_market_hours.py
    ├── test_sizing.py
    ├── test_state_machine.py
    └── test_integration.py
```

## 🚀 Quick Start

### Prerequisites

1. **Interactive Brokers Account** (Paper or Live)
2. **IB Gateway** installed and configured
3. **Python 3.11+** installed

### Installation

```bash
# Clone or download the project
cd crazy_trade

# Install dependencies
pip install -r requirements.txt

# Configure IB Gateway
# - Start IB Gateway
# - Set API port to 5000 (or adjust config.yaml)
# - Enable API connections
# - Disable read-only mode
```

### Configuration

Edit `config.yaml`:

```yaml
ibkr:
  host: "127.0.0.1"
  port: 5000           # IB Gateway port
  client_id: 12
  account: null        # Optional for multi-account

mode: "paper"          # "paper" | "live"

watchlist:             # Your symbols (up to ~20)
  - "TSLA"
  - "NVDA"
  - "SMCI"
  - "META"

allocation:
  total_usd_cap: 20000
  per_symbol_usd: 1000
  min_cash_reserve_percent: 10
```

### Running the Bot

```bash
# Start the bot
python main.py

# Or specify custom config
python main.py my_config.yaml
```

## 📋 Trading Logic

### State Machine (Per Symbol)

Each symbol operates independently through these states:

1. **NO_POSITION** → Place Buy Stop at +5% above current price
2. **ENTRY_PENDING** → Monitor entry order (DAY order)
3. **POSITION_OPEN** → Ensure 10% Trailing Stop exists and is healthy
4. **COOLDOWN** → Wait 15-30 minutes after stop-out before re-entry

### Order Flow

#### Entry Orders
- **Type**: Buy Stop (or Stop Limit with slippage cap)
- **Trigger**: +5% above last traded price
- **TIF**: DAY (auto-cancels at market close)
- **RTH Only**: `outsideRth=False` prevents pre/post-market fills

#### Risk Management
- **Type**: Trailing Stop (or Trailing Limit)
- **Trail**: 10% from high-water mark
- **TIF**: GTC (persists across sessions)
- **Attached**: Created as OCO child of entry order

### Position Sizing

Dollar-based sizing with multiple safety limits:

```python
# Basic calculation
qty = floor(per_symbol_usd / last_price)

# Constraints checked:
# 1. Per-symbol exposure limit ($2000 default)
# 2. Total portfolio exposure limit ($20,000 default)
# 3. Minimum cash reserve (10% of account)
```

### Market Hours Enforcement

- Uses `pandas_market_calendars` for accurate RTH detection
- Only places/modifies/cancels orders during 9:30 AM - 4:00 PM ET
- Automatically cancels unfilled entries 15 minutes before close
- Bot runs 24/7 but remains dormant outside RTH

### Risk Controls

1. **Cooldown After Stop-Out**: 15-30 minute pause prevents revenge trading
2. **Exposure Limits**: Per-symbol and total portfolio caps
3. **Duplicate Detection**: Automatically cancels duplicate trailing stops
4. **Quantity Verification**: Ensures stop size matches position size
5. **Cash Reserve**: Maintains minimum cash buffer

## 🗄️ Database Schema

SQLite database (`bot.db`) tracks all activity:

### Tables

**state** - Per-symbol state
- `symbol` (PK): Stock symbol
- `cooldown_until_ts`: Cooldown expiration timestamp
- `last_parent_id`: Last entry order ID
- `last_trail_id`: Last trailing stop ID

**orders** - All orders placed
- `order_id` (PK): IBKR order ID
- `symbol`, `side`, `order_type`, `status`
- `qty`, `stop_price`, `limit_price`, `trailing_pct`
- `parent_id`: For child orders

**fills** - All executions
- `exec_id` (PK): Execution ID
- `symbol`, `side`, `qty`, `price`
- `order_id`, `ts`

**events** - Audit trail
- `event_type`: e.g., "entry_order_placed", "stopout_cooldown_started"
- `symbol`, `payload_json`, `ts`

**performance_snapshots** - Daily performance tracking
- `date`: Snapshot timestamp
- `account_value`, `cash_value`, `position_value`
- `unrealized_pnl`, `realized_pnl`, `daily_pnl`
- `num_positions`, `num_trades`

## 🧪 Testing

Comprehensive test suite covering:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_state_machine.py

# Run integration tests only
pytest -m integration

# Run with coverage
pytest --cov=src --cov-report=html
```

### Test Scenarios

✅ **Gap-up through stop** - Entry fills, trailing stop activates  
✅ **Trailing stop triggers** - Cooldown starts, prevents re-entry  
✅ **Cooldown expiration** - New entries allowed after timeout  
✅ **Duplicate stop detection** - Extras cancelled automatically  
✅ **RTH gating** - Orders only during regular hours  
✅ **Position sizing** - Exposure limits enforced  
✅ **End-of-day cancellation** - Unfilled entries cancelled  

## 📊 Monitoring & Logging

### Structured Logging

All logs in JSON format (structlog):

```json
{
  "event": "entry_order_placed",
  "symbol": "TSLA",
  "order_id": 1001,
  "qty": 10,
  "stop_price": 262.50,
  "timestamp": "2024-10-24T14:30:00.123Z",
  "level": "info"
}
```

### Key Events Logged

- `bot_started` / `bot_stopped`
- `entry_order_placed` / `order_filled` / `order_cancelled`
- `trailing_stop_placed` / `trailing_stop_recreated`
- `stopout_cooldown_started`
- `duplicate_stop_cancelled`
- `exposure_limit_exceeded`

### Monitoring Commands

```bash
# View performance & P/L
python scripts/show_performance.py

# Export trades to CSV
python scripts/export_trades.py

# Check bot status
python scripts/check_status.py

# Tail logs in real-time
tail -f bot.log | jq .

# Filter by symbol
grep "TSLA" bot.log | jq .

# Count fills by symbol
grep "fill_received" bot.log | jq -r .symbol | sort | uniq -c

# Check cooldown status
sqlite3 bot.db "SELECT symbol, cooldown_until_ts FROM state WHERE cooldown_until_ts > datetime('now')"
```

## ⚙️ Configuration Reference

### Entry Strategy

```yaml
entries:
  type: "buy_stop"              # "buy_stop" | "buy_stop_limit"
  buy_stop_pct_above_last: 5.0  # Entry trigger above last price
  stop_limit_max_slip_pct: 1.0  # Max slippage for limit orders
  tif: "DAY"
  cancel_at_close: true          # Cancel unfilled at EOD
  rearm_next_session: true       # Recreate next day
```

### Stop Strategy

```yaml
stops:
  trailing_stop_pct: 10.0        # Trail distance from peak
  use_trailing_limit: false      # Use TRAIL LIMIT for slippage control
  trail_limit_offset_pct: 0.2    # Limit offset if above enabled
  tif: "GTC"                     # Persist across sessions
```

### Risk Management

```yaml
risk:
  max_total_exposure_usd: 20000  # Portfolio-wide cap
  max_symbol_exposure_usd: 2000  # Per-symbol cap

allocation:
  per_symbol_usd: 1000           # Default per symbol
  per_symbol_override:           # Symbol-specific overrides
    TSLA: 1500
  min_cash_reserve_percent: 10   # Keep 10% in cash
```

### Market Hours

```yaml
hours:
  calendar: "XNYS"               # NYSE calendar
  allow_pre_market: false        # Strict RTH only
  allow_after_hours: false
```

### Cooldowns

```yaml
cooldowns:
  after_stopout_minutes: 20      # Wait after stop-out (15-30 recommended)
```

## 🔧 Advanced Usage

### Custom Watchlist Management

```python
# Dynamic watchlist from file
with open('watchlist.txt') as f:
    config['watchlist'] = [line.strip().upper() for line in f]
```

### Symbol-Specific Allocation

```yaml
allocation:
  per_symbol_override:
    TSLA: 1500    # More for high-conviction plays
    NVDA: 1200
    # Others use default 1000
```

### Fractional Shares

```yaml
allocation:
  allow_fractional: true  # Enable if your account supports it
```

### Multiple Accounts

```yaml
ibkr:
  account: "U1234567"     # Specify account ID
```

## 🛡️ Safety Features

### Automatic Safeguards

1. **Connection Loss**: Bot stops placing orders until reconnected
2. **Data Staleness**: Skips symbols with stale price data
3. **Corporate Actions**: Detects quantity mismatches and adjusts stops
4. **Rate Limiting**: Built-in throttling on API calls
5. **Exponential Backoff**: On API errors

### Manual Controls

```bash
# Graceful shutdown (Ctrl+C)
# - Closes IBKR connection cleanly
# - Logs shutdown event
# - Does NOT cancel existing orders

# Emergency stop (kill bot + cancel all orders)
# - Stop bot: Ctrl+C or kill <pid>
# - Use TWS/IB Gateway to cancel orders manually
```

### Order Verification

Before going live:
1. Test in **paper trading** mode for at least 1 week
2. Review `bot.db` to verify order logic
3. Start with **small allocations** (e.g., $100/symbol)
4. Monitor first few trades closely

## 🐛 Troubleshooting

### Common Issues

**Connection refused (port 5000)**
- Ensure IB Gateway is running
- Check port in Gateway settings
- Verify API connections enabled

**"No market data" errors**
- Subscribe to market data in TWS/Gateway
- Real-time data requires subscriptions
- Use paper account for testing

**Orders not placing**
- Check market hours (must be RTH)
- Verify sufficient buying power
- Review logs for exposure limit warnings

**Cooldown too aggressive**
- Adjust `after_stopout_minutes` in config
- Check database for stuck cooldowns:
  ```sql
  UPDATE state SET cooldown_until_ts = NULL;
  ```

### Debug Mode

```yaml
logging:
  level: "DEBUG"  # More verbose output
```

```bash
# Check state machine status
sqlite3 bot.db "SELECT * FROM state"

# View recent orders
sqlite3 bot.db "SELECT * FROM orders ORDER BY created_at DESC LIMIT 10"

# Audit trail
sqlite3 bot.db "SELECT event_type, symbol, ts FROM events ORDER BY ts DESC LIMIT 20"
```

## 📈 Performance Tracking

The bot includes comprehensive P&L analytics:

### View Performance Report
```bash
python scripts/show_performance.py
```

Shows:
- **Account Summary**: Real-time values from IBKR
- **Overall Statistics**: Win rate, total P&L, Sharpe ratio, max drawdown
- **Per-Symbol Performance**: Breakdown by ticker
- **Daily P&L**: Recent trading days

### Export Trades
```bash
python scripts/export_trades.py
```

Exports all trades to CSV with:
- Entry/exit prices and timestamps
- P&L per trade ($ and %)
- Trade duration
- Win/loss classification

### Key Metrics Tracked

- **Win Rate**: % of profitable trades
- **Profit Factor**: Gross profit / gross loss ratio
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Expectancy**: Average profit per trade
- **Average Trade Duration**: Typical holding period

See **`PERFORMANCE_GUIDE.md`** for detailed documentation.

### Performance Notes

- **Latency**: Orders typically placed within 1-2 seconds of trigger
- **Resource Usage**: Minimal (~50MB RAM, <1% CPU)
- **Scalability**: Handles 20+ symbols comfortably
- **Reliability**: Designed for 24/7 operation
- **Analytics**: Automated daily snapshots for historical tracking

## 🔄 Upgrading

```bash
# Backup database
cp bot.db bot.db.backup

# Pull updates
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart bot
python main.py
```

## 📝 License

This is a custom trading bot. Use at your own risk. Not financial advice.

## ⚠️ Disclaimer

**IMPORTANT**: 
- Trading involves substantial risk of loss
- Past performance does not guarantee future results
- Test thoroughly in paper trading before going live
- The authors are not responsible for any losses incurred
- This bot is for educational purposes

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## 📞 Support

For issues:
1. Check logs: `tail -f bot.log | jq .`
2. Review database: `sqlite3 bot.db`
3. Consult IBKR API docs: https://interactivebrokers.github.io/tws-api/
4. File an issue with logs and config (redact sensitive data)

---

**Happy Trading! 🚀📈**

