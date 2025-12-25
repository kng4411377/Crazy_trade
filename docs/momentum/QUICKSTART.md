# Momentum Layer Quick Start (v2 - Multi-Factor)

**Updated**: December 22, 2025  
**Status**: ✅ Production Ready (FREE Providers Only)

---

## 🎯 What You Get

### Two FREE Momentum Factors:

1. **Volume Anomaly** (YFinance)
   - Unusual trading volume detection
   - RVOL (Relative Volume) analysis
   - Volume trend momentum

2. **Retail Attention** (Google Trends) 🆕
   - Retail investor FOMO detection
   - Search interest breakouts
   - Viral momentum prediction

### Combined Power:
- **Volume** = Confirms what's happening NOW
- **Retail** = Predicts what's coming NEXT
- **Together** = Best momentum signals!

---

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
pip install yfinance pytrends
```

### 2. Copy Config
```bash
cp momentum_config.yaml.example momentum_config.yaml
```

### 3. Enable Factors
Edit `momentum_config.yaml`:
```yaml
momentum_layer:
  enabled: true
  
  factors:
    volume_anomaly:
      enabled: true
      weight: 0.50
    
    retail_attention:  # NEW!
      enabled: true
      weight: 0.50
  
  providers:
    yfinance:
      enabled: true
    
    google_trends:  # NEW!
      enabled: true
```

### 4. Test It
```bash
python examples/momentum_example.py
```

### 5. Run Bot
```bash
python main.py
```

---

## 🧪 Quick Test

```bash
# All-in-one install and test
./INSTALL_GOOGLE_TRENDS.sh

# Or step by step
pip install pytrends
python scripts/test_google_trends.py
```

**Expected Output:**
```
TSLA:
  Volume Score:  0.756
  Retail Score:  0.645
  Composite:     0.701  🔥

GME:
  Volume Score:  0.823
  Retail Score:  0.912  🔥 (Breakout!)
  Composite:     0.868  🔥🔥
```

---

## 📊 Factor Weight Strategies

### Conservative (Volume-Heavy)
```yaml
volume_anomaly: 0.70
retail_attention: 0.30
```
**Best for**: Lower risk, confirmed momentum

### Balanced (Recommended)
```yaml
volume_anomaly: 0.50
retail_attention: 0.50
```
**Best for**: Mix of confirmation + prediction

### Aggressive (Retail-Heavy)
```yaml
volume_anomaly: 0.30
retail_attention: 0.70
```
**Best for**: Meme stocks, early entries, higher risk

---

## 🎯 Use Cases

### Meme Stock Trading
```yaml
# Optimize for viral plays
volume_anomaly: 0.30
retail_attention: 0.70
min_score: 0.6
```
**Targets**: GME, AMC, BBBY, etc.

### Tech Momentum
```yaml
# Balance volume + retail
volume_anomaly: 0.60
retail_attention: 0.40
min_score: 0.5
```
**Targets**: TSLA, NVDA, AMD, etc.

### Blue Chip Breakouts
```yaml
# Volume-focused
volume_anomaly: 0.80
retail_attention: 0.20
min_score: 0.4
```
**Targets**: AAPL, MSFT, GOOGL, etc.

---

## 🔍 How to Read Scores

### Volume Anomaly Score:
- **0.8-1.0**: 🔥🔥🔥 Extreme volume, strong momentum
- **0.6-0.8**: 🔥🔥 High volume, good momentum
- **0.4-0.6**: 🔥 Elevated volume, moderate momentum
- **0.0-0.4**: 📊 Normal volume, weak signal

### Retail Attention Score:
- **0.8-1.0**: 🔥🔥🔥 Viral, breakout, extreme FOMO
- **0.6-0.8**: 🔥🔥 High interest, building momentum
- **0.4-0.6**: 🔥 Moderate interest, watch closely
- **0.0-0.4**: 📊 Low interest, weak signal

### Composite Score:
- **0.8+**: 🎯 **STRONG BUY** - High conviction
- **0.6-0.8**: ✅ **BUY** - Good signal
- **0.4-0.6**: ⚠️ **WATCH** - Moderate signal
- **<0.4**: ❌ **PASS** - Weak signal

---

## 💡 Pro Tips

### 1. Watch for Breakouts
```
Retail Attention: Breakout = YES 🔥
```
This means search interest spiked >2x average.  
**Action**: High conviction entry!

### 2. Combine Signals
```
Volume Score: 0.85 🔥
Retail Score: 0.78 🔥
Composite:    0.82 🔥🔥
```
Both factors agree = strongest signal.

### 3. Divergence Trading
```
Volume Score: 0.45 (low)
Retail Score: 0.85 (high)
```
Retail interest building, volume hasn't caught up yet.  
**Action**: Early entry opportunity!

### 4. Timeframe Tuning
```yaml
retail_attention:
  timeframe: "now 1-d"   # Intraday momentum
  timeframe: "now 7-d"   # Weekly trends (default)
  timeframe: "today 1-m" # Monthly context
```

---

## 🆚 Provider Comparison

| Provider | Cost | Rate Limit | Best For |
|----------|------|------------|----------|
| **YFinance** | FREE | None | Volume, price, OHLC |
| **Google Trends** | FREE | 1/sec | Retail sentiment, FOMO |
| Alpha Vantage | FREE | 25/day ⚠️ | Backup (not recommended) |
| StockTwits | FREE | Limited | Social sentiment (buggy) |

**Recommendation**: Use YFinance + Google Trends only!

---

## 🐛 Troubleshooting

### "pytrends not installed"
```bash
pip install pytrends
```

### "No data for symbol"
- Try popular symbols first (TSLA, GME, AAPL)
- Some low-volume symbols have no Google data
- Check spelling

### Low Scores for Everything
- Adjust `min_score` in config (try 0.3-0.4)
- Check if market is open
- Verify providers are enabled

### Rate Limit Errors
- Google Trends: 1 req/sec (auto-handled)
- YFinance: No limits
- Should rarely see errors

---

## 📚 Documentation

- **Full Requirements**: `docs/MOMENTUM_LAYER_REQUIREMENTS.md`
- **Configuration Guide**: `docs/MOMENTUM_CONFIG_GUIDE.md`
- **Implementation Details**: `GOOGLE_TRENDS_IMPLEMENTATION.md`
- **API Fixes**: `API_FIXES_SUMMARY.md`
- **YFinance Switch**: `YFINANCE_SWITCH_SUMMARY.md`

---

## 🎬 Example Session

```bash
# 1. Install
pip install yfinance pytrends

# 2. Setup config
cp momentum_config.yaml.example momentum_config.yaml
nano momentum_config.yaml  # Enable factors

# 3. Test providers
python scripts/test_google_trends.py

# 4. Run examples
python examples/momentum_example.py

# 5. Start bot
python main.py
```

**Output:**
```
🚀 Momentum Intelligence Layer - Usage Examples
================================================================
Multi-Factor Analysis with FREE Providers:
  ✅ YFinance - Volume & price data
  ✅ Google Trends - Retail attention
  🎉 100% FREE - No API keys needed!
  ⚡ UNLIMITED - No rate limits!
================================================================

Example 1: Score a Single Symbol
==================================================
Scoring GME...

✅ Results for GME:
  Composite Score: 0.868
  Confidence: 0.850
  Factors Used: 2/2
  Is Strong Signal: True

  Factor Breakdown:
    VolumeAnomalyFactor: 0.823 (confidence: 0.780)
    RetailAttentionFactor: 0.912 (confidence: 0.920)
      → Google Interest: 87.0/100
      → Breakout: 🔥 YES

🎯 Top Momentum Symbols:
  1. GME
  2. NVDA
  3. TSLA
```

---

## 🚀 Next Steps

### Phase 1: Current (FREE)
- [x] Volume Anomaly (YFinance)
- [x] Retail Attention (Google Trends)
- [ ] Integrate with main bot

### Phase 2: Future (Optional)
- [ ] Options Flow (MarketData.app - free tier)
- [ ] Short Interest (FINRA - free but limited)
- [ ] Dark Pool (Insight - requires setup)

### Phase 3: Premium ($$)
- [ ] Unusual Whales (options flow)
- [ ] S3 Partners (borrow data)
- [ ] SpotGamma (GEX data)

**Recommendation**: Stay on Phase 1 for now. It's powerful and FREE!

---

## ✅ Checklist

- [ ] Install: `pip install yfinance pytrends`
- [ ] Copy: `cp momentum_config.yaml.example momentum_config.yaml`
- [ ] Enable: Set `enabled: true` for both factors
- [ ] Test: `python scripts/test_google_trends.py`
- [ ] Run: `python examples/momentum_example.py`
- [ ] Trade: `python main.py`

---

## 🎉 You're Ready!

You now have a **multi-factor momentum intelligence layer** with:
- ✅ Volume anomaly detection
- ✅ Retail FOMO prediction
- ✅ 100% FREE providers
- ✅ No API keys needed
- ✅ Unlimited requests

**Happy Trading! 🚀📈**

---

## 💬 Support

Questions? Check:
1. `GOOGLE_TRENDS_IMPLEMENTATION.md` - Full technical details
2. `docs/MOMENTUM_LAYER_REQUIREMENTS.md` - Provider specs
3. `examples/momentum_example.py` - Working code examples
4. `scripts/test_google_trends.py` - Test suite

Or just run `./INSTALL_GOOGLE_TRENDS.sh` and follow the prompts!

