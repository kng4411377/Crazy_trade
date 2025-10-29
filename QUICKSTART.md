# Quick Start Guide

Get up and running with Crazy Trade Bot in 5 minutes.

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] IB Gateway downloaded and installed
- [ ] Paper trading or live IBKR account

## Step 1: Setup

```bash
# Run setup script
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Configure IB Gateway

1. **Start IB Gateway**
   - Launch IB Gateway application
   - Login with your credentials

2. **Configure API Settings**
   - Go to: Configure → Settings → API → Settings
   - Enable "Enable ActiveX and Socket Clients"
   - Set Socket Port: `5000`
   - Disable "Read-Only API"
   - Trusted IP: `127.0.0.1`
   - Click OK and restart Gateway

3. **Market Data** (Paper Trading)
   - Paper trading includes free delayed data
   - For real-time data, you need subscriptions

## Step 3: Configure Bot

Edit `config.yaml`:

```yaml
mode: "paper"          # ⚠️ START WITH PAPER!

watchlist:
  - "TSLA"             # Start with 1-2 symbols
  - "NVDA"

allocation:
  per_symbol_usd: 100  # Start small!
  total_usd_cap: 500
```

**Key Settings for Beginners:**
- `mode: "paper"` - Always test first!
- `per_symbol_usd: 100` - Start with tiny positions
- `watchlist` - 2-3 symbols max initially

## Step 4: First Run

```bash
# Start the bot
./run.sh

# Or manually:
python main.py
```

**What to expect:**
```
{"event": "trading_bot_initialized", "mode": "paper", ...}
{"event": "ibkr_connected", "host": "127.0.0.1", ...}
{"event": "entering_main_loop", ...}
```

## Step 5: Monitor

**Open another terminal:**

```bash
# Watch live logs
tail -f bot.log | jq .

# Check database
sqlite3 bot.db "SELECT * FROM state"
sqlite3 bot.db "SELECT * FROM orders ORDER BY created_at DESC LIMIT 5"
```

## Stop the Bot

Press `Ctrl+C` for graceful shutdown.

## Common First-Time Issues

### "Connection refused"
→ IB Gateway not running or wrong port
```bash
# Check config.yaml port matches Gateway
ibkr:
  port: 5000  # Match this to Gateway settings
```

### "No position data available"
→ Normal! Wait for market hours (9:30 AM - 4:00 PM ET)

### "quantity_too_small"
→ Price too high for allocation. Increase `per_symbol_usd` or choose cheaper stocks

### Orders not appearing in TWS
→ Check client ID conflicts. Each bot needs unique `client_id`:
```yaml
ibkr:
  client_id: 12  # Change this if running multiple bots
```

## Testing Checklist

Before going live, verify:

- [ ] Bot connects to IB Gateway successfully
- [ ] Orders appear in TWS/Gateway Activity log
- [ ] Entry orders placed at correct price (+5%)
- [ ] Trailing stops attached to positions
- [ ] Cooldown works after simulated stop-out
- [ ] Orders cancel at market close
- [ ] Database logging works

## Simulate a Trade

1. **Wait for market open** (9:30 AM ET)
2. **Watch for entry order** - Check TWS Activity log
3. **Gap up test** - Order fills when price hits trigger
4. **Verify trailing stop** - Check database:
   ```bash
   sqlite3 bot.db "SELECT * FROM orders WHERE order_type LIKE '%TRAIL%'"
   ```

## Daily Operation

**Morning (before 9:30 AM):**
1. Start IB Gateway
2. Start bot: `./run.sh`
3. Verify connection in logs

**During Market Hours:**
- Monitor logs occasionally
- Check positions in TWS

**After Market Close:**
- Bot auto-cancels unfilled entries
- Positions held with GTC trailing stops
- Safe to leave bot running overnight

## Next Steps

Once comfortable:
1. Increase allocation gradually
2. Add more symbols (up to ~20)
3. Adjust entry/stop percentages
4. Review `bot.db` for performance analysis

## Get Help

```bash
# View recent events
sqlite3 bot.db "SELECT event_type, symbol, ts FROM events ORDER BY ts DESC LIMIT 20"

# Check cooldowns
sqlite3 bot.db "SELECT symbol, cooldown_until_ts FROM state WHERE cooldown_until_ts > datetime('now')"

# View fills
sqlite3 bot.db "SELECT * FROM fills ORDER BY ts DESC LIMIT 10"
```

## Safety Reminder

⚠️ **CRITICAL**:
- Test in paper trading for at least 1 week
- Start with small allocations ($100-$500 total)
- Monitor closely for first few days
- Never risk more than you can afford to lose

---

**You're ready!** Start with paper trading and experiment safely. 🚀

