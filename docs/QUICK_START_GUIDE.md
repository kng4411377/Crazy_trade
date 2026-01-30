# Quick Start Guide – Essential Scripts

Get the bot running and know which scripts to use day-to-day.

---

## 1. First-time setup

```bash
./setup.sh
```

Then edit **`secrets.yaml`** (Alpaca API keys) and **`config.yaml`** (watchlist, allocation, mode).  
All secrets go in **`secrets.yaml`** only — see [SETUP_SECRETS.md](SETUP_SECRETS.md).

---

## 2. Essential scripts (what to run)

| What you want              | Command |
|----------------------------|--------|
| **Run the bot**            | `./run.sh` or `python3 main.py` |
| **Run API server**        | `./run_api.sh` |
| **Run bot + API + system monitor** (PM2) | `pm2 start ecosystem.config.js` |
| **First-time setup**      | `./setup.sh` |
| **Test Alpaca connection**| `python3 test_connection.py` |
| **Test Gemini (if used)** | `python scripts/test_gemini.py --api-only` |
| **Run tests**              | `./run_tests.sh` or `pytest` |

---

## 3. Running the bot

**Foreground (development):**
```bash
./run.sh
# or: python3 main.py
# optional config file: ./run.sh path/to/config.yaml
```

**With system monitor (recommended on a server):**  
The system monitor checks CPU/temperature every 30s and writes `health_status.json`.  
If CPU > 80% or temp ≥ 75°C it sets `low_power_mode: true`; the bot then runs only RSI (no VWAP/OBV/ATR) until recovery.

```bash
# Start bot + monitor together with PM2
mkdir -p logs
pm2 start ecosystem.config.js

# Or only bot + monitor (no API)
pm2 start ecosystem.config.js --only crazy-trade-bot --only crazy-trade-monitor
```

**PM2 useful commands:**
```bash
pm2 status
pm2 logs crazy-trade-bot
pm2 logs crazy-trade-monitor
pm2 monit
pm2 stop all
pm2 delete all
```

---

## 4. Verify before trading

1. **Alpaca:** `python3 test_connection.py` → expect “Connected” and account value.
2. **Gemini (if enabled):** `python scripts/test_gemini.py --api-only`.
3. **Config:** Start in **paper** mode in `config.yaml` (`mode: "paper"`).

---

## 5. Where things are

| Item            | Location |
|-----------------|----------|
| API keys        | `secrets.yaml` (gitignored) |
| Strategy/config | `config.yaml` (gitignored) |
| Templates       | `config.yaml.example`, `secrets.yaml.example` |
| Logs            | `bot.log`, or `./logs/` when using PM2 |
| DB              | `bot.db` (SQLite) |
| Health (monitor)| `health_status.json` (written by `system_monitor.py`) |

---

## 6. More docs

- **Secrets (single file):** [SETUP_SECRETS.md](SETUP_SECRETS.md)  
- **Config reference:** [CONFIGURATION.md](CONFIGURATION.md)  
- **5-minute setup:** [QUICKSTART.md](QUICKSTART.md)  
- **API endpoints:** [API_GUIDE.md](API_GUIDE.md)  
- **Crypto:** [CRYPTO_GUIDE.md](CRYPTO_GUIDE.md)
