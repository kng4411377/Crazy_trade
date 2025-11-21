# Documentation Map

Visual guide to all documentation in the Crazy Trade Bot project.

## 📁 File Structure

```
crazy_trade/
│
├── README.md                           ← Main project overview (START HERE!)
├── reset_bot.sh                        ← Interactive reset script
│
└── docs/                               ← All documentation
    │
    ├── INDEX.md                        ← Complete documentation index
    ├── DOC_MAP.md                      ← This file (visual guide)
    │
    ├── Getting Started/
    │   ├── QUICKSTART.md               ← 5-minute setup guide
    │   ├── SETUP_SECRETS.md            ← API keys configuration
    │   ├── QUICK_REFERENCE.md          ← Quick command reference
    │   └── README.md                   ← Documentation overview
    │
    ├── User Guides/
    │   ├── BOT_REFERENCE.md            ← Complete bot functionality
    │   ├── API_GUIDE.md                ← REST API for monitoring
    │   └── RESET_GUIDE.md              ← How to reset transactions
    │
    ├── Crypto Trading/
    │   ├── CRYPTO_GUIDE.md             ← Complete crypto guide
    │   ├── CRYPTO_SETUP.md             ← Step-by-step crypto setup
    │   ├── CRYPTO_SYMBOLS.md           ← Supported crypto pairs
    │   └── CRYPTO_LIMITATIONS.md       ← Crypto limitations
    │
    ├── Deployment/
    │   ├── UBUNTU_DEPLOYMENT.md        ← Ubuntu deployment (recommended)
    │   └── DEPLOY_TO_SERVER.md         ← General server deployment
    │
    ├── Technical/
    │   ├── DOCUMENTATION.md            ← Technical architecture
    │   └── CHANGELOG.md                ← Complete version history (all fixes) ⭐
    │
    └── Reference/
        ├── DOC_MAP.md                  ← This file (visual guide)
        └── QUICK_REFERENCE.md          ← Quick command reference
```

---

## 🎯 Reading Paths

### Path 1: Brand New User

```
1. README.md (project root)
   ↓
2. docs/QUICKSTART.md
   ↓
3. docs/SETUP_SECRETS.md
   ↓
4. docs/BOT_REFERENCE.md
   ↓
5. docs/QUICK_REFERENCE.md (keep this handy!)
```

### Path 2: Just Updated (v1.1.0)

```
1. docs/CHANGELOG.md ⭐ START HERE (see v1.1.0 section)
   ↓
2. Restart bot: ./run.sh
   ↓
3. docs/QUICK_REFERENCE.md (verify it's working)
```

### Path 3: Crypto Trading Setup

```
1. docs/CRYPTO_GUIDE.md (overview)
   ↓
2. docs/CRYPTO_SETUP.md (step-by-step)
   ↓
3. docs/CRYPTO_SYMBOLS.md (check supported pairs)
   ↓
4. docs/CRYPTO_LIMITATIONS.md (important!)
   ↓
5. config.crypto.yaml (configure)
```

### Path 4: Production Deployment

```
1. docs/UBUNTU_DEPLOYMENT.md (recommended)
   OR
   docs/DEPLOY_TO_SERVER.md (general)
   ↓
2. docs/API_GUIDE.md (set up monitoring)
   ↓
3. docs/QUICK_REFERENCE.md (operational commands)
   ↓
4. docs/RESET_GUIDE.md (when needed)
```

### Path 5: Troubleshooting

```
1. docs/CHANGELOG.md (all fixes documented)
   ↓
2. Check specific issue:
   • Trailing stops → CHANGELOG v1.1.0
   • Missing fills → CHANGELOG v1.0.1
   • Need to reset → docs/RESET_GUIDE.md
   • Crypto issues → docs/CRYPTO_LIMITATIONS.md
   ↓
3. docs/BOT_REFERENCE.md (general troubleshooting)
```

---

## 📋 Document Categories

### 🚀 Essential (Read These First)
- [README.md](../README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command reference
- [CHANGELOG.md](CHANGELOG.md) - Complete version history

### 📖 User Documentation
- [BOT_REFERENCE.md](BOT_REFERENCE.md) - Complete bot guide
- [API_GUIDE.md](API_GUIDE.md) - Remote monitoring
- [RESET_GUIDE.md](RESET_GUIDE.md) - Reset & restart

### 💰 Crypto Specific
- [CRYPTO_GUIDE.md](CRYPTO_GUIDE.md) - Complete crypto guide
- [CRYPTO_SETUP.md](CRYPTO_SETUP.md) - Setup instructions
- [CRYPTO_SYMBOLS.md](CRYPTO_SYMBOLS.md) - Supported pairs
- [CRYPTO_LIMITATIONS.md](CRYPTO_LIMITATIONS.md) - Limitations

### 🚀 Deployment
- [UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md) - Ubuntu (recommended)
- [DEPLOY_TO_SERVER.md](DEPLOY_TO_SERVER.md) - General

### 🔧 Technical
- [DOCUMENTATION.md](DOCUMENTATION.md) - Architecture
- [CHANGELOG.md](CHANGELOG.md) - Complete version history with all fixes ⭐

### 📋 Reference
- [INDEX.md](INDEX.md) - Complete index
- [DOC_MAP.md](DOC_MAP.md) - This file (visual guide)
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick commands

---

## 🔗 Quick Links by Task

### "I just want to get started"
→ [QUICKSTART.md](QUICKSTART.md)

### "I just updated to v1.1.0"
→ [CHANGELOG.md v1.1.0](CHANGELOG.md#110---2024-11-21)

### "I want to trade crypto"
→ [CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)

### "I want to deploy to a server"
→ [UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md)

### "I want to monitor remotely"
→ [API_GUIDE.md](API_GUIDE.md)

### "I need to reset/start over"
→ [RESET_GUIDE.md](RESET_GUIDE.md)

### "Trailing stop didn't get placed"
→ [CHANGELOG.md v1.1.0](CHANGELOG.md#110---2024-11-21)

### "I'm missing fills after restart"
→ [CHANGELOG.md v1.0.1](CHANGELOG.md#101---2024-11-20)

### "Show me all commands"
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### "What's the bot's architecture?"
→ [DOCUMENTATION.md](DOCUMENTATION.md)

### "Show me everything"
→ [INDEX.md](INDEX.md)

---

## 📊 Document Relationships

```
README.md (root)
    ├── Points to: docs/INDEX.md (complete index)
    ├── Points to: docs/WHAT_CHANGED.md (latest updates)
    └── Points to: docs/QUICKSTART.md (getting started)

docs/INDEX.md
    ├── References: All documentation files
    ├── Organized by: Category & reading path
    └── Points to: DOC_MAP.md (this file)

docs/CHANGELOG.md (complete version history)
    ├── Contains: All version details
    ├── Contains: All technical fixes
    └── Contains: Upgrade instructions

docs/QUICKSTART.md
    ├── Points to: SETUP_SECRETS.md (API keys)
    ├── Points to: BOT_REFERENCE.md (features)
    └── Points to: QUICK_REFERENCE.md (commands)

docs/CRYPTO_GUIDE.md
    ├── Points to: CRYPTO_SETUP.md (setup)
    ├── Points to: CRYPTO_SYMBOLS.md (symbols)
    └── Points to: CRYPTO_LIMITATIONS.md (limits)

docs/BOT_REFERENCE.md
    ├── Points to: API_GUIDE.md (monitoring)
    ├── Points to: RESET_GUIDE.md (reset)
    └── Points to: CHANGELOG.md (fixes/troubleshooting)
```

---

## 📝 Document Sizes (Approx)

| Category | Document | Size | Reading Time |
|----------|----------|------|--------------|
| Essential | README.md | ~15 KB | 10 min |
| Essential | QUICKSTART.md | ~5 KB | 3 min |
| Essential | QUICK_REFERENCE.md | ~3 KB | 2 min |
| Essential | CHANGELOG.md | ~25 KB | 15 min |
| User Guide | BOT_REFERENCE.md | ~20 KB | 15 min |
| User Guide | API_GUIDE.md | ~10 KB | 7 min |
| User Guide | RESET_GUIDE.md | ~8 KB | 5 min |
| Crypto | CRYPTO_GUIDE.md | ~15 KB | 10 min |
| Crypto | CRYPTO_SETUP.md | ~8 KB | 5 min |
| Deployment | UBUNTU_DEPLOYMENT.md | ~12 KB | 8 min |
| Technical | DOCUMENTATION.md | ~25 KB | 20 min |
| Index | INDEX.md | ~10 KB | 5 min |

**Total documentation:** ~130 KB  
**Complete read time:** ~1.5 hours (but you don't need to read everything!)

---

## 🎯 Recommended Reading Order

### Minimal Path (20 minutes)
Just want to get started quickly?
1. [QUICKSTART.md](QUICKSTART.md) - 3 min
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 2 min
3. Start bot, refer back as needed

### Standard Path (45 minutes)
Want to understand the system well?
1. [README.md](../README.md) - 10 min
2. [QUICKSTART.md](QUICKSTART.md) - 3 min
3. [BOT_REFERENCE.md](BOT_REFERENCE.md) - 15 min
4. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 2 min
5. [API_GUIDE.md](API_GUIDE.md) - 7 min
6. [RESET_GUIDE.md](RESET_GUIDE.md) - 5 min

### Complete Path (2+ hours)
Want to master everything?
1. Read everything in [INDEX.md](INDEX.md) order
2. Study technical fixes
3. Review CHANGELOG.md

---

## 🔄 Keeping Docs Up to Date

When you update the bot:
1. Check [CHANGELOG.md](CHANGELOG.md) for changes
2. Read [WHAT_CHANGED.md](WHAT_CHANGED.md) for summaries
3. Review relevant fix docs if issues were addressed

When reading docs:
- All links are relative within `/docs`
- Links to project root use `../`
- External links are clearly marked

---

## 📞 Need Help?

If you can't find what you're looking for:
1. Check [INDEX.md](INDEX.md) - Complete index
2. Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands
3. Check [BOT_REFERENCE.md](BOT_REFERENCE.md) - General troubleshooting
4. Check [CHANGELOG.md](CHANGELOG.md) - Recent fixes

Still stuck? File an issue with:
- What you're trying to do
- What documentation you've read
- What error you're seeing

---

**Happy Trading! 📈**

