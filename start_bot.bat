@echo off
REM Start Autonomous Trading Bot (Windows)

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 🤖 AUTONOMOUS TRADING BOT
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Check if .env exists
if not exist .env (
    echo ❌ Error: .env file not found!
    echo Please create .env with your DEEPSEEK_API_KEY
    exit /b 1
)

REM Default intervals
set ANALYSIS_INTERVAL=900
set MONITOR_INTERVAL=60

if not "%1"=="" set ANALYSIS_INTERVAL=%1
if not "%2"=="" set MONITOR_INTERVAL=%2

set /a ANALYSIS_MIN=%ANALYSIS_INTERVAL% / 60

echo ⚙️  Configuration:
echo    Analysis interval: %ANALYSIS_INTERVAL%s (%ANALYSIS_MIN% min)
echo    Monitor interval: %MONITOR_INTERVAL%s
echo.
echo 🚀 Starting bot...
echo    Press Ctrl+C to stop gracefully
echo.

cd src
python trading_bot.py --analysis-interval %ANALYSIS_INTERVAL% --monitor-interval %MONITOR_INTERVAL%

echo.
echo 👋 Bot stopped.

