#!/bin/bash
# Bot Management Script - Start/Stop/Status autonomous trading bot

BOT_DIR="/home/flow/langtest"
PID_FILE="$BOT_DIR/bot.pid"
LOG_FILE="$BOT_DIR/logs/bot_background.log"
VENV_DIR="$BOT_DIR/venv"

cd "$BOT_DIR"

start_bot() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  Bot is already running (PID: $PID)"
            echo "   Use: ./bot.sh status"
            return 1
        else
            echo "🧹 Removing stale PID file..."
            rm -f "$PID_FILE"
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
    nohup python3 src/trading_bot_dynamic.py > "$LOG_FILE" 2>&1 &
    BOT_PID=$!
    
    # Save PID
    echo $BOT_PID > "$PID_FILE"
    
    echo "✅ Dynamic bot started successfully!"
    echo "   Mode: Multi-strategy (flexible intervals & timeframes)"
    echo "   PID: $BOT_PID"
    echo "   Background log: $LOG_FILE"
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
        echo "❌ Bot failed to start! Check: tail $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_bot() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️  Bot is not running (no PID file)"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  Bot is not running (stale PID file)"
        rm -f "$PID_FILE"
        return 1
    fi
    
    echo "🛑 Stopping bot (PID: $PID)..."
    
    # Send SIGTERM for graceful shutdown
    kill -TERM $PID
    
    # Wait for graceful shutdown (max 10 seconds)
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            echo "✅ Bot stopped gracefully"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo "⚠️  Forcing bot shutdown..."
    kill -9 $PID 2>/dev/null
    rm -f "$PID_FILE"
    echo "✅ Bot stopped (forced)"
}

status_bot() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⏸️  Bot is NOT running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
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
        rm -f "$PID_FILE"
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

restart_bot() {
    echo "🔄 Restarting bot..."
    stop_bot
    sleep 2
    start_bot
}

# Main command dispatcher
case "${1:-}" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        status_bot
        ;;
    logs)
        view_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start bot in background"
        echo "  stop     - Stop bot gracefully"
        echo "  restart  - Restart bot"
        echo "  status   - Show bot status and stats"
        echo "  logs     - View live logs"
        echo ""
        echo "Examples:"
        echo "  ./bot.sh start     # Start bot"
        echo "  ./bot.sh status    # Check if running"
        echo "  ./bot.sh logs      # Watch what's happening"
        echo "  ./bot.sh stop      # Stop bot"
        exit 1
        ;;
esac

