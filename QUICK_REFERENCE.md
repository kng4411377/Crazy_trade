# Quick Reference Card

## 🔄 How to Reset Transactions

### Easy Way (Interactive)
```bash
./reset_bot.sh
```
Pick your option from the menu!

### Manual Commands

**Close positions & cancel orders:**
```bash
python scripts/reset_paper_account.py
```

**Delete transaction history:**
```bash
rm bot.db
```

**Full reset (everything):**
```bash
python scripts/reset_paper_account.py && rm bot.db
```

**Clear cooldowns only:**
```bash
sqlite3 bot.db "UPDATE state SET cooldown_until_ts = NULL;"
```

---

## 📚 Documentation Quick Links

| What You Need | Where to Find It |
|---------------|------------------|
| **All Documentation** | `docs/INDEX.md` |
| **Getting Started** | `docs/QUICKSTART.md` |
| **Reset Guide** | `docs/RESET_GUIDE.md` |
| **Bot Features** | `docs/BOT_REFERENCE.md` |
| **API Monitoring** | `docs/API_GUIDE.md` |
| **Crypto Trading** | `docs/CRYPTO_GUIDE.md` |
| **Deployment** | `docs/UBUNTU_DEPLOYMENT.md` |

---

## 🚀 Common Commands

```bash
# Start the bot
./run.sh

# Check status
python scripts/check_status.py

# View performance
python scripts/show_performance.py

# Export trades
python scripts/export_trades.py

# Reset (interactive)
./reset_bot.sh

# View logs
tail -f bot.log | jq .
```

---

## 🗂️ Project Structure

```
crazy_trade/
├── README.md              ← Main README
├── reset_bot.sh          ← Interactive reset tool
├── run.sh                ← Start the bot
├── config.yaml           ← Configuration
│
├── docs/                 ← All documentation here
│   ├── INDEX.md          ← Documentation index
│   ├── RESET_GUIDE.md    ← How to reset
│   ├── QUICKSTART.md     ← Getting started
│   └── ...
│
├── scripts/              ← Utility scripts
│   ├── reset_paper_account.py
│   ├── check_status.py
│   ├── show_performance.py
│   └── export_trades.py
│
└── src/                  ← Bot source code
    ├── bot.py
    ├── alpaca_client.py
    └── ...
```

---

## ⚡ Quick Answers

**Q: How do I start over completely?**
```bash
./reset_bot.sh   # Choose option 3 (Full Reset)
./run.sh         # Start fresh
```

**Q: How do I just close positions but keep history?**
```bash
./reset_bot.sh   # Choose option 1 (Account Only)
```

**Q: How do I clear my transaction database?**
```bash
./reset_bot.sh   # Choose option 2 (Database Only)
```

**Q: Where's all the documentation?**
```bash
open docs/INDEX.md   # Opens the documentation index
```

**Q: Symbol stuck in cooldown?**
```bash
./reset_bot.sh   # Choose option 4 (Clear Cooldowns)
```

---

## 📖 More Help

- **Detailed reset guide**: `docs/RESET_GUIDE.md`
- **All documentation**: `docs/INDEX.md`
- **Organization summary**: `ORGANIZATION_SUMMARY.md`

