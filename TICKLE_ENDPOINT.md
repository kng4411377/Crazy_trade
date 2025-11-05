# Tickle Endpoint - Keep-Alive for Monitoring

## Overview

The `/v1/api/tickle` endpoint is a simple keep-alive endpoint designed for external monitoring services like UptimeRobot, Pingdom, or custom health check scripts.

## Why the Empty Body is Required

The endpoint requires a POST request with an empty JSON body `{}`. This is necessary because:

1. **HTTP 411 Error**: Some servers (including Flask's development server) require a `Content-Length` header for POST requests
2. **curl Behavior**: By default, `curl -X POST` without data doesn't send a `Content-Length` header
3. **Solution**: Using `-d '{}'` sends an empty JSON body and automatically includes the `Content-Length: 2` header

## Correct Usage

### ✅ Working Command
```bash
curl -sk --http1.1 --noproxy 127.0.0.1,localhost \
  -H "Content-Type: application/json" \
  -X POST "http://127.0.0.1:8080/v1/api/tickle" \
  -d '{}'
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-10-31T14:30:00.123456"
}
```

### ❌ Won't Work (411 Length Required)
```bash
# This fails because no Content-Length header
curl -vk -X POST "http://127.0.0.1:8080/v1/api/tickle"
```

**Error:**
```
< HTTP/1.1 411 Length Required
```

## Command Breakdown

| Flag | Purpose |
|------|---------|
| `-s` | Silent mode (no progress bar) |
| `-k` | Allow insecure SSL (if using HTTPS) |
| `--http1.1` | Force HTTP/1.1 protocol |
| `--noproxy 127.0.0.1,localhost` | Bypass proxy for localhost |
| `-H "Content-Type: application/json"` | Set content type header |
| `-X POST` | Use POST method |
| `-d '{}'` | Send empty JSON body (auto-adds Content-Length) |

## Use Cases

### 1. UptimeRobot Monitoring
Configure UptimeRobot to send POST request:
- **URL**: `http://your-server:8080/v1/api/tickle`
- **Method**: POST
- **Headers**: `Content-Type: application/json`
- **Body**: `{}`
- **Interval**: Every 5 minutes

### 2. Cron Job Health Check
```bash
#!/bin/bash
# /etc/cron.d/api-health-check
# Check every 5 minutes

*/5 * * * * curl -sk --http1.1 --noproxy 127.0.0.1,localhost \
  -H "Content-Type: application/json" \
  -X POST "http://127.0.0.1:8080/v1/api/tickle" \
  -d '{}' || echo "API down!" | mail -s "Alert" admin@example.com
```

### 3. Python Monitoring Script
```python
import requests
import time

def check_api_health():
    url = "http://127.0.0.1:8080/v1/api/tickle"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json={}, headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"✅ API is healthy: {response.json()}")
            return True
        else:
            print(f"❌ API returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API check failed: {e}")
        return False

# Check every 5 minutes
while True:
    check_api_health()
    time.sleep(300)
```

### 4. JavaScript/Node.js
```javascript
const axios = require('axios');

async function tickleAPI() {
  try {
    const response = await axios.post(
      'http://127.0.0.1:8080/v1/api/tickle',
      {},
      { headers: { 'Content-Type': 'application/json' } }
    );
    console.log('✅ API is healthy:', response.data);
  } catch (error) {
    console.error('❌ API check failed:', error.message);
  }
}

// Check every 5 minutes
setInterval(tickleAPI, 5 * 60 * 1000);
```

## Port Configuration

**Default Port**: `8080`

If you're running the API on a different port (e.g., `5000`), update the URL accordingly:

```bash
curl -sk --http1.1 --noproxy 127.0.0.1,localhost \
  -H "Content-Type: application/json" \
  -X POST "http://127.0.0.1:5000/v1/api/tickle" \
  -d '{}'
```

To change the default port:
```bash
./run_api.sh 5000
# Or
python3 api_server.py --port 5000
```

## Difference from `/health` Endpoint

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Full health check with DB connection test |
| `/v1/api/tickle` | POST | Lightweight keep-alive ping |

- Use `/health` for comprehensive health checks
- Use `/v1/api/tickle` for simple keep-alive pings from monitoring services

## Troubleshooting

### 411 Length Required Error
```bash
# Problem: Missing Content-Length header
curl -X POST "http://127.0.0.1:8080/v1/api/tickle"

# Solution: Add empty JSON body
curl -X POST "http://127.0.0.1:8080/v1/api/tickle" -d '{}'
```

### Connection Refused
```bash
# Check if API server is running
ps aux | grep api_server

# Check if port is in use
lsof -i :8080

# Start the API server
./run_api.sh
```

### Wrong Port
```bash
# If you're running on port 5000 instead of 8080
curl -sk --http1.1 --noproxy 127.0.0.1,localhost \
  -H "Content-Type: application/json" \
  -X POST "http://127.0.0.1:5000/v1/api/tickle" \
  -d '{}'
```

## Summary

✅ **Always use `-d '{}'`** to avoid 411 errors  
✅ **POST method required** (not GET)  
✅ **Lightweight endpoint** - instant response  
✅ **Perfect for monitoring** - UptimeRobot, Pingdom, custom scripts  
✅ **Port 8080 by default** - adjust as needed  

The tickle endpoint ensures your monitoring tools can verify the API is alive with a simple, reliable POST request. 🚀

