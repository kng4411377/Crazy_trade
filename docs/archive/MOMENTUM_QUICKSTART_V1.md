# Momentum Intelligence Layer - Quick Start

🎉 **The Momentum Intelligence Layer has been implemented!**

This layer adds dynamic symbol scoring based on volume anomalies and social sentiment to help you identify high-momentum trading opportunities.

---

## 🚀 5-Minute Setup

### Step 1: Get API Keys (Free)

1. **Alpha Vantage** (Required):
   - Sign up: https://www.alphavantage.co/
   - Click "Get Your Free API Key Today"
   - Copy your API key

2. **StockTwits** (Optional but recommended):
   - Sign up: https://stocktwits.com/developers
   - Create an app
   - Copy your access token
3. **StockTwits** (via RapidAPI):
   - Sign up at [RapidAPI](https://rapidapi.com/)
   - Search for "StockTwits" API
   - Subscribe to free tier
   - Copy your RapidAPI key

### Step 2: Set Environment Variables

**Create a `.env` file** (recommended):

```bash
# Create .env from template
cp ENV_EXAMPLE.txt .env

# Edit .env and add your keys:
nano .env
```

Add your keys to `.env`:
```bash
ALPHAVANTAGE_API_KEY=your_actual_key_here
RAPIDAPI_KEY=your_actual_rapidapi_key_here
STOCKTWITS_USE_RAPIDAPI=true
```

**Or export in terminal** (temporary):
```bash
export ALPHAVANTAGE_API_KEY="your_key_here"
export RAPIDAPI_KEY="your_rapidapi_key_here"
export STOCKTWITS_USE_RAPIDAPI="true"
```

**Note**: 
- `.env` file is gitignored - your keys are safe
- Direct StockTwits API registration is currently paused. Use RapidAPI instead.
- See [ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md) for troubleshooting

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
# This installs aiohttp for async HTTP requests
```

### Step 4: Test It!

```bash
python scripts/test_momentum_providers.py
```

You should see:
```
✅ Alpha Vantage: ALL TESTS PASSED
✅ StockTwits: ALL TESTS PASSED
✅ Factors: ALL TESTS PASSED

🎉 ALL TESTS PASSED! 🎉
```

---

## 📊 Try It Out

### Example 1: Score a Symbol

```bash
python examples/momentum_example.py
```

Output:
```
Scoring TSLA...

Results for TSLA:
  Composite Score: 0.725
  Confidence: 0.680
  Factors Used: 2/2
  Is Strong Signal: True

  Factor Breakdown:
    VolumeAnomalyFactor: 0.820 (confidence: 0.750)
    SentimentVelocityFactor: 0.630 (confidence: 0.610)
```

### Example 2: Generate Watchlist

```python
# In Python
import asyncio
from src.momentum.engine import MomentumEngine
from src.momentum.providers.alphavantage import AlphaVantageProvider
from src.momentum.providers.stocktwits import StockTwitsProvider
from src.momentum.factors.volume_anomaly import VolumeAnomalyFactor
from src.momentum.factors.sentiment_velocity import SentimentVelocityFactor

async def get_top_momentum():
    # Setup
    engine = MomentumEngine({'enabled': True})
    
    av = AlphaVantageProvider({})
    st = StockTwitsProvider({})
    await av.initialize()
    await st.initialize()
    
    engine.provider_registry.register(av)
    engine.provider_registry.register(st)
    
    engine.register_factor(VolumeAnomalyFactor([av], {'weight': 0.5}))
    engine.register_factor(SentimentVelocityFactor([st], {'weight': 0.5}))
    
    await engine.initialize()
    
    # Score universe
    universe = ["TSLA", "NVDA", "AMD", "AAPL", "GME"]
    watchlist = await engine.generate_watchlist(universe, max_symbols=3)
    
    print(f"Top momentum: {watchlist}")
    # Output: ['NVDA', 'TSLA', 'AMD']
    
    await av.close()
    await st.close()

asyncio.run(get_top_momentum())
```

---

## 🎯 What Does It Score?

### Volume Anomaly Factor (30% weight)

**Measures**: Unusual volume patterns
- RVOL > 2.0: 🔥 Very strong (Score: 0.9-1.0)
- RVOL 1.5-2.0: 💪 Strong (Score: 0.7-0.9)
- RVOL 1.2-1.5: 👍 Moderate (Score: 0.4-0.7)
- RVOL < 1.2: 😐 Weak (Score: 0.0-0.4)

**Example**:
```
NVDA:
  RVOL: 2.3x (230% of normal volume!)
  Volume Trend: +35% (increasing)
  Score: 0.920 ⭐
```

### Sentiment Velocity Factor (30% weight)

**Measures**: Social media momentum
- High velocity + bullish: 🚀 Strong (Score: 0.7-1.0)
- High velocity + neutral: 📈 Moderate (Score: 0.4-0.7)
- Low velocity: 💤 Weak (Score: 0.0-0.4)

**Example**:
```
TSLA:
  Velocity: 45 messages/hour
  Bullish Ratio: 72%
  Sentiment Trend: +8% (getting more bullish)
  Score: 0.780 ⭐
```

### Composite Score

**Formula**: Weighted average of all factors

**Interpretation**:
- **0.8 - 1.0**: 🔥 Extremely strong momentum
- **0.6 - 0.8**: 💪 Strong momentum
- **0.4 - 0.6**: 👍 Moderate momentum
- **0.0 - 0.4**: 😐 Weak momentum

---

## 🔧 Configuration

### Copy the Template

```bash
cp momentum_config.yaml.example momentum_config.yaml
```

**Note:** `momentum_config.yaml` is gitignored - your local changes won't be committed.

### Updating Configuration

When you pull new updates, merge new features using:

```bash
python3 merge_config.py  # Merges both config.yaml and momentum_config.yaml
```

See [docs/MOMENTUM_CONFIG_GUIDE.md](docs/MOMENTUM_CONFIG_GUIDE.md) for details.

### Enable It

```yaml
momentum_layer:
  enabled: true  # Change from false to true
```

### Customize Weights

```yaml
momentum_layer:
  factors:
    volume_anomaly:
      weight: 0.40  # Give more weight to volume
    
    sentiment_velocity:
      weight: 0.30  # Less weight to sentiment
```

### Set Thresholds

```yaml
momentum_layer:
  factors:
    volume_anomaly:
      rvol_threshold: 2.0  # Only score symbols with 2x+ volume
      volume_trend_threshold: 0.3  # Require 30%+ trend
```

---

## ⚠️ Important Notes

### Rate Limits

**Alpha Vantage (Free)**:
- 5 requests per minute
- 500 requests per day
- **Impact**: Scoring 10 symbols takes ~2 minutes

**Tips**:
- Start with 5-10 symbols
- Score every 15-30 minutes (not every second)
- Consider premium plan for higher limits

### Data Freshness

- Volume data: Updated once per day (EOD)
- Sentiment data: Real-time
- **Recommendation**: Re-score every 15-30 minutes

---

## 📈 Next Steps

### 1. Integrate with Your Bot

```python
# In your bot code
from src.momentum import MomentumEngine

# Setup momentum engine
momentum_engine = MomentumEngine(config.momentum)
await momentum_engine.initialize()

# Before entering trade, check momentum
score = await momentum_engine.calculate_score(symbol)
if score and score.is_strong_signal():
    # High momentum - proceed with entry
    place_entry_order(symbol)
else:
    # Low momentum - skip
    logger.info("skipping_low_momentum", symbol=symbol)
```

### 2. Dynamic Watchlist

```python
# Replace static watchlist with dynamic one
universe = ["TSLA", "NVDA", "AMD", ...] # 20-50 symbols

watchlist = await momentum_engine.generate_watchlist(
    universe,
    max_symbols=10  # Top 10 momentum symbols
)

# Use this watchlist for trading
bot.update_watchlist(watchlist)
```

### 3. Add More Providers (Phase 2)

- Unusual Whales (options flow)
- S3 Partners (borrow data)
- Dark pool data
- See [MOMENTUM_LAYER_REQUIREMENTS.md](docs/MOMENTUM_LAYER_REQUIREMENTS.md)

---

## 🆘 Troubleshooting

### "ALPHAVANTAGE_API_KEY not set"

```bash
# Check if it's set
echo $ALPHAVANTAGE_API_KEY

# If empty, set it:
export ALPHAVANTAGE_API_KEY="your_key_here"
```

### "Provider not available"

1. Check API key is valid
2. Try the test script: `python scripts/test_momentum_providers.py`
3. Check you're not rate limited (wait 1 minute)

### "Failed to calculate score"

- Symbol might not have enough data
- Check logs for specific error
- Try a different symbol (AAPL, TSLA, NVDA usually work)

---

## 📚 Documentation

- **Full Requirements**: [docs/MOMENTUM_LAYER_REQUIREMENTS.md](docs/MOMENTUM_LAYER_REQUIREMENTS.md)
- **Implementation Status**: [docs/MOMENTUM_LAYER_STATUS.md](docs/MOMENTUM_LAYER_STATUS.md)
- **Examples**: `examples/momentum_example.py`
- **Tests**: `scripts/test_momentum_providers.py`

---

## 💬 Quick Q&A

**Q: Do I need all the API keys?**
A: Only Alpha Vantage is required. StockTwits works without a token but has lower rate limits.

**Q: How much does it cost?**
A: Phase 1 is 100% FREE! Alpha Vantage and StockTwits both have free tiers.

**Q: Can I use it for crypto?**
A: Yes! Both providers support crypto symbols (BTC/USD, ETH/USD, etc.)

**Q: How often should I re-score symbols?**
A: Every 15-30 minutes is optimal. Faster wastes API calls, slower misses momentum shifts.

**Q: What if a provider is down?**
A: The system gracefully degrades. If Alpha Vantage is down, it will skip the volume factor and score with sentiment only.

---

## 🎉 You're Ready!

The Momentum Intelligence Layer is fully functional and ready to use!

1. ✅ Get API keys (5 min)
2. ✅ Run test script (1 min)
3. ✅ Try examples (2 min)
4. ✅ Start scoring! 🚀

**Have fun finding momentum! 📈**

---

**Need help?** See [docs/MOMENTUM_LAYER_STATUS.md](docs/MOMENTUM_LAYER_STATUS.md) for detailed info.

