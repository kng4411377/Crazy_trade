# Quick Start Guide

Get up and running with Crazy Trade Bot in 5 minutes.

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Alpaca Trading account (free)
- [ ] Alpaca API keys generated

## Step 1: Setup

```bash
# Run setup script
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Get Alpaca API Keys

1. **Sign up for Alpaca**
   - Go to https://alpaca.markets/
   - Create a free account
   - Verify your email

2. **Generate API Keys**
   - Log into https://app.alpaca.markets/
   - Navigate to Paper Trading section
   - Click "Generate New Keys" or view existing keys
   - Copy both:
     - **API Key ID**
     - **Secret Key**

3. **Important Notes**
   - Paper trading is completely free
   - Paper keys are separate from live keys
   - Never share your secret key

## Step 3: Configure Bot

Edit `config.yaml`:

```yaml
alpaca:
  api_key: "YOUR_API_KEY_HERE"        # Paste your API key
  secret_key: "YOUR_SECRET_KEY_HERE"  # Paste your secret key

mode: "paper"          # ⚠️ START WITH PAPER!

watchlist:
  - "TSLA"             # Start with 1-2 symbols
  - "NVDA"

allocation:
  total_usd_cap: 20000          # Max capital to deploy
  per_symbol_usd: 1000          # Max per symbol
  min_cash_reserve_percent: 10  # Keep 10% cash

entries:
  type: "buy_stop"
  buy_stop_pct_above_last: 5.0  # Enter at +5%
  tif: "DAY"

stops:
  trailing_stop_pct: 10.0        # 10% trailing stop
  tif: "GTC"

hours:
  calendar: "XNYS"
  allow_pre_market: false        # RTH only
  allow_after_hours: false
```

⚠️ **Security**: Never commit `config.yaml` with real API keys to Git!

## Step 4: Test Connection

```bash
# Quick connection test
python3 test_connection.py
```

Expected output:
```
✅ Connected!
Account Value: $100,000.00
Cash: $100,000.00
...
✅ ALL TESTS PASSED!
```

## Step 5: Start the Bot

```bash
# Start trading bot
./run.sh
```

You should see:
```json
{"event": "alpaca_connected", "account_number": "...", ...}
{"event": "trading_bot_initialized", "num_symbols": 2, ...}
{"event": "entering_main_loop"}
```

## Step 6: Monitor (Optional)

In another terminal, start the API server:

```bash
./run_api.sh
```

Then check status:
```bash
# Check bot status
curl http://localhost:8080/status

# View performance
curl http://localhost:8080/performance

# Recent fills
curl http://localhost:8080/fills
```

Or use your browser:
- http://localhost:8080/status
- http://localhost:8080/performance

## Common Issues

### "Invalid API Key"

**Problem**: Connection fails with authentication error

**Solution**:
1. Verify you copied the full API key and secret
2. Make sure you're using Paper Trading keys if mode is "paper"
3. Check for extra spaces in config.yaml
4. Regenerate keys if needed

### "No Market Data"

**Problem**: Can't fetch prices

**Solution**:
- Paper trading includes real-time data for free
- Verify internet connection
- Check Alpaca service status: https://status.alpaca.markets

### "Orders Not Filling"

**Problem**: Entry orders aren't executing

**Solution**:
- Paper trading uses real market conditions
- Check if market is open (RTH only by default)
- Verify buy stop price is reachable
- Look at recent fills: `curl http://localhost:8080/fills`

## Market Hours

By default, the bot only trades during Regular Trading Hours (RTH):
- **Monday-Friday**: 9:30 AM - 4:00 PM ET
- **Closed**: Weekends and holidays

The bot will:
- ✅ Place orders during RTH
- ❌ Skip trading outside RTH
- ✅ Automatically handle market holidays

## What Happens Next?

Once running, the bot will:

1. **Monitor Prices** - Check symbols every 10 seconds
2. **Place Entry Orders** - Buy Stop at +5% above current price
3. **Wait for Fills** - Entry orders are DAY orders
4. **Place Trailing Stops** - 10% trailing stop after entry fills
5. **Manage Risk** - Cancel unfilled entries at market close
6. **Cooldown** - Wait 20 minutes after stop-outs

## Next Steps

- ✅ Review logs to understand bot behavior
- ✅ Check database: `scripts/show_performance.py`
- ✅ Monitor via API: http://localhost:8080/status
- ✅ Read full documentation: `README.md`
- ✅ Understand configuration: `COMMANDS.md`

## Safety Tips

⚠️ **IMPORTANT**:

1. **Always test in paper mode first** - Don't rush to live trading
2. **Start with 1-2 symbols** - Learn how it works
3. **Use small allocations** - Test with minimal capital
4. **Monitor regularly** - Check logs and performance
5. **Understand the strategy** - Read the full documentation

## Going Live (When Ready)

**Only after extensive paper trading testing:**

1. Set `mode: "live"` in config.yaml
2. Use your **Live Trading** API keys (not paper keys)
3. Start with very small allocations
4. Monitor closely for the first few days

⚠️ **Live trading involves real money and real risk!**

## Need Help?

- Check logs in the console
- Review `TROUBLESHOOTING.md`
- Read `ALPACA_MIGRATION.md` for detailed setup
- Check Alpaca API docs: https://docs.alpaca.markets/

---

**You're all set! Happy trading! 📈**
