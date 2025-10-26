#!/bin/bash
# Start Trading Dashboard Web UI

echo "🌐 Starting Trading Dashboard..."
echo ""

cd "$(dirname "$0")"

# Check if venv exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start web server
cd src
python web_api.py

