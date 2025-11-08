# 🔧 Crypto Trading Fixes - Summary

## ✅ Issues Fixed (November 8, 2024)

### 1. **Invalid Order Type Error** ✅
**Problem:**
```json
{"error": "invalid order type for crypto order"}
```

**Root Cause:**  
Alpaca crypto does NOT support:
- Stop orders
- Stop-limit orders  
- Trailing stop orders

**Solution:**  
Modified `src/alpaca_client.py` to:
- Auto-detect crypto symbols (contains `/`)
- Use **limit orders** for crypto entries (instead of stop orders)
- Use **fixed stop-loss limit orders** for crypto exits (instead of trailing stops)

**Code Changes:**
- Updated `place_entry_with_trailing_stop()` - lines 165-257
- Updated `place_trailing_stop()` - lines 259-340
- Added `LimitOrderRequest` import

---

### 2. **Account Summary Error** ✅
**Problem:**
```json
{"error": "unsupported operand type(s) for -: 'str' and 'str'"}
```

**Root Cause:**  
`account.equity` and `account.last_equity` were strings, not floats. The code tried to subtract them before converting to float.

**Solution:**  
Modified `get_account_summary()` to:
- Convert to float BEFORE subtracting
- Add None checks for all account attributes
- Wrap in try/except for robustness

**Code Changes:**
- Updated `get_account_summary()` - lines 519-538
- Updated `get_positions()` - lines 373-391 (similar safety improvements)

---

### 3. **Crypto Price Fetching Error** ✅
**Problem:**
```json
{"error": "invalid symbol: BTC/USD"}
```

**Root Cause:**  
Code was using `StockHistoricalDataClient` for all symbols, including crypto.

**Solution:**  
Modified `get_last_price()` to:
- Detect crypto symbols (contains `/`)
- Use `CryptoHistoricalDataClient` for crypto
- Use `StockHistoricalDataClient` for stocks

**Code Changes:**
- Updated `get_last_price()` - previously fixed
- Added `crypto_data_client` initialization in `__init__()`

---

## 🪙 Crypto Support Status

### Supported Cryptos (14 out of top 20)
✅ **Working:** BTC, ETH, DOGE, SHIB, SOL, XRP, LINK, LTC, BCH, DOT, UNI, AVAX, USDT, USDC  
❌ **Not Available:** BNB, ADA, TRX, TON, MATIC, ATOM

### Trading Mechanism

| Aspect | Stocks | Crypto |
|--------|--------|--------|
| **Entry** | Stop orders (breakout) | Limit orders (breakout price) |
| **Exit** | Trailing stops (dynamic) | Fixed stop-loss (static) |
| **Hours** | Market hours only | 24/7 |
| **Fractional** | Optional | Required |

---

## 📝 Important Limitations

### ⚠️ Crypto Does NOT Have Trailing Stops
- **Stock:** Trailing stop automatically adjusts as price rises (locks in gains)
- **Crypto:** Fixed stop-loss at entry - X% (does NOT trail!)

**Example:**
- Buy BTC at $100,000
- Stop-loss placed at $92,000 (8% below entry)
- If BTC goes to $120,000, stop-loss STAYS at $92,000 ❌
- (Stock trailing stop would have moved to ~$110,000 ✅)

### 💡 Workarounds
1. **Manual Trailing:** Periodically cancel and replace stop-loss at higher price
2. **Accept Fixed Stops:** Simpler but may leave money on table
3. **Market Order Exits:** Bot monitors price and uses market orders when threshold hit (future enhancement)

---

## 🚀 How to Use

### Start Trading Crypto + Stocks
```bash
./run.sh  # Uses config.yaml (17 stocks + 4 cryptos)
```

### Start Crypto-Only Trading
```bash
python main.py config.crypto.yaml  # Crypto only (BTC, ETH, DOGE, SHIB, SOL, etc.)
```

### Current Config
Your `config.yaml` now has:
- **17 stock symbols** (market hours)
- **4 crypto symbols** (24/7):
  - BTC/USD ✅
  - ETH/USD ✅
  - DOGE/USD ✅
  - SHIB/USD ✅

---

## 📚 Documentation Created

1. **[docs/CRYPTO_SYMBOLS.md](docs/CRYPTO_SYMBOLS.md)** - Full list of supported cryptos
2. **[docs/CRYPTO_LIMITATIONS.md](docs/CRYPTO_LIMITATIONS.md)** - Order type limitations and workarounds
3. **[docs/CRYPTO_GUIDE.md](docs/CRYPTO_GUIDE.md)** - Complete crypto trading guide
4. **[docs/CRYPTO_SETUP.md](docs/CRYPTO_SETUP.md)** - Quick setup guide

---

## 🧪 Test Results

All tests passed ✅:
- ✅ Crypto symbol detection (BTC/USD, ETH/USD identified as crypto)
- ✅ Stock symbol detection (TSLA, AAPL identified as stocks)
- ✅ Crypto price fetching (BTC/USD: $102,595.77)
- ✅ Account summary (no more string subtraction errors)
- ✅ Positions fetching (safe None handling)

---

## 🔮 Future Enhancements

### Smart Trailing Script (Recommended)
Create a background script that:
1. Monitors crypto positions every N seconds
2. Gets current price
3. Cancels old stop-loss if price has risen significantly
4. Places new stop-loss at higher price
5. Mimics true trailing stop behavior

**Benefits:** Much better performance for crypto trending moves  
**Complexity:** Moderate (would need separate monitoring process)

---

## 🎯 Recommended Settings

For optimal crypto trading with fixed stops:

```yaml
entries:
  buy_stop_pct_above_last: 2.0  # Tighter entries for crypto

stops:
  trailing_stop_pct: 12.0  # Wider stops for crypto volatility

allocation:
  per_symbol_usd: 500  # Lower allocation due to volatility
  allow_fractional: true  # REQUIRED for crypto!

cooldowns:
  after_stopout_minutes: 30  # Longer cooldown for crypto
```

---

## ✅ Summary

**All crypto issues are FIXED!** 🎉

Your bot can now:
- ✅ Trade 14 different cryptocurrencies
- ✅ Trade 24/7 (no market hours restriction)
- ✅ Use limit orders for entries (crypto-compatible)
- ✅ Use fixed stop-loss for exits (crypto-compatible)
- ✅ Mix crypto and stock trading simultaneously
- ✅ Handle account summary safely
- ✅ Fetch crypto prices correctly

**Ready to trade!** 🚀

---

**Files Modified:**
- `src/alpaca_client.py` - Order types, price fetching, account summary
- `config.yaml` - Added DOGE/USD and SHIB/USD
- `config.crypto.yaml` - Updated with verified crypto list
- `docs/DOCUMENTATION.md` - Added crypto references
- `docs/CRYPTO_SYMBOLS.md` - New (verified crypto list)
- `docs/CRYPTO_LIMITATIONS.md` - New (explains limitations)

**Last Updated:** November 8, 2024, 8:00 PM PST  
**Status:** ✅ All issues resolved, bot ready for crypto trading

