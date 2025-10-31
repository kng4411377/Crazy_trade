# 🚀 API Server - Quick Reference

A simple REST API added to the Crazy Trade Bot for easy remote monitoring.

## What's New?

**New Files:**
- `api_server.py` - REST API server (Flask-based)
- `run_api.sh` - Startup script for the API
- `API_GUIDE.md` - Full API documentation
- `TEST_API.md` - Quick testing guide

**Updated Files:**
- `requirements.txt` - Added Flask dependency
- `README.md` - Added API section
- `COMMANDS.md` - Added API commands

## Quick Start

### 1. Install Flask
```bash
pip install -r requirements.txt
```

### 2. Start the API
```bash
./run_api.sh
```

### 3. Test it
```bash
curl http://localhost:8080/status | jq .
```

## Available Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | API documentation |
| `GET /health` | Health check |
| `GET /status` | Bot status & symbol states |
| `GET /performance` | Performance metrics & P&L |
| `GET /fills` | Recent fills |
| `GET /orders` | Active orders |
| `GET /events` | Event log |
| `GET /daily` | Daily P&L |

## Features

✅ **Simple** - Just JSON endpoints, no fancy UI  
✅ **Lightweight** - ~20MB RAM usage  
✅ **Read-only** - Never modifies database  
✅ **Remote access** - Works from anywhere on your network  
✅ **No auth** - Perfect for internal networks (add auth if exposing publicly)  

## Usage Examples

### From Terminal
```bash
# Check status
curl http://localhost:8080/status

# Get performance
curl http://localhost:8080/performance | jq .

# Recent fills
curl http://localhost:8080/fills?limit=50
```

### From Python
```python
import requests

api = "http://localhost:8080"
status = requests.get(f"{api}/status").json()
print(f"Active orders: {status['active_orders']}")
```

### From Browser
Just open: `http://localhost:8080/status`

### Remote Access
```bash
# From any machine on your network
curl http://192.168.1.100:8080/status
```

## Running in Production

### Background Service
```bash
# Using nohup
nohup python3 api_server.py --port 8080 > api.log 2>&1 &

# Using screen
screen -S tradebot-api
./run_api.sh
# Press Ctrl+A then D to detach
```

### Check if Running
```bash
ps aux | grep api_server
lsof -i :8080
```

## Security Notes

⚠️ The API has **no authentication** by default
- Safe for internal networks
- Don't expose to public internet without adding security
- Consider SSH tunneling for remote access:
  ```bash
  ssh -L 8080:localhost:8080 user@server
  ```

## Documentation

- **`API_GUIDE.md`** - Complete API documentation with examples
- **`TEST_API.md`** - Step-by-step testing guide
- **`COMMANDS.md`** - All commands including API

## Troubleshooting

**Can't start the API?**
- Check if Flask is installed: `pip list | grep Flask`
- Try different port: `./run_api.sh 9000`

**Can't connect remotely?**
- Check firewall settings
- Verify server is listening: `netstat -an | grep 8080`

**Database errors?**
- Ensure `bot.db` exists in the same directory
- API reads from `sqlite:///bot.db` by default

## Architecture

```
┌─────────────────┐
│  Trading Bot    │  ← Main bot (main.py)
│  (main.py)      │
└────────┬────────┘
         │ writes
         ▼
    ┌─────────┐
    │  bot.db │  ← SQLite database
    └────┬────┘
         │ reads
         ▼
┌─────────────────┐
│   API Server    │  ← REST API (api_server.py)
│  (api_server.py)│  
└────────┬────────┘
         │
         ▼
    HTTP Clients
    (curl, browser, scripts)
```

Both services run **independently**:
- Main bot writes to database
- API server reads from database
- No direct communication between them

## What's Next?

The API is intentionally minimal. If you need more features:

**Easy additions:**
- Add authentication (API keys, JWT)
- Add CORS for web dashboards
- Add WebSocket for real-time updates
- Add more filtering/querying options

**Advanced:**
- Build a web dashboard (React, Vue, etc.)
- Integrate with Grafana for charts
- Add Prometheus metrics endpoint
- Create mobile app using the API

---

**Keep it simple!** The API does one thing well: provide read-only access to your bot's data. 🎯

