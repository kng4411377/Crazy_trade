# StockTwits API Update

## 📋 Summary of Changes

The StockTwits provider has been updated to support **RapidAPI access** as the primary method, since direct StockTwits API registration is currently paused for new developers.

---

## 🔄 What Changed

### 1. **Provider Code** (`src/momentum/providers/stocktwits.py`)

Added support for two access methods:

- ✅ **RapidAPI** (Recommended - Free tier available)
- ⚠️ **Direct API** (Legacy - currently unavailable for new registrations)

**Key Features**:
- Automatic detection of access method based on environment variables
- Graceful fallback if no credentials provided
- Clear logging of which method is being used

### 2. **Environment Variables**

**New (Recommended)**:
```bash
RAPIDAPI_KEY=your_rapidapi_key_here
STOCKTWITS_USE_RAPIDAPI=true  # Default: true
```

**Legacy (Still Supported)**:
```bash
STOCKTWITS_ACCESS_TOKEN=your_access_token
STOCKTWITS_USE_RAPIDAPI=false
```

### 3. **Configuration** (`momentum_config.yaml.example`)

Updated to reflect RapidAPI as primary method:

```yaml
providers:
  stocktwits:
    enabled: true
    use_rapidapi: true  # Use RapidAPI (recommended)
```

### 4. **Documentation**

**Updated Files**:
- `MOMENTUM_QUICKSTART.md` - Updated setup instructions
- `docs/MOMENTUM_LAYER_REQUIREMENTS.md` - Updated provider details
- `momentum_config.yaml.example` - Updated comments

**New Files**:
- `docs/STOCKTWITS_SETUP.md` - Comprehensive setup guide
  - Step-by-step RapidAPI setup
  - Troubleshooting tips
  - Cost comparison
  - Configuration reference

---

## 🚀 How to Use (New Users)

### Step 1: Get RapidAPI Key

1. Sign up at [RapidAPI](https://rapidapi.com/)
2. Search for "StockTwits" API
3. Subscribe to free tier (0 cost)
4. Copy your RapidAPI key

### Step 2: Set Environment Variables

```bash
# In terminal or .env file:
export RAPIDAPI_KEY="your_rapidapi_key_here"
export STOCKTWITS_USE_RAPIDAPI="true"
```

### Step 3: Enable in Config

```yaml
# In momentum_config.yaml
providers:
  stocktwits:
    enabled: true
    use_rapidapi: true
```

### Step 4: Test It

```bash
python scripts/test_momentum_providers.py
```

---

## 🔧 Migration (Existing Users with Direct API)

**If you already have a StockTwits access token**, no action needed! The bot will continue using your existing token.

**To switch to RapidAPI**:

1. Get RapidAPI key (see above)
2. Update environment variables:
   ```bash
   export RAPIDAPI_KEY="your_rapidapi_key"
   export STOCKTWITS_USE_RAPIDAPI="true"
   ```
3. Update config:
   ```yaml
   providers:
     stocktwits:
       use_rapidapi: true
   ```

---

## 📊 Rate Limits

### RapidAPI Free Tier:
- **Requests**: 100-500/month (varies by plan)
- **Rate**: ~1 request/second
- **Cost**: $0
- **Sufficient for**: Scoring 10-20 symbols daily

### Paid Tiers (if needed):
- **Basic**: $9.99/month - 5,000 requests
- **Pro**: $49.99/month - 50,000 requests

---

## 🧪 Testing

The provider automatically selects the correct API endpoint based on your configuration:

```python
# RapidAPI mode
BASE_URL = "https://stocktwits.p.rapidapi.com/api/2"
headers = {
    'X-RapidAPI-Key': your_key,
    'X-RapidAPI-Host': 'stocktwits.p.rapidapi.com'
}

# Direct API mode
BASE_URL = "https://api.stocktwits.com/api/2"
headers = {
    'Authorization': f'Bearer {access_token}'
}
```

---

## 🆘 Troubleshooting

### "No credentials found"
- Set `RAPIDAPI_KEY` environment variable
- Verify it's exported: `echo $RAPIDAPI_KEY`

### "Rate limited"
- You've exceeded free tier quota
- Wait for monthly reset
- Consider upgrading tier

### "401 Unauthorized"
- Invalid RapidAPI key
- Check your RapidAPI dashboard
- Regenerate key if needed

---

## 📚 References

- **[StockTwits Setup Guide](docs/STOCKTWITS_SETUP.md)** - Detailed setup
- **[Momentum Quickstart](MOMENTUM_QUICKSTART.md)** - Full momentum layer setup
- **[Momentum Requirements](docs/MOMENTUM_LAYER_REQUIREMENTS.md)** - Technical specs

---

## ✅ Backwards Compatibility

All existing configurations continue to work:

- ✅ Existing `STOCKTWITS_ACCESS_TOKEN` still works
- ✅ No breaking changes to API
- ✅ Automatic fallback to direct API if RapidAPI key not found
- ✅ Clear logging of which method is active

**Bottom line**: Existing users see no disruption, new users get free access via RapidAPI! 🎉

