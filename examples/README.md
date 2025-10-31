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

# Monitor remote bot
python examples/monitor_bot.py --host 192.168.1.100 --watch

# Custom refresh interval (60 seconds)
python examples/monitor_bot.py --watch --interval 60
```

### Features

- ✅ Bot status (active orders, fills, cooldowns)
- ✅ Performance metrics (win rate, P&L, per-symbol)
- ✅ Continuous monitoring mode
- ✅ Works with remote servers
- ✅ Colored output with emojis

### Usage

```
python examples/monitor_bot.py [OPTIONS]

Options:
  --host HOST        API host (default: localhost)
  --port PORT        API port (default: 8080)
  --watch            Enable continuous monitoring
  --interval SECONDS Update interval (default: 30)
```

### Examples

```bash
# Check local bot once
python examples/monitor_bot.py

# Watch local bot
python examples/monitor_bot.py --watch

# Watch remote bot at 192.168.1.100
python examples/monitor_bot.py --host 192.168.1.100 --watch

# Fast refresh (every 10 seconds)
python examples/monitor_bot.py --watch --interval 10
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

