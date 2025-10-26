#!/bin/bash
# Start Autonomous Trading Bot

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 AUTONOMOUS TRADING BOT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env with your DEEPSEEK_API_KEY"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Get intervals from args or use defaults
ANALYSIS_INTERVAL=${1:-900}  # 15 minutes default
MONITOR_INTERVAL=${2:-60}    # 1 minute default

echo "⚙️  Configuration:"
echo "   Analysis interval: ${ANALYSIS_INTERVAL}s ($(($ANALYSIS_INTERVAL / 60)) min)"
echo "   Monitor interval: ${MONITOR_INTERVAL}s"
echo ""
echo "🚀 Starting bot..."
echo "   Press Ctrl+C to stop gracefully"
echo ""

cd src
python trading_bot.py --analysis-interval $ANALYSIS_INTERVAL --monitor-interval $MONITOR_INTERVAL

echo ""
echo "👋 Bot stopped."

