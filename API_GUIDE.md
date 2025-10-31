# API Guide - Remote Monitoring

Simple REST API for monitoring your trading bot remotely. No fancy UI, just clean JSON endpoints.

## 🚀 Quick Start

### Start the API Server

```bash
# Default port 8080
./run_api.sh

# Custom port
./run_api.sh 9000

# With options
python3 api_server.py --host 0.0.0.0 --port 8080
```

The server runs on `0.0.0.0` by default, so it's accessible from other machines.

### Test Locally

```bash
# Check if it's running
curl http://localhost:8080/health

# Get status
curl http://localhost:8080/status | jq .
```

## 📡 API Endpoints

### `GET /`
API documentation (lists all available endpoints)

**Example:**
```bash
curl http://localhost:8080/
```

---

### `GET /health`
Health check - verify API and database are working

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-10-31T14:30:00.123456",
  "database": "connected"
}
```

**Example:**
```bash
curl http://localhost:8080/health
```

---

### `GET /status`
Bot status, symbol states, and activity summary

**Response:**
```json
{
  "timestamp": "2024-10-31T14:30:00.123456",
  "symbols": [
    {
      "symbol": "TSLA",
      "in_cooldown": false,
      "cooldown_until": null,
      "last_parent_id": 1001,
      "last_trail_id": 1002
    }
  ],
  "active_orders": 3,
  "total_fills": 45,
  "last_event": {
    "type": "entry_order_placed",
    "symbol": "NVDA",
    "timestamp": "2024-10-31 14:25:30"
  },
  "bot_started": "2024-10-31 09:30:00"
}
```

**Example:**
```bash
curl http://localhost:8080/status
```

---

### `GET /performance`
Performance metrics, win rate, P&L, and per-symbol breakdown

**Response:**
```json
{
  "timestamp": "2024-10-31T14:30:00.123456",
  "overall": {
    "total_trades": 25,
    "winning_trades": 15,
    "losing_trades": 10,
    "win_rate_pct": 60.0,
    "total_pnl": 1250.50,
    "gross_profit": 2500.00,
    "gross_loss": 1249.50,
    "profit_factor": 2.0,
    "avg_win": 166.67,
    "avg_loss": 124.95
  },
  "by_symbol": {
    "TSLA": {
      "trades": 10,
      "pnl": 500.00,
      "wins": 6,
      "losses": 4
    },
    "NVDA": {
      "trades": 15,
      "pnl": 750.50,
      "wins": 9,
      "losses": 6
    }
  }
}
```

**Example:**
```bash
curl http://localhost:8080/performance
```

---

### `GET /fills`
Recent fills (executions)

**Parameters:**
- `limit` (optional): Number of fills to return (default: 20, max: 200)

**Response:**
```json
{
  "timestamp": "2024-10-31T14:30:00.123456",
  "count": 20,
  "fills": [
    {
      "timestamp": "2024-10-31 14:25:30",
      "symbol": "TSLA",
      "side": "BUY",
      "quantity": 10,
      "price": 262.50,
      "order_id": 1001,
      "exec_id": "0001f4e8.67239c8a.01.01"
    }
  ]
}
```

**Examples:**
```bash
# Last 20 fills
curl http://localhost:8080/fills

# Last 50 fills
curl http://localhost:8080/fills?limit=50
```

---

### `GET /orders`
Active orders (pending/submitted)

**Response:**
```json
{
  "timestamp": "2024-10-31T14:30:00.123456",
  "count": 3,
  "orders": [
    {
      "order_id": 1001,
      "symbol": "TSLA",
      "side": "BUY",
      "order_type": "STP",
      "quantity": 10,
      "status": "Submitted",
      "stop_price": 262.50,
      "limit_price": null,
      "trailing_pct": null,
      "parent_id": null,
      "created_at": "2024-10-31 09:35:00"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8080/orders
```

---

### `GET /events`
Recent events (audit trail)

**Parameters:**
- `limit` (optional): Number of events to return (default: 20, max: 200)

**Response:**
```json
{
  "timestamp": "2024-10-31T14:30:00.123456",
  "count": 20,
  "events": [
    {
      "timestamp": "2024-10-31 14:25:30",
      "event_type": "entry_order_placed",
      "symbol": "TSLA",
      "payload": "{\"order_id\": 1001, \"qty\": 10}"
    }
  ]
}
```

**Examples:**
```bash
# Last 20 events
curl http://localhost:8080/events

# Last 100 events
curl http://localhost:8080/events?limit=100
```

---

### `GET /daily`
Daily P&L breakdown

**Parameters:**
- `days` (optional): Number of days to return (default: 10, max: 90)

**Response:**
```json
{
  "timestamp": "2024-10-31T14:30:00.123456",
  "days": 10,
  "count": 10,
  "daily_pnl": [
    {
      "date": "2024-10-31",
      "pnl": 250.50,
      "trades": 3
    },
    {
      "date": "2024-10-30",
      "pnl": -150.00,
      "trades": 2
    }
  ]
}
```

**Examples:**
```bash
# Last 10 days
curl http://localhost:8080/daily

# Last 30 days
curl http://localhost:8080/daily?days=30
```

---

## 🌐 Remote Access

### From Your Phone/Laptop

If the bot is running on a server at `192.168.1.100`:

```bash
# Check status
curl http://192.168.1.100:8080/status

# View performance
curl http://192.168.1.100:8080/performance | jq .
```

### Using a Browser

Just open these URLs in any browser:
- `http://your-server-ip:8080/` - API docs
- `http://your-server-ip:8080/status` - Bot status
- `http://your-server-ip:8080/performance` - Performance
- `http://your-server-ip:8080/fills` - Recent fills

### Pretty Print JSON

```bash
# Install jq (if not already)
# macOS: brew install jq
# Linux: apt install jq

# Pretty print any endpoint
curl http://localhost:8080/status | jq .
curl http://localhost:8080/performance | jq .
```

## 🔧 Advanced Usage

### Quick Status Script

Create `check_remote.sh`:

```bash
#!/bin/bash
SERVER="http://your-server-ip:8080"

echo "=== BOT STATUS ==="
curl -s $SERVER/status | jq -r '.last_event'

echo ""
echo "=== PERFORMANCE ==="
curl -s $SERVER/performance | jq -r '.overall | "Trades: \(.total_trades) | Win Rate: \(.win_rate_pct)% | P&L: $\(.total_pnl)"'

echo ""
echo "=== ACTIVE ORDERS ==="
curl -s $SERVER/orders | jq -r '.count'
```

### Watch for Updates

```bash
# Poll status every 30 seconds
watch -n 30 'curl -s http://localhost:8080/status | jq .'

# Check performance every 5 minutes
watch -n 300 'curl -s http://localhost:8080/performance | jq .overall'
```

### Integration with Scripts

```python
import requests

# Python example
api_url = "http://your-server:8080"

# Get status
response = requests.get(f"{api_url}/status")
status = response.json()
print(f"Active orders: {status['active_orders']}")

# Get performance
response = requests.get(f"{api_url}/performance")
perf = response.json()
print(f"Win rate: {perf['overall']['win_rate_pct']}%")
```

```javascript
// JavaScript example
const API_URL = "http://your-server:8080";

async function getStatus() {
  const response = await fetch(`${API_URL}/status`);
  const data = await response.json();
  console.log(`Active orders: ${data.active_orders}`);
}
```

## 🔒 Security Notes

⚠️ **Important:**
- The API has **no authentication** - it's meant for internal networks
- Don't expose to the public internet without adding security
- Consider using SSH tunneling for external access:
  ```bash
  # Create SSH tunnel
  ssh -L 8080:localhost:8080 user@your-server
  
  # Then access locally
  curl http://localhost:8080/status
  ```

### Adding Basic Security (Optional)

To add simple token authentication, you can modify `api_server.py`:

```python
from flask import request, jsonify

API_TOKEN = "your-secret-token"  # Store securely!

@app.before_request
def check_token():
    if request.endpoint != 'health':  # Allow health checks
        token = request.headers.get('X-API-Token')
        if token != API_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401

# Then use it:
curl -H "X-API-Token: your-secret-token" http://server:8080/status
```

## 🐛 Troubleshooting

### API won't start
```bash
# Check if port is already in use
lsof -i :8080

# Try different port
./run_api.sh 9000
```

### Can't connect remotely
```bash
# Check firewall (allow port 8080)
# macOS: System Preferences → Security → Firewall
# Linux: ufw allow 8080

# Verify server is listening
netstat -an | grep 8080
```

### Database errors
```bash
# Ensure bot.db exists
ls -lh bot.db

# Check API can read it
sqlite3 bot.db "SELECT COUNT(*) FROM fills"
```

## 💡 Tips

- **Run alongside the bot**: API server and trading bot are separate - run both
- **Lightweight**: API uses minimal resources (~20MB RAM)
- **Read-only**: API never modifies the database
- **No caching**: All data is fresh from database
- **JSON only**: All responses are JSON (no HTML/UI)

## 📊 Monitoring Dashboard (DIY)

Want a simple dashboard? Use any tool that can fetch JSON:

- **Grafana** - Connect to API endpoints
- **Datadog** - Custom metrics from API
- **Prometheus** - Add `/metrics` endpoint
- **Simple HTML** - Fetch and display with JavaScript

---

**Keep it simple!** The API is intentionally minimal - just what you need for remote monitoring. 🚀

