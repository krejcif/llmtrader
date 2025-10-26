@echo off
REM Trade Monitor - Windows version

echo 🔍 Trade Monitor
echo ================
echo.

REM Check if .env exists
if not exist .env (
    echo ❌ Error: .env file not found!
    exit /b 1
)

cd src

REM Check if continuous mode
if "%1"=="--continuous" (
    echo Running in CONTINUOUS mode
    echo Press Ctrl+C to stop
    echo.
    python monitor_trades.py --continuous
) else if "%1"=="-c" (
    echo Running in CONTINUOUS mode
    echo Press Ctrl+C to stop
    echo.
    python monitor_trades.py --continuous
) else (
    echo Running SINGLE check...
    echo.
    python monitor_trades.py
)

