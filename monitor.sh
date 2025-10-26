#!/bin/bash
# Trade Monitor - Checks open trades and closes them if SL/TP hit

echo "🔍 Trade Monitor"
echo "================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Activating virtual environment..."
    source venv/bin/activate
fi

cd src

# Check if continuous mode requested
if [ "$1" == "--continuous" ] || [ "$1" == "-c" ]; then
    echo "Running in CONTINUOUS mode (checks every minute)"
    echo "Press Ctrl+C to stop"
    echo ""
    python monitor_trades.py --continuous
else
    echo "Running SINGLE check..."
    echo ""
    python monitor_trades.py
fi

