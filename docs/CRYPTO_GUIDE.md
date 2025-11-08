# 🪙 Crypto Trading Guide

This bot now supports **cryptocurrency trading** alongside stocks, using the same momentum breakout strategy!

## 🎯 Key Features

- **24/7 Trading**: Crypto markets never close
- **Separate Watchlist**: Keep crypto and stocks organized
- **Same Strategy**: Uses the same buy-stop + trailing-stop approach
- **Fractional Shares**: Trade any amount of crypto
- **Lower Entry Threshold**: Crypto is more volatile, so tighter entries work better

## 🚀 Quick Start

### Option 1: Mixed (Stocks + Crypto)

Use the regular `config.yaml` with both watchlists:

```yaml
# Stock watchlist (trades during market hours only)
watchlist: 
  - "GME"
  - "AMC"

# Crypto watchlist (trades 24/7)
crypto_watchlist:
  - "BTC/USD"
  - "ETH/USD"
  - "DOGE/USD"
```

Run the bot:
```bash
python main.py config.yaml
```

### Option 2: Crypto-Only

Use the dedicated crypto config:

```bash
# Copy and customize
cp config.crypto.yaml my_crypto.yaml

# Edit your crypto watchlist
nano my_crypto.yaml

# Run crypto-only bot
python main.py config.crypto.yaml
```

## ⚙️ Configuration Differences

### Stocks vs Crypto Settings

| Setting | Stocks | Crypto | Why? |
|---------|--------|--------|------|
| **Trading Hours** | 9:30 AM - 4:00 PM EST | 24/7 | Crypto never closes |
| **Entry %** | 5% above last | 3% above last | Crypto moves faster |
| **Trailing Stop** | 10% | 8% | Crypto is more volatile |
| **TIF** | DAY | GTC | No "day" in crypto |
| **Cancel at Close** | Yes | No | No market close |
| **Fractional** | Usually No | Yes | Crypto supports it |
| **Cooldown** | 20 min | 30 min | More time to settle |

### Recommended Crypto Settings

```yaml
crypto_watchlist:
  - "BTC/USD"      # Bitcoin (most liquid)
  - "ETH/USD"      # Ethereum (second largest)
  - "DOGE/USD"     # Meme coin (high volatility)

allocation:
  per_symbol_usd: 500
  per_symbol_override:
    "BTC/USD": 1000    # Allocate more to BTC
    "ETH/USD": 1000    # Allocate more to ETH
  allow_fractional: true  # MUST be true for crypto

entries:
  buy_stop_pct_above_last: 3.0  # Tighter entry
  tif: "GTC"                     # Not DAY
  cancel_at_close: false         # No close

stops:
  trailing_stop_pct: 8.0         # Tighter stop
```

## 📊 Alpaca Crypto Format

Alpaca uses the format `SYMBOL/USD`:
- ✅ `BTC/USD`
- ✅ `ETH/USD`
- ✅ `DOGE/USD`
- ❌ `BTC`
- ❌ `BTCUSD`

The bot will automatically add `/USD` if you forget:
```yaml
crypto_watchlist:
  - "BTC"      # Becomes BTC/USD
  - "ETH/USD"  # Already correct
```

## 🔍 Monitoring

The monitor script shows crypto separately:

```bash
python examples/monitor_bot.py --watch --show-all
```

Output:
```
📊 SYMBOLS (20)
  🟢 GME    - Cooldown: None          # Stock
  🟢 AMC    - Cooldown: None          # Stock
  🟢 BTC/USD - Cooldown: None         # Crypto
  🟢 ETH/USD - Cooldown: None         # Crypto
```

## 💡 Strategy Tips for Crypto

### 1. **Higher Volatility**
Crypto moves fast! Use:
- **Tighter entries**: 2-4% instead of 5%
- **Tighter stops**: 6-10% instead of 10-15%
- **Smaller positions**: $200-500 instead of $1000

### 2. **24/7 Trading**
The bot will trade at night and weekends:
- Check your bot regularly
- Set up alerts
- Use smaller position sizes

### 3. **Best Cryptos for This Strategy**

**High Liquidity (Recommended)**:
- `BTC/USD` - Bitcoin (most liquid)
- `ETH/USD` - Ethereum (second best)
- `MATIC/USD` - Polygon (good volume)

**High Volatility (Risky)**:
- `DOGE/USD` - Dogecoin (meme coin, huge swings)
- `SHIB/USD` - Shiba Inu (extreme volatility)

**Avoid Low Volume**:
- Check Alpaca's supported cryptos
- Stick to top 20 by market cap

### 4. **Fractional Shares**
MUST enable fractional for crypto:
```yaml
allocation:
  allow_fractional: true  # Required!
```

Otherwise you can't trade $500 of BTC at $40,000/BTC!

## 🎯 Example Strategies

### Conservative Crypto
```yaml
crypto_watchlist:
  - "BTC/USD"
  - "ETH/USD"

allocation:
  per_symbol_usd: 1000
  allow_fractional: true

entries:
  buy_stop_pct_above_last: 4.0

stops:
  trailing_stop_pct: 10.0
```

### Aggressive Meme Coins
```yaml
crypto_watchlist:
  - "DOGE/USD"
  - "SHIB/USD"

allocation:
  per_symbol_usd: 200  # Small size!
  allow_fractional: true

entries:
  buy_stop_pct_above_last: 2.0

stops:
  trailing_stop_pct: 6.0
```

### Mixed Portfolio
```yaml
watchlist:
  - "GME"
  - "AMC"

crypto_watchlist:
  - "BTC/USD"
  - "ETH/USD"

allocation:
  per_symbol_usd: 500
  per_symbol_override:
    "BTC/USD": 1000  # More for BTC
```

## ⚠️ Important Notes

### 1. **Paper Trading First**
Always test crypto trading in paper mode:
```yaml
mode: "paper"
```

### 2. **Separate Database**
Use a different database for crypto-only bots:
```yaml
persistence:
  db_url: "sqlite:///bot_crypto.db"
```

### 3. **Alpaca Crypto Requirements**
- ✅ Available in both paper and live trading
- ✅ Trades 24/7
- ✅ Fractional shares supported
- ❌ No options on crypto
- ❌ Limited to Alpaca's supported coins

### 4. **Network Issues**
Crypto API might be slower:
```yaml
polling:
  event_check_seconds: 5  # Check less frequently
  keepalive_seconds: 600  # Longer keepalive
```

## 📈 Performance Tracking

Performance is tracked separately:
- Stock P&L vs Crypto P&L
- Different symbols in reports
- Same overall metrics

View performance:
```bash
curl http://localhost:8080/performance
```

## 🐛 Troubleshooting

### "Symbol not found: BTC"
Add `/USD`:
```yaml
crypto_watchlist:
  - "BTC/USD"  # Not "BTC"
```

### "Fractional shares not allowed"
Enable in config:
```yaml
allocation:
  allow_fractional: true
```

### "Orders not placing"
Check Alpaca supports the crypto:
```python
# In test_connection.py, add:
await client.get_last_price("BTC/USD")
```

### Bot stops overnight
It shouldn't! Crypto trades 24/7. Check:
1. Do you have crypto in watchlist?
2. Is the bot still running?
3. Check logs for errors

## 🚀 Next Steps

1. **Start with paper trading**
   ```bash
   python main.py config.crypto.yaml
   ```

2. **Monitor in real-time**
   ```bash
   python examples/monitor_bot.py --watch --show-all
   ```

3. **Check performance**
   ```bash
   python scripts/show_performance.py
   ```

4. **Export trades**
   ```bash
   python scripts/export_trades.py
   ```

Happy crypto trading! 🪙📈

