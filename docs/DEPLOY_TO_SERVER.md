# 🚀 Deploy Updated Code to Remote Server

## Issues Fixed in This Update

1. ✅ **UUID database errors** - All order IDs converted to strings
2. ✅ **UUID JSON serialization errors** - Event payloads now serialize UUIDs
3. ✅ **SHIB price rounding to 0** - Auto-detect tick size based on price magnitude
4. ✅ **UUID logging display** - Clean UUID format in logs (not "UUID('...')")

---

## Quick Deploy (Recommended)

### Step 1: Upload Files to Server

From your **local machine**, run:

```bash
cd /Users/tony.ng/work/temp/crazy_trade

# Upload the updated Python files to your remote server
scp src/database.py remoteuser@YOUR_SERVER:/home/remoteuser/Crazy_trade/src/
scp src/state_machine.py remoteuser@YOUR_SERVER:/home/remoteuser/Crazy_trade/src/
scp src/bot.py remoteuser@YOUR_SERVER:/home/remoteuser/Crazy_trade/src/
scp src/alpaca_client.py remoteuser@YOUR_SERVER:/home/remoteuser/Crazy_trade/src/
```

Replace `YOUR_SERVER` with your server's IP address or hostname.

### Step 2: Backup and Reset Database

SSH into your **remote server**:

```bash
ssh remoteuser@YOUR_SERVER
cd /home/remoteuser/Crazy_trade
```

Then backup and remove the old database:

```bash
# Backup old database
mv bot.db bot.db.backup_$(date +%Y%m%d_%H%M%S)

# The bot will create a new database with the correct schema on next start
```

### Step 3: Restart the Bot

```bash
# If running in background
pkill -f main.py

# Start again
./run.sh

# Or run in background
nohup ./run.sh > bot.log 2>&1 &
```

---

## Alternative: Git Deploy (If Using Git)

### Step 1: Commit and Push Changes (Local)

```bash
cd /Users/tony.ng/work/temp/crazy_trade

git add src/database.py src/state_machine.py src/bot.py src/alpaca_client.py
git commit -m "Fix UUID errors and SHIB price rounding"
git push origin main
```

### Step 2: Pull Changes (Remote Server)

SSH into your server and pull:

```bash
ssh remoteuser@YOUR_SERVER
cd /home/remoteuser/Crazy_trade

# Pull latest changes
git pull origin main

# Backup and remove old database
mv bot.db bot.db.backup_$(date +%Y%m%d_%H%M%S)

# Restart bot
pkill -f main.py
./run.sh
```

---

## Verification

After deploying, check the logs to ensure no errors:

```bash
# On remote server
tail -f bot.log

# Or if using systemd
journalctl -u crazy-trade-bot -f
```

### ✅ What to Look For

**Good signs:**
```json
{"event": "database_tables_created"}
{"event": "trading_bot_initialized", "num_crypto": 4}
{"event": "entry_order_placed", "symbol": "BTC/USD"}
{"event": "crypto_entry_order_type", "note": "Stop orders not supported"}
```

**Bad signs (should NOT appear):**
```json
{"error": "type 'UUID' is not supported"}  ❌
{"error": "Object of type UUID is not JSON serializable"}  ❌
{"error": "limit price must be > 0"}  ❌
```

---

## Files Changed

- ✅ `src/database.py` - Changed order ID columns from Integer to String
- ✅ `src/state_machine.py` - Convert all UUIDs to strings (9 locations)
- ✅ `src/bot.py` - Convert UUIDs to strings (2 locations)
- ✅ `src/alpaca_client.py` - Auto-detect tick size for very small prices

---

## What Changed in Each File

### src/database.py
```python
# Before
last_parent_id = Column(Integer, nullable=True)
order_id = Column(Integer, unique=True, index=True)

# After  
last_parent_id = Column(String, nullable=True)  # UUID support
order_id = Column(String, unique=True, index=True)  # UUID support
```

### src/state_machine.py & src/bot.py
```python
# Before
order_id=order.id  # UUID object - causes error

# After
order_id=str(order.id)  # String - works!
```

### src/alpaca_client.py
```python
# Before
def round_to_tick(self, price: float, tick_size: float = 0.01):
    # Always used 0.01 - too large for SHIB!

# After
def round_to_tick(self, price: float, tick_size: float = None):
    if tick_size is None:
        # Auto-detect based on price:
        if price < 0.01:  # SHIB at $0.00001
            tick_size = 0.0000001  # 7 decimals
        elif price < 1.0:
            tick_size = 0.0001
        else:
            tick_size = 0.01
```

---

## Rollback (If Needed)

If something goes wrong, you can rollback:

```bash
# Stop the bot
pkill -f main.py

# Restore old database
mv bot.db.backup_YYYYMMDD_HHMMSS bot.db

# Restore old code files (if you have backups)
# or use git to revert
git checkout HEAD~1

# Restart
./run.sh
```

---

## Testing

After deploying, test with a small allocation:

1. **Reduce position sizes** temporarily in `config.yaml`:
   ```yaml
   allocation:
     per_symbol_usd: 100  # Small test size
   ```

2. **Watch the first few orders** to ensure no errors

3. **Increase allocation** once confirmed working

---

## Support

If you encounter issues:

1. Check logs: `tail -f bot.log`
2. Check database was recreated: `ls -la bot.db`
3. Verify UUID fix: Look for "entry_order_placed" events
4. Verify SHIB fix: Look for SHIB orders with valid prices

---

**Last Updated:** November 8, 2024  
**Version:** 1.1.0 (UUID fixes + SHIB price rounding)

