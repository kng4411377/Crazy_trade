# Quick API Test

Simple test to verify the API is working.

## 1. Install Flask

```bash
pip install Flask>=3.0.0

# Or install all dependencies
pip install -r requirements.txt
```

## 2. Start the API Server

```bash
./run_api.sh
```

You should see:
```
🚀 Starting Crazy Trade Bot API Server
📡 Listening on http://0.0.0.0:8080
📊 Endpoints available at http://localhost:8080/
🔍 API docs at http://localhost:8080/

Press Ctrl+C to stop
```

## 3. Test the Endpoints

Open a new terminal and run:

```bash
# Test 1: Health check
curl http://localhost:8080/health
# Expected: {"status":"healthy",...}

# Test 2: API docs
curl http://localhost:8080/
# Expected: List of endpoints

# Test 3: Status
curl http://localhost:8080/status
# Expected: Bot status and symbol states

# Test 4: Performance (may be empty if no trades yet)
curl http://localhost:8080/performance

# Test 5: Fills (may be empty if no trades yet)
curl http://localhost:8080/fills

# Test 6: Events
curl http://localhost:8080/events
```

## 4. Pretty Print (with jq)

```bash
curl -s http://localhost:8080/status | jq .
curl -s http://localhost:8080/performance | jq .
```

## 5. Browser Test

Open in your browser:
- http://localhost:8080/
- http://localhost:8080/health
- http://localhost:8080/status

## Expected Results

### Fresh Database (No Trades Yet)
- `/health` → ✅ healthy
- `/status` → Shows symbols, 0 fills
- `/performance` → "No closed trades yet"
- `/fills` → Empty list
- `/events` → May show bot_started events

### With Trading Data
- `/status` → Shows symbol states, order counts
- `/performance` → Win rate, P&L, per-symbol stats
- `/fills` → List of recent executions
- `/daily` → Daily P&L breakdown

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
```bash
pip install Flask
```

### "Connection refused"
- Check if API server is running: `ps aux | grep api_server`
- Try a different port: `./run_api.sh 9000`

### "Database not found"
- Make sure `bot.db` exists in the same directory
- Run the main bot first: `./run.sh` (then stop it)
- Or just test with empty/missing database (will show empty data)

### Port already in use
```bash
# Find what's using port 8080
lsof -i :8080

# Use different port
./run_api.sh 9000
```

## Quick Validation

Run this one-liner to test all endpoints:

```bash
for endpoint in health status performance fills orders events daily; do
  echo "Testing /$endpoint..."
  curl -s http://localhost:8080/$endpoint | head -c 100
  echo -e "\n---"
done
```

If all endpoints return JSON (even if empty), the API is working! ✅

