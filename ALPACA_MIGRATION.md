# Migration Guide: IBKR to Alpaca Trading

This guide helps you migrate your trading bot from IBKR Gateway to Alpaca Trading API.

## 🎯 Overview

The bot has been completely migrated to use **Alpaca Trading API** instead of Interactive Brokers (IBKR) Gateway. Alpaca offers:

- ✅ **Paper Trading for Free** - Test with real-time data without risking capital
- ✅ **Simple REST API** - No complex gateway setup
- ✅ **Commission-Free Trading** - No commission on stocks
- ✅ **Easy Setup** - Just API keys, no local gateway required
- ✅ **Cloud-Ready** - Perfect for running on remote servers

## 📋 Prerequisites

### 1. Create Alpaca Account

1. Go to [Alpaca](https://alpaca.markets/)
2. Sign up for a free account
3. Complete verification (if needed for live trading)

### 2. Get API Keys

1. Log into [Alpaca Dashboard](https://app.alpaca.markets/)
2. Navigate to **Paper Trading** section
3. Generate API keys:
   - **API Key ID** 
   - **Secret Key**
   
⚠️ **Security**: Keep your secret key secure! Never commit it to version control.

## 🔧 Migration Steps

### Step 1: Update Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate

# Install new dependencies
pip install -r requirements.txt
```

### Step 2: Update Configuration

Edit your `config.yaml`:

**OLD (IBKR):**
```yaml
ibkr:
  host: "localhost"
  port: 5000
  client_id: 12
  account: null
```

**NEW (Alpaca):**
```yaml
alpaca:
  api_key: "YOUR_ALPACA_API_KEY"
  secret_key: "YOUR_ALPACA_SECRET_KEY"
```

### Step 3: Update Environment Variables (Optional but Recommended)

For better security, use environment variables:

```bash
# Add to your .env file or shell profile
export ALPACA_API_KEY="your_api_key_here"
export ALPACA_SECRET_KEY="your_secret_key_here"
```

Then update `config.yaml`:
```yaml
alpaca:
  api_key: "${ALPACA_API_KEY}"
  secret_key: "${ALPACA_SECRET_KEY}"
```

### Step 4: Remove Old IBKR Files (Optional)

The old IBKR client is no longer used:
```bash
# Optional cleanup
rm src/ibkr_client.py
```

### Step 5: Test Connection

```bash
python3 -c "
from alpaca.trading.client import TradingClient
client = TradingClient('YOUR_API_KEY', 'YOUR_SECRET_KEY', paper=True)
print('✅ Connection successful!')
print(f'Account: {client.get_account()}')
"
```

## 🆕 Key Differences

### Order Handling

**IBKR:**
- Used bracket orders with entry + trailing stop
- Immediate child order attachment

**Alpaca:**
- Entry order placed first
- Trailing stop placed **after** entry fills
- Handled automatically by the bot

### Event System

**IBKR:**
- Event-driven via Gateway connection
- Real-time order updates

**Alpaca:**
- REST API polling (every 5 seconds by default)
- Configured via `polling.event_check_seconds`

### Market Data

**IBKR:**
- Real-time data through Gateway

**Alpaca:**
- Free real-time data for paper trading
- Uses latest quotes for pricing

## 📊 Updated Configuration Options

New polling setting for Alpaca:

```yaml
polling:
  price_seconds: 10        # Price check interval
  orders_seconds: 15       # Order status check interval  
  keepalive_seconds: 300   # Keep-alive ping
  event_check_seconds: 5   # NEW: Alpaca order event polling
```

## ✅ Verification Checklist

Before going live, verify:

- [ ] Alpaca API keys are configured
- [ ] `mode: "paper"` is set for testing
- [ ] Bot connects successfully
- [ ] Entry orders are placed correctly
- [ ] Trailing stops are created after fills
- [ ] Stop-outs trigger cooldown
- [ ] API server shows correct data

## 🚀 Running the Bot

```bash
# Start the trading bot
./run.sh

# In another terminal, start the API server (optional)
./run_api.sh
```

## 🔍 Monitoring

The API server works the same way:

```bash
# Check status
curl http://localhost:8080/status

# View performance
curl http://localhost:8080/performance

# Recent fills
curl http://localhost:8080/fills
```

## ⚠️ Important Notes

### Paper vs Live Trading

- **Paper Trading**: Uses `mode: "paper"` - connects to Alpaca paper endpoint
- **Live Trading**: Uses `mode: "live"` - connects to real trading endpoint

⚠️ Always test thoroughly in paper mode first!

### Order Types

Alpaca supports:
- ✅ Market orders
- ✅ Limit orders
- ✅ Stop orders
- ✅ Stop-limit orders
- ✅ Trailing stop orders

### Fractional Shares

Alpaca supports fractional shares:
```yaml
allocation:
  allow_fractional: true  # Enable fractional trading
```

### Rate Limits

Alpaca API limits:
- 200 requests per minute per API key
- The bot's polling intervals are designed to stay well under this limit

## 🆘 Troubleshooting

### "Invalid API Key"
- Verify you're using the correct paper/live keys
- Check for extra spaces in config.yaml

### "Connection Failed"
- Verify internet connectivity
- Check Alpaca service status: https://status.alpaca.markets

### Orders Not Filling
- Paper trading uses real market data
- Orders follow normal market rules (market hours, limit prices, etc.)

### Missing Trailing Stop
- Trailing stops are placed after entry fills
- Check logs for `trailing_stop_placed_after_entry` events

## 📚 Additional Resources

- [Alpaca API Documentation](https://docs.alpaca.markets/docs/trading-api)
- [Alpaca Python SDK](https://github.com/alpacahq/alpaca-py)
- [Paper Trading Dashboard](https://app.alpaca.markets/paper/dashboard/overview)

## 🤝 Support

If you encounter issues:

1. Check the bot logs for errors
2. Review Alpaca API documentation
3. Verify your configuration matches this guide
4. Test with a simple symbol list first

## 🎉 Benefits of Alpaca

- **No Gateway Required**: No need to run IBKR Gateway locally
- **Cloud-Friendly**: Easy to deploy on cloud servers
- **Better API**: Modern REST API with great Python SDK
- **Free Paper Trading**: Unlimited paper trading with real-time data
- **Active Community**: Large community and good documentation

---

**Migration Complete!** Your bot is now running on Alpaca's modern trading infrastructure. 🚀

