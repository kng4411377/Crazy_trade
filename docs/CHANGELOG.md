# Changelog

All notable changes to the Crazy Trade Bot project with detailed technical information.

---

## [1.2.0] - 2024-11-21

### 🛡️ Safety Features Added (Phase 1 - Quick Wins)

Implemented 3 critical safety features from the [Enhancement Roadmap](ENHANCEMENTS_ROADMAP.md):

---

#### 1. Daily Drawdown Circuit Breaker

**Feature:** Automatic halt of new entries when daily loss limits are breached.

**Configuration:**
```yaml
risk:
  max_daily_loss_pct: 3.0     # Stop trading if daily loss > 3%
  max_daily_loss_usd: 500     # Stop trading if daily loss > $500
```

**How It Works:**
- Checks daily P&L before each new entry
- If daily loss exceeds threshold → stops all new entries
- Existing positions continue to be managed
- Resets next trading day

**Benefits:**
- ✅ Prevents cascading losses on bad days
- ✅ Capital preservation
- ✅ Emotional discipline enforced

**Code Changes:**
- `src/config.py`: Added `max_daily_loss_pct` and `max_daily_loss_usd` to `RiskConfig`
- `src/bot.py`: Added `_check_daily_drawdown_ok()` method
- `src/bot.py`: Circuit breaker check in `_process_trading_logic()`

**Example Log:**
```json
{
  "event": "daily_loss_pct_limit_breached",
  "daily_loss_pct": -3.2,
  "limit": 3.0,
  "alert": "CIRCUIT BREAKER: Stopping new entries"
}
```

---

#### 2. Session Time Filters

**Feature:** Skip first/last minutes of trading day to avoid high volatility periods.

**Configuration:**
```yaml
hours:
  skip_first_minutes: 5       # Skip first 5 minutes after open
  skip_last_minutes: 10       # Skip last 10 minutes before close
```

**How It Works:**
- Skips first 5 minutes after market open (9:30-9:35 AM ET)
- Skips last 10 minutes before close (3:50-4:00 PM ET)
- Reduces exposure to opening/closing volatility and slippage
- Crypto trading unaffected (24/7)

**Benefits:**
- ✅ Avoids open/close volatility
- ✅ Better execution quality
- ✅ Reduced slippage

**Code Changes:**
- `src/config.py`: Added `skip_first_minutes` and `skip_last_minutes` to `HoursConfig`
- `src/market_hours.py`: Added `is_in_trading_window()` method
- `src/bot.py`: Uses `is_in_trading_window()` instead of `is_regular_trading_hours()`

---

#### 3. Concurrent Position Limit

**Feature:** Maximum number of simultaneous open positions.

**Configuration:**
```yaml
risk:
  max_concurrent_positions: 5   # Max 5 positions at once
```

**How It Works:**
- Counts current open positions
- If at limit → skips new entry signals
- Allows existing positions to continue
- Opens up when positions close

**Benefits:**
- ✅ Limits portfolio concentration
- ✅ Better risk management
- ✅ Easier to monitor/manage

**Code Changes:**
- `src/config.py`: Added `max_concurrent_positions` to `RiskConfig`
- `src/bot.py`: Added `_check_position_limit_ok()` method
- `src/bot.py`: Position limit check before processing symbols

---

#### 4. Enhanced Metrics API

**Feature:** New `/metrics` endpoint with detailed performance statistics.

**Access:**
```bash
curl http://localhost:8080/metrics | jq .
```

**Returns:**
- Win rate, profit factor, Sharpe ratio
- Max drawdown, average R:R
- Trade counts, activity metrics
- Symbols in cooldown
- Estimated open positions
- Risk metrics

**Benefits:**
- ✅ Better visibility into performance
- ✅ Real-time monitoring
- ✅ Data-driven optimization

**Code Changes:**
- `api_server.py`: Added `/metrics` endpoint
- Returns comprehensive statistics from performance tracker
- Includes 24-hour activity metrics

---

### 📝 Files Modified

**Code:**
- `src/config.py` - Added new config options for safety features
- `src/market_hours.py` - Added `is_in_trading_window()` method
- `src/bot.py` - Added circuit breaker and position limit checks
- `api_server.py` - Added `/metrics` endpoint

**Config:**
- `config.yaml` - Added risk limits and session filters
- `config.crypto.yaml` - Added risk limits (adjusted for crypto volatility)

**Documentation:**
- `docs/ENHANCEMENTS_ROADMAP.md` - Comprehensive enhancement plan (NEW)

---

### 🔄 Deployment

**No database changes required** - just restart the bot:

```bash
# Pull updates
git pull

# Restart bot
./run.sh
```

**Verify it's working:**
```bash
# Check metrics endpoint
curl http://localhost:8080/metrics | jq .

# Check logs for circuit breaker
grep "circuit_breaker\|daily_loss" bot.log | jq .

# Check session filtering
grep "skipping_first_minutes\|skipping_last_minutes" bot.log | jq .
```

---

### ⚙️ Default Settings

**Stock Trading (`config.yaml`):**
- Daily loss limit: 3% or $500
- Skip first 5 minutes after open
- Skip last 10 minutes before close
- Max 5 concurrent positions

**Crypto Trading (`config.crypto.yaml`):**
- Daily loss limit: 5% or $500 (higher volatility tolerance)
- No session filters (24/7 trading)
- Max 8 concurrent positions

**Customize:**
Edit `config.yaml` or `config.crypto.yaml` to adjust limits.

---

### 📊 What's Next?

This is **Phase 1** of the [Enhancement Roadmap](ENHANCEMENTS_ROADMAP.md).

**Coming in future releases:**
- Volume filters (Phase 2)
- ATR-based entry scaling (Phase 2)
- Fixed-risk stop layer (Phase 3)
- Take-profit brackets (Phase 3)
- Correlation guard (Phase 4)
- Alert webhooks (Phase 5)

See [ENHANCEMENTS_ROADMAP.md](ENHANCEMENTS_ROADMAP.md) for the complete plan.

---

## [1.1.0] - 2024-11-21

### 🔧 Trailing Stop Reliability Fix

**Problem:** Trailing stop orders sometimes weren't placed immediately after entry fills, leaving positions unprotected.

**Root Cause:** Used `asyncio.create_task()` which runs in background - if it failed, the error went unnoticed.

**Solution:** Implemented retry logic with up to 3 automatic attempts.

#### Changes Made:
- **`src/bot.py`**: Added `_place_trailing_stop_with_retry()` method
  - Up to 3 retry attempts with 2-second delays
  - Logs every attempt for monitoring
  - Critical alerts if all retries fail
  - Records failure events in database
  
- **`src/state_machine.py`**: Updated `place_trailing_stop_after_entry()` 
  - Now returns `bool` for success/failure detection
  - Enhanced logging

**Code Example:**
```python
# OLD (risky):
asyncio.create_task(place_trailing_stop(...))  # Fire and forget

# NEW (reliable):
async def _place_trailing_stop_with_retry(symbol, qty, price):
    for attempt in range(1, 4):  # Try 3 times
        try:
            success = await place_trailing_stop(...)
            if success:
                return True
        except Exception as e:
            logger.error("attempt_failed", attempt=attempt)
        await asyncio.sleep(2)  # Wait before retry
    logger.critical("POSITION WITHOUT PROTECTION!")  # Alert if all failed
```

**Benefits:**
- ✅ Positions always protected (3 chances to place stop)
- ✅ Clear logging of retry attempts
- ✅ Critical alerts for failures
- ✅ Database audit trail

---

### ⏱️ Extended Cooldown Period

**Problem:** After stop-outs, bot waited only 20 minutes before re-entering, leading to overtrading and revenge trading.

**Root Cause:** Default cooldown was too aggressive (20 minutes for stocks, 30 for crypto).

**Solution:** Extended cooldown to **1 day (1440 minutes)** for both stocks and crypto.

#### Configuration Changes:
- **`config.yaml`**: `after_stopout_minutes: 20` → `1440`
- **`config.crypto.yaml`**: `after_stopout_minutes: 30` → `1440`

**Cooldown Duration:**
- 1 day = 24 hours = 1440 minutes

#### Code Enhancements:
- **`src/state_machine.py`**: Enhanced `on_stop_out()` method
  - Logs cooldown in days, hours, and minutes
  - Shows exact expiration timestamp
  - Better monitoring during cooldown period

**Example Logs:**
```json
{
  "event": "stopout_cooldown_started",
  "cooldown_minutes": 1440,
  "cooldown_hours": 24.0,
  "cooldown_days": 1.0,
  "cooldown_until": "2024-11-22T14:30:00Z"
}
```

**Benefits:**
- ✅ Prevents overtrading
- ✅ Reduces revenge trading
- ✅ Time to analyze why stop triggered
- ✅ Better capital preservation

---

### 📝 Files Modified

- `src/bot.py` - Added retry logic for trailing stops
- `src/state_machine.py` - Enhanced cooldown logging, added return values
- `config.yaml` - Cooldown 20 → 1440 minutes
- `config.crypto.yaml` - Cooldown 30 → 1440 minutes

### 🔄 Deployment

**No database changes required** - just restart the bot:
```bash
./run.sh
```

**Verify it's working:**
```bash
# Check trailing stops placed
grep "trailing_stop_placed_successfully" bot.log | jq .

# Check cooldown is 1 day
grep "cooldown_days" bot.log | jq .
```

---

## [1.0.1] - 2024-11-20

### 🔄 Fill Synchronization Fix

**Problem:** Bot showed **0 fills** even though trades executed on Alpaca. Fills were missed after bot restarts.

**Root Cause:** Bot only detected fills for orders in its in-memory `tracked_orders` dictionary. When restarted, this dictionary was cleared, so historical fills were never detected.

#### Changes Made:

**1. Detect Untracked Fills** (`src/alpaca_client.py`)
- Modified `check_for_events()` to process **ALL filled orders**, not just tracked ones
- Processes historical fills from before restarts

```python
# OLD: Only checked tracked orders
if order.id in self.tracked_orders:
    # process fill

# NEW: Also processes untracked filled orders
elif order.status.value in ['filled', 'partially_filled']:
    wrapper = AlpacaOrder(order, is_tracked=False)
    # process fill even if not tracked
```

**2. Prevent Duplicate Fills** (`src/database.py`)
- Added `fill_exists()` method to check for duplicates
- Updated `add_fill()` to skip duplicates automatically

```python
def fill_exists(self, session: Session, exec_id: str) -> bool:
    return session.query(FillRecord).filter(
        FillRecord.exec_id == exec_id
    ).first() is not None
```

**3. Check Before Processing** (`src/bot.py`)
- Updated `_on_fill()` to verify fill doesn't already exist
- Prevents duplicate database entries and multiple trailing stops

**4. Track Processed Fills** (`src/alpaca_client.py`)
- Added `processed_fills` set to track fills in memory
- Prevents re-processing same fill on every polling cycle

**5. Distinguish Historical vs New** (`src/alpaca_client.py`)
- Added `is_tracked` flag to `AlpacaOrder` wrapper
- Historical fills marked with `is_tracked=False`
- Prevents attempting to place trailing stops for old positions

#### Files Modified:
- `src/alpaca_client.py` - Enhanced event detection, added duplicate tracking
- `src/database.py` - Added `fill_exists()` method
- `src/bot.py` - Added duplicate check before processing fills

**Benefits:**
- ✅ All fills captured, even after restart
- ✅ No duplicate fill records
- ✅ Prevents multiple trailing stops for same entry
- ✅ Backward compatible (no database changes)

**Deployment:**
Just restart the bot - it will automatically sync missed fills from Alpaca:
```bash
./run.sh
```

---

## [1.0.0] - 2024-11-06

### 🚀 Major Platform Migration: IBKR → Alpaca

**Breaking Change:** Migrated from Interactive Brokers (IBKR) to Alpaca Trading API.

#### Why Alpaca?
- ✅ Simpler API (REST vs complex TWS/Gateway)
- ✅ Better paper trading support
- ✅ No local gateway required
- ✅ Easier deployment
- ✅ Better documentation
- ✅ Native crypto support

---

### Added Features

#### 1. Alpaca Integration
- Full Alpaca Trading API support via `alpaca-py` SDK
- Paper trading and live trading modes
- Automatic position and order recovery on restart
- Real-time market data quotes
- Support for stocks and crypto (24/7)

**New File:** `src/alpaca_client.py`
- Replaces `ibkr_client.py`
- Wraps Alpaca Trading API
- Handles order placement, position tracking, fills
- REST API polling for events (every 5 seconds)

#### 2. Security Improvements
- Separate `secrets.yaml` for API keys (not in Git)
- API keys excluded via `.gitignore`
- Environment variable support
- Clear security documentation

**New Files:**
- `secrets.yaml.example` - Template for API keys
- `docs/SETUP_SECRETS.md` - Security setup guide

#### 3. Deployment Features
- Background mode script (`start_background.sh`)
- Systemd service files for Ubuntu (`crazy-trade-bot.service`, `crazy-trade-api.service`)
- Automatic restart on failure
- State recovery after restart
- Process management

#### 4. REST API Server
- Monitoring API on port 8080 (`api_server.py`)
- Endpoints: `/status`, `/performance`, `/fills`, `/orders`
- Read-only for safety
- Remote monitoring support

**New Files:**
- `api_server.py` - Flask-based monitoring API
- `run_api.sh` - Start API server
- `docs/API_GUIDE.md` - API documentation

#### 5. Utility Scripts
- `scripts/reset_paper_account.py` - Reset paper trading account
- `scripts/check_status.py` - Check bot status
- `scripts/show_performance.py` - View P&L and metrics
- `scripts/export_trades.py` - Export trades to CSV
- `test_connection.py` - Test Alpaca API connection

#### 6. Crypto Trading Support
- Native 24/7 crypto trading on Alpaca
- Support for BTC, ETH, DOGE, SHIB, SOL, AVAX, UNI, LINK, and more
- Separate `config.crypto.yaml` for crypto-only trading
- Fractional shares support
- Different entry/stop strategies for crypto volatility

**New Files:**
- `config.crypto.yaml` - Crypto-specific configuration
- `docs/CRYPTO_GUIDE.md` - Complete crypto trading guide
- `docs/CRYPTO_SETUP.md` - Crypto setup instructions
- `docs/CRYPTO_SYMBOLS.md` - Supported crypto pairs
- `docs/CRYPTO_LIMITATIONS.md` - Known limitations
- `test_crypto_symbols.py` - Test crypto symbol support

#### 7. Documentation Overhaul
- Reorganized all documentation in `/docs` directory
- Created comprehensive guides for every aspect
- Added quick start guide
- Deployment guides for Ubuntu and general servers

**New Documentation:**
- `docs/QUICKSTART.md` - 5-minute setup guide
- `docs/BOT_REFERENCE.md` - Complete bot functionality
- `docs/UBUNTU_DEPLOYMENT.md` - Ubuntu deployment
- `docs/SETUP_SECRETS.md` - Security setup
- `docs/INDEX.md` - Documentation index
- `docs/DOC_MAP.md` - Visual documentation map

---

### Changed

#### Configuration
- **`config.yaml`**: Now uses Alpaca settings (removed all IBKR config)
- Simplified structure
- Added `secrets.yaml` for sensitive data
- Separate configs for stocks vs crypto

**Key Changes:**
```yaml
# OLD (IBKR):
ibkr:
  host: "127.0.0.1"
  port: 7497
  client_id: 1

# NEW (Alpaca):
# API keys now in secrets.yaml
mode: "paper"  # or "live"
```

#### Order Handling
- Entry orders placed first
- Trailing stops placed after entry fills (vs OCO in IBKR)
- REST API polling for order events (5-second intervals)
- Compatible with Alpaca's order model

**Order Flow:**
1. Place entry order (buy stop)
2. Poll for fill event
3. When filled → place trailing stop
4. Monitor trailing stop until filled
5. On stop-out → enter cooldown

#### Database
- **Schema unchanged** - existing `bot.db` compatible
- Enhanced UUID support for Alpaca order IDs
- All historical data preserved
- State recovery from database

#### Logging
- Enhanced structured logging with `structlog`
- JSON format for easy parsing
- Better error messages
- More detailed event tracking

---

### Removed

- ❌ IBKR Gateway dependency
- ❌ `ibkr_client.py` (replaced with `alpaca_client.py`)
- ❌ All IBKR-specific configuration
- ❌ TWS/Gateway connection management
- ❌ IBKR market data subscriptions
- ❌ Outdated migration docs

---

### Technical Details

#### Order Flow
```
NO_POSITION → Place entry order (buy stop +5% above last price)
     ↓
ENTRY_PENDING → Monitor for fill
     ↓
Position filled → Place trailing stop (10% trail)
     ↓
POSITION_OPEN → Monitor trailing stop
     ↓
Trailing stop filled → COOLDOWN (1 day)
     ↓
Cooldown expires → Back to NO_POSITION
```

#### Event System
- REST API polling every 5 seconds
- Checks for order updates and fills
- Processes events via callbacks
- Keep-alive ping every 5 minutes

#### State Recovery
- On restart: Query Alpaca for current state
- Sync positions from Alpaca
- Recover order state from database
- Resume monitoring open positions
- Cooldown timers preserved in database

#### Market Data
- Real-time quotes via Alpaca Data API
- Stock data: bid/ask mid-point
- Crypto data: 24/7 availability
- Fallback handling for stale data

---

### Migration Notes

#### For Existing Users

**Database:**
- ✅ Existing `bot.db` remains compatible
- ✅ All historical data preserved
- ✅ No migration scripts needed

**Configuration:**
1. Create `secrets.yaml` from template
2. Add your Alpaca API keys
3. Update `config.yaml` (remove IBKR settings)
4. Restart bot

**Positions:**
- Existing positions managed by Alpaca dashboard
- Bot will track new positions going forward
- Old IBKR positions need manual closure

**Deployment:**
- No more IB Gateway to manage
- Simpler deployment (just Python + Alpaca keys)
- Can run as systemd service on Ubuntu

---

### Breaking Changes

1. **IBKR Not Supported**
   - Must migrate to Alpaca
   - No backward compatibility with IBKR

2. **Configuration Format Changed**
   - Must update `config.yaml`
   - Create new `secrets.yaml`

3. **Order Types Different**
   - Alpaca uses different order model
   - OCO replaced with sequential order placement

4. **No Migration Path**
   - Clean break from IBKR
   - Must close IBKR positions manually
   - Start fresh with Alpaca

---

## Version Scheme

- **Major.Minor.Patch** (e.g., 1.1.0)
- **Major**: Breaking changes or platform switches
- **Minor**: New features, non-breaking changes
- **Patch**: Bug fixes only

---

## Release History

| Version | Date | Description |
|---------|------|-------------|
| 1.2.0 | 2024-11-21 | Safety features: Daily drawdown limit, session filters, position limits |
| 1.1.0 | 2024-11-21 | Trailing stop reliability + extended cooldown |
| 1.0.1 | 2024-11-20 | Fill synchronization fix |
| 1.0.0 | 2024-11-06 | Alpaca platform migration (from IBKR) |

---

## Upgrading

### To v1.2.0 (from v1.1.x)
```bash
git pull
./run.sh  # New safety features auto-enabled
```

### To v1.1.0 (from v1.0.x)
```bash
git pull
./run.sh  # Configs already updated
```

### To v1.0.x (from IBKR version)
```bash
# 1. Close all IBKR positions manually
# 2. Pull latest code
git pull

# 3. Create secrets.yaml
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with your Alpaca API keys

# 4. Update config.yaml (remove IBKR settings)
# 5. Start bot
./run.sh
```

---

## Need Help?

- **Quick commands**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Full documentation**: [INDEX.md](INDEX.md)
- **Reset guide**: [RESET_GUIDE.md](RESET_GUIDE.md)
- **Issues**: Check logs with `tail -f bot.log | jq .`

---

**Happy Trading! 📈**
