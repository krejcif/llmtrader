#!/bin/bash
# Bot Management Script - Start/Stop/Status autonomous trading bot + dashboard

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOT_PID_FILE="$BOT_DIR/bot.pid"
BOT_LOG_FILE="$BOT_DIR/logs/bot_background.log"
DASHBOARD_PID_FILE="$BOT_DIR/dashboard.pid"
DASHBOARD_LOG_FILE="$BOT_DIR/logs/web_api.log"
VENV_DIR="$BOT_DIR/venv"
DASHBOARD_PORT=5000

cd "$BOT_DIR"

start_bot() {
    if [ -f "$BOT_PID_FILE" ]; then
        PID=$(cat "$BOT_PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  Bot is already running (PID: $PID)"
            echo "   Use: ./bot.sh status"
            return 1
        else
            echo "🧹 Removing stale PID file..."
            rm -f "$BOT_PID_FILE"
        fi
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🤖 STARTING DYNAMIC MULTI-STRATEGY TRADING BOT"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check .env
    if [ ! -f .env ]; then
        echo "❌ Error: .env file not found!"
        echo "   Please create .env with DEEPSEEK_API_KEY"
        return 1
    fi
    
    # Activate venv if exists
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        echo "✅ Virtual environment activated"
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Start bot in background (DYNAMIC system)
    echo "🚀 Starting dynamic bot in background..."
    echo "   Using: trading_bot_dynamic.py"
    nohup python3 src/trading_bot_dynamic.py > "$BOT_LOG_FILE" 2>&1 &
    BOT_PID=$!
    
    # Save PID
    echo $BOT_PID > "$BOT_PID_FILE"
    
    echo "✅ Dynamic bot started successfully!"
    echo "   Mode: Multi-strategy (flexible intervals & timeframes)"
    echo "   PID: $BOT_PID"
    echo "   Background log: $BOT_LOG_FILE"
    echo "   Main log: logs/trading_bot.log"
    echo ""
    echo "📋 Useful commands:"
    echo "   ./bot.sh status    # Check bot status"
    echo "   ./bot.sh logs      # View live logs"
    echo "   ./bot.sh stop      # Stop bot"
    echo "   ./view_logs.sh     # Interactive log viewer"
    echo ""
    echo "📊 Active strategies: Check strategy_config.py"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Wait a moment and check
    sleep 2
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo "✅ Bot is running healthy"
    else
        echo "❌ Bot failed to start! Check: tail $BOT_LOG_FILE"
        rm -f "$BOT_PID_FILE"
        return 1
    fi
}

stop_bot() {
    if [ ! -f "$BOT_PID_FILE" ]; then
        echo "⚠️  Bot is not running (no PID file)"
        return 1
    fi
    
    PID=$(cat "$BOT_PID_FILE")
    
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  Bot is not running (stale PID file)"
        rm -f "$BOT_PID_FILE"
        return 1
    fi
    
    echo "🛑 Stopping bot (PID: $PID)..."
    
    # Send SIGTERM for graceful shutdown
    kill -TERM $PID
    
    # Wait for graceful shutdown (max 10 seconds)
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            echo "✅ Bot stopped gracefully"
            rm -f "$BOT_PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo "⚠️  Forcing bot shutdown..."
    kill -9 $PID 2>/dev/null
    rm -f "$BOT_PID_FILE"
    echo "✅ Bot stopped (forced)"
}

status_bot() {
    if [ ! -f "$BOT_PID_FILE" ]; then
        echo "⏸️  Bot is NOT running"
        return 1
    fi
    
    PID=$(cat "$BOT_PID_FILE")
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ Bot is RUNNING"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "   PID: $PID"
        echo "   Started: $(ps -p $PID -o lstart= 2>/dev/null)"
        echo "   CPU: $(ps -p $PID -o %cpu= 2>/dev/null | xargs)%"
        echo "   Memory: $(ps -p $PID -o rss= 2>/dev/null | awk '{printf "%.1f MB", $1/1024}')"
        echo ""
        
        # Show recent activity from logs
        if [ -f "logs/trading_bot.log" ]; then
            echo "📊 Recent Activity:"
            tail -5 logs/trading_bot.log | sed 's/^/   /'
        fi
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Show stats
        if command -v python &> /dev/null; then
            echo ""
            source "$VENV_DIR/bin/activate" 2>/dev/null
            cd src && python trade_manager.py stats 2>/dev/null && cd ..
        fi
        
        return 0
    else
        echo "⏸️  Bot is NOT running (stale PID file)"
        rm -f "$BOT_PID_FILE"
        return 1
    fi
}

view_logs() {
    if [ -f "logs/trading_bot.log" ]; then
        echo "📋 Viewing live logs (Ctrl+C to exit)..."
        tail -f logs/trading_bot.log
    else
        echo "❌ No log file found. Bot hasn't run yet."
        return 1
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DASHBOARD FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

start_dashboard() {
    if [ -f "$DASHBOARD_PID_FILE" ]; then
        PID=$(cat "$DASHBOARD_PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  Dashboard is already running (PID: $PID)"
            echo "   URL: http://localhost:$DASHBOARD_PORT"
            return 1
        else
            echo "🧹 Removing stale dashboard PID file..."
            rm -f "$DASHBOARD_PID_FILE"
        fi
    fi
    
    # Kill any process using the port
    lsof -ti:$DASHBOARD_PORT | xargs kill -9 2>/dev/null
    sleep 1
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 STARTING DASHBOARD"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Activate venv if exists
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        echo "✅ Virtual environment activated"
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Start dashboard in background
    echo "🚀 Starting web API on port $DASHBOARD_PORT..."
    nohup python3 src/web_api.py > "$DASHBOARD_LOG_FILE" 2>&1 &
    DASHBOARD_PID=$!
    
    # Save PID
    echo $DASHBOARD_PID > "$DASHBOARD_PID_FILE"
    
    echo "✅ Dashboard started successfully!"
    echo "   PID: $DASHBOARD_PID"
    echo "   URL: http://localhost:$DASHBOARD_PORT"
    echo "   Log: $DASHBOARD_LOG_FILE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Wait a moment and check
    sleep 2
    if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
        echo "✅ Dashboard is running healthy"
    else
        echo "❌ Dashboard failed to start! Check: tail $DASHBOARD_LOG_FILE"
        rm -f "$DASHBOARD_PID_FILE"
        return 1
    fi
}

stop_dashboard() {
    if [ ! -f "$DASHBOARD_PID_FILE" ]; then
        echo "⚠️  Dashboard is not running (no PID file)"
        return 1
    fi
    
    PID=$(cat "$DASHBOARD_PID_FILE")
    
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  Dashboard is not running (stale PID file)"
        rm -f "$DASHBOARD_PID_FILE"
        return 1
    fi
    
    echo "🛑 Stopping dashboard (PID: $PID)..."
    
    # Send SIGTERM for graceful shutdown
    kill -TERM $PID
    
    # Wait for graceful shutdown (max 5 seconds)
    for i in {1..5}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            echo "✅ Dashboard stopped gracefully"
            rm -f "$DASHBOARD_PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo "⚠️  Forcing dashboard shutdown..."
    kill -9 $PID 2>/dev/null
    rm -f "$DASHBOARD_PID_FILE"
    echo "✅ Dashboard stopped (forced)"
}

status_dashboard() {
    if [ ! -f "$DASHBOARD_PID_FILE" ]; then
        echo "⏸️  Dashboard is NOT running"
        return 1
    fi
    
    PID=$(cat "$DASHBOARD_PID_FILE")
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ Dashboard is RUNNING"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "   PID: $PID"
        echo "   URL: http://localhost:$DASHBOARD_PORT"
        echo "   Started: $(ps -p $PID -o lstart= 2>/dev/null)"
        echo "   CPU: $(ps -p $PID -o %cpu= 2>/dev/null | xargs)%"
        echo "   Memory: $(ps -p $PID -o rss= 2>/dev/null | awk '{printf "%.1f MB", $1/1024}')"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return 0
    else
        echo "⏸️  Dashboard is NOT running (stale PID file)"
        rm -f "$DASHBOARD_PID_FILE"
        return 1
    fi
}

restart_dashboard() {
    echo "🔄 Restarting dashboard..."
    stop_dashboard
    sleep 2
    start_dashboard
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMBINED FUNCTIONS (Bot + Dashboard)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

start_all() {
    echo "🚀 Starting bot + dashboard..."
    echo ""
    start_bot
    echo ""
    start_dashboard
}

stop_all() {
    echo "🛑 Stopping bot + dashboard..."
    echo ""
    stop_bot
    echo ""
    stop_dashboard
}

restart_all() {
    echo "🔄 Restarting bot + dashboard..."
    stop_all
    sleep 2
    start_all
}

status_all() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 SYSTEM STATUS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    status_bot
    echo ""
    status_dashboard
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

restart_bot() {
    echo "🔄 Restarting bot..."
    stop_bot
    sleep 2
    start_bot
}

# Main command dispatcher
case "${1:-}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        status_all
        ;;
    logs)
        view_logs
        ;;
    
    # Individual bot commands
    start-bot)
        start_bot
        ;;
    stop-bot)
        stop_bot
        ;;
    restart-bot)
        restart_bot
        ;;
    status-bot)
        status_bot
        ;;
    
    # Individual dashboard commands
    start-dashboard)
        start_dashboard
        ;;
    stop-dashboard)
        stop_dashboard
        ;;
    restart-dashboard)
        restart_dashboard
        ;;
    status-dashboard)
        status_dashboard
        ;;
    
    *)
        echo "Usage: $0 {command}"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📋 COMBINED COMMANDS (Bot + Dashboard)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  start       - Start bot + dashboard"
        echo "  stop        - Stop bot + dashboard"
        echo "  restart     - Restart bot + dashboard"
        echo "  status      - Show status of both"
        echo "  logs        - View live bot logs"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🤖 BOT COMMANDS"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  start-bot       - Start only bot"
        echo "  stop-bot        - Stop only bot"
        echo "  restart-bot     - Restart only bot"
        echo "  status-bot      - Show bot status"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📊 DASHBOARD COMMANDS"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  start-dashboard     - Start only dashboard"
        echo "  stop-dashboard      - Stop only dashboard"
        echo "  restart-dashboard   - Restart only dashboard"
        echo "  status-dashboard    - Show dashboard status"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "💡 Examples:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  ./bot.sh start              # Start everything"
        echo "  ./bot.sh status             # Check status"
        echo "  ./bot.sh restart-dashboard  # Restart only dashboard"
        echo "  ./bot.sh stop               # Stop everything"
        exit 1
        ;;
esac

