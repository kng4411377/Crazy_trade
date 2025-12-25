# Documentation Index

Complete guide to the Crazy Trade Bot documentation.

---

## 📚 Documentation Structure

```
docs/
├── Getting Started/
│   ├── QUICKSTART.md          # 5-minute setup guide
│   ├── SETUP_SECRETS.md       # API key configuration
│   └── CONFIGURATION.md       # Config file reference
│
├── User Guides/
│   ├── CRYPTO_GUIDE.md        # 24/7 cryptocurrency trading
│   ├── UPDATING_CONFIG.md     # Merging config updates
│   ├── RESET_GUIDE.md         # Reset paper account
│   └── QUICK_REFERENCE.md     # Command cheat sheet
│
├── Technical/
│   ├── BOT_REFERENCE.md       # Complete bot functionality
│   ├── API_GUIDE.md           # REST API documentation
│   ├── DOCUMENTATION.md       # Architecture details
│   └── CHANGELOG.md           # Version history
│
└── Deployment/
    ├── UBUNTU_DEPLOYMENT.md   # Ubuntu server setup
    └── DEPLOY_TO_SERVER.md    # General deployment
```

---

## 🚀 Getting Started

### New Users Start Here

1. **[QUICKSTART.md](QUICKSTART.md)** ⭐
   - 5-minute setup guide
   - Installation steps
   - First run walkthrough
   - Basic configuration

2. **[SETUP_SECRETS.md](SETUP_SECRETS.md)**
   - Alpaca API key setup
   - Security best practices
   - Environment variables
   - Troubleshooting auth issues

3. **[CONFIGURATION.md](CONFIGURATION.md)**
   - Complete config.yaml reference
   - All configuration options explained
   - Entry strategies (current/SMA/opening)
   - Risk management settings
   - Examples for different strategies

---

## 📖 User Guides

### Core Functionality

**[BOT_REFERENCE.md](BOT_REFERENCE.md)** - Complete bot functionality
- How the state machine works
- Entry order behavior and re-arming
- Trailing stop management
- Cooldown periods explained
- Position sizing logic
- Safety features

**[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command cheat sheet
- Common commands
- Useful SQL queries
- Log filtering
- Quick diagnostics

### Momentum Intelligence Layer 🚀

**[momentum/README.md](momentum/README.md)** - Momentum layer overview
- Dynamic stock discovery and ranking
- Multi-phase momentum analysis
- Reddit + Volume signals
- Trading strategy guides

**[momentum/QUICKSTART.md](momentum/QUICKSTART.md)** - Get started with momentum scanning
- Setup providers (YFinance, Apewisdom)
- Run your first scan
- Interpret results

**[momentum/STRATEGY.md](momentum/STRATEGY.md)** - Multi-phase trading strategy
- Why simple averaging misses opportunities
- Early signal detection (Reddit buzz pre-volume)
- Volume confirmation strategies
- 4-phase momentum workflow

### Specialized Topics

**[CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)** - 24/7 cryptocurrency trading
- Setup for crypto-only trading
- Supported crypto pairs
- Crypto-specific limitations
- Example configurations
- Best practices

**[CRYPTO_SYMBOLS.md](CRYPTO_SYMBOLS.md)** - Supported symbols
- All verified cryptocurrency pairs
- Which cryptos work on Alpaca
- Testing notes

**[CRYPTO_LIMITATIONS.md](CRYPTO_LIMITATIONS.md)** - Known limitations
- Alpaca crypto API limitations
- Workarounds and solutions
- What features don't work for crypto

**[UPDATING_CONFIG.md](UPDATING_CONFIG.md)** - Merging config updates
- How to update config.yaml safely
- Smart merge tools (merge_config.py)
- Viewing differences
- Rollback procedures

**[RESET_GUIDE.md](RESET_GUIDE.md)** - Reset & start over
- How to reset paper trading account
- Clear database
- Fresh start procedures
- Backup/restore

---

## 🔧 Technical Documentation

### API & Integration

**[API_GUIDE.md](API_GUIDE.md)** - REST API for monitoring
- API endpoints reference
- Running the API server
- Remote monitoring
- Authentication
- Example requests

### Architecture & Design

**[DOCUMENTATION.md](DOCUMENTATION.md)** - Technical architecture
- System architecture
- Component overview
- Data flow diagrams
- Design decisions

**[CHANGELOG.md](CHANGELOG.md)** - Version history
- All versions and changes
- New features by version
- Breaking changes
- Migration guides

**Momentum Intelligence Layer** - Dynamic Momentum Scanning 🚀
- **[momentum/README.md](momentum/README.md)** - Momentum documentation index
- **[momentum/QUICKSTART.md](momentum/QUICKSTART.md)** - Quick setup guide
- **[momentum/STRATEGY.md](momentum/STRATEGY.md)** - Multi-phase trading strategy
- **[momentum/APEWISDOM_SETUP.md](momentum/APEWISDOM_SETUP.md)** - Reddit sentiment setup
- **[MOMENTUM_CONFIG_GUIDE.md](MOMENTUM_CONFIG_GUIDE.md)** - Configuration reference
- **[MOMENTUM_LAYER_REQUIREMENTS.md](MOMENTUM_LAYER_REQUIREMENTS.md)** - Technical specification

---

## 🚀 Deployment

### Server Deployment

**[UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md)** - Ubuntu setup
- Complete Ubuntu 22.04 deployment
- Systemd service setup
- Autostart configuration
- Log management
- Security hardening

**[DEPLOY_TO_SERVER.md](DEPLOY_TO_SERVER.md)** - General deployment
- General server deployment guide
- Background running
- Process management
- Monitoring setup

---

## 📋 Quick Reference by Topic

### Setup & Installation

| Topic | Document |
|-------|----------|
| First-time setup | [QUICKSTART.md](QUICKSTART.md) |
| API keys | [SETUP_SECRETS.md](SETUP_SECRETS.md) |
| Configuration | [CONFIGURATION.md](CONFIGURATION.md) |

### Trading Strategies

| Topic | Document |
|-------|----------|
| Entry strategies | [CONFIGURATION.md](CONFIGURATION.md#entry-strategies) |
| Stock trading | [BOT_REFERENCE.md](BOT_REFERENCE.md) |
| Crypto trading | [CRYPTO_GUIDE.md](CRYPTO_GUIDE.md) |
| Momentum scanning | [momentum/README.md](momentum/README.md) 🚀 |
| Multi-phase momentum | [momentum/STRATEGY.md](momentum/STRATEGY.md) |
| Risk management | [CONFIGURATION.md](CONFIGURATION.md#risk-management) |

### Operation & Monitoring

| Topic | Document |
|-------|----------|
| Running the bot | [QUICKSTART.md](QUICKSTART.md#running) |
| Monitoring | [API_GUIDE.md](API_GUIDE.md) |
| Performance tracking | [BOT_REFERENCE.md](BOT_REFERENCE.md#performance) |
| Logs | [QUICK_REFERENCE.md](QUICK_REFERENCE.md#logs) |

### Troubleshooting

| Topic | Document |
|-------|----------|
| Common issues | README.md → Troubleshooting |
| Reset & fresh start | [RESET_GUIDE.md](RESET_GUIDE.md) |
| Config updates | [UPDATING_CONFIG.md](UPDATING_CONFIG.md) |
| Crypto issues | [CRYPTO_LIMITATIONS.md](CRYPTO_LIMITATIONS.md) |

### Deployment

| Topic | Document |
|-------|----------|
| Ubuntu server | [UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md) |
| General deployment | [DEPLOY_TO_SERVER.md](DEPLOY_TO_SERVER.md) |
| Background running | [DEPLOY_TO_SERVER.md](DEPLOY_TO_SERVER.md#background) |

---

## 🔍 Finding What You Need

### "I want to..."

**...get started quickly**
→ [QUICKSTART.md](QUICKSTART.md)

**...understand how the bot works**
→ [BOT_REFERENCE.md](BOT_REFERENCE.md)

**...trade cryptocurrency**
→ [CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)

**...configure entry strategies**
→ [CONFIGURATION.md](CONFIGURATION.md) → Entry Strategies section

**...deploy to a server**
→ [UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md) or [DEPLOY_TO_SERVER.md](DEPLOY_TO_SERVER.md)

**...monitor remotely**
→ [API_GUIDE.md](API_GUIDE.md)

**...update my config safely**
→ [UPDATING_CONFIG.md](UPDATING_CONFIG.md)

**...reset and start over**
→ [RESET_GUIDE.md](RESET_GUIDE.md)

**...understand cooldown periods**
→ [BOT_REFERENCE.md](BOT_REFERENCE.md) → Cooldown section

**...scan for momentum stocks** 🚀
→ [momentum/QUICKSTART.md](momentum/QUICKSTART.md)

**...catch early Reddit signals**
→ [momentum/STRATEGY.md](momentum/STRATEGY.md) → Early Signals section

**...see what changed in updates**
→ [CHANGELOG.md](CHANGELOG.md)

---

## 📖 Reading Order

### Recommended Path for New Users

1. **[QUICKSTART.md](QUICKSTART.md)** - Get bot running (5 min)
2. **[CONFIGURATION.md](CONFIGURATION.md)** - Understand your options (10 min)
3. **[BOT_REFERENCE.md](BOT_REFERENCE.md)** - Learn how it works (15 min)
4. **[CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)** - If trading crypto (10 min)
5. **[API_GUIDE.md](API_GUIDE.md)** - If monitoring remotely (5 min)

### Total: ~45 minutes to full understanding

---

## 🆕 Recent Documentation Updates

### Latest Additions

- **[UPDATING_CONFIG.md](UPDATING_CONFIG.md)** - New guide for merging config updates
- **[CONFIGURATION.md](CONFIGURATION.md)** - Added entry_price_strategy documentation
- **[CHANGELOG.md](CHANGELOG.md)** - Updated with latest features (SMA strategy, TIF config)

### Recently Updated

- **README.md** - Corrected IBKR → Alpaca references, updated auto-rearm explanation
- **[CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)** - Added GTC time-in-force notes
- **[SETUP_SECRETS.md](SETUP_SECRETS.md)** - Updated file structure (gitignored configs)

---

## 📝 Documentation Standards

### Format Guidelines

- **Headers**: Use clear, descriptive headers
- **Code Blocks**: Always specify language (```bash, ```yaml, ```python)
- **Examples**: Provide real, working examples
- **Links**: Use relative links within docs/ folder
- **Updates**: Update INDEX.md when adding new docs

### Contributing Documentation

When adding new documentation:
1. Create file in appropriate category
2. Add entry to this INDEX.md
3. Update README.md if major feature
4. Add to CHANGELOG.md
5. Link from related documents

---

## 🔗 External Resources

- **Alpaca Docs**: https://alpaca.markets/docs/
- **Alpaca API**: https://alpaca.markets/docs/api-references/trading-api/
- **Paper Trading**: https://app.alpaca.markets/paper/dashboard/overview
- **Alpaca Markets**: https://alpaca.markets/

---

## 📞 Need Help?

1. **Search this index** for your topic
2. **Check README.md** troubleshooting section
3. **Review logs**: `tail -f bot.log | jq .`
4. **Check database**: `sqlite3 bot.db "SELECT * FROM state"`
5. **File an issue** with logs (redact API keys!)

---

Last Updated: 2024-12-22  
Version: 1.4.0 (with Momentum Intelligence Layer)
