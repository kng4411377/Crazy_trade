# 🔧 UUID Database Fix

## Issue
```
sqlite3.ProgrammingError: Error binding parameter 3: type 'UUID' is not supported
```

**Root Cause:** Alpaca API returns order IDs as UUID objects (e.g., `UUID('c8d1892d-be67-4589-8b42-e238252a2cb6')`), but SQLite doesn't support UUID types directly. The database columns were defined as `Integer`, causing type errors when trying to store UUIDs.

---

## Fix Applied

### 1. **Updated Database Schema** (`src/database.py`)

Changed all order ID columns from `Integer` to `String`:

```python
# SymbolState table
last_parent_id = Column(String, nullable=True)  # Was: Integer
last_trail_id = Column(String, nullable=True)   # Was: Integer

# OrderRecord table  
order_id = Column(String, unique=True, index=True)  # Was: Integer
parent_id = Column(String, nullable=True)           # Was: Integer

# FillRecord table
order_id = Column(String, index=True, nullable=False)  # Was: Integer
```

### 2. **Convert UUIDs to Strings** (`src/state_machine.py`, `src/bot.py`)

Added `str()` conversion whenever storing order IDs:

```python
# state_machine.py
last_parent_id=str(parent_order.order.id)  # Convert UUID to string
order_id=str(order.id)                     # Convert UUID to string

# bot.py  
order_id = str(order.id)  # Convert UUID to string
```

### 3. **Database Migration**

The old database was backed up and removed to allow the bot to create a new database with the correct schema:

```bash
bot.db → bot.db.backup_YYYYMMDD_HHMMSS
```

---

## Files Modified

1. **`src/database.py`**
   - Changed `SymbolState.last_parent_id` from Integer to String
   - Changed `SymbolState.last_trail_id` from Integer to String
   - Changed `OrderRecord.order_id` from Integer to String
   - Changed `OrderRecord.parent_id` from Integer to String
   - Changed `FillRecord.order_id` from Integer to String

2. **`src/state_machine.py`**
   - Line 129: Convert `parent_order.order.id` to string
   - Line 137: Convert `order.id` to string
   - Line 330: Convert `order_wrapper.order.id` to string
   - Line 337: Convert `order.id` to string
   - Line 354: Convert `order.id` to string (in payload)

3. **`src/bot.py`**
   - Line 306: Convert `order.id` to string
   - Line 359: Convert `order_wrapper.order.id` to string

---

## Testing

The bot will now:
1. ✅ Accept UUID order IDs from Alpaca API
2. ✅ Convert them to strings automatically
3. ✅ Store them in SQLite database (String columns)
4. ✅ No more `type 'UUID' is not supported` errors

---

## Next Steps

1. **Restart your bot** - it will create a new database with the correct schema:
   ```bash
   ./run.sh
   ```

2. **Monitor the logs** - ensure no UUID errors appear:
   ```bash
   tail -f bot.log
   ```

3. **Historical data** - if you need your old order/fill history, the backup is at:
   ```
   bot.db.backup_YYYYMMDD_HHMMSS
   ```

---

## Why This Happened

Alpaca recently switched to using **UUIDs for order IDs** (e.g., `c8d1892d-be67-4589-8b42-e238252a2cb6`) instead of simple integers. Our database schema was designed for integer IDs, but UUIDs are 128-bit identifiers that can't fit in a standard integer field.

**Solution:** Store them as strings, which is the standard approach for UUIDs in SQLite.

---

**Status:** ✅ FIXED  
**Date:** November 8, 2024  
**Impact:** Breaking change - requires database recreation

