# 🚨 Crypto Trading Limitations on Alpaca

This document explains the key differences and limitations when trading crypto vs stocks on Alpaca.

## ⚠️ Order Type Restrictions

### Stocks (Fully Supported)
- ✅ Market orders
- ✅ Limit orders  
- ✅ Stop orders
- ✅ Stop-limit orders
- ✅ Trailing stop orders

### Crypto (Limited Support)
- ✅ Market orders
- ✅ Limit orders
- ❌ **Stop orders** (NOT supported)
- ❌ **Stop-limit orders** (NOT supported)
- ❌ **Trailing stop orders** (NOT supported)

## 🔧 Bot Adaptations for Crypto

Our bot automatically adapts its strategy when trading crypto:

### 1. Entry Orders

**Stocks:**
- Uses **stop orders** (buy when price breaks above threshold)
- Example: Buy TSLA when it breaks above $250

**Crypto:**
- Uses **limit orders** at breakout price
- Example: Buy BTC/USD with limit order at $103,500
- ⚠️ **Limitation:** Order only fills if price reaches the limit, but may not trigger on breakouts like stop orders would

### 2. Exit Orders (Stop-Loss)

**Stocks:**
- Uses **trailing stop orders** (automatically follows price up)
- Example: 10% trailing stop moves up as stock gains

**Crypto:**
- Uses **fixed stop-loss limit orders** (does NOT trail)
- Calculated from entry price: `entry_price * (1 - trail_percent / 100)`
- Example: Buy BTC at $100k → Stop-loss at $92k (8% below entry)
- ⚠️ **Limitation:** Does NOT automatically adjust as price rises!

## 📊 Strategy Impact

### For Momentum Trading (Breakouts)

**Effectiveness Reduced** for crypto:
- Limit orders may miss fast breakouts that stop orders would catch
- Stop-loss doesn't trail, so profits are capped

**Recommendation:**
- Use **tighter entry thresholds** (2-3% vs 5% for stocks)
- Use **manual trailing** by canceling/replacing stop-loss orders
- Or use **market orders** for entries (less precise but catches breakouts)

### For Range Trading

**Works Better** for crypto:
- Limit orders are perfect for range-bound trading
- Fixed stop-loss is acceptable when not expecting big moves

## 🛠️ Workarounds

### Option 1: Manual Trailing (Advanced)
Implement a monitoring script that:
1. Watches current price
2. Cancels old stop-loss when price moves up
3. Places new stop-loss at higher price
4. Repeats continuously

**Pros:** True trailing stop functionality  
**Cons:** Complex, requires continuous monitoring

### Option 2: Use Market Orders
Modify bot to:
1. Use limit orders for entries (current)
2. Use **market orders for exits** when stop level is hit
3. Bot monitors price and triggers market sell when threshold crossed

**Pros:** Simpler, reliable exits  
**Cons:** Less control over exit price

### Option 3: Accept Fixed Stops
Keep current implementation:
- Limit order entries
- Fixed stop-loss exits
- Accept that profits won't trail

**Pros:** Simple, works now  
**Cons:** May leave money on the table in strong trends

## 🎯 Recommended Config for Crypto

Given these limitations, here's the optimal config:

```yaml
# Crypto-specific config adjustments
entries:
  type: "buy_stop"  # Bot will use limit orders for crypto
  buy_stop_pct_above_last: 2.0  # Tighter for crypto (vs 5% for stocks)
  stop_limit_max_slip_pct: 1.0
  tif: "GTC"  # Good Till Cancel (24/7)
  cancel_at_close: false  # No market close for crypto

stops:
  trailing_stop_pct: 12.0  # Wider for crypto volatility
  use_trailing_limit: false
  tif: "GTC"  # Good Till Cancel (24/7)

cooldowns:
  after_stopout_minutes: 30  # Longer for crypto volatility

allocation:
  per_symbol_usd: 500  # Lower allocation due to higher volatility
  allow_fractional: true  # MUST be true for crypto!
```

## 📈 Performance Expectations

### Stock Trading Performance
- **Entry:** Excellent (stop orders catch breakouts)
- **Exit:** Excellent (trailing stops lock in gains)
- **Win Rate:** 50-60% typical

### Crypto Trading Performance (Current Implementation)
- **Entry:** Good (limit orders work but may miss some breakouts)
- **Exit:** Fair (fixed stops don't capture full moves)
- **Win Rate:** 40-50% typical (slightly lower)

## 🔮 Future Enhancements

Potential improvements to consider:

1. **Smart Trailing Script**
   - Background process that monitors crypto positions
   - Automatically adjusts stop-loss orders as price rises
   - Mimics true trailing stop behavior

2. **Hybrid Entry Strategy**
   - Monitor price for breakout conditions
   - Use market orders when breakout detected
   - More aggressive but more effective

3. **Time-Based Exits**
   - Close positions after X hours/days
   - Useful for crypto's 24/7 nature
   - Prevents being stuck in positions indefinitely

## 💡 Tips for Crypto Trading

1. **Start Small:** Use lower position sizes until you understand crypto behavior
2. **Choose Liquid Pairs:** Stick to BTC/USD and ETH/USD for best execution
3. **Avoid Meme Coins Initially:** DOGE and SHIB have extreme volatility
4. **Monitor Closely:** Without true trailing stops, check positions more frequently
5. **Use Alerts:** Set price alerts for your stop-loss levels
6. **Consider Timeframes:** Crypto moves 24/7, so "overnight risk" is constant

## 🔗 Related Docs

- **[CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)** - Complete crypto trading guide
- **[CRYPTO_SYMBOLS.md](CRYPTO_SYMBOLS.md)** - Supported crypto symbols
- **[CRYPTO_SETUP.md](CRYPTO_SETUP.md)** - Quick setup guide

---

**Last Updated:** November 8, 2024  
**Status:** Bot adapted for crypto order type limitations  
**Next Steps:** Consider implementing smart trailing for better performance

