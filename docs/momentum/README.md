# 🎯 Momentum Intelligence Layer Documentation

The Momentum Intelligence Layer dynamically discovers and ranks trending stocks based on multiple data sources, helping you identify high-probability momentum plays before they break out.

---

## 📚 Documentation Index

### Getting Started
1. **[QUICKSTART.md](QUICKSTART.md)** - Set up and run your first momentum scan
   - API key setup
   - Environment configuration
   - Running test scans
   - Example usage

### Trading Strategies
2. **[STRATEGY.md](STRATEGY.md)** - Multi-phase momentum strategy guide
   - Why simple averaging misses opportunities
   - 4-phase momentum analysis
   - Early signal detection
   - Trading workflows

### Provider Setup
3. **[APEWISDOM_SETUP.md](APEWISDOM_SETUP.md)** - Reddit sentiment via Apewisdom
   - Free tier usage (no API key!)
   - Update schedule (2x daily)
   - Best practices
   - Configuration options

### Configuration
4. **[MOMENTUM_CONFIG_GUIDE.md](../MOMENTUM_CONFIG_GUIDE.md)** - Detailed configuration reference
   - Factor weights
   - Provider settings
   - Thresholds and filters
   - Advanced options

---

## 🚀 Quick Links

### Run a Scan
```bash
# Basic scan
python scripts/scan_momentum.py

# Advanced options
python scripts/scan_momentum.py --mode max --top 20

# Volume-only mode (no Reddit)
python scripts/scan_momentum.py --no-retail
```

### Key Concepts

**Data Sources:**
- **YFinance** - Real-time volume data (free, unlimited)
- **Apewisdom** - Reddit/WSB sentiment (free, 2x daily updates)

**Momentum Phases:**
1. 🦍 **Early Signals** - Reddit buzz before volume (best entries)
2. 🔥 **Volume Breakouts** - Volume confirming now (scalps)
3. 🏆 **Confirmed Momentum** - Both factors strong (late stage)
4. 📊 **Top Overall** - Composite ranking (watchlist)

---

## 🎯 Recommended Reading Order

1. Start with **QUICKSTART.md** to get up and running
2. Read **STRATEGY.md** to understand the trading approach
3. Check **APEWISDOM_SETUP.md** for provider details
4. Refer to **MOMENTUM_CONFIG_GUIDE.md** for customization

---

## 🔗 Related Documentation

- [Main README](../../README.md) - Project overview
- [Configuration Guide](../CONFIGURATION.md) - Main bot configuration
- [API Guide](../API_GUIDE.md) - REST API documentation

---

## ❓ Need Help?

- Check the [FAQ section](QUICKSTART.md#faq) in the quickstart guide
- Review [example scans](../../scripts/scan_momentum.py) in the scripts directory
- See [archived development notes](../archive/) for technical deep-dives

