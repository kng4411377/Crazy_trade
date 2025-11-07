# Examples

Example scripts for using the API.

## monitor_bot.py

Monitor your trading bot remotely using the REST API.

### Quick Start

```bash
# Install requests library
pip install requests

# Single status check
python examples/monitor_bot.py

# Continuous monitoring (updates every 30s)
python examples/monitor_bot.py --watch

# Show everything (orders, fills, daily P&L chart)
python examples/monitor_bot.py --watch --show-all

# Monitor remote bot
python examples/monitor_bot.py --host 192.168.1.100 --watch

# Custom refresh interval (60 seconds)
python examples/monitor_bot.py --watch --interval 60 --show-orders --show-fills
```

### Features

- ✅ Bot status (active orders, fills, cooldowns)
- ✅ Performance metrics (win rate, P&L, per-symbol, avg win/loss)
- ✅ **NEW:** Active orders display with details
- ✅ **NEW:** Recent fills/trades display
- ✅ **NEW:** Daily P&L chart (visual bar chart)
- ✅ **NEW:** Auto screen clearing for clean updates
- ✅ Continuous monitoring mode
- ✅ Works with remote servers
- ✅ Colored output with emojis

### Usage

```
python examples/monitor_bot.py [OPTIONS]

Options:
  --host HOST         API host (default: localhost)
  --port PORT         API port (default: 8080)
  --watch             Enable continuous monitoring mode
  --interval SECONDS  Update interval in seconds (default: 30)
  --show-orders       Show active orders
  --show-fills        Show recent fills/trades
  --show-daily        Show daily P&L chart (last 7 days)
  --show-all          Show all information (orders + fills + daily)
  --no-clear          Don't clear screen between updates
```

### Examples

```bash
# Check local bot once
python examples/monitor_bot.py

# Watch local bot with all info
python examples/monitor_bot.py --watch --show-all

# Watch with orders and fills only
python examples/monitor_bot.py --watch --show-orders --show-fills

# Watch remote bot at 192.168.1.100
python examples/monitor_bot.py --host 192.168.1.100 --watch --show-all

# Fast refresh (every 10 seconds) with daily chart
python examples/monitor_bot.py --watch --interval 10 --show-daily

# Keep history visible (don't clear screen)
python examples/monitor_bot.py --watch --show-all --no-clear
```

## Create Your Own

Use the API in your own scripts:

```python
import requests

api = "http://localhost:8080"

# Get status
status = requests.get(f"{api}/status").json()
print(f"Active orders: {status['active_orders']}")

# Get performance
perf = requests.get(f"{api}/performance").json()
if 'overall' in perf:
    print(f"Win rate: {perf['overall']['win_rate_pct']}%")

# Get recent fills
fills = requests.get(f"{api}/fills?limit=10").json()
for fill in fills['fills']:
    print(f"{fill['symbol']}: {fill['side']} {fill['quantity']} @ ${fill['price']}")
```

See **`API_GUIDE.md`** for full API documentation.

