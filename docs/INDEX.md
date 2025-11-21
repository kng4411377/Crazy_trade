# Documentation Index

Complete guide to all documentation in the Crazy Trade Bot project.

**🗺️ Visual Guide:** See [DOC_MAP.md](DOC_MAP.md) for a visual map of how all docs are organized and recommended reading paths.

## 📚 Table of Contents

### 🚀 Getting Started (Start Here!)
- **[QUICKSTART.md](QUICKSTART.md)** - Quick 5-minute setup guide
- **[SETUP_SECRETS.md](SETUP_SECRETS.md)** - How to configure API keys and secrets
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference card for common tasks
- **[README.md](README.md)** - Main documentation overview

### 📖 User Guides
- **[BOT_REFERENCE.md](BOT_REFERENCE.md)** - Complete bot functionality reference
- **[API_GUIDE.md](API_GUIDE.md)** - REST API documentation for remote monitoring
- **[RESET_GUIDE.md](RESET_GUIDE.md)** - How to reset transactions and start over

### 💰 Crypto Trading
- **[CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)** - Complete guide for crypto trading setup
- **[CRYPTO_SETUP.md](CRYPTO_SETUP.md)** - Step-by-step crypto configuration
- **[CRYPTO_SYMBOLS.md](CRYPTO_SYMBOLS.md)** - List of supported crypto symbols
- **[CRYPTO_LIMITATIONS.md](CRYPTO_LIMITATIONS.md)** - Known limitations for crypto trading

### 🚀 Deployment
- **[UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md)** - Ubuntu-specific deployment guide (recommended)
- **[DEPLOY_TO_SERVER.md](DEPLOY_TO_SERVER.md)** - General server deployment guide

### 🔧 Technical Documentation
- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Technical architecture overview
- **[CHANGELOG.md](CHANGELOG.md)** - Complete version history with all fixes and updates ⭐

### 📋 Reference & Quick Guides
- **[DOC_MAP.md](DOC_MAP.md)** - Visual documentation map (how docs are organized)
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference for common commands

---

## 📖 Documentation by Topic

### 🎯 First Time Setup
1. Read overview: [Main README](../README.md)
2. Quick start: [QUICKSTART.md](QUICKSTART.md)
3. Configure secrets: [SETUP_SECRETS.md](SETUP_SECRETS.md)
4. Understand the bot: [BOT_REFERENCE.md](BOT_REFERENCE.md)
5. Learn common commands: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### 💰 Crypto Trading Setup
1. Read crypto guide: [CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)
2. Follow setup steps: [CRYPTO_SETUP.md](CRYPTO_SETUP.md)
3. Check supported symbols: [CRYPTO_SYMBOLS.md](CRYPTO_SYMBOLS.md)
4. Understand limitations: [CRYPTO_LIMITATIONS.md](CRYPTO_LIMITATIONS.md)

### 🚀 Production Deployment
1. Deploy to Ubuntu: [UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md) (recommended)
2. Alternative deployment: [DEPLOY_TO_SERVER.md](DEPLOY_TO_SERVER.md)
3. Set up monitoring: [API_GUIDE.md](API_GUIDE.md)

### 🔧 Daily Operations
1. Monitor remotely: [API_GUIDE.md](API_GUIDE.md)
2. Check quick commands: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
3. Reset when needed: [RESET_GUIDE.md](RESET_GUIDE.md)
4. Track changes: [CHANGELOG.md](CHANGELOG.md)

### 🆕 Latest Updates (Nov 2024)
1. Read version history: [CHANGELOG.md](CHANGELOG.md#110---2024-11-21) ← Complete details
2. Quick commands: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
3. Just restart: `./run.sh`

---

## 🔍 Quick Reference

### Common Tasks

| Task | Documentation |
|------|---------------|
| First time setup | [QUICKSTART.md](QUICKSTART.md) |
| Configure API keys | [SETUP_SECRETS.md](SETUP_SECRETS.md) |
| Trade crypto | [CRYPTO_GUIDE.md](CRYPTO_GUIDE.md) |
| Deploy to server | [UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md) |
| Monitor remotely | [API_GUIDE.md](API_GUIDE.md) |
| Reset database | [RESET_GUIDE.md](RESET_GUIDE.md) |
| Understand architecture | [DOCUMENTATION.md](DOCUMENTATION.md) |

### Troubleshooting

| Issue | Documentation |
|-------|---------------|
| Trailing stop not placed | [CHANGELOG.md v1.1.0](CHANGELOG.md#110---2024-11-21) |
| Too many trades after stops | [CHANGELOG.md v1.1.0](CHANGELOG.md#110---2024-11-21) |
| Missing fills after restart | [CHANGELOG.md v1.0.1](CHANGELOG.md#101---2024-11-20) |
| Crypto not working | [CRYPTO_LIMITATIONS.md](CRYPTO_LIMITATIONS.md) |
| General issues | [BOT_REFERENCE.md](BOT_REFERENCE.md) |

---

## 📝 Document Categories

### User Documentation
Essential reading for users:
- QUICKSTART.md
- BOT_REFERENCE.md
- API_GUIDE.md
- RESET_GUIDE.md
- CRYPTO_GUIDE.md
- SETUP_SECRETS.md

### Deployment Documentation
For setting up production environments:
- DEPLOY_TO_SERVER.md
- UBUNTU_DEPLOYMENT.md

### Technical Documentation
For developers and troubleshooting:
- DOCUMENTATION.md
- FILL_SYNC_FIX.md
- CRYPTO_FIXES_SUMMARY.md
- UUID_FIX_SUMMARY.md
- CHANGELOG.md

### Reference Documentation
Lists and specifications:
- CRYPTO_SYMBOLS.md
- CRYPTO_LIMITATIONS.md

---

## 🆕 Recent Updates (v1.1.0 - November 21, 2024)

### Latest Changes - Trailing Stop & Cooldown Fixes

**What's New:**
- ✅ Trailing stops now placed reliably (up to 3 automatic retries)
- ✅ Cooldown extended from 20 minutes to 1 day after stop-outs
- ✅ Better logging for trailing stop placement and cooldowns
- ✅ Critical alerts if trailing stop placement fails

**Also Fixed:**
- ✅ Fill synchronization (v1.0.1) - Bot now captures all fills even after restart
- ✅ UUID support for Alpaca order IDs
- ✅ Crypto trading enhancements

📖 **See all changes:** [CHANGELOG.md](CHANGELOG.md) - Complete version history with detailed technical information for all fixes and updates

---

## 🤔 Not Sure Where to Start?

### 🆕 Just Updated the Bot?
1. [CHANGELOG.md](CHANGELOG.md#110---2024-11-21) - See what's new (v1.1.0)
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands
3. Just restart: `./run.sh`

### 👤 Brand New Users
1. [Main README](../README.md) - Project overview
2. [QUICKSTART.md](QUICKSTART.md) - Get up and running in 5 minutes
3. [BOT_REFERENCE.md](BOT_REFERENCE.md) - Understand what the bot does
4. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Handy command reference

### 💰 Crypto Traders
1. [CRYPTO_GUIDE.md](CRYPTO_GUIDE.md) - Complete crypto setup
2. [CRYPTO_SETUP.md](CRYPTO_SETUP.md) - Step-by-step instructions
3. [CRYPTO_SYMBOLS.md](CRYPTO_SYMBOLS.md) - See supported pairs
4. [CRYPTO_LIMITATIONS.md](CRYPTO_LIMITATIONS.md) - What to know

### 👨‍💻 Developers/Advanced Users
1. [DOCUMENTATION.md](DOCUMENTATION.md) - Technical architecture
2. [API_GUIDE.md](API_GUIDE.md) - API integration
3. [CHANGELOG.md](CHANGELOG.md) - Version history

### 🚀 Production Deployment
1. [UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md) - Deploy to server (recommended)
2. [DEPLOY_TO_SERVER.md](DEPLOY_TO_SERVER.md) - General deployment
3. [API_GUIDE.md](API_GUIDE.md) - Set up monitoring

### 🔧 Troubleshooting
1. [CHANGELOG.md](CHANGELOG.md) - All fixes and solutions
2. [RESET_GUIDE.md](RESET_GUIDE.md) - How to reset
3. [BOT_REFERENCE.md](BOT_REFERENCE.md) - General troubleshooting
4. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands

---

## 📞 Need Help?

If you can't find what you're looking for:
1. Check the main [README.md](../README.md) in the project root
2. Review [BOT_REFERENCE.md](BOT_REFERENCE.md) for comprehensive bot documentation
3. Look at the examples in `/examples/` directory
4. Check recent fixes in [CHANGELOG.md](CHANGELOG.md)

