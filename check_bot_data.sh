#!/bin/bash
# Quick diagnostic script to check bot data status

echo "======================================"
echo "  CRAZY TRADE BOT - DATA CHECK"
echo "======================================"
echo ""

cd "$(dirname "$0")"

echo "📁 Files Check:"
echo "--------------"
if [ -f "bot.db" ]; then
    echo "✅ bot.db exists ($(ls -lh bot.db | awk '{print $5}'))"
    echo ""
    echo "📊 Database Contents:"
    echo "--------------"
    sqlite3 bot.db <<EOF
.mode column
.headers on
SELECT 'Orders' as Table, COUNT(*) as Count FROM orders
UNION ALL
SELECT 'Fills' as Table, COUNT(*) as Count FROM fills
UNION ALL
SELECT 'Events' as Table, COUNT(*) as Count FROM events
UNION ALL
SELECT 'States' as Table, COUNT(*) as Count FROM state
UNION ALL
SELECT 'Performance' as Table, COUNT(*) as Count FROM performance_snapshots;
EOF
    echo ""
    
    # Show recent events
    echo "📝 Recent Events (last 5):"
    echo "--------------"
    sqlite3 bot.db "SELECT datetime(ts, 'localtime') as Time, event_type as Event, symbol as Symbol FROM events ORDER BY ts DESC LIMIT 5;" 2>/dev/null || echo "No events yet"
    
else
    echo "❌ bot.db NOT FOUND - Bot has never been run!"
fi
echo ""

echo "🔧 Process Check:"
echo "--------------"
if pgrep -f "main.py" > /dev/null 2>&1; then
    echo "✅ Bot is running (PID: $(pgrep -f 'main.py'))"
else
    echo "❌ Bot is NOT running"
fi

if pgrep -f "api_server.py" > /dev/null 2>&1; then
    echo "✅ API server is running (PID: $(pgrep -f 'api_server.py'))"
else
    echo "❌ API server is NOT running"
fi
echo ""

echo "🌐 API Check:"
echo "--------------"
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ API server responding at http://localhost:8080"
    echo ""
    echo "Try these commands:"
    echo "  curl http://localhost:8080/status | jq ."
    echo "  curl http://localhost:8080/performance | jq ."
    echo "  curl http://localhost:8080/fills | jq ."
else
    echo "❌ API server not responding at http://localhost:8080"
    echo ""
    echo "To start API server:"
    echo "  ./run_api.sh"
fi
echo ""

echo "📋 Configuration:"
echo "--------------"
if [ -f "secrets.yaml" ]; then
    echo "✅ secrets.yaml exists"
else
    echo "❌ secrets.yaml missing!"
fi

if [ -f "config.yaml" ]; then
    echo "✅ config.yaml exists"
    echo ""
    echo "Watchlist:"
    grep -A 20 "^watchlist:" config.yaml | grep -E "^\s+-\s+" | head -5
    echo ""
    echo "Crypto Watchlist:"
    grep -A 20 "^crypto_watchlist:" config.yaml | grep -E "^\s+-\s+" | head -5
else
    echo "❌ config.yaml missing!"
fi
echo ""

echo "======================================"
echo "📊 SUMMARY"
echo "======================================"

if [ ! -f "bot.db" ]; then
    echo ""
    echo "🚨 THE BOT HAS NEVER RUN!"
    echo ""
    echo "To start the bot and generate data:"
    echo ""
    echo "  # Option 1: Foreground (see logs in terminal)"
    echo "  python3 main.py"
    echo ""
    echo "  # Option 2: Background (bot + API together)"
    echo "  ./start_background.sh start"
    echo ""
    echo "After the bot runs, it will:"
    echo "  1. Create bot.db database"
    echo "  2. Connect to Alpaca"
    echo "  3. Start placing orders"
    echo "  4. Generate data for API endpoints"
    echo ""
elif [ $(sqlite3 bot.db "SELECT COUNT(*) FROM fills;") -eq 0 ]; then
    echo ""
    echo "⚠️  Bot has run but NO FILLS yet"
    echo ""
    echo "This means:"
    echo "  - Bot is working"
    echo "  - Orders may be placed"
    echo "  - But no trades have executed yet"
    echo ""
    echo "Check if:"
    echo "  - Market is open (for stocks)"
    echo "  - Prices are hitting your entry triggers"
    echo "  - Orders are being placed: curl localhost:8080/orders"
    echo ""
else
    echo ""
    echo "✅ Bot is working and has trade data!"
    echo ""
    echo "View data:"
    echo "  curl http://localhost:8080/status | jq ."
    echo "  curl http://localhost:8080/performance | jq ."
    echo "  curl http://localhost:8080/fills | jq ."
    echo ""
fi

echo "======================================"

