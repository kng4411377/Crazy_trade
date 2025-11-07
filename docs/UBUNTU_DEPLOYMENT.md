# Ubuntu Server Deployment Guide

Complete guide to running the Crazy Trade Bot on Ubuntu Server.

## 🚀 Quick Start (Background Mode)

### Method 1: Simple Background Script (Recommended for Testing)

```bash
# Start bot and API in background
./start_background.sh start

# Check status
./start_background.sh status

# View logs
./start_background.sh logs

# Stop everything
./start_background.sh stop
```

---

## 🔧 Method 2: Systemd Service (Recommended for Production)

### Step 1: Prepare Service Files

Edit the service files with your actual paths:

```bash
# Edit bot service
nano crazy-trade-bot.service

# Replace:
#   YOUR_USERNAME with your actual username (e.g., ubuntu, tony)
#   /home/YOUR_USERNAME/crazy_trade with your actual path
```

### Step 2: Install Services

```bash
# Copy service files
sudo cp crazy-trade-bot.service /etc/systemd/system/
sudo cp crazy-trade-api.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable crazy-trade-bot
sudo systemctl enable crazy-trade-api
```

### Step 3: Start Services

```bash
# Start bot
sudo systemctl start crazy-trade-bot

# Start API
sudo systemctl start crazy-trade-api

# Check status
sudo systemctl status crazy-trade-bot
sudo systemctl status crazy-trade-api
```

### Step 4: Monitor Logs

```bash
# View bot logs (live)
journalctl -u crazy-trade-bot -f

# View API logs (live)
journalctl -u crazy-trade-api -f

# View last 100 lines
journalctl -u crazy-trade-bot -n 100
```

---

## 🔄 Common Systemd Commands

```bash
# Start
sudo systemctl start crazy-trade-bot

# Stop
sudo systemctl stop crazy-trade-bot

# Restart (preserves state from database)
sudo systemctl restart crazy-trade-bot

# Check status
sudo systemctl status crazy-trade-bot

# Enable (start on boot)
sudo systemctl enable crazy-trade-bot

# Disable (don't start on boot)
sudo systemctl disable crazy-trade-bot

# View logs
journalctl -u crazy-trade-bot -f
```

---

## 💾 State Recovery After Restart

### How the Bot Recovers State

When the bot restarts, it automatically recovers by:

#### 1. **Database State Recovery**
```python
# From bot.db (SQLite database)
- Symbol states (cooldowns, last order IDs)
- Historical fills
- Event log
- Performance snapshots
```

#### 2. **Live Position Check via Alpaca API**
```python
# On startup, bot queries Alpaca:
positions = alpaca.get_positions()
open_orders = alpaca.get_open_orders()

# Bot discovers:
- Current positions (symbol, quantity, avg price)
- Active trailing stops
- Pending entry orders
```

#### 3. **State Machine Synchronization**
```python
# For each symbol, bot determines:
if position exists:
    status = POSITION_OPEN
    # Check if trailing stop exists
    # If missing → create one
    
elif pending_entry_order:
    status = ENTRY_PENDING
    
elif in_cooldown (from database):
    status = COOLDOWN
    
else:
    status = NO_POSITION
    # Ready to place new entry
```

### What Gets Preserved Through Restart

✅ **Preserved:**
- Open positions (stored at Alpaca)
- Active trailing stops (GTC orders at Alpaca)
- Cooldown timers (in bot.db)
- Historical trade data (in bot.db)
- Performance metrics (in bot.db)

❌ **Lost (but recoverable):**
- In-memory state (rebuilt from database + Alpaca)
- Pending API calls (restarted on next cycle)

### Example Recovery Scenario

**Before Restart:**
```
TSLA: Position open (100 shares), trailing stop active
NVDA: In cooldown (stopped out 10 mins ago)
AAPL: Entry pending (buy stop order placed)
```

**Bot Restarts...**

**After Restart:**
```python
# Bot startup sequence:
1. Load config.yaml + secrets.yaml
2. Connect to Alpaca API
3. Query Alpaca for positions → Finds TSLA position
4. Query Alpaca for open orders → Finds AAPL entry + TSLA stop
5. Load bot.db → Finds NVDA cooldown timer
6. Rebuild state:
   - TSLA: POSITION_OPEN (trailing stop verified)
   - NVDA: COOLDOWN (timer still active)
   - AAPL: ENTRY_PENDING (monitoring for fill)
7. Resume normal operation
```

**Result:** Bot continues exactly where it left off! ✅

---

## 🔍 State Recovery Code

The bot automatically recovers state in `src/state_machine.py`:

```python
def get_status(self) -> SymbolStatus:
    """Determine current status of the symbol."""
    
    # Check cooldown from database
    with self.db.get_session() as session:
        state = self.db.get_symbol_state(session, self.symbol)
        if state and state.cooldown_until_ts:
            if datetime.utcnow() < state.cooldown_until_ts:
                return SymbolStatus.COOLDOWN
    
    # Check position from Alpaca API
    positions = self.alpaca.get_positions()
    if self.symbol in positions:
        return SymbolStatus.POSITION_OPEN
    
    # Check pending orders from Alpaca API
    open_orders = self.alpaca.get_open_orders()
    for order in open_orders:
        if order.symbol == self.symbol and order.side == "BUY":
            return SymbolStatus.ENTRY_PENDING
    
    return SymbolStatus.NO_POSITION
```

This runs on **every processing cycle**, so state is always synchronized!

---

## 🛡️ Reliability Features

### Automatic Restart on Failure
```bash
# Systemd config:
Restart=on-failure
RestartSec=10
```
If bot crashes → systemd restarts it after 10 seconds

### Log Retention
```bash
# View logs from any date:
journalctl -u crazy-trade-bot --since "2024-01-01"
journalctl -u crazy-trade-bot --since "1 hour ago"
```

### Manual Recovery
```bash
# If bot seems stuck, restart it:
sudo systemctl restart crazy-trade-bot

# Bot will:
# 1. Reconnect to Alpaca
# 2. Reload database state
# 3. Check current positions
# 4. Resume trading
```

---

## 📊 Monitoring Your Bot

### Check if Bot is Running
```bash
sudo systemctl status crazy-trade-bot
```

### View Recent Activity
```bash
journalctl -u crazy-trade-bot -n 50
```

### Monitor Live
```bash
# Terminal 1: Bot logs
journalctl -u crazy-trade-bot -f

# Terminal 2: API endpoint
curl http://localhost:8080/status
```

### Check API Server
```bash
# Status
curl http://localhost:8080/health

# Recent fills
curl http://localhost:8080/fills

# Performance
curl http://localhost:8080/performance
```

---

## 🔧 Troubleshooting

### Bot Won't Start

**Check logs:**
```bash
journalctl -u crazy-trade-bot -n 100
```

**Common issues:**
- secrets.yaml not found → Create it from secrets.yaml.example
- Wrong paths in service file → Edit service file
- Permission issues → Check file ownership

### Bot Starts Then Stops

**Check:**
```bash
# View crash logs
journalctl -u crazy-trade-bot --since "5 minutes ago"

# Test manually
cd /path/to/crazy_trade
source venv/bin/activate
python3 main.py
```

### State Not Recovering

**Verify database:**
```bash
# Check database exists
ls -lh bot.db

# Verify positions
python3 scripts/show_performance.py
```

---

## 🔐 Security Recommendations

### File Permissions
```bash
# Secure secrets file
chmod 600 secrets.yaml

# Restrict database access
chmod 600 bot.db
```

### Firewall
```bash
# If accessing API remotely
sudo ufw allow 8080/tcp

# Or restrict to specific IP
sudo ufw allow from YOUR_IP to any port 8080
```

### Run as Non-Root User
```bash
# Create dedicated user (optional)
sudo useradd -m -s /bin/bash tradebot
sudo su - tradebot

# Install bot in user's home directory
cd ~
git clone <your-repo>
```

---

## 🎯 Production Checklist

- [ ] Ubuntu server running and updated
- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `secrets.yaml` created with real API keys
- [ ] `config.yaml` reviewed and customized
- [ ] Connection tested (`python3 test_connection.py`)
- [ ] Service files edited with correct paths
- [ ] Services installed and enabled
- [ ] Bot and API started successfully
- [ ] Logs verified (no errors)
- [ ] State recovery tested (restart bot, verify positions)
- [ ] Monitoring setup (API endpoints or logs)

---

## 📚 Quick Reference

```bash
# Start everything
./start_background.sh start

# Check status
./start_background.sh status

# View logs
./start_background.sh logs

# Restart (preserves state)
./start_background.sh restart

# Stop everything
./start_background.sh stop

# Using systemd:
sudo systemctl restart crazy-trade-bot  # Restart bot
journalctl -u crazy-trade-bot -f        # View logs
curl http://localhost:8080/status       # Check API
```

---

**Your bot will automatically recover all state after restart!** 🚀

