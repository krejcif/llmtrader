#!/bin/bash

# Run script for Multi-Agent Trading System

echo "🚀 Starting Multi-Agent Trading System..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your DeepSeek API key"
    echo ""
    echo "  cp .env.example .env"
    echo "  # Then edit .env and add your DEEPSEEK_API_KEY"
    echo ""
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "Consider activating it first:"
    echo "  source venv/bin/activate"
    echo ""
fi

# Change to src directory and run
cd src
python main.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ Analysis completed successfully!"
else
    echo ""
    echo "❌ Analysis failed with exit code: $exit_code"
fi

exit $exit_code

