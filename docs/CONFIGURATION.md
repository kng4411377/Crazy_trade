# Configuration Reference

Complete guide to `config.yaml` settings and options.

---

## 📋 Table of Contents

1. [File Structure](#file-structure)
2. [Basic Settings](#basic-settings)
3. [Watchlists](#watchlists)
4. [Entry Strategies](#entry-strategies)
5. [Stop Management](#stop-management)
6. [Risk Management](#risk-management)
7. [Position Sizing](#position-sizing)
8. [Market Hours](#market-hours)
9. [Cooldowns](#cooldowns)
10. [Polling Intervals](#polling-intervals)
11. [Examples](#examples)

---

## File Structure

The bot uses **two separate files** for configuration:

```
config.yaml          # Your trading strategy & settings (gitignored)
secrets.yaml         # Your Alpaca API keys (gitignored)
```

**Templates** (committed to git):
```
config.yaml.example  # Shows all available options
secrets.yaml.example # Shows API key structure
```

### Setup

```bash
# Copy templates
cp config.yaml.example config.yaml
cp secrets.yaml.example secrets.yaml

# Edit with your settings
nano config.yaml
nano secrets.yaml
```

---

## Basic Settings

### Mode

```yaml
mode: "paper"  # "paper" | "live"
```

- **`paper`**: Paper trading (virtual money, no risk) ⭐ Start here!
- **`live`**: Live trading (real money, real risk) ⚠️

### Persistence

```yaml
persistence:
  db_url: "sqlite:///bot.db"  # SQLite database path
```

- Stores all orders, fills, state, and performance data
- Use different databases for different strategies

### Logging

```yaml
logging:
  level: "INFO"  # "DEBUG" | "INFO" | "WARNING" | "ERROR"
```

- **DEBUG**: Very verbose (for troubleshooting)
- **INFO**: Normal operation ⭐ Recommended
- **WARNING**: Only warnings and errors
- **ERROR**: Only errors

---

## Watchlists

### Stock Watchlist

```yaml
watchlist:
  - "TSLA"
  - "NVDA"
  - "AMD"
  - "AAPL"
```

- **Stocks trade during regular market hours** (9:30 AM - 4:00 PM ET)
- Symbol format: Simple ticker (e.g., `TSLA`)
- Up to ~20 symbols recommended

### Crypto Watchlist

```yaml
crypto_watchlist:
  - "BTC/USD"
  - "ETH/USD"
  - "DOGE/USD"
```

- **Crypto trades 24/7** (no market hours restrictions)
- Symbol format: `SYMBOL/USD` (e.g., `BTC/USD`)
- See [CRYPTO_GUIDE.md](CRYPTO_GUIDE.md) for full setup

### Empty Watchlists

```yaml
# Stock-only trading
watchlist: ["TSLA", "NVDA"]
crypto_watchlist: []

# Crypto-only trading
watchlist: []
crypto_watchlist: ["BTC/USD", "ETH/USD"]

# Mixed trading
watchlist: ["TSLA"]
crypto_watchlist: ["BTC/USD"]
```

---

## Entry Strategies

### Overview

Entry orders are placed at a percentage above a **base price**. You can choose how the base price is calculated.

```yaml
entries:
  entry_price_strategy: "current"  # "current" | "sma" | "opening"
  sma_periods: 10                  # For SMA strategy
  buy_stop_pct_above_last: 5.0    # % above base price
```

**Formula**: `entry_trigger = base_price × (1 + buy_stop_pct_above_last / 100)`

### Strategy 1: Current Price (Default)

```yaml
entries:
  entry_price_strategy: "current"
  buy_stop_pct_above_last: 5.0
```

**How it works**:
- Uses current spot price as base
- Recalculates every time order is placed
- Most responsive to price changes

**Example**:
```
Current price: $100
Entry trigger: $100 × 1.05 = $105
```

**Best for**:
- Day trading
- Fast-moving stocks
- Intraday momentum
- Crypto (24/7 markets)

---

### Strategy 2: SMA (Simple Moving Average)

```yaml
entries:
  entry_price_strategy: "sma"
  sma_periods: 10
  buy_stop_pct_above_last: 5.0
```

**How it works**:
- Uses SMA of last N closing prices as base
- Fetches historical daily bars from Alpaca
- Smooths out noise and volatility
- Recalculates with fresh data each day

**Example**:
```
Last 10 daily closes: [$98, $99, $97, $100, $102, $101, $99, $100, $101, $103]
SMA(10) = $100
Entry trigger: $100 × 1.05 = $105
```

**Best for**:
- Swing trading
- Avoiding false breakouts
- Trading above long-term trend
- Volatile meme stocks

**Configuration**:
```yaml
entries:
  entry_price_strategy: "sma"
  sma_periods: 10    # Try 10, 20, or 50 days
```

---

### Strategy 3: Opening Price

```yaml
entries:
  entry_price_strategy: "opening"
  buy_stop_pct_above_last: 5.0
```

**How it works**:
- Uses today's opening price as base
- Stays constant throughout the day
- Provides consistent reference point

**Example**:
```
Today's open: $100
Entry trigger: $100 × 1.05 = $105
(Stays $105 all day, regardless of price movement)
```

**Best for**:
- Day trading with consistent levels
- Avoiding chasing intraday moves
- Gap-up/gap-down trading
- **Not recommended for crypto** (opening becomes stale)

---

### Entry Order Type

```yaml
entries:
  type: "buy_stop"              # "buy_stop" | "buy_stop_limit"
  stop_limit_max_slip_pct: 1.0  # Only for buy_stop_limit
```

**`buy_stop`** (recommended):
- Triggers at stop price, buys at market
- Guarantees fill but not price
- Best for liquid stocks

**`buy_stop_limit`**:
- Triggers at stop price, limit order placed
- Guarantees price but not fill
- Can miss entries if gaps through

---

### Time-in-Force

```yaml
entries:
  tif: "DAY"  # "DAY" | "GTC" | "IOC" | "FOK"
```

**`DAY`** (recommended for stocks):
- Order expires at market close
- Auto-rearms next trading day
- Prevents stale orders

**`GTC`** (Good Till Cancelled):
- Order stays active until filled or cancelled
- Recommended for crypto (24/7 trading)
- Use with caution for stocks

**`IOC`** (Immediate Or Cancel):
- Fill immediately or cancel
- Rarely used

**`FOK`** (Fill Or Kill):
- Fill entire order immediately or cancel
- Rarely used

---

### End-of-Day Behavior

```yaml
entries:
  cancel_at_close: true       # Cancel unfilled at EOD
  rearm_next_session: true    # Recreate next day
```

**With `DAY` + `cancel_at_close: true`**:
```
Day 1: Place order at $105 → Expires at 4:00 PM if unfilled
Day 2: Auto-place new order (recalculates price)
Day 3: Auto-place new order (recalculates price)
...continues until filled or you stop bot
```

**With `GTC`**:
```
Day 1: Place order at $105
Day 2-N: Same order stays active (no recalculation)
```

---

## Stop Management

### Trailing Stops

```yaml
stops:
  trailing_stop_pct: 10.0       # Trail 10% from peak
  use_trailing_limit: false     # Use trailing limit orders
  trail_limit_offset_pct: 0.2   # Limit offset if enabled
  tif: "GTC"                    # Time-in-force
```

**How trailing stops work**:
```
Entry fill: $105
Position opens, trailing stop placed at $94.50 (10% below)

Price rises to $120 → Stop trails up to $108 (10% below new high)
Price rises to $130 → Stop trails up to $117 (10% below new high)
Price drops to $118 → Stop stays at $117 (doesn't trail down)
Price hits $117 → Stop fills, position closed
```

**Stop Types**:

**`use_trailing_limit: false`** (default):
- Trailing stop market order
- Triggers at trail level, sells at market
- Guarantees exit but not price
- Recommended for most use cases

**`use_trailing_limit: true`**:
- Trailing stop limit order
- Triggers at trail level, limit order placed
- Better price control but may not fill
- Use with wide `trail_limit_offset_pct`

---

### Stop Time-in-Force

```yaml
stops:
  tif: "GTC"  # "GTC" | "DAY"
```

**`GTC`** (recommended):
- Stop persists across trading sessions
- Protects position 24/7
- Standard for risk management

**`DAY`**:
- Stop expires at market close
- Position unprotected overnight
- ⚠️ Only use if you have a reason!

---

## Risk Management

### Circuit Breakers

```yaml
risk:
  max_daily_loss_pct: 3.0    # Stop trading if daily loss > 3%
  max_daily_loss_usd: 500    # Stop trading if daily loss > $500
```

**How it works**:
- Bot checks P&L before each new entry
- If either limit exceeded → stops placing new entries
- Existing positions continue to be managed
- Resets at start of next trading day

**Example**:
```yaml
risk:
  max_daily_loss_pct: 3.0
  max_daily_loss_usd: 500

# Account value: $10,000
# Daily P&L: -$350 (3.5% loss)
# Bot stops new entries (exceeds 3% limit)
# Existing positions still have trailing stops
```

**Recommended settings**:
- Conservative: 2-3% or $200-500
- Moderate: 3-5% or $500-1000
- Aggressive: 5-10% or $1000-2000

---

### Position Limits

```yaml
risk:
  max_concurrent_positions: 5  # Max positions at once
```

**How it works**:
- Bot counts open positions before new entries
- If limit reached → skips symbols without positions
- Allows existing positions to close before new entries

**Recommended**:
- Small account: 3-5 positions
- Medium account: 5-10 positions
- Large account: 10-20 positions

---

### Exposure Limits

```yaml
risk:
  max_total_exposure_usd: 20000   # Portfolio-wide cap
  max_symbol_exposure_usd: 2000   # Per-symbol cap
```

**How it works**:
- Bot checks total market value of all positions
- Prevents oversizing any single symbol
- Protects against concentration risk

**Example**:
```yaml
risk:
  max_total_exposure_usd: 20000
  max_symbol_exposure_usd: 2000

# Current positions:
# TSLA: $1,800
# NVDA: $1,500
# AMD: $1,200
# Total: $4,500

# Can add:
# - New TSLA? No ($1,800 already, $2,000 limit)
# - New AAPL? Yes (under $2,000 per-symbol)
# - Would exceed $20,000 total? Check first
```

---

## Position Sizing

### Basic Allocation

```yaml
allocation:
  per_symbol_usd: 1000           # Default per symbol
  total_usd_cap: 20000           # Max total deployed
  min_cash_reserve_percent: 10   # Keep 10% cash
```

**Formula**:
```python
qty = floor(per_symbol_usd / last_price)

# Example:
per_symbol_usd = $1000
last_price = $105
qty = floor(1000 / 105) = 9 shares
```

---

### Symbol-Specific Overrides

```yaml
allocation:
  per_symbol_usd: 1000     # Default
  per_symbol_override:
    TSLA: 1500             # More for TSLA
    BTC/USD: 2000          # More for Bitcoin
    AMD: 500               # Less for AMD
```

**Use cases**:
- Higher conviction symbols get more capital
- Lower conviction symbols get less
- Expensive stocks (like BRK.A) get special sizing

---

### Fractional Shares

```yaml
allocation:
  allow_fractional: false  # true for crypto
```

- **`false`** (stocks): Only whole shares
- **`true`** (crypto): Allows fractional (required for crypto!)

---

### Cash Reserve

```yaml
allocation:
  min_cash_reserve_percent: 10
```

**How it works**:
- Ensures you always have X% cash available
- Prevents overleverage
- Maintains buffer for margin requirements

**Example**:
```
Account value: $10,000
min_cash_reserve_percent: 10
Max deployed: $9,000 (keeps $1,000 in cash)
```

---

## Market Hours

### Calendar Settings (Stocks Only)

```yaml
hours:
  calendar: "XNYS"              # NYSE calendar
  allow_pre_market: false       # 4:00 AM - 9:30 AM ET
  allow_after_hours: false      # 4:00 PM - 8:00 PM ET
```

**Calendars**:
- `XNYS`: New York Stock Exchange (most common)
- `NASDAQ`: NASDAQ exchange
- See `pandas_market_calendars` for more

**Extended hours**:
- ⚠️ Pre-market and after-hours have low liquidity
- Wider spreads and slippage
- Generally not recommended

---

### Session Time Filters

```yaml
hours:
  skip_first_minutes: 5    # Skip first 5min after open
  skip_last_minutes: 10    # Skip last 10min before close
```

**How it works**:
- Bot won't place new orders during these windows
- Avoids opening volatility
- Avoids closing auction volatility
- Existing positions still managed

**Example**:
```yaml
skip_first_minutes: 5
skip_last_minutes: 10

# Market hours: 9:30 AM - 4:00 PM
# Bot trades: 9:35 AM - 3:50 PM
```

**Recommended**:
- First minutes: 5-10 (avoid opening volatility)
- Last minutes: 10-15 (avoid closing auction)

---

## Cooldowns

### After Stop-Out

```yaml
cooldowns:
  after_stopout_minutes: 1440  # 24 hours (1440 minutes)
```

**How it works**:
- When trailing stop fills → cooldown starts
- Symbol cannot enter new positions during cooldown
- Prevents revenge trading
- Enforces discipline

**Cooldown duration**:
```
Stop fills at 2:00 PM Tuesday
Cooldown until 2:00 PM Wednesday
Can re-enter after 2:00 PM Wednesday
```

**Recommended settings**:
- Conservative: 1440 minutes (24 hours) ⭐
- Moderate: 720 minutes (12 hours)
- Aggressive: 240 minutes (4 hours)
- Old default: 20 minutes ❌ (too short!)

**Important**: Cooldown only triggers on **stop-out**, not order expiration!

---

## Polling Intervals

### Connection Management

```yaml
polling:
  keepalive_seconds: 300      # Ping Alpaca every 5 min
  event_check_seconds: 5      # Check for fills/updates
  orders_seconds: 15          # Main loop interval
```

**`keepalive_seconds`**:
- Prevents connection timeout
- Alpaca automatically disconnects inactive connections
- 300 seconds (5 minutes) is safe

**`event_check_seconds`**:
- How often to check for order updates and fills
- 5 seconds is responsive
- Lower = more API calls

**`orders_seconds`**:
- Main trading loop interval
- 10-15 seconds is typical
- Lower = more CPU/API usage

---

## Examples

### Conservative Stock Trading

```yaml
mode: "paper"

watchlist: ["SPY", "QQQ", "AAPL"]

entries:
  entry_price_strategy: "sma"
  sma_periods: 20
  buy_stop_pct_above_last: 3.0
  tif: "DAY"

stops:
  trailing_stop_pct: 8.0
  tif: "GTC"

risk:
  max_concurrent_positions: 3
  max_daily_loss_pct: 2.0
  max_daily_loss_usd: 300

allocation:
  per_symbol_usd: 500
  total_usd_cap: 5000

cooldowns:
  after_stopout_minutes: 1440
```

---

### Aggressive Meme Stock Trading

```yaml
mode: "paper"

watchlist: ["GME", "AMC", "BBBY", "BB"]

entries:
  entry_price_strategy: "current"
  buy_stop_pct_above_last: 7.0
  tif: "DAY"

stops:
  trailing_stop_pct: 15.0
  tif: "GTC"

risk:
  max_concurrent_positions: 5
  max_daily_loss_pct: 5.0
  max_daily_loss_usd: 1000

allocation:
  per_symbol_usd: 1000
  total_usd_cap: 10000

cooldowns:
  after_stopout_minutes: 720  # 12 hours
```

---

### Crypto 24/7 Trading

```yaml
mode: "paper"

watchlist: []  # No stocks

crypto_watchlist:
  - "BTC/USD"
  - "ETH/USD"
  - "DOGE/USD"

entries:
  entry_price_strategy: "current"  # SMA optional for crypto
  buy_stop_pct_above_last: 3.0
  tif: "GTC"                        # No market close
  cancel_at_close: false
  rearm_next_session: false

stops:
  trailing_stop_pct: 8.0
  tif: "GTC"

allocation:
  allow_fractional: true  # Required!
  per_symbol_usd: 500
  per_symbol_override:
    "BTC/USD": 1000
    "ETH/USD": 1000

risk:
  max_concurrent_positions: 8
  max_daily_loss_pct: 5.0

cooldowns:
  after_stopout_minutes: 1440
```

---

## 📚 Related Docs

- **[QUICKSTART.md](QUICKSTART.md)** - Setup guide
- **[CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)** - Crypto trading
- **[BOT_REFERENCE.md](BOT_REFERENCE.md)** - How bot works
- **[UPDATING_CONFIG.md](UPDATING_CONFIG.md)** - Merge updates

---

## 🔧 Validation

Test your config:

```bash
# Validate syntax
python3 -c "from src.config import BotConfig; BotConfig.from_yaml('config.yaml'); print('✅ Valid')"

# Test run
python3 main.py
```

---

**Need help?** See [INDEX.md](INDEX.md) for all documentation.

