# Apewisdom Reddit Sentiment Provider

## 🎯 What is Apewisdom?

**Apewisdom** is a Reddit sentiment aggregation service that tracks stock mentions across multiple subreddits (r/wallstreetbets, r/stocks, r/investing, etc.) and provides:

- ✅ **Mention volume** - How much Reddit is talking about a stock
- ✅ **Mention velocity** - Rate of increase in discussion
- ✅ **Sentiment/positivity** - Bullish vs bearish sentiment (0-1 scale)
- ✅ **Rank tracking** - Position in trending list
- ✅ **Historical data** - 30 days of Reddit activity

## 🆚 Why Apewisdom > Google Trends?

| Feature | Apewisdom | Google Trends |
|---------|-----------|---------------|
| **Stock-Specific** | ✅ Yes | ❌ No (general search) |
| **Update Frequency** | 2x/day | Daily |
| **Sentiment Score** | ✅ Yes | ❌ No |
| **Rate Limits** | ✅ Generous (1000/day) | ❌ Severe (~30/hour) |
| **Meme Stock Detection** | ✅ Perfect | ⚠️ Lagging |
| **Reddit Focus** | ✅ Native | ❌ Indirect |
| **API Quality** | ✅ Good | ⚠️ Unofficial |
| **Cost** | Free | Free |

**Verdict:** Apewisdom is **much better** for momentum/meme stock trading!

---

## 🚀 Quick Start

### 1. **Install (Already Done!)**

Apewisdom provider is already implemented in your bot:
- `src/momentum/providers/apewisdom.py` - Provider
- `src/momentum/factors/reddit_attention.py` - Reddit attention factor
- Configuration already added to `momentum_config.yaml`

### 2. **Enable in Config**

Already enabled by default in `momentum_config.yaml`:

```yaml
providers:
  apewisdom:
    enabled: true  # ✅ Already enabled!

factors:
  reddit_attention:
    enabled: true  # ✅ Already enabled!
    weight: 0.30
    mention_threshold: 50      # Min mentions to score
    volume_weight: 0.3
    velocity_weight: 0.4
    sentiment_weight: 0.3
```

### 3. **Test It!**

```bash
python scripts/test_apewisdom.py
```

Expected output:
```
🧪 Testing Apewisdom Provider (Reddit/WSB Sentiment)
======================================================================

1. Initializing provider...
   ✅ Initialized: True
   ✅ Available: True

2. Fetching Reddit sentiment data...

   GME:
      Mentions: 1,234
      Change 24h: +45.2%
      Rank: #3
      Rank Change: +2
      Positivity: 0.72 (0-1 scale)
      🔥 TRENDING UP!
      😊 BULLISH SENTIMENT
```

---

## 📊 Understanding Apewisdom Data

### Update Schedule

**Free Tier Updates:**
- ✅ **9 AM EST** - Morning snapshot (captures overnight Reddit activity)
- ✅ **9 PM EST** - Evening snapshot (captures day's trading activity)

**Best Usage Times:**
- **9:30 AM** - After morning update, before market open → Plan your day
- **9:30 PM** - After evening update, after market close → Analyze day's sentiment

### Data Fields

**Mention Volume:**
- Number of times the stock ticker was mentioned on Reddit
- Typical ranges:
  - 50-100: Low activity
  - 100-500: Moderate activity
  - 500-1000: High activity
  - 1000+: Viral/meme stock

**Mention Change:**
- Percentage change in mentions vs 24 hours ago
- Key levels:
  - +100%: 2x mentions (strong momentum)
  - +200%: 3x mentions (explosive momentum)
  - -50%: Losing interest

**Rank:**
- Position in Apewisdom trending list (#1-#100)
- Lower rank = more popular
- Track rank_change to see if climbing or falling

**Positivity:**
- Sentiment score from 0-1
  - 0.0-0.4: Bearish
  - 0.4-0.6: Neutral
  - 0.6-1.0: Bullish

---

## 🎯 Usage Patterns

### Pattern 1: Pre-Market Scanning (Best!)

**When:** 9:30 AM (after 9 AM update)

```bash
python scripts/scan_momentum.py

# Results show:
# - Which stocks Reddit talked about overnight
# - Volume confirmation from YFinance
# - Combined momentum score
```

**Use for:**
- Planning your watchlist for the day
- Identifying potential meme stock moves
- Spotting WSB momentum early

**Example Results:**
```
🏆 TOP 10 MOMENTUM STOCKS
═══════════════════════════════════════════════

Rank  Symbol  Composite   Volume      Reddit      RVOL
────────────────────────────────────────────────────────
🥇 1   GME     0.850       0.750       0.950       1.45
🥈 2   AMC     0.720       0.680       0.760       1.32
🥉 3   PLTR    0.680       0.720       0.640       1.58
```

---

### Pattern 2: After-Hours Analysis

**When:** 9:30 PM (after 9 PM update)

```bash
python scripts/scan_momentum.py

# Results show:
# - Which stocks gained Reddit attention during trading
# - Day's volume performance
# - Prep watchlist for tomorrow
```

**Use for:**
- Analyzing day's Reddit activity
- Identifying stocks building momentum
- Planning next day's trades

---

### Pattern 3: Intraday (Volume-Only)

**When:** During trading hours

```bash
python scripts/scan_momentum.py --no-retail

# Results show:
# - Real-time volume momentum
# - Skip Reddit (hasn't updated yet)
# - Fast scanning
```

**Use for:**
- Tracking intraday volume spikes
- Quick momentum checks
- Not waiting for Reddit updates

---

## 📈 Score Interpretation

### Reddit Attention Score (0-1)

**Formula:**
```
score = (
    0.3 × volume_score +    # How many mentions
    0.4 × velocity_score +  # How fast mentions growing
    0.3 × sentiment_score   # How bullish Reddit is
)
```

**Score Ranges:**
- **0.8-1.0**: 🔥 Extreme Reddit attention (meme stock territory)
- **0.6-0.8**: 📈 High Reddit momentum (watch closely)
- **0.4-0.6**: 📊 Moderate Reddit interest (normal)
- **0.0-0.4**: 💤 Low Reddit activity (skip)

**Signals:**
- `is_breakout`: Mentions >100% increase + >200 mentions
- `is_trending_up`: Rank improved (moving up the list)
- `is_bullish`: Positivity >0.6

---

## 🎯 Real-World Examples

### Example 1: GME Meme Stock Run

```
Before:
- Mentions: 150
- Rank: #25
- Positivity: 0.55

During Breakout:
- Mentions: 1,500 (+900% 🔥)
- Rank: #1 (+24 spots)
- Positivity: 0.85 (bullish)
- Reddit Score: 0.95 (EXTREME)
```

**Signal:** Clear meme stock breakout, high Reddit attention

---

### Example 2: Normal Stock (AAPL)

```
AAPL:
- Mentions: 75
- Change: +5%
- Rank: #45
- Positivity: 0.52
- Reddit Score: 0.25 (low)
```

**Signal:** Normal activity, not a Reddit momentum play

---

### Example 3: Losing Steam (BYND)

```
BYND:
- Mentions: 45 (below threshold)
- Change: -60%
- Rank: #80 (-20 spots)
- Positivity: 0.35 (bearish)
- Reddit Score: N/A (below 50 mention threshold)
```

**Signal:** Reddit losing interest, momentum fading

---

## 💡 Trading Strategies

### Strategy 1: Reddit Momentum + Volume Confirmation

**Setup:**
```yaml
factors:
  volume_anomaly:
    weight: 0.5  # 50% weight
  reddit_attention:
    weight: 0.5  # 50% weight
```

**Logic:**
- ✅ High Reddit attention (>0.7)
- ✅ + Volume spike (RVOL >1.5)
- = Strong momentum play

**When to trade:**
- Reddit score >0.7
- Volume confirms with RVOL >1.5
- Positivity >0.6 (bullish)

---

### Strategy 2: Early Meme Stock Detection

**Setup:**
```yaml
reddit_attention:
  mention_threshold: 100  # Higher threshold
  velocity_weight: 0.5    # Focus on growth rate
```

**Logic:**
- Look for **rapid mention growth** (+100%+)
- Rank improving quickly
- Still under 1000 mentions (early)

**When to trade:**
- Mentions doubling daily
- Rank climbing fast
- Before mainstream attention

---

### Strategy 3: Contrarian (Fade the Reddit Hype)

**Setup:**
Use Reddit score to **avoid** overhyped stocks

**Logic:**
- Reddit score >0.9 = Too much hype
- Mentions >2000 = Overextended
- Positivity >0.85 = Euphoric

**When to trade:**
- **Short** or **avoid** when Reddit score extreme
- Wait for cooldown period
- Re-enter when score normalizes

---

## 🔧 Configuration Options

### Basic Settings

```yaml
reddit_attention:
  enabled: true
  weight: 0.30
  mention_threshold: 50       # Min mentions to generate score
  volume_weight: 0.3          # Weight for mention volume
  velocity_weight: 0.4        # Weight for mention growth
  sentiment_weight: 0.3       # Weight for positivity
```

### Aggressive (Meme Stock Hunter)

```yaml
reddit_attention:
  enabled: true
  weight: 0.50                # Higher weight
  mention_threshold: 100      # Only viral stocks
  velocity_weight: 0.6        # Focus on growth
  sentiment_weight: 0.2       # Care less about sentiment
```

### Conservative (Quality Filter)

```yaml
reddit_attention:
  enabled: true
  weight: 0.20                # Lower weight
  mention_threshold: 200      # Only established attention
  volume_weight: 0.5          # Focus on sustained volume
  velocity_weight: 0.2        # Less focus on spikes
```

---

## 🚨 Limitations & Considerations

### Update Frequency

**Free Tier:**
- ❌ Not real-time (2x daily updates)
- ✅ Perfect for pre-market & EOD analysis
- ⚠️ Intraday momentum may be stale

**Workaround:**
- Use `--no-retail` flag for intraday scans
- Rely on volume momentum during trading hours
- Use Reddit scores for overnight/morning planning

### Coverage

**What's Tracked:**
- ✅ Stocks mentioned on major subreddits
- ✅ Popular meme stocks (GME, AMC, etc.)
- ✅ Large-cap stocks with Reddit attention

**What's NOT Tracked:**
- ❌ Obscure penny stocks (unless viral)
- ❌ Stocks with <50 mentions
- ❌ Non-English discussions

### Data Quality

**Strengths:**
- ✅ Pre-aggregated sentiment (no parsing needed)
- ✅ Cross-subreddit aggregation
- ✅ Historical tracking

**Weaknesses:**
- ⚠️ Bot/spam mentions not always filtered
- ⚠️ Sarcasm detection not perfect
- ⚠️ Past performance doesn't guarantee future results

---

## 📚 API Reference

### Provider Methods

```python
from src.momentum.providers.apewisdom import ApewisdomProvider

provider = ApewisdomProvider({})
await provider.initialize()

# Get sentiment for a symbol
data = await provider.get_stock_sentiment("GME")

# Returns:
{
    'mentions': 1234,
    'mentions_24h_ago': 856,
    'mentions_change': 44.2,  # % change
    'rank': 3,
    'rank_24h_ago': 5,
    'rank_change': 2,  # Climbing
    'positivity': 0.72,  # 0-1 scale
    'timestamp': datetime(...)
}
```

### Factor Methods

```python
from src.momentum.factors.reddit_attention import RedditAttentionFactor

factor = RedditAttentionFactor([provider], {
    'weight': 0.5,
    'mention_threshold': 50
})

score = await factor.calculate_score("GME")

# Returns FactorScore with:
score.score  # 0-1 composite score
score.confidence  # 0-1 based on mention volume
score.metadata  # {mentions, positivity, is_breakout, etc.}
```

---

## 🎉 Summary

**Apewisdom gives you:**
- ✅ Reddit momentum tracking
- ✅ WSB/meme stock detection
- ✅ Pre-market planning data
- ✅ Free tier (no credit card)
- ✅ Better than Google Trends for stocks

**Perfect for:**
- Swing traders (2-7 day holds)
- Meme stock traders
- Pre-market scanners
- Reddit-aware trading

**Not ideal for:**
- High-frequency day trading (2x daily updates)
- Stocks without Reddit activity
- Real-time intraday sentiment

**Next Steps:**
1. ✅ Test: `python scripts/test_apewisdom.py`
2. ✅ Run scanner: `python scripts/scan_momentum.py`
3. ✅ Check results at 9:30 AM or 9:30 PM
4. ✅ Trade the momentum! 🚀

