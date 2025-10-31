# Command Reference - Quick Guide

## 🚀 Setup & Running

```bash
# First time setup
./setup.sh

# Start the bot
./run.sh

# Start with custom config
./run.sh my_config.yaml

# Stop the bot
Ctrl+C
```

## 📊 Monitoring

### Command-Line Tools

```bash
# Check status
python scripts/check_status.py

# View performance & P/L
python scripts/show_performance.py

# Export trades to CSV
python scripts/export_trades.py

# Watch live logs (requires jq)
tail -f bot.log | jq .

# Filter logs by symbol
grep "TSLA" bot.log | jq .

# Filter by event type
grep "entry_order_placed" bot.log | jq .
```

### API Server (Remote Access)

```bash
# Start API server (default port 8080)
./run_api.sh

# Or with custom port
./run_api.sh 9000

# Or run directly
python api_server.py --port 8080

# Access endpoints
curl http://localhost:8080/              # API docs
curl http://localhost:8080/health        # Health check
curl http://localhost:8080/status        # Bot status
curl http://localhost:8080/performance   # Performance metrics
curl http://localhost:8080/fills         # Recent fills
curl http://localhost:8080/fills?limit=50  # Last 50 fills
curl http://localhost:8080/orders        # Active orders
curl http://localhost:8080/events        # Recent events
curl http://localhost:8080/daily         # Daily P&L
curl http://localhost:8080/daily?days=30 # Last 30 days

# Remote access (from another machine)
curl http://your-server-ip:8080/status
```

## 🗄️ Database Queries

```bash
# Open database
sqlite3 bot.db

# View all symbols and their status
sqlite3 bot.db "SELECT * FROM state"

# Check active cooldowns
sqlite3 bot.db "SELECT symbol, cooldown_until_ts FROM state WHERE cooldown_until_ts > datetime('now')"

# View recent orders
sqlite3 bot.db "SELECT * FROM orders ORDER BY created_at DESC LIMIT 10"

# View all fills
sqlite3 bot.db "SELECT * FROM fills ORDER BY ts DESC LIMIT 20"

# View recent events
sqlite3 bot.db "SELECT event_type, symbol, ts FROM events ORDER BY ts DESC LIMIT 20"

# Count orders by symbol
sqlite3 bot.db "SELECT symbol, COUNT(*) as count FROM orders GROUP BY symbol"

# Count fills by symbol
sqlite3 bot.db "SELECT symbol, COUNT(*) as count FROM fills GROUP BY symbol"

# View stop-outs
sqlite3 bot.db "SELECT * FROM events WHERE event_type = 'stopout_cooldown_started' ORDER BY ts DESC"
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_state_machine.py

# Run integration tests only
pytest tests/test_integration.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_config.py::test_config_from_yaml -v
```

## 🔧 Maintenance

```bash
# Verify project completeness
python verify_project.py

# Clear database (CAREFUL!)
rm bot.db

# Clear logs
rm bot.log

# Update dependencies
pip install -r requirements.txt --upgrade

# Check for linting issues (if using pylint)
pylint src/

# Format code (if using black)
black src/ tests/
```

## 📝 Database Management

```bash
# Backup database
cp bot.db bot_backup_$(date +%Y%m%d).db

# Clear cooldowns (emergency reset)
sqlite3 bot.db "UPDATE state SET cooldown_until_ts = NULL"

# View database schema
sqlite3 bot.db ".schema"

# Export to CSV
sqlite3 bot.db -header -csv "SELECT * FROM fills" > fills.csv
sqlite3 bot.db -header -csv "SELECT * FROM orders" > orders.csv

# Count records
sqlite3 bot.db "SELECT 'Orders: ' || COUNT(*) FROM orders UNION ALL SELECT 'Fills: ' || COUNT(*) FROM fills"
```

## 🐛 Debugging

```bash
# Check Python version
python3 --version

# Check if dependencies are installed
pip list | grep ib-insync
pip list | grep pandas

# Test IBKR connection (manual)
python3 -c "from ib_insync import IB; ib = IB(); ib.connect('127.0.0.1', 5000, clientId=999); print('Connected!'); ib.disconnect()"

# Check if IB Gateway is running (macOS)
lsof -i :5000

# View detailed error logs
cat bot.log | jq 'select(.level=="error")'

# Debug mode - run bot with more logging
# Edit config.yaml: logging.level: "DEBUG"
./run.sh
```

## 📊 Analysis Queries

```bash
# Performance snapshots
sqlite3 bot.db "SELECT * FROM performance_snapshots ORDER BY date DESC LIMIT 10"

# Win rate (requires fills analysis)
sqlite3 bot.db "
SELECT 
    symbol,
    COUNT(*) as trades,
    SUM(CASE WHEN side='SELL' AND qty > 0 THEN 1 ELSE 0 END) as exits
FROM fills 
GROUP BY symbol
"

# Average fill prices
sqlite3 bot.db "
SELECT 
    symbol,
    side,
    AVG(price) as avg_price,
    COUNT(*) as count
FROM fills 
GROUP BY symbol, side
"

# Activity by hour
sqlite3 bot.db "
SELECT 
    strftime('%H', ts) as hour,
    COUNT(*) as orders
FROM orders 
GROUP BY hour 
ORDER BY hour
"

# Most active symbols
sqlite3 bot.db "
SELECT 
    symbol,
    COUNT(*) as order_count
FROM orders 
GROUP BY symbol 
ORDER BY order_count DESC
"
```

## ⚡ Quick Checks

```bash
# Is the bot running?
ps aux | grep "python.*main.py"

# Check bot log size
du -h bot.log

# Check database size
du -h bot.db

# Last 10 log entries
tail -10 bot.log | jq .

# Check for errors in logs
grep -i error bot.log | jq .

# Check last bot start
sqlite3 bot.db "SELECT * FROM events WHERE event_type='bot_started' ORDER BY ts DESC LIMIT 1"
```

## 🔄 Reset Everything (Fresh Start)

```bash
# CAUTION: This deletes all data!
rm bot.db bot.log
./run.sh
```

## 📦 Deployment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in production
pip install -r requirements.txt --no-cache-dir

# Run as background service (screen)
screen -S tradebot
./run.sh
# Press Ctrl+A then D to detach

# Reattach to running bot
screen -r tradebot

# Run as daemon (nohup)
nohup ./run.sh > output.log 2>&1 &

# Check daemon
ps aux | grep main.py

# Run API server in background
nohup python api_server.py --port 8080 > api.log 2>&1 &

# Or use screen for API
screen -S tradebot-api
./run_api.sh
# Press Ctrl+A then D to detach
```

## 🎯 Quick Status Check

```bash
# One-liner status
echo "=== BOT STATUS ===" && \
echo "Running: $(ps aux | grep -v grep | grep main.py | wc -l)" && \
echo "Active orders: $(sqlite3 bot.db "SELECT COUNT(*) FROM orders WHERE status IN ('Submitted', 'PreSubmitted')")" && \
echo "Total fills: $(sqlite3 bot.db "SELECT COUNT(*) FROM fills")" && \
echo "Last event: $(sqlite3 bot.db "SELECT event_type FROM events ORDER BY ts DESC LIMIT 1")"
```

## 💡 Tips

- Keep `bot.db` for analysis even after stopping bot
- Back up database daily in production
- Monitor logs regularly for errors
- Use `verify_project.py` after updates
- Test configuration changes in paper mode first
- Check IB Gateway connection before starting bot

---

Save this file for quick reference! 📌

