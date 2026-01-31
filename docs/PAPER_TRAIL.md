# Paper trail and local records

The bot keeps a local paper trail so you can audit decisions and use executed prices for risk logic (e.g. crypto stop-loss based on cost basis).

## What is stored locally

All of this is in the SQLite (or configured) database.

| Table / source | What it stores | Used for |
|----------------|----------------|----------|
| **fills** | Every execution: `exec_id`, `symbol`, `side`, `qty`, `price`, `order_id`, `ts` | P&L, trade stats, **effective entry price** for open position |
| **orders** | Every order placed: `order_id`, `symbol`, `side`, `order_type`, `status`, `qty`, `stop_price`, `limit_price`, `trailing_pct`, `parent_id`, `created_at` | Order history, which parent/child orders exist |
| **events** | Audit events: `event_type`, `symbol`, `payload_json`, `ts` | Paper trail for stops, recreated stops, AI exits, fills, errors |
| **state** | Per-symbol state: `symbol`, `cooldown_until_ts`, `last_parent_id`, `last_trail_id` | Cooldowns, last order IDs |
| **performance_snapshots** | Daily snapshots: account value, cash, position value, P&L, num positions/trades | Circuit breaker, reporting |

## Using local executed price

- **Crypto stop-loss** uses your **local cost basis** when available:
  - **After a fill:** The fill callback passes the executed price into the stop placement, so the stop is based on that fill price.
  - **When recreating a missing stop:** The bot calls `get_open_position_entry_from_fills(symbol)` to get open size and **volume‑weighted average entry price** from local fills (FIFO), then passes that as `entry_price_from_fills` so the stop is based on your recorded cost, not just current market.
- **Stocks** still use the broker’s trailing stop; no change there.

So for crypto, “maximum loss” style protection is driven by **your executed price** (local fills), not only by current price.

## Event types (paper trail)

Relevant `event_type` values in **events** and what they mean:

| event_type | When | payload (typical) |
|------------|------|-------------------|
| `trailing_stop_placed_after_entry` | Stop placed right after a BUY fill | `order_id`, `qty`, `entry_price_used`, `stop_price`, `source` (e.g. `local_fill`), `is_crypto` |
| `trailing_stop_recreated` | Missing stop detected; new stop placed | `order_id`, `qty`, `entry_price_used`, `stop_price`, `source` (`local_fills` or `broker_price`) |
| `trailing_stop_adjusted` | Stop qty mismatch; stop cancelled and recreated | `old_qty`, `new_qty`, `order_id`, `entry_price_used`, `stop_price`, `source` |
| `position_closed_ai_exit` | Position closed on Gemini SELL | `qty`, `reason` |
| `fill` | Fill recorded | `order_id`, `exec_id`, `side`, `qty`, `price` |
| `stopout_cooldown_started` | Stop hit; cooldown started | `cooldown_minutes`, `cooldown_until` |
| `daily_loss_pct_limit_breached` / `daily_loss_usd_limit_breached` | Circuit breaker | `daily_loss_pct` / `daily_pnl`, `limit` |

`payload_json` holds the details (e.g. `entry_price_used`, `stop_price`, `source`) for auditing.

## How to query the paper trail

### Via the API (with pagination)

- **`GET /fills`** – Fills (executed prices), **paginated**  
  - Query params: `limit` (default 20, max 200), `offset`, or `page` (1-based).  
  - Response includes `fills` and `pagination`: `{ limit, offset, count, total, total_pages }`.

- **`GET /events`** – Events (paper trail), **paginated**  
  - Same params: `limit`, `offset`, or `page`.  
  - Response includes `events` and `pagination`: `{ limit, offset, count, total, total_pages }`.

Examples:  
`/fills?limit=20&page=2` (fills 21–40), `/events?limit=50&offset=100` (events 101–150).  
See [API_GUIDE.md](API_GUIDE.md) for full details.

### Via the database

- **Fills for a symbol (executed prices):**
  - Use `get_recent_fills(session, symbol, limit)` or query `fills` where `symbol = ?` ordered by `ts desc`.
- **Effective entry for an open position (cost basis from fills):**
  - Use `get_open_position_entry_from_fills(session, symbol)` → `(open_qty, avg_entry_price)`.
- **Why a stop was placed and at what level:**
  - Query `events` where `event_type` in (`trailing_stop_placed_after_entry`, `trailing_stop_recreated`, `trailing_stop_adjusted`) and optionally `symbol = ?`; read `payload_json` for `entry_price_used`, `stop_price`, `source`.
- **Order history:**
  - Query `orders` by `symbol` and/or `order_id`, `created_at`.

Logs (structlog) also emit the same info (e.g. `crypto_stop_loss_placed` with `entry_price_used`, `stop_price`, `source`); the DB events give a queryable, durable paper trail.

## Summary

- **Executed price** is recorded in **fills** and used for crypto stop-loss (after fill and when recreating a stop) so protection is based on your real cost.
- **Paper trail** is in **events** (and logs): every stop placement/recreate/adjust is stored with `entry_price_used`, `stop_price`, and `source` so you can see exactly what was used and why.
