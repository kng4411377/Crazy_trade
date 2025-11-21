# Reset Guide - How to Start Over

This guide explains how to reset your trading bot and start fresh.

## Quick Reset Options

### Option 1: Reset Paper Account Only (Positions & Orders)

This closes all open positions and cancels all orders but **keeps your database history** (fills, orders, performance tracking).

```bash
python scripts/reset_paper_account.py
```

**What it does:**
- ✅ Closes all open positions
- ✅ Cancels all pending orders
- ❌ Does NOT delete database records

**When to use:** When you want to close positions but keep trading history.

---

### Option 2: Full Database Reset (Start Completely Fresh)

This deletes **all historical data** from the database but doesn't touch your Alpaca account.

```bash
# Stop the bot first if it's running
# Press Ctrl+C or kill the process

# Delete the database file
rm bot.db

# Restart the bot - it will create a fresh database
./run.sh
```

**What it does:**
- ✅ Deletes all order records
- ✅ Deletes all fill/transaction records
- ✅ Deletes all performance snapshots
- ✅ Clears all symbol states and cooldowns
- ❌ Does NOT close Alpaca positions/orders

**When to use:** When you want to start with completely clean data but keep existing positions.

---

### Option 3: Complete Reset (Account + Database)

This is the nuclear option - everything starts fresh.

```bash
# Step 1: Reset Alpaca account (close positions & cancel orders)
python scripts/reset_paper_account.py

# Step 2: Stop the bot if running
# Press Ctrl+C or kill the process

# Step 3: Delete database
rm bot.db

# Step 4: Restart bot
./run.sh
```

**What it does:**
- ✅ Closes all Alpaca positions
- ✅ Cancels all Alpaca orders
- ✅ Deletes all database records
- ✅ Fresh start for everything

**When to use:** When you want a complete fresh start.

---

## Detailed Instructions

### Resetting the Paper Account

The `reset_paper_account.py` script is safe and includes safeguards:

1. **Safety checks:**
   - Only works in paper trading mode
   - Requires explicit "yes" confirmation
   - Shows what will be closed before proceeding

2. **Usage:**
   ```bash
   python scripts/reset_paper_account.py
   ```

3. **Output example:**
   ```
   ============================================================
   RESET PAPER TRADING ACCOUNT
   ============================================================

   ✅ Mode: paper (paper trading)

   ⚠️  WARNING: This will close ALL positions and cancel ALL orders!

   Are you sure you want to continue? (yes/no): yes

   📊 Current Account State:
      Open Positions: 3
         - TSLA: 10 shares
         - NVDA: 5 shares
         - META: 8 shares
      Open Orders: 2

   🔄 Resetting account...
   ✅ Account reset successful!
   ```

### Resetting the Database

The database stores all historical trading data in `bot.db`:

**Tables that get cleared:**
- `orders` - All order records
- `fills` - All transaction/execution records
- `events` - All event logs
- `state` - Symbol states and cooldowns
- `performance_snapshots` - Daily performance tracking

**To reset:**
```bash
# Option A: Delete the file
rm bot.db

# Option B: Move it to backup
mv bot.db bot.db.backup.$(date +%Y%m%d_%H%M%S)

# The bot will create a new bot.db automatically on next startup
```

### Resetting Individual Symbol States

If you just want to clear cooldown for specific symbols without full reset:

```bash
# Connect to database
sqlite3 bot.db

# Clear cooldown for all symbols
UPDATE state SET cooldown_until_ts = NULL;

# Clear cooldown for specific symbol
UPDATE state SET cooldown_until_ts = NULL WHERE symbol = 'TSLA';

# Exit
.quit
```

---

## Common Scenarios

### Scenario 1: Testing a new strategy
**Need:** Keep positions, clear data
```bash
rm bot.db
./run.sh
```

### Scenario 2: Hit daily loss limit, want to stop
**Need:** Close everything but keep records
```bash
python scripts/reset_paper_account.py
# Don't delete bot.db - review performance later
```

### Scenario 3: Complete fresh start for new week
**Need:** Everything reset
```bash
python scripts/reset_paper_account.py
rm bot.db
./run.sh
```

### Scenario 4: Symbol stuck in cooldown
**Need:** Clear state for one symbol
```bash
sqlite3 bot.db "UPDATE state SET cooldown_until_ts = NULL WHERE symbol = 'TSLA';"
```

---

## Safety Notes

⚠️ **Before Resetting:**
1. Stop the bot (Ctrl+C) to avoid conflicts
2. Backup your database if you want to preserve data:
   ```bash
   cp bot.db bot.db.backup
   ```
3. Review your account on Alpaca dashboard

⚠️ **Paper Trading Only:**
- The reset script ONLY works in paper mode
- For live accounts, you must manually close positions via Alpaca dashboard

⚠️ **Data Loss:**
- Deleting `bot.db` is **permanent**
- Export trades first if you need them:
  ```bash
  python scripts/export_trades.py
  # Creates trades_export_YYYYMMDD_HHMMSS.csv
  ```

---

## Verification After Reset

After resetting, verify everything is clean:

```bash
# Check Alpaca account
python scripts/check_status.py

# Check database (should be empty or new)
sqlite3 bot.db "SELECT COUNT(*) FROM orders;"
sqlite3 bot.db "SELECT COUNT(*) FROM fills;"
sqlite3 bot.db "SELECT * FROM state;"
```

Expected results:
- ✅ No open positions
- ✅ No pending orders
- ✅ Empty or minimal database records
- ✅ No cooldown timestamps

---

## Quick Reference

| What to Reset | Command | Data Loss | Position Close |
|--------------|---------|-----------|----------------|
| Positions/Orders only | `python scripts/reset_paper_account.py` | No | Yes |
| Database only | `rm bot.db` | Yes | No |
| Everything | Both commands | Yes | Yes |
| One symbol state | `sqlite3 bot.db "UPDATE state SET cooldown_until_ts = NULL WHERE symbol = 'XXX';"` | No | No |

---

## Need Help?

If something goes wrong:
1. Check bot logs: `tail -f bot.log | jq .`
2. Verify Alpaca account in dashboard
3. Check database: `sqlite3 bot.db "SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;"`
4. See troubleshooting in main README.md

