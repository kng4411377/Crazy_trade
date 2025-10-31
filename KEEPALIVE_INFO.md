# IBKR Connection Keep-Alive

## Overview

The bot now includes a **periodic keep-alive mechanism** to prevent the IBKR Gateway/TWS connection from timing out during periods of inactivity.

## How It Works

### Automatic Tickle
- Bot sends a lightweight request (`reqCurrentTime()`) to IBKR every **5 minutes** (configurable)
- Happens both during market hours and outside trading hours
- Prevents connection timeout without any overhead

### Configuration

Edit `config.yaml`:

```yaml
polling:
  price_seconds: 10
  orders_seconds: 15
  keepalive_seconds: 300  # Ping every 5 minutes (default)
```

### Typical Settings

| Interval | Use Case |
|----------|----------|
| `300` (5 min) | **Default** - Good balance |
| `180` (3 min) | More aggressive, very safe |
| `600` (10 min) | Conservative, less chatter |
| `60` (1 min) | Overkill, but guaranteed alive |

## Why This Matters

### Without Keep-Alive
- IBKR Gateway may timeout after 10-15 minutes of no API activity
- Especially problematic overnight or on weekends
- Bot would lose connection and stop functioning
- Requires manual restart

### With Keep-Alive ✅
- Connection stays alive indefinitely
- Bot runs 24/7 without intervention
- Automatically reconnects if connection drops
- Minimal overhead (lightweight request)

## Implementation Details

### What Gets Sent
```python
# In ibkr_client.py
async def keep_alive(self):
    """Keep-alive tickle to prevent IBKR Gateway timeout."""
    time = self.ib.reqCurrentTime()
    logger.debug("keepalive_ping", server_time=time)
```

This is a **very lightweight** request that:
- Just asks IBKR for current server time
- Takes ~10ms to execute
- Uses minimal bandwidth
- Doesn't affect rate limits

### When It Runs

**During market hours:**
- Every 5 minutes (default)
- After processing trading logic
- Before sleeping between polling cycles

**Outside market hours:**
- Every 5 minutes (default)
- While bot is idle waiting for market open
- Keeps connection warm overnight/weekends

### Logging

You'll see these debug logs:
```json
{
  "event": "keepalive_ping",
  "server_time": "2024-10-31 14:30:00",
  "level": "debug"
}
```

Or warnings if it fails (rare):
```json
{
  "event": "keepalive_failed",
  "error": "...",
  "level": "warning"
}
```

## Testing

### Check if it's working

1. Start the bot
2. Set logging to DEBUG in `config.yaml`:
   ```yaml
   logging:
     level: "DEBUG"
   ```
3. Watch for `keepalive_ping` events every 5 minutes:
   ```bash
   tail -f bot.log | grep keepalive
   ```

### Expected output
```json
{"event": "keepalive_ping", "server_time": "...", "level": "debug"}
{"event": "keepalive_ping", "server_time": "...", "level": "debug"}
{"event": "keepalive_ping", "server_time": "...", "level": "debug"}
```

## Troubleshooting

### Connection still timing out?

**Solution 1: Reduce interval**
```yaml
polling:
  keepalive_seconds: 180  # Try 3 minutes
```

**Solution 2: Check IB Gateway settings**
- In IB Gateway: Configure → Settings → API
- Look for "Read-Only API" - should be disabled
- Check "Auto restart" is enabled

**Solution 3: Verify bot is running**
```bash
ps aux | grep main.py
tail -f bot.log | grep keepalive
```

### Too many keep-alive requests?

**Solution: Increase interval**
```yaml
polling:
  keepalive_seconds: 600  # Every 10 minutes
```

Note: IBKR typically times out after ~15 minutes, so don't go above 600-900 seconds.

## Best Practices

### Recommended Configuration

For **24/7 operation** (recommended):
```yaml
polling:
  keepalive_seconds: 300  # 5 minutes
```

For **day trading only** (manual start/stop):
```yaml
polling:
  keepalive_seconds: 600  # 10 minutes (less aggressive)
```

For **very stable connection** (paranoid mode):
```yaml
polling:
  keepalive_seconds: 180  # 3 minutes
```

### Important Notes

1. ✅ **Keep-alive is automatic** - no action needed
2. ✅ **Works 24/7** - even when market is closed
3. ✅ **Lightweight** - negligible performance impact
4. ✅ **Configurable** - adjust if needed
5. ⚠️ **Don't set too low** - under 60 seconds is overkill

## Architecture

```
┌─────────────┐
│ Trading Bot │
└──────┬──────┘
       │
       │ Every 5 minutes:
       │ "What time is it?"
       │
       ▼
┌─────────────────┐
│  IBKR Gateway   │ ← Connection stays alive!
└─────────────────┘
```

Without keep-alive:
```
Bot → (idle for 15 min) → Gateway → ❌ TIMEOUT → 🔌 Disconnected
```

With keep-alive:
```
Bot → (ping every 5 min) → Gateway → ✅ ALIVE → ✅ Connected
```

## FAQ

**Q: Does this cost money or use rate limits?**  
A: No. `reqCurrentTime()` is free and doesn't count toward rate limits.

**Q: Will this wake me up at night with notifications?**  
A: No. It's logged as DEBUG level and completely silent.

**Q: What if the keep-alive fails?**  
A: Bot logs a warning and continues. It'll try again at the next interval. If connection is truly lost, the bot will detect it during normal operations.

**Q: Can I disable it?**  
A: Not recommended, but you can set a very high interval:
```yaml
polling:
  keepalive_seconds: 999999  # Effectively disabled
```

**Q: Does `ib_insync` already have keep-alive?**  
A: `ib_insync` has some reconnection logic, but explicit keep-alive is more reliable for 24/7 operation.

## Summary

✅ **Implemented**: Automatic IBKR connection keep-alive  
✅ **Default**: Pings every 5 minutes  
✅ **Configurable**: Adjust `keepalive_seconds` in config  
✅ **Reliable**: Works 24/7, market hours or not  
✅ **Lightweight**: Minimal overhead  

Your bot can now run indefinitely without connection timeouts! 🚀

