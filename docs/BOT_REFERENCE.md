# 📘 Crazy Trade Bot - Complete Reference Guide

**Last Updated:** November 2024  
**Version:** 1.0 (Alpaca)

---

## 🎯 What is This Bot?

The **Crazy Trade Bot** is a production-ready, automated trading system designed to trade stocks and cryptocurrencies using a momentum-based breakout strategy with intelligent risk management. It connects to Alpaca Markets and operates autonomously, placing orders, managing positions, and protecting capital 24/7.

### Core Purpose

The bot monitors a watchlist of assets and automatically:
- **Detects momentum breakouts** by placing buy-stop orders above current price
- **Captures upward moves** when price breaks through resistance
- **Protects profits** with trailing stop-loss orders
- **Prevents overtrading** with cooldown periods after losses
- **Manages risk** through position sizing and exposure limits

---

## 🏗️ Architecture Overview

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        CRAZY TRADE BOT                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
            ┌───────▼────────┐      ┌──────▼─────────┐
            │   Bot Engine   │      │   API Server   │
            │   (main.py)    │      │ (api_server.py)│
            └───────┬────────┘      └──────┬─────────┘
                    │                       │
        ┌───────────┼───────────┐          │
        │           │           │          │
   ┌────▼────┐ ┌───▼────┐ ┌───▼────┐    │
   │ Alpaca  │ │Database│ │ State  │    │
   │ Client  │ │Manager │ │Machine │    │
   └────┬────┘ └───┬────┘ └───┬────┘    │
        │          │           │          │
        │          │           │          │
   ┌────▼──────────▼───────────▼──────────▼────┐
   │         Shared Components & Data           │
   │  • Position Sizer                          │
   │  • Market Hours Checker                    │
   │  • Performance Tracker                     │
   │  • SQLite Database (bot.db)                │
   └────────────────────────────────────────────┘
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **Bot Orchestrator** | `src/bot.py` | Main event loop, coordinates all operations |
| **State Machine** | `src/state_machine.py` | Per-symbol trading logic and state transitions |
| **Alpaca Client** | `src/alpaca_client.py` | Broker API wrapper for orders and data |
| **Database Manager** | `src/database.py` | SQLite operations for orders, fills, events |
| **Position Sizer** | `src/sizing.py` | Dollar-based position sizing with limits |
| **Market Hours** | `src/market_hours.py` | NYSE calendar and trading hours detection |
| **Performance Tracker** | `src/performance.py` | P&L calculations and analytics |
| **Config Manager** | `src/config.py` | Configuration loading and validation |
| **API Server** | `api_server.py` | REST API for remote monitoring |

---

## 🎲 Trading Strategy Explained

### The Momentum Breakout Approach

The bot implements a classic **breakout trading strategy**:

1. **Wait for Setup**: Monitor price, look for consolidation
2. **Set Entry Trap**: Place buy-stop order +5% above current price
3. **Catch the Move**: Order triggers when price breaks through
4. **Protect Profits**: Trailing stop follows price up, locks in gains
5. **Exit on Reversal**: Stop triggers when price pulls back 10%
6. **Cooldown Period**: Wait 15-30 minutes before next entry

### Why This Strategy?

**Advantages:**
- ✅ Captures strong momentum moves
- ✅ Avoids choppy, sideways markets
- ✅ Mechanical entry rules (no emotion)
- ✅ Built-in risk management
- ✅ Works in trending markets

**Best For:**
- High volatility stocks (GME, AMC, TSLA)
- Momentum stocks breaking out
- Cryptocurrencies (24/7 markets)
- Trending assets with clear direction

**Limitations:**
- ❌ Loses money in choppy/ranging markets
- ❌ Whipsaws in false breakouts
- ❌ Requires strong trends to profit
- ❌ Not suitable for low-volatility blue chips

---

## 📊 How It Works: Step-by-Step

### Lifecycle of a Trade

```
┌──────────────────────────────────────────────────────────────┐
│ 1. NO POSITION                                               │
│    • Bot fetches last price (e.g., $100)                     │
│    • Calculates entry trigger: $100 * 1.05 = $105           │
│    • Places BUY STOP order at $105                           │
│    • Order is DAY order (stocks) or GTC (crypto)             │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ Price rallies to $105+
                   │
┌──────────────────▼───────────────────────────────────────────┐
│ 2. ENTRY PENDING → FILLED                                    │
│    • Price hits $105.50                                      │
│    • Buy stop order executes at ~$105.50                     │
│    • Position opened: Long 10 shares @ $105.50               │
│    • Fill event recorded in database                         │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ Bot detects BUY fill
                   │
┌──────────────────▼───────────────────────────────────────────┐
│ 3. POSITION OPEN - Place Trailing Stop                      │
│    • Bot places TRAILING STOP order                         │
│    • Trail distance: 10% from high                           │
│    • Initial stop: $105.50 * 0.90 = $94.95                  │
│    • Stop follows price up (never down)                      │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ Price moves
                   │
┌──────────────────▼───────────────────────────────────────────┐
│ 4. POSITION MONITORING                                       │
│    • Price rises to $115 (new high)                          │
│    • Stop adjusts up: $115 * 0.90 = $103.50                 │
│    • Then price drops to $110                                │
│    • Stop stays at $103.50 (never moves down)                │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ Price continues down
                   │
┌──────────────────▼───────────────────────────────────────────┐
│ 5. STOP OUT - Exit Position                                 │
│    • Price falls to $103.50                                  │
│    • Trailing stop triggers                                  │
│    • SELL 10 shares @ ~$103.50                               │
│    • Profit: ($103.50 - $105.50) * 10 = -$20 (small loss)   │
│    • BUT locked in profit if high was $115!                  │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ Stop-out detected
                   │
┌──────────────────▼───────────────────────────────────────────┐
│ 6. COOLDOWN PERIOD                                           │
│    • Bot enters 20-minute cooldown                           │
│    • Prevents revenge trading                                │
│    • No new entries until cooldown expires                   │
│    • After cooldown: back to NO POSITION                     │
└──────────────────────────────────────────────────────────────┘
```

### State Machine Per Symbol

Each symbol (stock or crypto) operates independently through these states:

| State | Description | What Bot Does |
|-------|-------------|---------------|
| **NO_POSITION** | No position, no orders | Places buy-stop entry order +5% above |
| **ENTRY_PENDING** | Buy order placed, waiting | Monitors for fill |
| **POSITION_OPEN** | Position held, stop active | Monitors trailing stop health |
| **COOLDOWN** | After stop-out | Waits 15-30 min before re-entry |
| **HALT** | Manual override | Symbol suspended from trading |

---

## ⚙️ Core Features

### 1. Dual Market Support

**Stocks (Traditional)**
- Trades during regular hours: 9:30 AM - 4:00 PM ET
- NYSE/NASDAQ calendar-aware
- DAY orders (auto-cancel at close)
- Respects market holidays

**Cryptocurrencies (24/7)**
- Bitcoin, Ethereum, Dogecoin, etc.
- Trades weekends and holidays
- GTC orders (no expiration)
- Fractional shares supported

### 2. Intelligent Position Sizing

The bot calculates position sizes based on dollar allocation:

```python
# Example calculation
per_symbol_budget = $1000
last_price = $50.00
quantity = floor($1000 / $50) = 20 shares

# Multiple safety checks:
✓ Per-symbol exposure limit ($2000 max)
✓ Total portfolio exposure ($20,000 max)
✓ Minimum cash reserve (10% of account)
✓ Account buying power available
```

**Symbol-Specific Overrides:**
```yaml
allocation:
  per_symbol_usd: 1000
  per_symbol_override:
    TSLA: 1500  # Higher conviction
    DOGE/USD: 500  # More volatile, smaller size
```

### 3. Risk Management System

**Cooldown After Losses**
- 15-30 minute pause after each stop-out
- Prevents emotional revenge trading
- Configurable per your style

**Exposure Limits**
- Per-symbol caps (e.g., max $2000 per stock)
- Total portfolio cap (e.g., max $20,000 deployed)
- Cash reserve requirement (always keep 10% in cash)

**Order Safety**
- Duplicate detection (cancels extra stops)
- Quantity verification (adjusts mismatched stops)
- Stale data protection (skips old prices)
- Connection monitoring (stops trading if disconnected)

**End-of-Day Management**
- Cancels unfilled stock entries 15 min before close
- Preserves open positions and their stops
- Re-arms next trading day (optional)

### 4. Market Hours Enforcement

Uses `pandas_market_calendars` for accurate NYSE calendar:
- Automatically detects holidays
- Handles early closes (e.g., Black Friday)
- Prevents pre-market/after-hours fills
- Bot runs 24/7 but only trades during allowed hours

**Stocks:** RTH only (9:30 AM - 4:00 PM ET)  
**Crypto:** 24/7/365

### 5. Database Persistence

All activity stored in SQLite (`bot.db`):

**Tables:**

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `state` | Per-symbol state | symbol, cooldown_until_ts, last_parent_id |
| `orders` | All orders placed | order_id, symbol, side, status, qty, stop_price |
| `fills` | All executions | exec_id, symbol, side, qty, price, ts |
| `events` | Audit trail | event_type, symbol, payload_json, ts |
| `performance_snapshots` | Daily metrics | date, account_value, pnl, num_trades |

**Benefits:**
- Full audit trail of all activity
- State recovery after restart
- Performance analytics
- Trade history for backtesting

### 6. Real-Time Monitoring

**Structured JSON Logging:**
```json
{
  "event": "entry_order_placed",
  "symbol": "TSLA",
  "order_id": "abc-123",
  "qty": 10,
  "stop_price": 262.50,
  "timestamp": "2024-11-11T14:30:00Z",
  "level": "info"
}
```

**REST API Endpoints:**
- `GET /status` - Bot status and symbol states
- `GET /performance` - P&L metrics
- `GET /fills` - Recent trade fills
- `GET /orders` - Active and historical orders
- `GET /events` - Event audit log
- `GET /daily` - Daily P&L breakdown

**Command-Line Scripts:**
- `show_performance.py` - Detailed P&L report
- `export_trades.py` - CSV export of all trades
- `check_status.py` - Quick status check
- `monitor_bot.py` - Live monitoring dashboard

### 7. Keep-Alive System

Prevents connection timeout:
- Pings Alpaca every 5 minutes
- Works 24/7 (even when market closed)
- Configurable interval
- Ensures bot stays connected

---

## 🔧 Configuration System

Configuration is split into two files for security:

### `config.yaml` - Trading Parameters

```yaml
mode: "paper"  # or "live"

# Stock watchlist (trades during market hours)
watchlist: 
  - "GME"
  - "TSLA"

# Crypto watchlist (trades 24/7)
crypto_watchlist:
  - "BTC/USD"
  - "ETH/USD"

allocation:
  total_usd_cap: 50000
  per_symbol_usd: 1000
  min_cash_reserve_percent: 10
  allow_fractional: true

entries:
  type: "buy_stop"
  buy_stop_pct_above_last: 5.0
  tif: "DAY"
  cancel_at_close: true

stops:
  trailing_stop_pct: 10.0
  tif: "GTC"

cooldowns:
  after_stopout_minutes: 20

risk:
  max_total_exposure_usd: 20000
  max_symbol_exposure_usd: 2000
```

### `secrets.yaml` - API Keys (Not in Git)

```yaml
alpaca:
  api_key: "YOUR_API_KEY"
  secret_key: "YOUR_SECRET_KEY"
  base_url: "https://paper-api.alpaca.markets"  # or live
```

**Security:** `secrets.yaml` is in `.gitignore` and never committed.

---

## 📈 Performance Tracking

### Metrics Calculated

**Trade-Level:**
- Entry price, exit price
- Profit/loss ($)
- Return (%)
- Duration (time held)

**Overall:**
- Win rate (% profitable trades)
- Profit factor (gross profit / gross loss)
- Average win vs average loss
- Total P&L
- Sharpe ratio (risk-adjusted return)
- Max drawdown (largest peak-to-trough loss)
- Expectancy (average profit per trade)

**Per-Symbol:**
- Trades count
- Total P&L
- Win/loss breakdown
- Best/worst trades

**Daily:**
- Account value snapshots
- Unrealized P&L (open positions)
- Realized P&L (closed trades)
- Daily P&L change
- Number of trades per day

### Viewing Performance

**Command Line:**
```bash
python scripts/show_performance.py
```

Output:
```
╔════════════════════════════════════════════════════════════╗
║          CRAZY TRADE BOT - PERFORMANCE REPORT              ║
╚════════════════════════════════════════════════════════════╝

📊 ACCOUNT SUMMARY
  • Account Value:    $102,345.67
  • Cash:             $85,234.12
  • Positions Value:  $17,111.55
  • Unrealized P&L:   +$1,234.56
  • Realized P&L:     +$2,345.67

📈 OVERALL STATISTICS
  • Total Trades:     45
  • Winning Trades:   28 (62.2%)
  • Losing Trades:    17 (37.8%)
  • Total P&L:        +$2,345.67
  • Profit Factor:    1.85
  • Sharpe Ratio:     1.23
  • Max Drawdown:     -$456.78 (-4.2%)

🎯 PER-SYMBOL PERFORMANCE
  Symbol    Trades  P&L       Win Rate
  ────────────────────────────────────
  GME       12      +$567.89  58.3%
  TSLA      8       +$234.56  75.0%
  BTC/USD   10      +$1,123.45 60.0%
```

**API:**
```bash
curl http://localhost:8080/performance | jq .
```

---

## 🌐 API Server

The bot includes a Flask-based REST API for remote monitoring.

### Starting the API

```bash
# Default port 8080
./run_api.sh

# Custom port
./run_api.sh 9000

# Or directly
python api_server.py --host 0.0.0.0 --port 8080
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API documentation |
| `/health` | GET | Health check |
| `/status` | GET | Bot status and symbol states |
| `/performance` | GET | Performance metrics and P&L |
| `/fills?limit=N` | GET | Recent fills (default 20) |
| `/orders?status=all` | GET | Orders (active or all) |
| `/events?limit=N` | GET | Recent events |
| `/daily?days=N` | GET | Daily P&L (default 10 days) |

### Example Usage

```bash
# Check health
curl http://localhost:8080/health

# Get status
curl http://localhost:8080/status | jq .

# View performance
curl http://localhost:8080/performance | jq '.overall'

# Recent fills
curl http://localhost:8080/fills?limit=10

# Active orders
curl http://localhost:8080/orders

# Daily P&L
curl http://localhost:8080/daily?days=30
```

**Remote Access:**
```bash
# From another machine
curl http://your-server-ip:8080/status
```

---

## 🪙 Crypto vs Stock Trading

### Key Differences

| Aspect | Stocks | Crypto |
|--------|--------|--------|
| **Trading Hours** | 9:30 AM - 4:00 PM ET | 24/7/365 |
| **Calendar** | NYSE holidays | No holidays |
| **Order TIF** | DAY (auto-cancel EOD) | GTC (persistent) |
| **Fractional** | Usually no | Yes (required) |
| **Entry %** | 5% typical | 2-4% (more volatile) |
| **Trailing %** | 10% typical | 6-10% (tighter) |
| **Position Size** | $500-$2000 | $200-$1000 (smaller) |
| **Cancel at Close** | Yes | No (no close) |
| **Volatility** | Moderate | High |
| **Liquidity** | Exchange hours | 24/7 variable |

### Crypto Configuration

```yaml
crypto_watchlist:
  - "BTC/USD"   # Most liquid
  - "ETH/USD"   # Second largest
  - "DOGE/USD"  # High volatility

allocation:
  per_symbol_usd: 500
  per_symbol_override:
    "BTC/USD": 1000
  allow_fractional: true  # REQUIRED for crypto

entries:
  buy_stop_pct_above_last: 3.0  # Tighter
  tif: "GTC"
  cancel_at_close: false

stops:
  trailing_stop_pct: 8.0  # Tighter
```

### Supported Cryptocurrencies

Verified on Alpaca (14 total):
- **BTC/USD** - Bitcoin (most liquid)
- **ETH/USD** - Ethereum (most liquid)
- **DOGE/USD** - Dogecoin (meme, high vol)
- **SHIB/USD** - Shiba Inu (extreme vol)
- **LTC/USD** - Litecoin
- **BCH/USD** - Bitcoin Cash
- **XRP/USD** - Ripple
- **LINK/USD** - Chainlink
- **UNI/USD** - Uniswap
- **AAVE/USD** - Aave
- **AVAX/USD** - Avalanche
- **USDT/USD** - Tether (stablecoin)
- **USDC/USD** - USD Coin (stablecoin)
- **DOT/USD** - Polkadot

**Not Available:**
- MATIC/USD (no longer supported)
- ADA/USD (not supported)
- BNB/USD (Binance native)
- SOL/USD (check availability)

---

## 🛡️ Safety Features

### Automatic Safeguards

1. **Connection Monitoring**
   - Bot stops trading if connection lost
   - Keeps existing positions and orders
   - Logs disconnection event

2. **Duplicate Detection**
   - Scans for multiple trailing stops per position
   - Automatically cancels duplicates
   - Keeps only one stop per position

3. **Quantity Verification**
   - Checks stop qty matches position qty
   - Adjusts after corporate actions (splits, etc.)
   - Recreates stop if mismatch detected

4. **Stale Data Protection**
   - Skips entries if price data is old
   - Prevents trades on outdated information
   - Logs skipped symbols

5. **Exposure Monitoring**
   - Real-time checks before every order
   - Blocks orders exceeding limits
   - Logs limit violations

6. **Rate Limiting**
   - Built-in throttling on API calls
   - Exponential backoff on errors
   - Prevents API bans

### Manual Safety Controls

**Graceful Shutdown:**
```bash
# Press Ctrl+C
# Bot will:
# 1. Log shutdown event
# 2. Close database connections
# 3. Disconnect from Alpaca
# 4. Exit cleanly
# Note: Does NOT cancel orders or close positions
```

**Emergency Stop:**
```bash
# 1. Kill bot process
killall python

# 2. Use Alpaca dashboard to:
#    - Cancel all orders
#    - Close all positions (if needed)
```

**Database Recovery:**
```bash
# View current state
sqlite3 bot.db "SELECT * FROM state;"

# Clear stuck cooldowns
sqlite3 bot.db "UPDATE state SET cooldown_until_ts = NULL;"

# View recent events
sqlite3 bot.db "SELECT * FROM events ORDER BY ts DESC LIMIT 20;"
```

---

## 📚 Use Cases

### 1. Momentum Stock Trading

**Best For:**
- Volatile meme stocks (GME, AMC)
- High-beta tech stocks (TSLA, NVDA)
- Stocks with news catalysts
- Trending markets

**Configuration:**
```yaml
watchlist: ["GME", "AMC", "TSLA", "NVDA"]
allocation:
  per_symbol_usd: 1000
entries:
  buy_stop_pct_above_last: 5.0
stops:
  trailing_stop_pct: 10.0
```

### 2. Cryptocurrency Trading

**Best For:**
- 24/7 market access
- High volatility assets
- Weekend trading
- Fast-moving markets

**Configuration:**
```yaml
crypto_watchlist: ["BTC/USD", "ETH/USD", "DOGE/USD"]
allocation:
  per_symbol_usd: 500
  allow_fractional: true
entries:
  buy_stop_pct_above_last: 3.0
stops:
  trailing_stop_pct: 8.0
```

### 3. Mixed Portfolio

**Best For:**
- Diversification
- Different volatility profiles
- Round-the-clock opportunities

**Configuration:**
```yaml
watchlist: ["GME", "TSLA"]
crypto_watchlist: ["BTC/USD", "ETH/USD"]
allocation:
  per_symbol_usd: 1000
  per_symbol_override:
    "BTC/USD": 1500
```

### 4. Paper Trading Practice

**Best For:**
- Learning the strategy
- Testing configurations
- Gaining confidence
- No real money risk

**Setup:**
```yaml
mode: "paper"
watchlist: ["TSLA", "NVDA"]
allocation:
  per_symbol_usd: 100  # Small for testing
```

---

## 🚨 Important Warnings

### ⚠️ Risk Disclaimer

**THIS BOT CAN LOSE MONEY**
- Trading involves substantial risk of loss
- Past performance ≠ future results
- Momentum strategies lose in choppy markets
- Bot is mechanical, doesn't adapt to conditions
- You are responsible for all losses

### 🧪 Always Test First

1. **Start with paper trading**
   - Run for at least 1 week
   - Review all trades in database
   - Understand the strategy

2. **Start small in live**
   - Use $100-$200 per symbol
   - Monitor closely for first few days
   - Gradually increase size

3. **Monitor regularly**
   - Check logs daily
   - Review performance weekly
   - Adjust configuration based on results

### 🔐 Security Best Practices

1. **API Keys**
   - Never commit `secrets.yaml` to Git
   - Use paper keys for testing
   - Rotate keys periodically
   - Use read-only keys for monitoring

2. **Server Security**
   - Firewall API port (8080)
   - Use SSH for remote access
   - Keep system updated
   - Monitor access logs

3. **Database Backups**
   ```bash
   # Backup before upgrades
   cp bot.db bot.db.backup.$(date +%Y%m%d)
   
   # Regular backups
   crontab -e
   # Add: 0 2 * * * cp ~/crazy_trade/bot.db ~/backups/bot.db.$(date +\%Y\%m\%d)
   ```

---

## 📖 Related Documentation

- **[README.md](../README.md)** - Main overview and quick start
- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step setup guide
- **[API_GUIDE.md](API_GUIDE.md)** - Complete REST API reference
- **[CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)** - Cryptocurrency trading guide
- **[CRYPTO_SYMBOLS.md](CRYPTO_SYMBOLS.md)** - Supported crypto list
- **[UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md)** - Production deployment
- **[SETUP_SECRETS.md](SETUP_SECRETS.md)** - API keys setup
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## 🎓 Understanding the Strategy

### When This Strategy Works

**Trending Markets:**
- Strong directional moves (up or down if shorting)
- Clear momentum with follow-through
- Breakouts from consolidation
- News-driven rallies

**Example Scenario (Profitable):**
```
GME consolidates at $20-$22 for days
Bot places buy-stop at $23.10 (+5%)
Stock breaks out on news → fills at $23.50
Rallies to $30 over 2 days
Trailing stop adjusts to $27.00
Pulls back to $27.50 → stop triggers
Exit: $27.50, Entry: $23.50
Profit: +17%
```

### When This Strategy Fails

**Choppy/Ranging Markets:**
- No clear direction
- False breakouts (whipsaws)
- High volatility but no trend
- Sideways consolidation

**Example Scenario (Loss):**
```
AMC choppy between $8-$10
Bot places buy-stop at $10.50
Gaps up to $10.75 → fills
Immediately reverses down
Trailing stop at $9.45
Exits at $9.50
Entry: $10.75, Exit: $9.50
Loss: -11.6%
```

### Strategy Improvement Ideas

**Configuration Tweaks:**
- Tighten entry (3-4% instead of 5%) for less slippage
- Widen stops (12-15%) to avoid premature exits
- Increase cooldown (30-45 min) to avoid whipsaws
- Reduce position size during volatile periods

**Symbol Selection:**
- Focus on high-volume stocks (easier fills)
- Avoid low-float stocks (too volatile)
- Watch for catalysts (earnings, news)
- Remove underperformers from watchlist

**Time-Based Filters (Future Enhancement):**
- Only trade first/last hour of day (most volume)
- Avoid mid-day chop (11 AM - 2 PM)
- Disable on FOMC days (too volatile)

---

## 🔧 Advanced Topics

### State Recovery After Restart

The bot automatically recovers state when restarted:

1. **Reconnects to Alpaca**
   - Fetches all open positions
   - Gets all pending orders
   - Syncs with current market state

2. **Loads Database State**
   - Reads `state` table for cooldowns
   - Checks `orders` table for history
   - Reviews `fills` for recent trades

3. **Reconciles Differences**
   - Compares Alpaca data vs database
   - Creates missing trailing stops
   - Cancels orphaned orders
   - Updates state as needed

**Manual State Check:**
```bash
# Current symbol states
sqlite3 bot.db "SELECT * FROM state;"

# Open positions (via API)
curl http://localhost:8080/status | jq '.symbols'

# Active orders (via API)
curl http://localhost:8080/orders
```

### Database Schema

**Complete ERD:**
```sql
-- Symbol state tracking
CREATE TABLE state (
    symbol TEXT PRIMARY KEY,
    cooldown_until_ts TIMESTAMP,
    last_parent_id TEXT,
    last_trail_id TEXT
);

-- All orders placed
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    symbol TEXT,
    side TEXT,
    order_type TEXT,
    status TEXT,
    qty REAL,
    stop_price REAL,
    limit_price REAL,
    trailing_pct REAL,
    parent_id TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- All trade fills
CREATE TABLE fills (
    exec_id TEXT PRIMARY KEY,
    symbol TEXT,
    side TEXT,
    qty REAL,
    price REAL,
    order_id TEXT,
    ts TIMESTAMP
);

-- Event audit log
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    symbol TEXT,
    payload_json TEXT,
    ts TIMESTAMP
);

-- Daily performance snapshots
CREATE TABLE performance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TIMESTAMP,
    account_value REAL,
    cash_value REAL,
    position_value REAL,
    unrealized_pnl REAL,
    realized_pnl REAL,
    daily_pnl REAL,
    num_positions INTEGER,
    num_trades INTEGER
);
```

### Logging System

**Log Levels:**
- `DEBUG` - Verbose details (every price check)
- `INFO` - Important events (orders, fills)
- `WARNING` - Issues (missing stops, data stale)
- `ERROR` - Failures (API errors, crashes)

**Key Events Logged:**
- `bot_started` / `bot_stopped`
- `entry_order_placed`
- `order_filled`
- `trailing_stop_placed_after_entry`
- `stopout_cooldown_started`
- `entry_cancelled_eod`
- `duplicate_stop_cancelled`
- `exposure_limit_exceeded`

**Log Analysis:**
```bash
# View logs
tail -f bot.log | jq .

# Filter by symbol
grep "TSLA" bot.log | jq .

# Count fills
grep "fill_received" bot.log | jq -r .symbol | sort | uniq -c

# Find errors
grep '"level":"error"' bot.log | jq .
```

---

## 🎯 Quick Reference

### Start/Stop Commands

```bash
# Start bot (foreground)
./run.sh

# Start bot (background)
./start_background.sh start

# Start with custom config
python main.py config.crypto.yaml

# Stop bot
./start_background.sh stop
# or Ctrl+C

# Restart bot
./start_background.sh restart

# View logs (background mode)
./start_background.sh logs
```

### Monitoring Commands

```bash
# Check status
python scripts/check_status.py

# View performance
python scripts/show_performance.py

# Export trades to CSV
python scripts/export_trades.py

# Monitor in real-time
python examples/monitor_bot.py --watch
```

### API Commands

```bash
# Start API server
./run_api.sh

# Health check
curl http://localhost:8080/health

# Bot status
curl http://localhost:8080/status | jq .

# Performance
curl http://localhost:8080/performance | jq .

# Recent fills
curl http://localhost:8080/fills?limit=10

# Active orders
curl http://localhost:8080/orders
```

### Database Commands

```bash
# Open database
sqlite3 bot.db

# Symbol states
SELECT * FROM state;

# Recent orders
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;

# Recent fills
SELECT * FROM fills ORDER BY ts DESC LIMIT 10;

# Recent events
SELECT event_type, symbol, ts FROM events ORDER BY ts DESC LIMIT 20;

# Clear cooldowns (emergency)
UPDATE state SET cooldown_until_ts = NULL;

# Backup database
cp bot.db bot.db.backup
```

---

## 📞 Support & Troubleshooting

### Common Issues

**"Connection refused" error:**
- Verify Alpaca API keys in `secrets.yaml`
- Test connection: `python test_connection.py`
- Check Alpaca status: https://status.alpaca.markets

**Orders not placing:**
- Check if market is open (stocks only)
- Verify sufficient buying power
- Review logs for exposure limit warnings
- Ensure symbols are valid and tradable

**Bot not trading crypto:**
- Verify crypto symbols have `/USD` suffix
- Enable `allow_fractional: true`
- Check if crypto watchlist is populated
- Review Alpaca crypto support

**Database locked errors:**
- Close other database connections
- Restart bot
- Check file permissions on `bot.db`

**Performance issues:**
- Reduce watchlist size (max ~20 symbols)
- Increase polling intervals
- Check system resources (CPU, memory)

### Getting Help

1. **Check logs first:**
   ```bash
   tail -100 bot.log | jq .
   ```

2. **Review database:**
   ```bash
   sqlite3 bot.db
   SELECT * FROM events ORDER BY ts DESC LIMIT 20;
   ```

3. **Test connection:**
   ```bash
   python test_connection.py
   ```

4. **Check API server:**
   ```bash
   curl http://localhost:8080/health
   ```

5. **File an issue:**
   - Include relevant logs (redact API keys!)
   - Describe expected vs actual behavior
   - Provide config (redact secrets!)

---

## 📝 Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

**Current Version: 1.0** (Alpaca)
- Initial release with Alpaca support
- Stock and crypto trading
- REST API for monitoring
- Performance tracking
- State recovery
- Comprehensive testing

---

## ⚖️ License & Disclaimer

This is custom trading software for educational purposes.

**IMPORTANT:**
- Use at your own risk
- Not financial advice
- No warranty or guarantees
- Authors not responsible for losses
- Test thoroughly before live trading

**Trading involves risk. Past performance does not guarantee future results.**

---

**Happy Trading! 📈🚀**

*For questions or issues, consult the documentation or file an issue on the repository.*

