#!/bin/bash
# Quick verification script to check if fills are synced

echo "======================================="
echo "  FILL SYNC VERIFICATION"
echo "======================================="
echo ""

# Check if API is running
if ! curl -s http://localhost:8080/status > /dev/null 2>&1; then
    echo "❌ API server not responding at http://localhost:8080"
    exit 1
fi

echo "✅ API server is responding"
echo ""

# Get fill count
echo "📊 Checking fills..."
FILL_COUNT=$(curl -s http://localhost:8080/fills | jq -r '.count')

if [ "$FILL_COUNT" = "null" ] || [ -z "$FILL_COUNT" ]; then
    echo "❌ Failed to get fill count"
    exit 1
fi

echo "   Total fills: $FILL_COUNT"
echo ""

if [ "$FILL_COUNT" -gt 0 ]; then
    echo "✅ Fills are being recorded!"
    echo ""
    echo "Recent fills:"
    curl -s http://localhost:8080/fills | jq -r '.fills[] | "  - \(.symbol) \(.side) \(.quantity) @ $\(.price) (\(.timestamp))"' | head -10
    echo ""
    
    # Check performance
    echo "📈 Performance summary:"
    curl -s http://localhost:8080/performance | jq -r '
        if .total_trades then
            "  Total trades: \(.total_trades)\n  Win rate: \(.win_rate)%\n  Total P&L: $\(.total_pnl)"
        else
            "  \(.message // "No performance data yet")"
        end
    '
else
    echo "⚠️  No fills recorded yet"
    echo ""
    echo "This could be normal if:"
    echo "  - Bot just started and no orders have filled"
    echo "  - All historical orders were expired/cancelled (not filled)"
    echo ""
    echo "Check bot logs for 'untracked_fill_detected' events:"
    echo "  sudo journalctl -u crazy-trade-bot -n 50 | grep untracked"
fi

echo ""
echo "======================================="











