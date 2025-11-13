# Fill Synchronization Fix

## Problem

The bot was showing **0 fills** even though trades were executing on Alpaca's side. This was because:

1. The bot only detected fills for orders in its **in-memory `tracked_orders` dictionary**
2. When the bot restarts, this dictionary is **cleared**
3. Orders that filled after a restart were **never detected**, even though the bot polls Alpaca

## Root Cause

In `src/alpaca_client.py`, the `check_for_events()` method had this logic:

```python
for order in orders:
    if order.id in self.tracked_orders:  # ❌ Only checked tracked orders!
        # process fills...
```

This meant:
- ✅ Fills detected: Orders placed by the current bot session
- ❌ Fills missed: Orders from before a restart or any untracked orders

## Solution

The fix has **3 parts**:

### 1. Detect Untracked Fills (`alpaca_client.py`)

Modified `check_for_events()` to process **ALL filled orders from Alpaca**, not just tracked ones:

```python
# After checking tracked orders, also check untracked ones
elif order.status.value in ['filled', 'partially_filled'] and order.filled_qty:
    # Process this fill even though it wasn't tracked
    wrapper = AlpacaOrder(order)
    # ... trigger callbacks ...
```

### 2. Prevent Duplicate Fills (`database.py`)

Added `fill_exists()` method to check if a fill was already recorded:

```python
def fill_exists(self, session: Session, exec_id: str) -> bool:
    """Check if a fill with the given exec_id already exists."""
    return session.query(FillRecord).filter(FillRecord.exec_id == exec_id).first() is not None
```

Updated `add_fill()` to skip duplicates automatically.

### 3. Check Before Processing (`bot.py`)

Updated `_on_fill()` to check for duplicates before processing:

```python
# Check if fill already exists before processing
if self.db.fill_exists(session, exec_id):
    logger.debug("fill_already_processed", exec_id=exec_id, symbol=symbol)
    return
```

This prevents:
- ❌ Duplicate database entries
- ❌ Multiple trailing stop orders for the same entry
- ❌ Incorrect cooldown triggers

## What Happens Now

After deploying this fix and restarting the bot:

1. **Bot polls Alpaca** every few seconds (via `check_for_events()`)
2. **Gets ALL closed orders** (not just tracked ones)
3. **Finds filled orders** that weren't previously recorded
4. **Processes those fills** (records to database, places trailing stops, etc.)
5. **Skips duplicates** automatically

## Deployment

### On Your Remote Server

```bash
cd ~/Crazy_trade

# Stop the bot
sudo systemctl stop crazy-trade-bot

# Pull the changes
git pull

# Restart the bot
sudo systemctl start crazy-trade-bot

# Check logs to see fills being detected
sudo journalctl -u crazy-trade-bot -f
```

### Expected Log Output

You should see logs like:

```
{"event": "untracked_fill_detected", "symbol": "BTC/USD", "order_id": "...", "qty": 0.01, ...}
{"event": "fill_received", "symbol": "BTC/USD", "side": "BUY", ...}
```

### Verify the Fix

After restart, check the API:

```bash
curl http://localhost:8080/fills | jq .
curl http://localhost:8080/performance | jq .
```

You should now see:
- ✅ Fill records in the database
- ✅ Performance metrics calculated
- ✅ Trade history visible

## Important Notes

1. **One-time sync**: When the bot first starts with this fix, it will process the last 50 closed orders from Alpaca
2. **Duplicate protection**: The `exec_id` check prevents the same fill from being recorded twice
3. **No data loss**: All historical fills from Alpaca (last 50 closed orders) will be captured
4. **Continuous sync**: Going forward, all fills will be detected whether the bot was tracking the order or not

## Testing

You can verify the fix is working by:

1. Check bot logs for `untracked_fill_detected` events
2. Query the fills endpoint: `curl http://localhost:8080/fills | jq .`
3. Check the database: `sqlite3 bot.db "SELECT COUNT(*) FROM fills;"`

## Files Modified

- `src/alpaca_client.py` - Enhanced `check_for_events()` to process all fills
- `src/database.py` - Added `fill_exists()` and duplicate checking to `add_fill()`
- `src/bot.py` - Added duplicate check before processing fills

## Backward Compatibility

✅ This change is **fully backward compatible**:
- Existing database schema unchanged
- No config changes needed
- Works with existing data
- Gracefully handles duplicates

