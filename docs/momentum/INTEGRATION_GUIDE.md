# 🎯 Momentum Filter Integration Guide

## What is Hybrid Filtering?

**Hybrid Filtering (Option 3)** is the **recommended** approach for integrating the Momentum Intelligence Layer with your trading bot.

### How It Works:
1. You maintain your watchlist in `config.yaml` (full control)
2. Bot filters symbols by momentum scores before trading
3. Only symbols above the threshold are actively traded
4. Filtered-out symbols are logged but not traded

### Benefits:
- ✅ You control the universe (your watchlist)
- ✅ Bot optimizes within that universe (momentum filtering)
- ✅ Best balance of control and automation
- ✅ Clear audit trail of filtered symbols

---

## 📋 Setup Instructions

### Step 1: Enable Momentum Filter

Edit `momentum_config.yaml`:

```yaml
momentum_layer:
  filter:
    enabled: true         # Enable the filter
    min_score: 0.4        # Minimum momentum score (0-1)
    volume_weight: 0.7    # Weight for volume factor
    reddit_weight: 0.3    # Weight for reddit factor
    cache_duration: 3600  # Cache for 1 hour
    require_volume: true  # Require volume data
    require_reddit: false # Reddit data optional
    fail_open: true       # Include symbol on errors
```

### Step 2: Configure Your Watchlist

Your `config.yaml` watchlist remains unchanged:

```yaml
watchlist:
  - TSLA
  - AAPL
  - NVDA
  - AMD
  - MSFT
  - GOOGL
  - META
  - GME
  - AMC
  # Add more symbols...
```

### Step 3: Test the Filter

Before running the bot, test the filter:

```bash
python scripts/test_momentum_filter.py
```

**Expected output:**
```
🧪 TESTING MOMENTUM FILTER
======================================================================

1. Initializing filter...
   ✅ Filter initialized successfully!

2. Filtering 10 symbols...
   Input: ['TSLA', 'AAPL', 'NVDA', ...]

3. Results:
   Input symbols:    10
   Filtered symbols: 7
   Passed:           ['TSLA', 'NVDA', 'AMD', 'MSFT', 'GOOGL', 'META', 'AMC']
   Rejected:         ['AAPL', 'GME', 'PLTR']

4. Filter statistics:
   YFinance available: True
   Apewisdom available: True
   Cache size: 10

✅ Test completed!
```

### Step 4: Run the Bot

Start the bot normally:

```bash
python main.py
```

**The bot will automatically:**
1. Load momentum filter configuration
2. Initialize YFinance and Apewisdom providers
3. Filter your watchlist on startup
4. Log filtered symbols to database
5. Only trade symbols that pass the filter

---

## 📊 Configuration Options

### `min_score` (Threshold)

Controls how selective the filter is:

```yaml
min_score: 0.3  # Very permissive (most symbols pass)
min_score: 0.4  # Balanced (recommended)
min_score: 0.5  # Selective (fewer symbols)
min_score: 0.6  # Very selective (only strong momentum)
```

**Recommendation:** Start with `0.4` and adjust based on results.

---

### `volume_weight` / `reddit_weight`

Controls importance of each factor:

```yaml
# Volume-focused (institutional plays)
volume_weight: 0.8
reddit_weight: 0.2

# Balanced (recommended)
volume_weight: 0.7
reddit_weight: 0.3

# Reddit-focused (meme stocks)
volume_weight: 0.5
reddit_weight: 0.5
```

**Recommendation:** Use `0.7 / 0.3` for balanced approach.

---

### `require_volume` / `require_reddit`

Controls data requirements:

```yaml
# Recommended: Require volume, Reddit optional
require_volume: true
require_reddit: false

# Strict: Require both (fewer symbols)
require_volume: true
require_reddit: true

# Permissive: Either is fine (more symbols)
require_volume: false
require_reddit: false
```

**Recommendation:** Use `require_volume: true, require_reddit: false`

---

### `cache_duration`

How long to cache momentum scores:

```yaml
cache_duration: 1800   # 30 minutes (more updates)
cache_duration: 3600   # 1 hour (recommended)
cache_duration: 7200   # 2 hours (less API calls)
```

**Recommendation:** Use `3600` (1 hour) to balance freshness and API usage.

---

### `fail_open`

What to do when filtering fails:

```yaml
fail_open: true   # Include symbol on error (safe default)
fail_open: false  # Reject symbol on error (stricter)
```

**Recommendation:** Use `true` to avoid missing trades due to transient errors.

---

## 🔍 Monitoring

### Check Logs

The bot logs all filtering decisions:

```bash
# View filter logs
tail -f bot.log | jq 'select(.event | contains("momentum_filter"))'
```

**Key log events:**
- `momentum_filter_config_loaded` - Config loaded
- `momentum_filter_initializing` - Filter starting
- `momentum_filter_initialized` - Filter ready
- `momentum_filter_applying` - Filtering watchlist
- `momentum_filter_pass` - Symbol passed (with scores)
- `momentum_filter_reject` - Symbol rejected (with reason)
- `momentum_filter_applied` - Filtering complete

### Example Log Output

```json
{
  "event": "momentum_filter_pass",
  "symbol": "TSLA",
  "score": 0.52,
  "volume": 0.52,
  "reddit": 0.0
}

{
  "event": "momentum_filter_reject",
  "symbol": "AAPL",
  "reason": "below_threshold",
  "score": 0.35
}

{
  "event": "momentum_filter_applied",
  "original_stocks": 10,
  "filtered_stocks": 7,
  "crypto_count": 0,
  "total_active": 7,
  "filtered_out": ["AAPL", "GME", "PLTR"]
}
```

---

### Query Database

Check filtering history:

```bash
sqlite3 bot.db "SELECT * FROM events WHERE event_type = 'momentum_filter_applied' ORDER BY timestamp DESC LIMIT 5;"
```

---

## 🎯 Trading Workflow

### Bot Startup (One-Time)
1. Bot loads `config.yaml` watchlist
2. Bot loads `momentum_config.yaml` filter settings
3. Bot initializes momentum filter (YFinance + Apewisdom)
4. Bot filters watchlist by momentum scores
5. Bot logs filtered symbols to database
6. Bot trades only active (filtered) symbols

### During Trading
- Bot monitors **only active symbols** (those that passed filter)
- Filtered-out symbols are **completely ignored**
- No orders placed for filtered-out symbols
- Existing positions in filtered-out symbols continue (not force-closed)

### Important Notes:
- **Filtering happens once at startup** (not continuous)
- **To re-filter:** Restart the bot
- **Crypto symbols** bypass the filter (always active)
- **Existing positions** are not affected by filtering

---

## 📈 Example Scenarios

### Scenario 1: Stock Passes Filter
```
Watchlist: TSLA
Filter: min_score=0.4

TSLA momentum score: 0.52 (volume: 0.52, reddit: 0.0)
✅ PASSES - Bot will trade TSLA
```

---

### Scenario 2: Stock Rejected
```
Watchlist: AAPL
Filter: min_score=0.4

AAPL momentum score: 0.35 (volume: 0.35, reddit: 0.0)
❌ REJECTED - Bot will NOT trade AAPL
```

---

### Scenario 3: Mixed Watchlist
```
Watchlist: [TSLA, AAPL, NVDA, AMD, GME]
Filter: min_score=0.4

Results:
  TSLA: 0.52 ✅ PASS
  AAPL: 0.35 ❌ REJECT
  NVDA: 0.68 ✅ PASS
  AMD:  0.45 ✅ PASS
  GME:  0.38 ❌ REJECT

Active symbols: [TSLA, NVDA, AMD]
Bot trades only these 3 symbols
```

---

### Scenario 4: Crypto Always Active
```
Watchlist: [TSLA, BTC/USD]
Filter: min_score=0.4

TSLA: 0.35 ❌ REJECT (stock)
BTC/USD: -- ✅ PASS (crypto bypasses filter)

Active symbols: [BTC/USD]
```

---

## ⚙️ Advanced Configuration

### Disable Filter Temporarily

To disable without editing config:

```yaml
momentum_layer:
  filter:
    enabled: false  # Disable filter, trade all watchlist symbols
```

**Result:** Bot trades entire watchlist (no filtering).

---

### Adjust Threshold On-the-Fly

Edit `momentum_config.yaml` while bot is **stopped**:

```yaml
min_score: 0.3  # Lower threshold = more symbols pass
```

Then restart bot to apply new threshold.

---

### Volume-Only Filtering

Ignore Reddit, use only volume:

```yaml
volume_weight: 1.0
reddit_weight: 0.0
require_volume: true
require_reddit: false
```

**Use case:** Institutional plays, ignore meme stocks.

---

### Reddit-Focused Filtering

Prioritize Reddit sentiment:

```yaml
volume_weight: 0.3
reddit_weight: 0.7
require_volume: false
require_reddit: true
```

**Use case:** Meme stock trading, r/wallstreetbets plays.

---

## 🔧 Troubleshooting

### Filter Not Working

**Symptoms:** Bot trades all symbols, ignoring filter.

**Check:**
```bash
# 1. Is filter enabled?
grep "enabled: true" momentum_config.yaml

# 2. Check bot logs
tail -f bot.log | grep momentum_filter

# 3. Test filter directly
python scripts/test_momentum_filter.py
```

**Common causes:**
- `filter.enabled: false` in config
- `momentum_config.yaml` not found
- Filter initialization failed (check logs)

---

### All Symbols Rejected

**Symptoms:** No active symbols after filtering.

**Check:**
```bash
# View filter logs
tail -f bot.log | jq 'select(.event == "momentum_filter_applied")'
```

**Common causes:**
- `min_score` too high (try lowering to 0.3)
- Market closed (no volume data)
- Apewisdom data stale (wait for 9 AM / 9 PM update)

**Solution:**
```yaml
# Lower threshold
min_score: 0.3

# Or disable filter temporarily
enabled: false
```

---

### YFinance Unavailable

**Symptoms:** All stocks rejected with "no_volume_data".

**Check:**
```bash
python scripts/test_momentum_filter.py
```

**Solution:**
- Check internet connection
- Verify yfinance installed: `pip list | grep yfinance`
- Try updating: `pip install --upgrade yfinance`

---

### Apewisdom Unavailable

**Symptoms:** Reddit scores all 0.0, but filter still works.

**This is normal!** Reddit data is optional. Filter uses volume scores.

**Note:** Apewisdom updates 2x daily (9 AM / 9 PM EST). Data may be stale.

---

## 📚 Best Practices

### 1. Start Conservative
```yaml
min_score: 0.4     # Not too strict
require_reddit: false  # Optional
fail_open: true    # Safe default
```

### 2. Monitor First Week
- Check logs daily
- Review filtered symbols
- Adjust threshold if needed

### 3. Tune Threshold
- **Too many rejections?** Lower `min_score`
- **Too many weak signals?** Raise `min_score`
- **Missing meme stocks?** Increase `reddit_weight`

### 4. Periodic Review
- Review filter performance weekly
- Check which symbols are consistently rejected
- Remove permanently weak symbols from watchlist

### 5. Combine with Manual Scans
```bash
# Run scan before trading day
python scripts/scan_momentum.py --mode max --top 20

# Update config.yaml watchlist based on results
# Restart bot to re-filter
```

---

## 🎓 Understanding Filter Behavior

### What Gets Filtered?
- ✅ **Stock symbols** in `config.yaml` watchlist
- ❌ **Crypto symbols** (always active, bypass filter)

### When Does Filtering Happen?
- **Once** at bot startup
- **Not continuous** during trading
- **To re-filter:** Restart bot

### What Happens to Filtered Symbols?
- **Not traded** (no new orders)
- **Logged** to database and logs
- **Existing positions continue** (not force-closed)
- **Not monitored** by state machines

### What is the Composite Score?
```
composite_score = MAX(volume_score, reddit_score)
```

Uses **MAX aggregation** (like the scanner) to catch stocks strong in **any** factor.

**Example:**
```
Symbol: TSLA
  Volume score: 0.52
  Reddit score: 0.0
  Composite: MAX(0.52, 0.0) = 0.52 ✅ PASSES (if min_score=0.4)
```

---

## 🚀 Next Steps

1. ✅ **Test the filter:** `python scripts/test_momentum_filter.py`
2. ✅ **Enable in config:** Set `filter.enabled: true`
3. ✅ **Start bot:** `python main.py`
4. ✅ **Monitor logs:** Check filtering results
5. ✅ **Tune settings:** Adjust threshold as needed

---

**The hybrid filter is now integrated and ready to use!** 🎯

For more information:
- **Strategy Guide:** `docs/momentum/STRATEGY.md`
- **Scanner Usage:** `scripts/scan_momentum.py --help`
- **Provider Setup:** `docs/momentum/APEWISDOM_SETUP.md`

