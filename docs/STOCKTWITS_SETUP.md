# StockTwits API Setup Guide

StockTwits provides social sentiment data for stocks. This guide explains how to access it.

---

## 🌐 Access Methods

### Method 1: RapidAPI (Recommended) ⭐

**Status**: ✅ Available now  
**Cost**: Free tier available (100-500 requests/month)  
**Setup Time**: ~5 minutes

#### Steps:

1. **Sign up for RapidAPI**:
   - Visit [https://rapidapi.com/](https://rapidapi.com/)
   - Create a free account

2. **Find StockTwits API**:
   - Search for "StockTwits" in the API marketplace
   - Select the StockTwits API

3. **Subscribe to Free Tier**:
   - Click "Subscribe to Test"
   - Select the free plan (Basic/Free tier)
   - Complete subscription

4. **Get Your API Key**:
   - Copy your RapidAPI key from the dashboard
   - It looks like: `1234567890abcdef1234567890abcdef`

5. **Add to Environment**:
   ```bash
   # In your .env file or terminal:
   export RAPIDAPI_KEY="your_rapidapi_key_here"
   export STOCKTWITS_USE_RAPIDAPI="true"
   ```

6. **Configure the bot**:
   ```yaml
   # In momentum_config.yaml
   providers:
     stocktwits:
       enabled: true
       use_rapidapi: true
   ```

**Limits**:
- Free tier: 100-500 requests/month
- Rate limit: ~1 request/second
- Sufficient for scoring 10-20 symbols daily

---

### Method 2: Direct API (Legacy)

**Status**: ⚠️ Currently unavailable for new registrations  
**Alternative**: Contact StockTwits support for access

#### Background:

- StockTwits has paused new developer registrations on their official portal
- Existing API tokens continue to work
- They're updating their developer program

#### If You Have an Existing Token:

```bash
# In your .env file:
export STOCKTWITS_ACCESS_TOKEN="your_token_here"
export STOCKTWITS_USE_RAPIDAPI="false"
```

#### To Request Direct Access:

- Email: developers@stocktwits.com
- Subject: "Developer API Access Request"
- Include your use case and expected usage

---

## 🧪 Testing Your Setup

### Test the Connection:

```bash
python scripts/test_momentum_providers.py
```

Expected output:
```
Testing StockTwits provider...
✅ Initialization successful
✅ Health check passed
✅ Stream data retrieved for TSLA
✅ Sentiment metrics calculated

StockTwits Tests: PASSED
```

### Troubleshooting:

**Error: "No credentials found"**
```bash
# Check environment variables are set:
echo $RAPIDAPI_KEY
echo $STOCKTWITS_USE_RAPIDAPI

# If empty, export them:
export RAPIDAPI_KEY="your_key_here"
export STOCKTWITS_USE_RAPIDAPI="true"
```

**Error: "Rate limited"**
- You've exceeded your quota
- Wait until next billing cycle (usually monthly reset)
- Consider upgrading to a paid tier if needed

**Error: "401 Unauthorized"**
- Invalid or expired API key
- Check your RapidAPI dashboard for the correct key
- Regenerate key if needed

---

## 📊 What Data You Get

### Stream Data:

```json
{
  "messages": [
    {
      "id": 123456789,
      "body": "TSLA looking strong! 🚀",
      "created_at": "2025-01-15T14:30:00Z",
      "user": {
        "username": "trader123"
      },
      "entities": {
        "sentiment": {
          "basic": "Bullish"
        }
      }
    }
  ]
}
```

### Calculated Metrics:

- **Total Messages**: Count of recent messages
- **Bullish/Bearish Ratio**: Sentiment distribution
- **Velocity**: Messages per hour
- **Sentiment Trend**: Recent vs. overall sentiment change

---

## 💰 Cost Comparison

| Plan | Provider | Monthly Cost | Requests/Month | Best For |
|------|----------|--------------|----------------|----------|
| **Free** | RapidAPI | $0 | 100-500 | Testing, small watchlists |
| **Basic** | RapidAPI | $9.99 | 5,000 | Regular usage |
| **Pro** | RapidAPI | $49.99 | 50,000 | Heavy usage |
| **Direct API** | StockTwits | Varies | Contact | Enterprise |

**Recommendation**: Start with RapidAPI free tier. Upgrade only if needed.

---

## 🔧 Configuration Reference

### Environment Variables:

```bash
# RapidAPI access (recommended)
RAPIDAPI_KEY=your_rapidapi_key_here
STOCKTWITS_USE_RAPIDAPI=true

# Direct API access (if available)
STOCKTWITS_ACCESS_TOKEN=your_token_here
STOCKTWITS_USE_RAPIDAPI=false
```

### Config File (`momentum_config.yaml`):

```yaml
providers:
  stocktwits:
    enabled: true
    use_rapidapi: true  # Use RapidAPI
    priority: 1  # Core provider
```

---

## 📚 Related Docs

- [Momentum Layer Requirements](MOMENTUM_LAYER_REQUIREMENTS.md)
- [Momentum Quickstart](../MOMENTUM_QUICKSTART.md)
- [Momentum Config Guide](MOMENTUM_CONFIG_GUIDE.md)

---

## 🆘 Need Help?

1. **Check logs**: Look for StockTwits-related errors
2. **Test connection**: Run `test_momentum_providers.py`
3. **Verify credentials**: Double-check your API key
4. **Check rate limits**: Monitor your RapidAPI usage dashboard

**Still stuck?** Open an issue with:
- Error message
- Test script output
- Whether you're using RapidAPI or direct API

