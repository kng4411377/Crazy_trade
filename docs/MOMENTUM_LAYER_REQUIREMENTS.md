# Momentum Intelligence Layer – Environment & Integration Requirements

**Status**: 🚧 Planned Feature (Not Yet Implemented)

This document defines the external data providers and environment variables required to power the **Momentum Intelligence Layer** (dynamic watchlist / ProactiveMomentumScore) for the Crazy Trade Bot.

---

## 🎯 Overview

The Momentum Intelligence Layer will add:

- **Dynamic Watchlist**: Automatically discover and score high-momentum symbols
- **Multi-Factor Scoring**: Combine options flow, sentiment, volume, dark pool, and borrow data
- **Proactive Entries**: Enter positions based on momentum signals (not just watchlist)
- **Provider Resilience**: Gracefully degrade if API providers are unavailable

---

## 📋 Goals

**For the codebase:**
- Clear contract for which `.env` variables must be present
- Resilient factor system (missing provider = disabled factor, not crash)
- Configurable provider priorities

**For you:**
- Shopping list of which API keys/accounts to obtain
- Free vs premium provider options
- Implementation roadmap

---

## 1. Provider Strategy

### Core Providers (Free / Low Friction)

For prototyping and initial live tests:
- ✅ Alpha Vantage (price, volume, technicals)
- ✅ Marketstack (backup price data)
- ✅ StockTwits (social sentiment velocity)
- ✅ MarketData.app (options quotes & Greeks)
- ✅ FINRA Short Interest (public data, no key)
- ✅ Google Trends (retail attention)
- ✅ Insight (dark pool, community data)

### Premium Providers (Optional Upgrade)

For production-grade signals:
- 💎 Unusual Whales (options flow & sweeps)
- 💎 Optionomics (options analytics)
- 💎 S3 Partners (borrow cost & utilization)
- 💎 SpotGamma / SqueezeMetrics (gamma exposure)
- 💎 Twitter/X API (direct sentiment)

---

## 2. Environment Variables

### 2.1 Core Providers (Recommended for All)

```bash
# === Price & Volume Data ===
ALPHAVANTAGE_API_KEY=your_key_here
MARKETSTACK_API_KEY=your_key_here

# === Social Sentiment ===
STOCKTWITS_CLIENT_ID=your_client_id
STOCKTWITS_CLIENT_SECRET=your_client_secret
STOCKTWITS_ACCESS_TOKEN=your_access_token

# === Options Data (Basic) ===
MARKETDATA_APP_API_KEY=your_key_here

# === Short Interest (Optional) ===
VALUEINVESTING_API_KEY=your_key_here

# === Dark Pool & Community ===
INSIGHT_API_BASE_URL=https://your-insight-instance
INSIGHT_API_KEY=your_key_here  # if auth required

# === Google Trends ===
# No API key required (uses pytrends)
```

### 2.2 Premium Providers (Optional)

```bash
# === Options Flow (Premium) ===
UNUSUALWHALES_API_KEY=your_key_here
OPTIONOMICS_API_KEY=your_key_here

# === Short Borrow (Premium) ===
S3_API_KEY=your_key_here
S3_API_SECRET=your_secret_here  # if required

# === Gamma / GEX (Premium) ===
GEX_API_KEY=your_key_here

# === Twitter / X (Premium) ===
TWITTER_API_KEY=your_key_here
TWITTER_API_SECRET=your_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token
```

---

## 3. Provider Details

### 3.1 Alpha Vantage

**Purpose**: Price data, OHLCV, technical indicators

**Factors Enabled**:
- Volume/volatility anomalies
- RVOL (relative volume)
- VWAP, band compression/expansion

**Environment Variables**:
```bash
ALPHAVANTAGE_API_KEY=your_key_here
```

**How to Get**:
1. Register at [Alpha Vantage](https://www.alphavantage.co/)
2. Generate free API key
3. Add to `.env` file

**Limitations**:
- Free tier: 5 API requests/minute, 500 requests/day
- Premium: Higher limits available

---

### 3.2 Marketstack

**Purpose**: Backup/alternative for end-of-day and intraday prices

**Factors Enabled**:
- Redundancy for VolumeAnomalyFactor if Alpha Vantage is rate-limited

**Environment Variables**:
```bash
MARKETSTACK_API_KEY=your_key_here
```

**How to Get**:
1. Register at [Marketstack](https://marketstack.com/)
2. Generate API key (free tier available)

---

### 3.3 StockTwits

**Purpose**: Real-time social sentiment velocity

**Factors Enabled**:
- Mentions per minute
- Change in bullish vs bearish tags
- Influencer-weighted activity

**Environment Variables**:
```bash
STOCKTWITS_CLIENT_ID=your_client_id
STOCKTWITS_CLIENT_SECRET=your_client_secret
STOCKTWITS_ACCESS_TOKEN=your_access_token
```

**How to Get**:
1. Register at [StockTwits Developer](https://stocktwits.com/developers)
2. Create an application
3. Generate OAuth credentials

**Implementation Note**:
- Auth flow should be abstracted to support different token strategies
- May only need bearer/access token depending on flow

---

### 3.4 MarketData.app

**Purpose**: Options quotes + Greeks

**Factors Enabled**:
- Basic options activity proxies
- Intraday OI/volume ratios
- Implied volatility change
- Simple gamma estimates

**Environment Variables**:
```bash
MARKETDATA_APP_API_KEY=your_key_here
```

**How to Get**:
1. Register at [MarketData.app](https://www.marketdata.app/)
2. Generate API key

---

### 3.5 ValueInvesting.io (Short Interest API)

**Purpose**: Short interest for backtesting and structural short exposure

**Factors Enabled**:
- Baseline short interest data
- Sanity check vs FINRA

**Environment Variables**:
```bash
VALUEINVESTING_API_KEY=your_key_here
```

**How to Get**:
1. Register at [ValueInvesting.io](https://www.valueinvesting.io/)
2. Subscribe to API plan

---

### 3.6 FINRA Short Interest

**Purpose**: Official short interest data (delayed, for structural context)

**Factors Enabled**:
- Structural short exposure baseline

**Environment Variables**:
- **None required** (public data)

**Implementation**:
- Use HTTP or scheduled batch download
- Parse and store in database
- Updated bi-monthly

---

### 3.7 Google Trends (pytrends)

**Purpose**: Retail attention trend for each symbol

**Factors Enabled**:
- Search interest slope
- Retail attention velocity
- Breakout detection

**Environment Variables**:
- **None required**

**Implementation**:
- Use `pytrends` Python library
- Anonymous requests (may configure proxies if needed)

---

### 3.8 Insight (Dark Pool Data)

**Purpose**: Dark pool volume and premium estimates

**Factors Enabled**:
- Dark pool activity
- Off-exchange volume
- Sentiment/news integration (optional)

**Environment Variables**:
```bash
INSIGHT_API_BASE_URL=https://your-insight-instance
INSIGHT_API_KEY=your_key_here  # if auth enabled
```

**Implementation**:
- Self-hosted or community instance
- May wrap behind API gateway

---

## 4. Premium Providers

### 4.1 Unusual Whales 💎

**Purpose**: High-quality options flow and sweeps

**Factors Enabled**:
- OptionsFlowFactor (premium quality)
- Sweep detection
- Large order alerts

**Environment Variables**:
```bash
UNUSUALWHALES_API_KEY=your_key_here
```

**How to Get**:
1. Subscribe at [Unusual Whales](https://unusualwhales.com/)
2. Get API access

**Cost**: Premium subscription required

---

### 4.2 Optionomics 💎

**Purpose**: Alternative/additional options analytics

**Environment Variables**:
```bash
OPTIONOMICS_API_KEY=your_key_here
```

---

### 4.3 S3 Partners 💎

**Purpose**: Real-time borrow data

**Factors Enabled**:
- Real-time borrow rate
- Utilization %
- Availability drop rate
- Short squeeze signals

**Environment Variables**:
```bash
S3_API_KEY=your_key_here
S3_API_SECRET=your_secret_here  # if required by vendor
```

**Cost**: Enterprise pricing

---

### 4.4 Gamma / GEX Provider 💎

**Purpose**: Dealer gamma exposure positioning

**Factors Enabled**:
- GammaFactor
- Dealer hedging pressure
- Pin/magnet levels

**Environment Variables**:
```bash
GEX_API_KEY=your_key_here
```

**Providers**:
- SpotGamma
- SqueezeMetrics
- Similar services

---

### 4.5 Twitter / X API 💎

**Purpose**: Additional sentiment velocity from X

**Environment Variables**:
```bash
TWITTER_API_KEY=your_key_here
TWITTER_API_SECRET=your_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token
```

**Note**: Twitter API has become expensive; StockTwits may be better ROI

---

## 5. Configuration

### 5.1 Feature Toggles in `momentum_config.yaml`

```yaml
momentum_layer:
  enabled: true  # Master toggle
  
  # Factor toggles
  use_options_flow: true
  use_borrow_rate: true
  use_volume_anomalies: true
  use_sentiment_velocity: true
  use_dark_pool: true
  use_gamma_exposure: false  # Default off until GEX provider live
  
  # Provider priorities (in order)
  options_flow_providers:
    - "UNUSUALWHALES"      # Try premium first
    - "OPTIONOMICS"        # Fallback
    - "MARKETDATA_APP"     # Basic fallback
  
  short_interest_providers:
    - "S3"                 # Real-time (premium)
    - "VALUEINVESTING_IO"  # Delayed
    - "FINRA"              # Official (most delayed)
  
  sentiment_providers:
    - "STOCKTWITS"         # Primary
    - "TWITTER"            # Optional
    - "GOOGLE_TRENDS"      # Backup
  
  dark_pool_providers:
    - "INSIGHT"
  
  # Scoring weights
  factor_weights:
    volume_anomaly: 0.20
    options_flow: 0.25
    sentiment_velocity: 0.20
    dark_pool: 0.15
    borrow_rate: 0.10
    gamma_exposure: 0.10
```

### 5.2 Runtime Behavior

Each provider adapter checks at runtime:
1. ✅ Is this provider enabled in config?
2. ✅ Are the necessary env vars set?
3. ⚠️ If not → log warning and fall back to next provider
4. ❌ If all providers fail → disable that factor

**Example Log**:
```json
{
  "event": "momentum_provider_unavailable",
  "provider": "UNUSUALWHALES",
  "factor": "options_flow",
  "reason": "missing_api_key",
  "fallback": "MARKETDATA_APP"
}
```

---

## 6. Environment Template

### `.env.example` Addition

Add to your existing `.env.example`:

```bash
#############################################
# Momentum Intelligence Layer (Optional)
#############################################

# === Core Data Providers ===
ALPHAVANTAGE_API_KEY=
MARKETSTACK_API_KEY=

# === Social / Sentiment ===
STOCKTWITS_CLIENT_ID=
STOCKTWITS_CLIENT_SECRET=
STOCKTWITS_ACCESS_TOKEN=

# Optional: Twitter / X (if used)
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_BEARER_TOKEN=

# === Options Data ===
MARKETDATA_APP_API_KEY=

# === Short Interest / Borrow ===
VALUEINVESTING_API_KEY=
S3_API_KEY=
S3_API_SECRET=

# === Dark Pool & Community Feeds ===
INSIGHT_API_BASE_URL=
INSIGHT_API_KEY=

# === Options Flow Premium ===
UNUSUALWHALES_API_KEY=
OPTIONOMICS_API_KEY=

# === Gamma / GEX ===
GEX_API_KEY=
```

---

## 7. Implementation Phases

### Phase 1: Core Infrastructure (Free Tier)
- ✅ Alpha Vantage (volume/volatility)
- ✅ StockTwits (sentiment velocity)
- ✅ Google Trends (retail attention)
- ✅ MarketData.app (basic options)
- ✅ FINRA (short interest baseline)

**Deliverable**: Basic momentum scoring with free providers

### Phase 2: Premium Options & Flow
- 💎 Unusual Whales integration
- 💎 Enhanced options flow detection
- 💎 Sweep alerts

**Deliverable**: High-quality options signals

### Phase 3: Advanced Factors
- 💎 S3 Partners (borrow data)
- 💎 Dark pool integration (Insight)
- 💎 Gamma exposure (GEX provider)

**Deliverable**: Complete momentum intelligence

---

## 8. Cost Estimates

### Free Tier (Phase 1)
- Alpha Vantage: Free (rate limited)
- StockTwits: Free
- Google Trends: Free
- MarketData.app: Free tier available
- FINRA: Free

**Total**: $0/month (with limitations)

### Basic Paid (Phase 2)
- Alpha Vantage Pro: ~$50/month
- Unusual Whales Basic: ~$50-100/month
- MarketData.app Pro: ~$20-50/month

**Total**: ~$120-200/month

### Full Premium (Phase 3)
- All Phase 2 providers
- S3 Partners: ~$500-1000/month (enterprise)
- GEX Provider: ~$100-500/month
- Twitter API: ~$100/month

**Total**: ~$800-1800/month

---

## 9. Security Best Practices

### API Key Storage

**DO**:
- ✅ Store all API keys in `.env` (gitignored)
- ✅ Use environment variables in production
- ✅ Rotate keys periodically
- ✅ Use separate keys for dev/prod

**DON'T**:
- ❌ Commit API keys to git
- ❌ Hard-code keys in Python files
- ❌ Share keys across environments
- ❌ Use production keys in testing

### Key Rotation

```bash
# Rotate keys regularly
# 1. Generate new key in provider dashboard
# 2. Update .env
# 3. Restart bot
# 4. Revoke old key after verification
```

---

## 10. Testing & Validation

### Verify Provider Setup

```bash
# Test script to validate all providers
python scripts/test_momentum_providers.py

# Expected output:
# ✅ Alpha Vantage: Connected
# ✅ StockTwits: Connected
# ⚠️  Unusual Whales: Missing API key (optional)
# ✅ Google Trends: Available
```

### Check Factor Availability

```bash
# Query which factors are active
curl http://localhost:8080/momentum/factors

# Response:
{
  "enabled_factors": [
    "volume_anomaly",
    "sentiment_velocity",
    "google_trends"
  ],
  "disabled_factors": [
    "options_flow",  // Missing Unusual Whales key
    "borrow_rate",   // Missing S3 key
    "gamma_exposure" // Disabled in config
  ]
}
```

---

## 11. Monitoring & Alerts

### Provider Health

Log provider health status:
```json
{
  "event": "momentum_provider_health_check",
  "providers": {
    "ALPHAVANTAGE": "healthy",
    "STOCKTWITS": "rate_limited",
    "UNUSUALWHALES": "unavailable"
  },
  "active_factors": 3,
  "disabled_factors": 2
}
```

### Alert on Provider Failures

```yaml
alerts:
  momentum_provider_down:
    enabled: true
    webhook: "https://your-webhook.com/alerts"
```

---

## 12. Roadmap

### Q1 2025
- [ ] Implement core provider adapters
- [ ] Basic momentum scoring (free tier)
- [ ] Testing framework
- [ ] Documentation

### Q2 2025
- [ ] Premium provider integration (Unusual Whales)
- [ ] Options flow factor
- [ ] Dynamic watchlist generation

### Q3 2025
- [ ] Borrow rate integration (S3 Partners)
- [ ] Dark pool factor
- [ ] Gamma exposure factor

### Q4 2025
- [ ] Machine learning enhancements
- [ ] Backtesting framework
- [ ] Production optimization

---

## 📚 Related Documentation

- **[CONFIGURATION.md](CONFIGURATION.md)** - Main config reference
- **[API_GUIDE.md](API_GUIDE.md)** - REST API for querying momentum scores
- **[QUICKSTART.md](QUICKSTART.md)** - Initial setup
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## 📞 Support

Questions about this feature:
1. Check [INDEX.md](INDEX.md) for related docs
2. Review `.env.example` for variable names
3. Test providers with `scripts/test_momentum_providers.py`
4. File issues with provider name and error logs

---

**Status**: 🚧 This is a specification document for a planned feature. Implementation TBD.

**Last Updated**: 2024-12-16

