# 🌐 Remote Monitoring Setup Complete!

Your trading bot now has a simple REST API for remote monitoring. Here's everything you need to know.

## ✅ What Was Added

### Core Files
- **`api_server.py`** - REST API server (Flask-based, ~300 lines)
- **`run_api.sh`** - Easy startup script

### Documentation
- **`API_GUIDE.md`** - Complete API documentation with examples
- **`API_README.md`** - Quick reference guide
- **`TEST_API.md`** - Step-by-step testing instructions
- **`REMOTE_MONITORING_SETUP.md`** - This file

### Examples
- **`examples/monitor_bot.py`** - Python monitoring script
- **`examples/README.md`** - Example documentation

### Updates
- **`requirements.txt`** - Added Flask and requests
- **`README.md`** - Added API section
- **`COMMANDS.md`** - Added API commands

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

This installs Flask (for the API server).

### 2. Start the API Server
```bash
./run_api.sh
```

You should see:
```
🚀 Starting Crazy Trade Bot API Server
📡 Listening on http://0.0.0.0:8080
📊 Endpoints available at http://localhost:8080/
```

### 3. Test It!
```bash
# From same machine
curl http://localhost:8080/status | jq .

# From another machine on your network
curl http://YOUR-SERVER-IP:8080/status | jq .
```

## 📡 Available Endpoints

| Endpoint | What It Shows |
|----------|---------------|
| `/` | API documentation |
| `/health` | Health check (is API working?) |
| `/status` | Bot status, symbol states, cooldowns |
| `/performance` | Win rate, P&L, profit factor |
| `/fills` | Recent trades/executions |
| `/orders` | Active pending orders |
| `/events` | Event log (audit trail) |
| `/daily` | Daily P&L breakdown |

All responses are JSON.

## 💡 Common Use Cases

### Check Status from Phone
```bash
# Replace with your server's IP
curl http://192.168.1.100:8080/status
```

### Monitor Performance Remotely
```bash
curl http://192.168.1.100:8080/performance | jq .overall
```

### Use Python Script
```bash
# Single check
python examples/monitor_bot.py

# Continuous monitoring (refreshes every 30s)
python examples/monitor_bot.py --watch

# Monitor remote server
python examples/monitor_bot.py --host 192.168.1.100 --watch
```

### View in Browser
Just open in any browser:
- `http://YOUR-SERVER-IP:8080/status`
- `http://YOUR-SERVER-IP:8080/performance`

## 🏃 Running Both Services

You'll typically run TWO things:

### 1. Main Trading Bot
```bash
./run.sh
```
This runs the trading bot (places orders, monitors positions).

### 2. API Server
```bash
./run_api.sh
```
This runs the monitoring API (read-only access to data).

Both can run simultaneously and independently!

## 🖥️ Production Setup

### Using Screen (Recommended)

```bash
# Terminal 1: Start bot
screen -S tradebot
./run.sh
# Press Ctrl+A then D to detach

# Terminal 2: Start API
screen -S tradebot-api
./run_api.sh
# Press Ctrl+A then D to detach

# Later: Reattach to check
screen -r tradebot      # Check bot
screen -r tradebot-api  # Check API

# List running screens
screen -ls
```

### Using nohup

```bash
# Start bot in background
nohup ./run.sh > bot_output.log 2>&1 &

# Start API in background
nohup python api_server.py --port 8080 > api.log 2>&1 &

# Check if running
ps aux | grep -E 'main.py|api_server.py'
```

## 🌍 Access from Anywhere

### Local Network
If your server is at `192.168.1.100`:
```bash
curl http://192.168.1.100:8080/status
```

### Over Internet (via SSH Tunnel)
```bash
# On your local machine, create tunnel
ssh -L 8080:localhost:8080 user@your-server

# Then access as if it's local
curl http://localhost:8080/status
```

This is more secure than exposing the API directly to the internet.

### Firewall Setup
If you can't connect remotely, allow the port:

**macOS:**
- System Preferences → Security → Firewall → Allow incoming on port 8080

**Linux:**
```bash
sudo ufw allow 8080
```

## 🔒 Security Note

⚠️ **The API has NO authentication by default!**

This is fine for:
- Local machine only
- Private home/office network
- VPN connections
- SSH tunnels

**NOT recommended for:**
- Public internet exposure
- Untrusted networks

If you need to expose it publicly, add authentication (see API_GUIDE.md).

## 📊 Example Workflows

### Morning Check (from phone via Termux/SSH)
```bash
ssh user@server "curl -s http://localhost:8080/status | jq .active_orders"
```

### Dashboard on iPad
Open Safari: `http://192.168.1.100:8080/performance`

### Automated Alerts
```bash
# Check every hour, alert if issues
*/60 * * * * curl -s http://localhost:8080/health || echo "API down!" | mail -s Alert you@email.com
```

### Integration with Other Tools
```python
import requests

def check_bot():
    status = requests.get("http://192.168.1.100:8080/status").json()
    if status['active_orders'] == 0:
        send_slack_message("No active orders!")
```

## 🧪 Testing

### Quick Test
```bash
# Test all endpoints
curl http://localhost:8080/health
curl http://localhost:8080/status
curl http://localhost:8080/performance
curl http://localhost:8080/fills
curl http://localhost:8080/orders
curl http://localhost:8080/events
curl http://localhost:8080/daily
```

### Full Test Script
```bash
# One-liner to test everything
for ep in health status performance fills orders events daily; do
  echo "Testing /$ep..."
  curl -s http://localhost:8080/$ep | head -c 100
  echo -e "\n---"
done
```

See **`TEST_API.md`** for detailed testing guide.

## 🐛 Troubleshooting

### API Won't Start
```bash
# Check if Flask is installed
pip list | grep Flask

# Install if missing
pip install Flask

# Try different port
./run_api.sh 9000
```

### Can't Connect Remotely
```bash
# Check if API is listening
lsof -i :8080

# Check firewall
# macOS: System Preferences → Security → Firewall
# Linux: sudo ufw status

# Verify server IP
ifconfig | grep inet
```

### Empty Data
If endpoints return empty data, that's normal if:
- Bot hasn't traded yet (no fills/performance)
- Bot is not running (no recent events)

The API will still work; it just shows empty results.

### Port Already in Use
```bash
# Find what's using port 8080
lsof -i :8080

# Kill it or use different port
./run_api.sh 9000
```

## 📚 Documentation

- **`API_GUIDE.md`** - Full API documentation (all endpoints, parameters, examples)
- **`API_README.md`** - Quick reference guide
- **`TEST_API.md`** - Testing instructions
- **`COMMANDS.md`** - All monitoring commands (updated)
- **`examples/README.md`** - Example scripts

## 🎯 What's Next?

The API is intentionally simple. You can:

**Easy Extensions:**
- Build a web dashboard (HTML + JavaScript)
- Create mobile app using the API
- Add real-time updates with WebSocket
- Integrate with Grafana/Datadog for charts
- Add email/Slack notifications

**See API_GUIDE.md for ideas!**

## ✨ Summary

You now have:
1. ✅ Simple REST API with 8 endpoints
2. ✅ Easy startup script (`./run_api.sh`)
3. ✅ Python monitoring example
4. ✅ Complete documentation
5. ✅ Remote access capability

**Nothing fancy, just what you need!** 🚀

---

## Quick Command Reference

```bash
# Start API
./run_api.sh

# Test locally
curl http://localhost:8080/status

# Test remotely
curl http://YOUR-IP:8080/status

# Monitor continuously
python examples/monitor_bot.py --watch

# Run in background
nohup ./run_api.sh > api.log 2>&1 &

# Check if running
ps aux | grep api_server
```

**Happy monitoring!** 📊

