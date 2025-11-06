#!/bin/bash
# Start the Crazy Trade Bot in background
#
# Usage:
#   ./start_background.sh        # Start bot in background
#   ./start_background.sh stop   # Stop bot
#   ./start_background.sh status # Check status
#   ./start_background.sh logs   # View logs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BOT_PID_FILE="$SCRIPT_DIR/.bot.pid"
API_PID_FILE="$SCRIPT_DIR/.api.pid"
BOT_LOG_FILE="$SCRIPT_DIR/logs/bot.log"
API_LOG_FILE="$SCRIPT_DIR/logs/api.log"

# Create logs directory
mkdir -p logs

case "${1:-start}" in
    start)
        echo "🚀 Starting Crazy Trade Bot in background..."
        
        # Check if already running
        if [ -f "$BOT_PID_FILE" ]; then
            BOT_PID=$(cat "$BOT_PID_FILE")
            if ps -p "$BOT_PID" > /dev/null 2>&1; then
                echo "⚠️  Bot is already running (PID: $BOT_PID)"
            else
                echo "Removing stale PID file..."
                rm "$BOT_PID_FILE"
            fi
        fi
        
        # Activate venv
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        
        # Start bot
        if [ ! -f "$BOT_PID_FILE" ]; then
            nohup python3 main.py > "$BOT_LOG_FILE" 2>&1 &
            BOT_PID=$!
            echo $BOT_PID > "$BOT_PID_FILE"
            echo "✅ Bot started (PID: $BOT_PID)"
            echo "   Logs: $BOT_LOG_FILE"
        fi
        
        # Start API server
        echo ""
        echo "🌐 Starting API Server in background..."
        
        if [ -f "$API_PID_FILE" ]; then
            API_PID=$(cat "$API_PID_FILE")
            if ps -p "$API_PID" > /dev/null 2>&1; then
                echo "⚠️  API Server is already running (PID: $API_PID)"
            else
                echo "Removing stale PID file..."
                rm "$API_PID_FILE"
            fi
        fi
        
        if [ ! -f "$API_PID_FILE" ]; then
            nohup python3 api_server.py > "$API_LOG_FILE" 2>&1 &
            API_PID=$!
            echo $API_PID > "$API_PID_FILE"
            echo "✅ API Server started (PID: $API_PID)"
            echo "   URL: http://localhost:8080"
            echo "   Logs: $API_LOG_FILE"
        fi
        
        echo ""
        echo "📋 Quick Commands:"
        echo "   ./start_background.sh status  # Check status"
        echo "   ./start_background.sh logs    # View logs"
        echo "   ./start_background.sh stop    # Stop everything"
        echo ""
        ;;
        
    stop)
        echo "🛑 Stopping Crazy Trade Bot..."
        
        # Stop bot
        if [ -f "$BOT_PID_FILE" ]; then
            BOT_PID=$(cat "$BOT_PID_FILE")
            if ps -p "$BOT_PID" > /dev/null 2>&1; then
                kill "$BOT_PID"
                echo "✅ Bot stopped (PID: $BOT_PID)"
            else
                echo "⚠️  Bot was not running"
            fi
            rm "$BOT_PID_FILE"
        else
            echo "⚠️  Bot PID file not found"
        fi
        
        # Stop API
        if [ -f "$API_PID_FILE" ]; then
            API_PID=$(cat "$API_PID_FILE")
            if ps -p "$API_PID" > /dev/null 2>&1; then
                kill "$API_PID"
                echo "✅ API Server stopped (PID: $API_PID)"
            else
                echo "⚠️  API Server was not running"
            fi
            rm "$API_PID_FILE"
        else
            echo "⚠️  API Server PID file not found"
        fi
        
        echo ""
        echo "All processes stopped."
        ;;
        
    status)
        echo "📊 Crazy Trade Bot Status"
        echo "=========================="
        echo ""
        
        # Check bot
        if [ -f "$BOT_PID_FILE" ]; then
            BOT_PID=$(cat "$BOT_PID_FILE")
            if ps -p "$BOT_PID" > /dev/null 2>&1; then
                echo "Bot:        ✅ Running (PID: $BOT_PID)"
                echo "  Uptime:   $(ps -p "$BOT_PID" -o etime= | xargs)"
            else
                echo "Bot:        ❌ Not running (stale PID)"
            fi
        else
            echo "Bot:        ❌ Not running"
        fi
        
        # Check API
        if [ -f "$API_PID_FILE" ]; then
            API_PID=$(cat "$API_PID_FILE")
            if ps -p "$API_PID" > /dev/null 2>&1; then
                echo "API Server: ✅ Running (PID: $API_PID)"
                echo "  URL:      http://localhost:8080"
                echo "  Uptime:   $(ps -p "$API_PID" -o etime= | xargs)"
            else
                echo "API Server: ❌ Not running (stale PID)"
            fi
        else
            echo "API Server: ❌ Not running"
        fi
        
        echo ""
        echo "Log files:"
        echo "  Bot:  $BOT_LOG_FILE"
        echo "  API:  $API_LOG_FILE"
        ;;
        
    logs)
        echo "📜 Viewing bot logs (Ctrl+C to exit)..."
        echo ""
        tail -f "$BOT_LOG_FILE"
        ;;
        
    restart)
        echo "🔄 Restarting Crazy Trade Bot..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    *)
        echo "Usage: $0 {start|stop|status|logs|restart}"
        exit 1
        ;;
esac

