#!/bin/bash
# ==============================================================================
# Crazy Trade Bot - Background Process Manager
# ==============================================================================
#
# Usage:
#   ./start_background.sh           # Start bot + API in background
#   ./start_background.sh stop      # Gracefully stop all
#   ./start_background.sh restart   # Restart all
#   ./start_background.sh status    # Check status + health
#   ./start_background.sh logs      # View bot logs (live)
#   ./start_background.sh logs api  # View API logs (live)
#   ./start_background.sh bot       # Start bot only
#   ./start_background.sh api       # Start API only
#
# ==============================================================================

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Files
BOT_PID_FILE="$SCRIPT_DIR/.bot.pid"
API_PID_FILE="$SCRIPT_DIR/.api.pid"
LOG_DIR="$SCRIPT_DIR/logs"
BOT_LOG_FILE="$LOG_DIR/bot.log"
API_LOG_FILE="$LOG_DIR/api.log"

# Settings
GRACEFUL_TIMEOUT=10  # Seconds to wait for graceful shutdown
MAX_LOG_SIZE_MB=50   # Rotate logs larger than this

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠️ ${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

log_status() {
    echo -e "${BLUE}📊${NC} $1"
}

# Create logs directory
mkdir -p "$LOG_DIR"

# Rotate log if too large
rotate_log_if_needed() {
    local log_file="$1"
    if [ -f "$log_file" ]; then
        local size_mb=$(du -m "$log_file" 2>/dev/null | cut -f1)
        if [ "$size_mb" -gt "$MAX_LOG_SIZE_MB" ] 2>/dev/null; then
            local timestamp=$(date +%Y%m%d_%H%M%S)
            mv "$log_file" "${log_file}.${timestamp}"
            gzip "${log_file}.${timestamp}" 2>/dev/null &
            echo "Log rotated: ${log_file}.${timestamp}.gz"
        fi
    fi
}

# Check if process is running
is_running() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Gracefully stop a process
stop_process() {
    local pid_file="$1"
    local name="$2"
    
    if [ ! -f "$pid_file" ]; then
        log_warn "$name PID file not found"
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    
    if ! ps -p "$pid" > /dev/null 2>&1; then
        log_warn "$name was not running (stale PID: $pid)"
        rm -f "$pid_file"
        return 0
    fi
    
    # Send SIGTERM for graceful shutdown
    echo -n "Stopping $name (PID: $pid)..."
    kill -TERM "$pid" 2>/dev/null
    
    # Wait for graceful shutdown
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt $GRACEFUL_TIMEOUT ]; do
        echo -n "."
        sleep 1
        ((count++))
    done
    echo ""
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        log_warn "$name didn't stop gracefully, forcing..."
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi
    
    rm -f "$pid_file"
    log_info "$name stopped"
}

# Pre-flight checks
preflight_check() {
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not found. Please install Python 3.9+"
        exit 1
    fi
    
    # Check config
    if [ ! -f "config.yaml" ]; then
        log_error "config.yaml not found!"
        echo "  Run: cp config.yaml.example config.yaml"
        exit 1
    fi
    
    # Check secrets
    if [ ! -f "secrets.yaml" ]; then
        log_error "secrets.yaml not found!"
        echo "  Run: cp secrets.yaml.example secrets.yaml"
        echo "  Then add your Alpaca API keys"
        exit 1
    fi
    
    # Activate venv
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
}

# Start the trading bot
start_bot() {
    if is_running "$BOT_PID_FILE"; then
        local pid=$(cat "$BOT_PID_FILE")
        log_warn "Bot is already running (PID: $pid)"
        return 1
    fi
    
    # Rotate log if needed
    rotate_log_if_needed "$BOT_LOG_FILE"
    
    echo "🚀 Starting Trading Bot..."
    nohup python3 main.py >> "$BOT_LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$BOT_PID_FILE"
    
    # Wait a moment and verify it started
    sleep 2
    if ps -p "$pid" > /dev/null 2>&1; then
        log_info "Bot started (PID: $pid)"
        echo "   Log: $BOT_LOG_FILE"
    else
        log_error "Bot failed to start! Check logs:"
        tail -20 "$BOT_LOG_FILE"
        rm -f "$BOT_PID_FILE"
        return 1
    fi
}

# Start the API server
start_api() {
    if is_running "$API_PID_FILE"; then
        local pid=$(cat "$API_PID_FILE")
        log_warn "API Server is already running (PID: $pid)"
        return 1
    fi
    
    # Rotate log if needed
    rotate_log_if_needed "$API_LOG_FILE"
    
    echo "🌐 Starting API Server..."
    nohup python3 api_server.py >> "$API_LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$API_PID_FILE"
    
    # Wait and verify
    sleep 2
    if ps -p "$pid" > /dev/null 2>&1; then
        log_info "API Server started (PID: $pid)"
        echo "   URL: http://localhost:8080"
        echo "   Log: $API_LOG_FILE"
    else
        log_error "API Server failed to start! Check logs:"
        tail -20 "$API_LOG_FILE"
        rm -f "$API_PID_FILE"
        return 1
    fi
}

# Show status
show_status() {
    echo ""
    echo "=============================="
    echo " Crazy Trade Bot Status"
    echo "=============================="
    echo ""
    
    # Bot status
    if is_running "$BOT_PID_FILE"; then
        local pid=$(cat "$BOT_PID_FILE")
        local uptime=$(ps -p "$pid" -o etime= 2>/dev/null | xargs)
        local mem=$(ps -p "$pid" -o rss= 2>/dev/null | awk '{printf "%.1f MB", $1/1024}')
        local cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null | xargs)
        echo -e "Trading Bot:  ${GREEN}● Running${NC}"
        echo "  PID:        $pid"
        echo "  Uptime:     $uptime"
        echo "  Memory:     $mem"
        echo "  CPU:        ${cpu}%"
    else
        echo -e "Trading Bot:  ${RED}○ Stopped${NC}"
    fi
    echo ""
    
    # API status
    if is_running "$API_PID_FILE"; then
        local pid=$(cat "$API_PID_FILE")
        local uptime=$(ps -p "$pid" -o etime= 2>/dev/null | xargs)
        echo -e "API Server:   ${GREEN}● Running${NC}"
        echo "  PID:        $pid"
        echo "  Uptime:     $uptime"
        echo "  URL:        http://localhost:8080"
        
        # Health check
        if command -v curl &> /dev/null; then
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null | grep -q "200"; then
                echo -e "  Health:     ${GREEN}✓ Healthy${NC}"
            else
                echo -e "  Health:     ${YELLOW}? Not responding${NC}"
            fi
        fi
    else
        echo -e "API Server:   ${RED}○ Stopped${NC}"
    fi
    echo ""
    
    # Log files
    echo "Log Files:"
    if [ -f "$BOT_LOG_FILE" ]; then
        local bot_size=$(du -h "$BOT_LOG_FILE" 2>/dev/null | cut -f1)
        echo "  Bot: $BOT_LOG_FILE ($bot_size)"
    else
        echo "  Bot: (not created yet)"
    fi
    if [ -f "$API_LOG_FILE" ]; then
        local api_size=$(du -h "$API_LOG_FILE" 2>/dev/null | cut -f1)
        echo "  API: $API_LOG_FILE ($api_size)"
    else
        echo "  API: (not created yet)"
    fi
    echo ""
    
    # Quick commands
    echo "Commands:"
    echo "  ./start_background.sh logs      # View bot logs"
    echo "  ./start_background.sh restart   # Restart all"
    echo "  ./start_background.sh stop      # Stop all"
    echo ""
}

# ==============================================================================
# Main Command Handler
# ==============================================================================

show_help() {
    echo "Crazy Trade Bot - Background Process Manager"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     Start bot and API server (default)"
    echo "  stop      Gracefully stop all services"
    echo "  restart   Restart all services"
    echo "  status    Show status and health"
    echo "  logs      View bot logs (live)"
    echo "  logs api  View API logs (live)"
    echo "  bot       Start bot only"
    echo "  api       Start API only"
    echo "  health    Quick health check (for scripts)"
    echo ""
    echo "Examples:"
    echo "  $0              # Start everything"
    echo "  $0 status       # Check if running"
    echo "  $0 logs         # Watch bot logs"
    echo "  $0 stop         # Stop gracefully"
    echo ""
}

# Show help if requested
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${1:-}" == "help" ]]; then
    show_help
    exit 0
fi

case "${1:-start}" in
    start)
        preflight_check
        echo ""
        start_bot
        echo ""
        start_api
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo " All services started!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Commands:"
        echo "  ./start_background.sh status   # Check status"
        echo "  ./start_background.sh logs     # View logs"
        echo "  ./start_background.sh stop     # Stop all"
        echo ""
        ;;
        
    bot)
        preflight_check
        start_bot
        ;;
        
    api)
        preflight_check
        start_api
        ;;
        
    stop)
        echo ""
        echo "🛑 Stopping all services..."
        echo ""
        stop_process "$BOT_PID_FILE" "Trading Bot"
        stop_process "$API_PID_FILE" "API Server"
        echo ""
        log_info "All services stopped"
        echo ""
        ;;
        
    restart)
        echo ""
        echo "🔄 Restarting all services..."
        echo ""
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        show_status
        ;;
        
    logs)
        case "${2:-bot}" in
            api)
                echo "📜 API Server logs (Ctrl+C to exit)"
                echo ""
                tail -f "$API_LOG_FILE"
                ;;
            *)
                echo "📜 Trading Bot logs (Ctrl+C to exit)"
                echo ""
                tail -f "$BOT_LOG_FILE"
                ;;
        esac
        ;;
        
    health)
        # Quick health check for monitoring scripts
        if is_running "$BOT_PID_FILE" && is_running "$API_PID_FILE"; then
            echo "OK"
            exit 0
        else
            echo "UNHEALTHY"
            exit 1
        fi
        ;;
        
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
