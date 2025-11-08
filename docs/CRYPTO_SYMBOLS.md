# 🪙 Alpaca Crypto Symbols Support

This is a **verified** list of cryptocurrency symbols supported on Alpaca (as of November 2024).

## ✅ Top Cryptos Supported (14 out of Top 20)

All symbols use `/USD` pairs for USD trading.

### 🏆 Tier 1 - Most Liquid (Recommended)

| Symbol | Name | Notes |
|--------|------|-------|
| `BTC/USD` | Bitcoin | Most liquid, best for trading |
| `ETH/USD` | Ethereum | Most liquid, best for trading |

### 🚀 Tier 2 - High Volume Altcoins

| Symbol | Name | Notes |
|--------|------|-------|
| `SOL/USD` | Solana | High volume |
| `XRP/USD` | Ripple | High volume |
| `LINK/USD` | Chainlink | DeFi blue chip |
| `LTC/USD` | Litecoin | Established coin |
| `BCH/USD` | Bitcoin Cash | Bitcoin fork |
| `DOT/USD` | Polkadot | Layer 0 protocol |
| `UNI/USD` | Uniswap | DEX token |
| `AVAX/USD` | Avalanche | Layer 1 blockchain |

### ⚠️ Tier 3 - High Volatility (Use with Caution!)

| Symbol | Name | Notes |
|--------|------|-------|
| `DOGE/USD` | Dogecoin | **VERY high volatility!** Meme coin |
| `SHIB/USD` | Shiba Inu | **EXTREME volatility!** Meme coin |

### 💵 Stablecoins

| Symbol | Name | Notes |
|--------|------|-------|
| `USDT/USD` | Tether | USD-pegged stablecoin |
| `USDC/USD` | USD Coin | USD-pegged stablecoin |

## ❌ Top Cryptos NOT Available on Alpaca

| Symbol | Name | Why Not? |
|--------|------|----------|
| `BNB` | Binance Coin | Binance exchange token |
| `ADA` | Cardano | Not supported |
| `TRX` | TRON | Not supported |
| `TON` | Toncoin | Not supported |
| `MATIC` | Polygon | Not supported |
| `ATOM` | Cosmos | Not supported |

## 📊 Alternative Pairs

Some cryptos have multiple trading pairs:

| Crypto | Available Pairs |
|--------|----------------|
| BTC | `BTC/USD`, `BTC/USDC`, `BTC/USDT` |
| ETH | `ETH/USD`, `ETH/USDC`, `ETH/BTC`, `ETH/USDT` |
| DOGE | `DOGE/USD`, `DOGE/USDT`, `DOGE/USDC` |
| SHIB | `SHIB/USD`, `SHIB/USDT`, `SHIB/USDC` |

**Recommendation:** Stick with `/USD` pairs for simplicity.

## 💡 Trading Recommendations

### Conservative Strategy
Start with these low-volatility, high-liquidity pairs:
```yaml
crypto_watchlist:
  - "BTC/USD"    # Bitcoin
  - "ETH/USD"    # Ethereum
  - "SOL/USD"    # Solana
  - "LINK/USD"   # Chainlink
```

### Moderate Strategy
Add some mid-cap altcoins:
```yaml
crypto_watchlist:
  - "BTC/USD"    # Bitcoin
  - "ETH/USD"    # Ethereum
  - "SOL/USD"    # Solana
  - "AVAX/USD"   # Avalanche
  - "UNI/USD"    # Uniswap
  - "LINK/USD"   # Chainlink
```

### Aggressive Strategy (High Risk!)
Include meme coins (requires tight risk management):
```yaml
crypto_watchlist:
  - "BTC/USD"    # Bitcoin (anchor)
  - "ETH/USD"    # Ethereum (anchor)
  - "DOGE/USD"   # Dogecoin ⚠️
  - "SHIB/USD"   # Shiba Inu ⚠️
  - "SOL/USD"    # Solana
```

## ⚙️ Configuration Tips

### For Meme Coins (DOGE, SHIB)
These are **extremely volatile**. Adjust your config:

```yaml
allocation:
  per_symbol_usd: 200       # Lower allocation for meme coins
  
entries:
  buy_stop_pct_above_last: 2.0  # Tighter entry

stops:
  trailing_stop_pct: 15.0   # Wider stops for volatility

cooldowns:
  after_stopout_minutes: 30  # Longer cooldown
```

### For Blue Chips (BTC, ETH)
More stable, can use standard settings:

```yaml
allocation:
  per_symbol_usd: 1000      # Higher allocation for stable coins
  
entries:
  buy_stop_pct_above_last: 3.0

stops:
  trailing_stop_pct: 8.0    # Tighter stops

cooldowns:
  after_stopout_minutes: 15
```

## 🔍 How to Verify Support

Run this command to check current Alpaca crypto availability:

```bash
python check_crypto_support.py
```

(This tool was removed after verification, but you can always check the Alpaca API docs)

## 📚 Additional Resources

- **Alpaca Crypto Docs:** https://alpaca.markets/docs/trading/crypto-trading/
- **Crypto Trading Guide:** See `docs/CRYPTO_GUIDE.md`
- **Quick Setup:** See `docs/CRYPTO_SETUP.md`

---

**Last Updated:** November 8, 2024  
**Total Supported:** 14 out of top 20 cryptos by market cap  
**Verification:** All symbols tested on Alpaca Paper Trading

