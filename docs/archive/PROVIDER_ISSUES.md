# 🔍 Provider Issues & Solutions

Based on your test results, here's what's happening:

---

## ✅ Good News First

- **Environment loading works!** ✅ ALPHAVANTAGE_API_KEY is detected
- **Momentum factors work!** ✅ Factor calculation logic is correct

---

## ⚠️ Issue 1: Alpha Vantage Rate Limited

### What's Happening:
```
❌ Provider not available
Rate Limited: True
Error: Rate limited
```

### Possible Causes:

**A) You Already Hit the Rate Limit Today**
- Free tier: **5 calls/minute**, **500 calls/day**
- The health check itself counts as 1 call
- If you tested multiple times, you might be rate limited

**B) Invalid API Key**
- Alpha Vantage returns rate limit message for invalid keys

**C) API Key Not Activated Yet**
- New keys take ~5 minutes to activate

### Solutions:

#### 1. Check Your API Key:
```bash
# Test your key directly
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_KEY"
```

**Good response**:
```json
{
  "Global Quote": {
    "01. symbol": "AAPL",
    "05. price": "185.23"
  }
}
```

**Rate limited response**:
```json
{
  "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute..."
}
```

**Invalid key response**:
```json
{
  "Error Message": "Invalid API call..."
}
```

#### 2. Wait and Retry:
```bash
# Wait 1 minute, then test again
sleep 60
python scripts/test_momentum_providers.py
```

#### 3. Get a New Key (if needed):
1. Visit: https://www.alphavantage.co/support/#api-key
2. Use different email
3. Get new key
4. Update `.env`:
   ```bash
   ALPHAVANTAGE_API_KEY=your_new_key_here
   ```

---

## ❌ Issue 2: StockTwits HTTP 404

### What's Happening:
```
❌ Provider not available
Error: HTTP 404
```

### Root Cause:

**The RapidAPI StockTwits endpoint structure is different from the official API.**

The code is trying: `https://stocktwits.p.rapidapi.com/api/2/streams/symbol/AAPL.json`

But RapidAPI's StockTwits might use a different URL structure or API name.

### Solutions:

#### Option 1: Disable StockTwits for Now (Quickest)

```yaml
# In momentum_config.yaml
providers:
  stocktwits:
    enabled: false  # Disable until we fix the endpoint
```

The bot will work with **just Alpha Vantage** - it will use volume anomalies only.

#### Option 2: Find the Correct RapidAPI Endpoint

1. Go to your RapidAPI dashboard: https://rapidapi.com/hub
2. Search for "StockTwits" or "Twitter Sentiment" or "Stock Social Sentiment"
3. Find the API you subscribed to
4. Check the **Endpoints** tab for the correct URL structure
5. Let me know what you find, and I'll update the code

#### Option 3: Use Direct API (If You Have Access)

If you have a direct StockTwits token:

```bash
# In .env
STOCKTWITS_ACCESS_TOKEN=your_token_here
STOCKTWITS_USE_RAPIDAPI=false
```

---

## 🚀 Quick Fix to Test Now

### Disable StockTwits and test with Alpha Vantage only:

```bash
# 1. Edit momentum_config.yaml
nano momentum_config.yaml

# 2. Set stocktwits.enabled to false

# 3. Wait 1 minute (for Alpha Vantage rate limit to reset)
sleep 60

# 4. Test again
python scripts/test_momentum_providers.py
```

---

## 💡 Working Configuration (Alpha Vantage Only)

This will work while we fix StockTwits:

```yaml
# momentum_config.yaml
momentum_layer:
  enabled: true
  
  providers:
    alphavantage:
      enabled: true
    
    stocktwits:
      enabled: false  # Disable for now
  
  factors:
    volume_anomaly:
      enabled: true
      weight: 1.0  # 100% weight since sentiment is disabled
    
    sentiment_velocity:
      enabled: false  # Disable until StockTwits is fixed
```

---

## 📊 What You'll Get with Alpha Vantage Only

Even without StockTwits, you'll still get:

✅ **Volume Anomalies**:
- Relative Volume (RVOL)
- Volume trend analysis
- Price volatility
- Volume-based momentum scoring

✅ **Scoring** based on:
- Unusual volume patterns
- Volume increasing/decreasing trends
- Price movement correlation

**This is enough to identify momentum!** Volume is often the best early signal.

---

## 🔧 Next Steps

1. **Immediate**: Disable StockTwits, test with Alpha Vantage only
2. **Today**: Check your Alpha Vantage rate limits
3. **This Week**: Find correct RapidAPI StockTwits endpoint (or we disable it)

---

## 🆘 Need Help?

Share:
1. Output of: `curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_KEY"`
2. Name of the API you subscribed to on RapidAPI
3. Whether you want to just use Alpha Vantage only (simplest!)

---

**TL;DR**: 
- ✅ Alpha Vantage: Rate limited (wait or get new key)
- ❌ StockTwits: Wrong endpoint (disable for now)
- 🎯 **Quickest path**: Use Alpha Vantage only, disable StockTwits

