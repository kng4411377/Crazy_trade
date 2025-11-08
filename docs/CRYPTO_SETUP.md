# 🚀 Quick Crypto Setup

Your bot now supports crypto trading! Here's how to get started:

## ✅ What's Been Added

1. **Separate `crypto_watchlist`** in `config.yaml`
2. **24/7 trading** for crypto symbols
3. **Auto-detection** - symbols with `/` are crypto
4. **Config validation** - auto-adds `/USD` suffix
5. **API updates** - shows crypto separately in status
6. **Crypto-only config** - `config.crypto.yaml`

## 🎯 Quick Start

### Option 1: Add Crypto to Existing Config

Edit `config.yaml`:

```yaml
# Your existing stock watchlist
watchlist: 
  - "GME"
  - "AMC"
  # ... your stocks

# NEW: Add crypto watchlist
crypto_watchlist:
  - "BTC/USD"      # Bitcoin
  - "ETH/USD"      # Ethereum
  - "DOGE/USD"     # Dogecoin
  - "SHIB/USD"     # Shiba Inu
```

**Important**: Set `allow_fractional: true` for crypto:
```yaml
allocation:
  allow_fractional: true  # Required for crypto!
```

Run normally:
```bash
python main.py config.yaml
```

### Option 2: Crypto-Only Bot

Use the dedicated crypto config:

```bash
# Use the crypto-only config
python main.py config.crypto.yaml
```

This config:
- ✅ Has no stocks (empty `watchlist`)
- ✅ Only crypto symbols
- ✅ Optimized settings for crypto
- ✅ Uses separate database (`bot_crypto.db`)

## 📊 Key Differences: Stocks vs Crypto

| Feature | Stocks | Crypto |
|---------|--------|--------|
| **Trading Hours** | 9:30 AM - 4:00 PM EST | 24/7 |
| **Market Close** | Yes (orders cancelled) | No close |
| **Fractional Shares** | Usually No | YES (required!) |
| **Entry %** | 5% recommended | 3% recommended |
| **Stop %** | 10% recommended | 8% recommended |
| **Symbol Format** | `GME` | `BTC/USD` |

## ⚙️ Recommended Settings for Crypto

```yaml
crypto_watchlist:
  - "BTC/USD"
  - "ETH/USD"
  - "DOGE/USD"

allocation:
  per_symbol_usd: 500          # Smaller positions
  allow_fractional: true       # REQUIRED!

entries:
  buy_stop_pct_above_last: 3.0 # Tighter entry
  tif: "GTC"                    # Not DAY
  cancel_at_close: false        # No close

stops:
  trailing_stop_pct: 8.0        # Tighter stop
```

## 🔍 Test It

1. **Load config**:
```bash
python -c "from src.config import BotConfig; config = BotConfig.from_yaml('config.yaml'); print('Crypto:', config.crypto_watchlist)"
```

2. **Run bot**:
```bash
python main.py config.yaml
```

You should see:
```json
{"num_stocks": 17, "num_crypto": 4, "total_symbols": 21}
```

3. **Monitor**:
```bash
python examples/monitor_bot.py --watch --show-all
```

## 📈 Supported Cryptos on Alpaca

Check current list: https://alpaca.markets/support/crypto-wallet-supported-currencies/

Popular ones:
- `BTC/USD` - Bitcoin
- `ETH/USD` - Ethereum
- `DOGE/USD` - Dogecoin
- `SHIB/USD` - Shiba Inu
- `MATIC/USD` - Polygon
- `AVAX/USD` - Avalanche
- `UNI/USD` - Uniswap
- `LINK/USD` - Chainlink

## ⚠️ Important Notes

### 1. **Always Enable Fractional Shares**
```yaml
allocation:
  allow_fractional: true
```
Otherwise you can't trade $500 of BTC at $40,000/coin!

### 2. **Use GTC Orders**
```yaml
entries:
  tif: "GTC"  # Not "DAY"
```
Crypto has no "day" - it's 24/7.

### 3. **Start with Paper Trading**
```yaml
mode: "paper"
```
Test crypto trading before going live!

### 4. **Symbol Format**
Use `BTC/USD` not `BTC` or `BTCUSD`:
```yaml
crypto_watchlist:
  - "BTC/USD"  # ✅ Correct
  - "BTC"      # ✅ Also works (auto-converts)
  - "BTCUSD"   # ❌ Wrong format
```

## 🎯 Example Configurations

### Conservative (BTC + ETH Only)
```yaml
watchlist: []  # No stocks
crypto_watchlist:
  - "BTC/USD"
  - "ETH/USD"

allocation:
  per_symbol_usd: 1000
  allow_fractional: true

stops:
  trailing_stop_pct: 10.0  # Wider stop
```

### Aggressive (Meme Coins)
```yaml
watchlist: []
crypto_watchlist:
  - "DOGE/USD"
  - "SHIB/USD"

allocation:
  per_symbol_usd: 200  # Smaller size!
  allow_fractional: true

entries:
  buy_stop_pct_above_last: 2.0

stops:
  trailing_stop_pct: 6.0  # Tight stop
```

### Mixed Portfolio
```yaml
watchlist:
  - "GME"
  - "AMC"
  - "TSLA"

crypto_watchlist:
  - "BTC/USD"
  - "ETH/USD"

allocation:
  per_symbol_usd: 500
  per_symbol_override:
    "BTC/USD": 1000  # More for Bitcoin
```

## 📚 Full Documentation

See **[CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)** for complete crypto trading guide!

## 🐛 Troubleshooting

**"Watchlist must contain at least one symbol"**
- Add crypto to `crypto_watchlist` if `watchlist` is empty

**"Fractional shares not allowed"**
- Set `allow_fractional: true`

**"Symbol not found"**
- Use correct format: `BTC/USD` not `BTC`
- Check Alpaca supports the crypto

**Bot stops overnight**
- Crypto should trade 24/7
- Check you have crypto in `crypto_watchlist`
- Check logs for errors

## 🚀 Ready to Trade!

1. Edit `config.yaml` and add crypto symbols
2. Set `allow_fractional: true`
3. Run: `python main.py config.yaml`
4. Monitor: `python examples/monitor_bot.py --watch --show-all`

Happy crypto trading! 🪙📈

