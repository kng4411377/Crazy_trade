# Crazy Trade Bot - Alpaca Automated Trading System

A sophisticated, production-ready automated trading bot for Alpaca that implements momentum-based breakout strategies with trailing stop risk management. Includes a **🦍 Momentum Intelligence Layer** that discovers trending stocks via Reddit/WSB buzz, volume anomalies, and social signals. Supports both **stocks** (during market hours) and **cryptocurrency** (24/7).

## 🎯 What This Bot Does

This bot continuously monitors your watchlist and automatically:

✅ **Places breakout entry orders** when price approaches momentum levels  
✅ **Manages trailing stops** to protect profits and limit losses  
✅ **Enforces cooldown periods** (24hr default) after stop-outs to prevent overtrading  
✅ **Supports stocks** (during regular trading hours) and **crypto** (24/7 trading)  
✅ **Auto-rearms orders** - If unfilled at market close, places new order next day  
✅ **Manages position sizing** based on dollar allocation and exposure limits  
✅ **Circuit breakers** - Stops trading if daily loss limits are exceeded  
✅ **🦍 Momentum Scanner** - Find trending stocks via Reddit/WSB buzz and volume spikes  

### Key Features

- **🦍 Momentum Intelligence Layer**: Find trending stocks via Reddit/WSB buzz, volume anomalies, and social signals
- **Configurable Entry Strategies**: Use current price, SMA, or opening price as entry reference
- **Smart Re-arming**: Automatically places new orders each trading session
- **24/7 Crypto Support**: Trade Bitcoin, Ethereum, Dogecoin, and more around the clock
- **Risk Management**: Multiple layers of safety including cooldowns, exposure limits, circuit breakers
- **Paper Trading**: Test strategies risk-free with Alpaca's paper trading
- **REST API**: Monitor bot remotely via HTTP endpoints

---

## 🚀 Quick Start

### Prerequisites

1. **Alpaca Trading Account** (Free paper trading or live)
   - Sign up at [alpaca.markets](https://alpaca.markets/)
   - Generate API keys from dashboard (Paper Trading section)
2. **Python 3.9+** installed

### Installation

```bash
# Clone or download the project
cd crazy_trade

# Run setup script (creates venv, installs deps, copies configs)
./setup.sh

# Or manual setup:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.yaml.example config.yaml
cp secrets.yaml.example secrets.yaml
```

### Configuration

**Step 1: Add your Alpaca API keys to `secrets.yaml`**

```yaml
alpaca:
  api_key: "YOUR_ALPACA_API_KEY"        # From Alpaca dashboard
  secret_key: "YOUR_ALPACA_SECRET_KEY"  # Keep secure!
```

**Step 2: Customize `config.yaml` for your strategy**

All settings are in a single unified config file with labeled sections:

```yaml
mode: "paper"          # "paper" | "live" - START WITH PAPER!

# SECTION 2: STOCK WATCHLIST
watchlist:
  - "TSLA"
  - "NVDA"
  - "AMD"

# SECTION 3: POSITION SIZING
allocation:
  total_usd_cap: 50000
  per_symbol_usd: 1000
  min_cash_reserve_percent: 10

# SECTION 4: ENTRY STRATEGY
entries:
  entry_price_strategy: "current"
  buy_stop_pct_above_last: 5.0
  tif: "DAY"

# SECTION 5: EXIT STRATEGY
stops:
  trailing_stop_pct: 10.0
  tif: "GTC"

# SECTION 6: RISK MANAGEMENT
risk:
  max_concurrent_positions: 5
  max_daily_loss_pct: 3.0

# MOMENTUM INTELLIGENCE (optional)
momentum:
  enabled: false
  filter:
    enabled: false
  dynamic_watchlist:
    enabled: false

# CRYPTO (disabled by default, at bottom of file)
crypto:
  enabled: false
```

⚠️ **Security**: `config.yaml` and `secrets.yaml` are gitignored - safe from commits!

### Running the Bot

```bash
# Start the bot (uses config.yaml)
./run.sh

# Or run directly
python3 main.py

# For crypto: set crypto.enabled = true and add symbols to crypto.watchlist in config.yaml, then ./run.sh

# Stop gracefully
Ctrl+C
```

### Test Connection

```bash
# Quick test to verify API keys work
python3 test_connection.py

# Expected: ✅ Connected! Account Value: $100,000.00
```

### Scripts (Startup & Tests)

| Purpose | Command |
|--------|--------|
| **Start bot** | `./run.sh` |
| **Start API server** | `./run_api.sh` |
| **Background (status/stop)** | `./start_background.sh [start\|stop\|status]` |
| **First-time setup** | `./setup.sh` |
| **Test Alpaca** | `python3 test_connection.py` |
| **Test crypto symbols** | `python3 test_crypto_symbols.py` |
| **Test everything** | `python scripts/test_all.py` |
| **Test Gemini AI** | `python scripts/test_gemini.py` |
| **Test order/fills** | `./verify_fills.sh` (API must be running) |
| **Run pytest** | `./run_tests.sh` or `python run_tests.py` |

Other scripts (momentum scanner, export trades, reset, etc.) are in **`archive/`** — see `archive/README.md`.

---

## 📋 How It Works

### Trading Flow (Per Symbol)

Each symbol operates independently through these states:

```
1. NO_POSITION
   └─> Places entry order (buy stop at price + X%)
   
2. ENTRY_PENDING
   └─> Monitors entry order
       ├─> Filled? → Go to POSITION_OPEN
       ├─> Cancelled/Expired? → Back to NO_POSITION (re-arms next session)
       └─> Market closes? → Cancelled, re-arms tomorrow
   
3. POSITION_OPEN
   └─> Trailing stop active
       ├─> Price rises? → Stop trails up
       └─> Stop fills? → Go to COOLDOWN
   
4. COOLDOWN (24 hours default)
   └─> Wait period to prevent revenge trading
       └─> Expires? → Back to NO_POSITION
```

### Entry Strategy Options

**1. Current Price (default)**
```yaml
entry_price_strategy: "current"
# Entry = current_price × 1.05 (if buy_stop_pct_above_last = 5.0)
# Most responsive, recalculates every time
```

**2. SMA (Simple Moving Average)**
```yaml
entry_price_strategy: "sma"
sma_periods: 10
# Entry = SMA(10 days) × 1.05
# Smoother, filters out noise, good for swing trading
```

**3. Opening Price**
```yaml
entry_price_strategy: "opening"
# Entry = today_open × 1.05
# Stable reference throughout the day
```

### Auto-Rearm Behavior

**Important**: When entry orders expire or get cancelled:
- ✅ Bot automatically places **new order next trading session**
- ✅ Uses fresh price calculation (SMA/opening/current at that time)
- ✅ Continues until filled or you stop the bot
- ❌ Cooldown period **only triggers after stop-out**, not order expiration

Example:
```
Day 1: Place buy stop at $105 (current price $100)
       → Market closes, order expired
Day 2: Auto-place new buy stop at $108 (current price now $103)
       → Market closes, order expired
Day 3: Auto-place new buy stop at $110 (current price now $105)
       → Order fills! Position opened, trailing stop activated
```

### Risk Management

**Position Sizing**
```python
# Dollar-based sizing
qty = floor(per_symbol_usd / last_price)

# With constraints:
# 1. Per-symbol exposure limit (default $2000)
# 2. Total portfolio exposure limit (default $20000)
# 3. Minimum cash reserve (default 10%)
# 4. Max concurrent positions (default 5)
```

**Safety Features**
- **Cooldown After Stop-Out**: Default 24hr wait prevents revenge trading
- **Circuit Breakers**: Stop trading if daily loss > 3% or $500
- **Exposure Limits**: Per-symbol and total portfolio caps
- **Duplicate Detection**: Automatically cancels duplicate trailing stops
- **Market Hours Enforcement** (stocks): Only trades 9:30 AM - 4:00 PM ET
- **Session Time Filters**: Skip first 5min after open, last 10min before close

---

## 🏗️ Architecture

### Tech Stack
- **Language**: Python 3.9+
- **Broker API**: Alpaca Trading API via `alpaca-py` SDK
- **Data**: Historical bars from Alpaca Data API
- **Configuration**: Pydantic models + YAML
- **Market Hours**: pandas_market_calendars
- **Database**: SQLite (SQLAlchemy)
- **Logging**: structlog (structured JSON)

### Project Structure

```
crazy_trade/
├── config.yaml              # Your unified config (gitignored)
├── config.yaml.example      # Template with ALL settings (committed to git)
├── secrets.yaml             # Your API keys (gitignored)
├── secrets.yaml.example     # API key template
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
│
├── src/                     # Core bot logic
│   ├── bot.py              # Main orchestrator
│   ├── state_machine.py    # Per-symbol state machine
│   ├── alpaca_client.py    # Alpaca API wrapper
│   ├── config.py           # Configuration models
│   ├── database.py         # SQLite models & ops
│   ├── sizing.py           # Position sizing logic
│   ├── market_hours.py     # Trading hours checking
│   ├── performance.py      # P&L tracking
│   │
│   └── momentum/           # 🦍 Momentum Intelligence Layer
│       ├── engine.py       # Main scoring engine
│       ├── filter.py       # Watchlist momentum filter
│       ├── discovery.py    # Trending stock discovery
│       ├── providers/      # Data providers
│       │   ├── apewisdom.py      # Reddit/WSB sentiment (FREE)
│       │   ├── yfinance_provider.py  # Volume data (FREE)
│       │   └── google_trends.py  # Search interest (FREE)
│       └── factors/        # Scoring factors
│           ├── reddit_attention.py   # Reddit buzz scoring
│           └── volume_anomaly.py     # Volume spike detection
│
├── scripts/                 # Test & main scripts
│   ├── test_all.py         # Full test (Alpaca, Gemini, momentum, order)
│   └── test_gemini.py      # Test Gemini AI connection & analysis
├── archive/                 # Archived (limited-usage) scripts
│   ├── shell/              # reset_bot.sh, update_config.sh, check_bot_data.sh
│   ├── scripts/            # scan_momentum, export_trades, show_performance, etc.
│   └── README.md            # What’s archived and how to run
│
├── docs/                    # Documentation
│   ├── QUICKSTART.md       # 5-minute setup guide
│   ├── CONFIGURATION.md    # Config reference
│   ├── API_GUIDE.md        # REST API docs
│   ├── CRYPTO_GUIDE.md     # Crypto trading setup
│   ├── UPDATING_CONFIG.md  # How to merge config updates
│   └── CHANGELOG.md        # Version history
│
└── tests/                   # Test suite
    ├── test_state_machine.py
    ├── test_alpaca_client.py
    └── ...
```

---

## 🗄️ Database

SQLite database (`bot.db`) tracks all activity:

### Tables

**`state`** - Per-symbol state
- `symbol` (PK): Stock or crypto symbol
- `cooldown_until_ts`: Cooldown expiration timestamp
- `last_parent_id`: Last entry order ID
- `last_trail_id`: Last trailing stop ID

**`orders`** - All orders placed by bot
- `order_id` (PK): Alpaca order ID (UUID)
- `symbol`, `side`, `order_type`, `status`
- `qty`, `stop_price`, `limit_price`, `trailing_pct`

**`fills`** - All trade executions
- `exec_id` (PK): Execution ID
- `symbol`, `side`, `qty`, `price`, `order_id`, `ts`

**`events`** - Audit trail
- `event_type`: e.g., "entry_order_placed", "stopout_cooldown_started"
- `symbol`, `payload_json`, `ts`

**`performance_snapshots`** - Daily performance tracking
- `date`, `account_value`, `cash_value`, `position_value`
- `unrealized_pnl`, `realized_pnl`, `num_positions`, `num_trades`

---

## 📊 Monitoring

### View Performance

Archived scripts (run from project root when needed):

```bash
python archive/scripts/show_performance.py   # P&L report
python archive/scripts/export_trades.py      # Export trades to CSV
python archive/scripts/check_status.py       # Bot status from DB
```

### Logs

Structured JSON logging:

```bash
# Tail logs in real-time
tail -f bot.log | jq .

# Filter by symbol
grep "TSLA" bot.log | jq .

# Count fills by symbol
grep "fill_received" bot.log | jq -r .symbol | sort | uniq -c
```

### REST API (Optional)

For remote monitoring:

```bash
# Start API server
./run_api.sh

# Then access from anywhere:
curl http://localhost:8080/status | jq .
curl http://localhost:8080/performance | jq .
curl http://localhost:8080/fills
```

See **[docs/API_GUIDE.md](docs/API_GUIDE.md)** for full API documentation.

---

## ⚙️ Configuration Reference

### Entry Orders

```yaml
entries:
  type: "buy_stop"              # "buy_stop" | "buy_stop_limit"
  
  # Entry price strategy
  entry_price_strategy: "current"  # "current" | "sma" | "opening"
  sma_periods: 10                  # If using "sma" strategy
  
  # Entry trigger
  buy_stop_pct_above_last: 5.0  # % above base price
  stop_limit_max_slip_pct: 1.0  # Max slippage (if using buy_stop_limit)
  
  # Order behavior
  tif: "DAY"                    # "DAY" | "GTC"
  cancel_at_close: true         # Cancel unfilled at EOD
  rearm_next_session: true      # Recreate next day
```

### Trailing Stops

```yaml
stops:
  trailing_stop_pct: 10.0       # Trail 10% from peak
  use_trailing_limit: false     # Use trailing limit orders
  trail_limit_offset_pct: 0.2   # Limit offset if above enabled
  tif: "GTC"                    # Usually want GTC for stops
```

### Risk Management

```yaml
risk:
  max_total_exposure_usd: 20000     # Portfolio-wide cap
  max_symbol_exposure_usd: 2000     # Per-symbol cap
  max_daily_loss_pct: 3.0           # Circuit breaker: stop if daily loss > 3%
  max_daily_loss_usd: 500           # Circuit breaker: stop if daily loss > $500
  max_concurrent_positions: 5       # Max positions at once

cooldowns:
  after_stopout_minutes: 1440       # 24 hours (prevents revenge trading)
```

### Market Hours (Stocks Only)

```yaml
hours:
  calendar: "XNYS"              # NYSE calendar
  allow_pre_market: false       # Regular hours only
  allow_after_hours: false
  skip_first_minutes: 5         # Skip first 5min (volatility)
  skip_last_minutes: 10         # Skip last 10min (volatility)
```

---

## 🔧 Advanced Features

### 🦍 Momentum Intelligence Layer (Social/News Signals)

The bot includes a **Momentum Intelligence Layer** that can discover and filter stocks based on social media buzz and volume anomalies. This helps you find stocks that are trending up due to Reddit/WSB attention before major price moves.

#### What It Does

| Factor | Source | What It Detects |
|--------|--------|-----------------|
| **Reddit Attention** | Apewisdom (FREE) | WSB mentions, sentiment, trending rank |
| **Volume Anomaly** | Yahoo Finance (FREE) | Unusual trading volume (RVOL) |
| **Retail Attention** | Google Trends (FREE) | Search interest spikes |

#### Quick Start - Momentum Scanner

```bash
# Scan for trending stocks with social buzz (archived script)
python archive/scripts/scan_momentum.py

# Output shows:
# 🦍 EARLY SIGNALS - Reddit buzz before volume spike (best entry!)
# 🔥 VOLUME BREAKOUTS - High volume right now
# 🏆 CONFIRMED MOMENTUM - Both Reddit + Volume (strongest signal)
```

#### Enable Momentum Filter in Bot

The bot can automatically filter your watchlist to only trade stocks with momentum signals.

Edit the `momentum` section in your `config.yaml`:

```yaml
momentum:
  enabled: true
  
  filter:
    enabled: true           # Filter watchlist by momentum
    min_score: 0.4          # Minimum score to trade (0-1)
    volume_weight: 0.7      # Weight for volume factor
    reddit_weight: 0.3      # Weight for Reddit factor
    require_volume: true    # Must have volume data
    require_reddit: false   # Reddit data optional
```

#### How Momentum Scoring Works

Each stock gets scored 0.0 to 1.0 based on:

**Reddit Attention Score** (via Apewisdom):
- Mention volume (how much WSB is talking about it)
- Mention velocity (rate of increase in mentions)
- Sentiment/positivity (bullish vs bearish)
- Rank momentum (climbing the trending list)

**Volume Anomaly Score** (via Yahoo Finance):
- RVOL (Relative Volume) - current vs 20-day average
- Volume trend - recent 5 days vs previous 15 days

```
Example Output:
┌─────────┬───────────┬────────┬─────────┬───────────────────────┐
│ Symbol  │ Composite │ Volume │ Reddit  │ Signals               │
├─────────┼───────────┼────────┼─────────┼───────────────────────┤
│ GME     │ 0.850     │ 0.720  │ 0.920   │ 🦍 High Reddit 💥 WSB │
│ NVDA    │ 0.780     │ 0.850  │ 0.650   │ 🔥 High Volume        │
│ TSLA    │ 0.720     │ 0.680  │ 0.710   │ 🔥🦍 Both signals     │
└─────────┴───────────┴────────┴─────────┴───────────────────────┘
```

#### Trading Strategy with Momentum

1. **🦍 Early Entry** - Reddit buzz WITHOUT volume yet
   - Best entry point - catch before the move
   - Watch for volume confirmation

2. **🔥 Volume Breakouts** - High volume RIGHT NOW
   - Momentum is confirming
   - Good for quick scalps

3. **🏆 Confirmed Momentum** - Both Reddit + Volume
   - Strongest signal but may have missed early entry
   - Good for continuation trades

#### Data Sources (All FREE!)

| Provider | Data | Rate Limits | Notes |
|----------|------|-------------|-------|
| **Apewisdom** | Reddit/WSB sentiment | Unlimited | Updates 2x daily (9AM & 9PM EST) |
| **Yahoo Finance** | Volume, price data | Unlimited | Real-time |
| **Google Trends** | Search interest | ~10 req/min | Can hit 429 errors |

See **[docs/momentum/README.md](docs/momentum/README.md)** for full momentum documentation.

---

### 🤖 Gemini AI Analysis Layer

The bot can use Google's Gemini AI to analyze stocks and crypto with technical indicators, providing trade signals with confidence scores.

#### Features

- **Batched Analysis**: All tickers analyzed in a single API call (respects 1 call/minute limit)
- **Technical Indicators**: RSI, MACD, Bollinger Bands calculated locally
- **Strategy Context**: Different strategies for stocks (Wheel Strategy) vs crypto (Day Trading)
- **Confidence Scores**: AI provides 0-1 confidence for each signal

#### Quick Setup

1. Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

2. Add to `secrets.yaml`:
```yaml
gemini:
  api_key: "YOUR_GEMINI_API_KEY"
```

3. Enable in `config.yaml`:
```yaml
gemini:
  enabled: true
  model: "gemini-1.5-flash"      # Fast and cheap
  
  enable_stocks: true             # Analyze stocks
  enable_crypto: true             # Analyze crypto
  
  crypto_watchlist:               # Static crypto list for AI
    - "BTC/USD"
    - "ETH/USD"
    - "SOL/USD"
  
  strategies:
    stocks: "Wheel Strategy"      # Context for stock analysis
    crypto: "Day Trading"         # Context for crypto analysis
  
  min_confidence: 0.6             # Only act on high-confidence signals
```

#### Example Output

```
gemini_signal | symbol=NVDA | action=BUY | confidence=0.82 | strategy=Wheel Strategy
              | reasoning=RSI oversold at 28, MACD crossing bullish, price near BB lower band
              
gemini_signal | symbol=BTC/USD | action=HOLD | confidence=0.71 | strategy=Day Trading
              | reasoning=Consolidating near resistance, wait for breakout confirmation
```

#### Technical Indicators Calculated

| Indicator | Description |
|-----------|-------------|
| **RSI** | Relative Strength Index (14 period) |
| **MACD** | Moving Average Convergence Divergence |
| **Bollinger Bands** | 20-period with 2 std dev |
| **SMA** | Simple Moving Averages (20, 50, 200) |
| **Volume** | Relative volume vs 20-day average |

---

### Crypto Trading (24/7)

```yaml
# Separate config for crypto
mode: "paper"

watchlist: []  # No stocks

crypto_watchlist:
  - "BTC/USD"
  - "ETH/USD"
  - "DOGE/USD"

allocation:
  allow_fractional: true  # Required for crypto!

entries:
  tif: "GTC"              # No market close for crypto
  cancel_at_close: false
```

See **[docs/CRYPTO_GUIDE.md](docs/CRYPTO_GUIDE.md)** for full crypto setup.

### Symbol-Specific Allocation

```yaml
allocation:
  per_symbol_usd: 1000     # Default
  per_symbol_override:
    TSLA: 1500             # More for high-conviction
    BTC/USD: 2000          # More for Bitcoin
```

### Custom config file

```bash
# Single config.yaml holds stocks + crypto. For a different file:
./run.sh path/to/my_config.yaml
```

---

## 🐛 Troubleshooting

### Common Issues

**"No such file: config.yaml"**
```bash
# Copy from template
cp config.yaml.example config.yaml
cp secrets.yaml.example secrets.yaml
```

**"Invalid API key" or "Unauthorized"**
- Verify you copied the full API key (no spaces)
- Check you're using **Paper Trading** keys (start with `PK`)
- Regenerate keys in Alpaca dashboard if needed

**Orders not placing**
- Check market hours (stocks trade 9:30 AM - 4:00 PM ET only)
- Verify sufficient buying power in your account
- Review logs for exposure limit warnings
- Check if in cooldown period: `sqlite3 bot.db "SELECT * FROM state"`

**Bot stops trading mid-day**
- Check if circuit breaker triggered (daily loss limit)
- Review logs for "circuit breaker" or "daily_loss" messages
- Limits reset at start of next trading day

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

# Check cooldowns
sqlite3 bot.db "SELECT symbol, cooldown_until_ts FROM state WHERE cooldown_until_ts > datetime('now')"
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_state_machine.py

# Run with coverage
pytest --cov=src --cov-report=html
```

---

## 📚 Documentation

All documentation is in the `/docs` folder:

### 🚀 Getting Started
- **[QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute setup guide
- **[CONFIGURATION.md](docs/CONFIGURATION.md)** - Complete config reference
- **[SETUP_SECRETS.md](docs/SETUP_SECRETS.md)** - API key setup

### 📖 Guides
- **[CRYPTO_GUIDE.md](docs/CRYPTO_GUIDE.md)** - 24/7 cryptocurrency trading
- **[UPDATING_CONFIG.md](docs/UPDATING_CONFIG.md)** - How to merge config updates
- **[RESET_GUIDE.md](docs/RESET_GUIDE.md)** - Reset paper account

### 🦍 Momentum Intelligence
- **[momentum/README.md](docs/momentum/README.md)** - Full momentum layer docs
- **[momentum/QUICKSTART.md](docs/momentum/QUICKSTART.md)** - Quick start guide
- **[MOMENTUM_CONFIG_GUIDE.md](docs/MOMENTUM_CONFIG_GUIDE.md)** - Configuration reference

### 🔧 Technical
- **[API_GUIDE.md](docs/API_GUIDE.md)** - REST API documentation
- **[BOT_REFERENCE.md](docs/BOT_REFERENCE.md)** - Complete bot functionality
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Version history

### 🚀 Deployment
- **[UBUNTU_DEPLOYMENT.md](docs/UBUNTU_DEPLOYMENT.md)** - Deploy to Ubuntu server
- **[DEPLOY_TO_SERVER.md](docs/DEPLOY_TO_SERVER.md)** - General server deployment

See **[docs/INDEX.md](docs/INDEX.md)** for complete documentation index.

---

## 🖥️ PM2 Deployment (Headless Server)

For running on a headless Ubuntu server with PM2:

```bash
# Install PM2 globally
npm install -g pm2

# Start the bot
pm2 start ecosystem.config.js

# Or start individually
pm2 start main.py --interpreter python3 --name crazy-trade-bot

# Monitor
pm2 status
pm2 logs crazy-trade-bot
pm2 monit

# Auto-start on reboot
pm2 startup
pm2 save
```

### Using .env for Configuration

```bash
# Copy template
cp .env.example .env

# Edit with your keys
nano .env
```

```env
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
GEMINI_API_KEY=your_gemini_key

# Feature toggles
STOCKS_ENABLED=true
CRYPTO_ENABLED=true
GEMINI_ENABLED=true
LOG_LEVEL=INFO
```

---

## 🔄 Updating

When you pull new code updates:

```bash
# Your local configs are gitignored - safe from overwrites!
git pull

# Merge new features from config.yaml.example into your config.yaml (keeps your settings)
python3 merge_config.py

# Or see what changed (archived)
./archive/shell/update_config.sh

# Update dependencies
pip install -r requirements.txt --upgrade
```

See **[docs/UPDATING_CONFIG.md](docs/UPDATING_CONFIG.md)** for detailed guide.

---

## 🛡️ Safety & Best Practices

### Before Going Live

1. ✅ Test in **paper trading** for at least 1 week
2. ✅ Review `bot.db` to verify order logic
3. ✅ Start with **small allocations** ($100/symbol)
4. ✅ Monitor first few trades closely
5. ✅ Understand cooldown behavior (24hr after stop-out)
6. ✅ Set appropriate risk limits (daily loss, position limits)

### Risk Disclaimer

⚠️ **IMPORTANT**: 
- Trading involves substantial risk of loss
- Past performance does not guarantee future results
- This bot is for educational purposes
- Test thoroughly before risking real capital
- The authors are not responsible for any losses incurred

---

## 📈 Performance Notes

- **Latency**: Orders typically placed within 1-2 seconds
- **Resource Usage**: ~50MB RAM, <1% CPU
- **Scalability**: Handles 20+ symbols comfortably
- **Reliability**: Designed for 24/7 operation
- **API Limits**: Respects Alpaca rate limits (200 req/min)

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

---

## 📞 Support

For issues:
1. Check logs: `tail -f bot.log | jq .`
2. Review database: `sqlite3 bot.db "SELECT * FROM state"`
3. See troubleshooting section above
4. Check [docs/CHANGELOG.md](docs/CHANGELOG.md) for recent fixes
5. File an issue with logs and config (redact API keys!)

---

## 📝 License

MIT License - Use at your own risk. Not financial advice.

---

**Happy Trading! 🚀📈**

*Trade smart. Trade safe. Test first.* ✅
