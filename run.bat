@echo off
REM Run script for Multi-Agent Trading System (Windows)

echo 🚀 Starting Multi-Agent Trading System...
echo.

REM Check if .env exists
if not exist .env (
    echo ❌ Error: .env file not found!
    echo Please copy .env.example to .env and configure your DeepSeek API key
    echo.
    echo   copy .env.example .env
    echo   REM Then edit .env and add your DEEPSEEK_API_KEY
    echo.
    exit /b 1
)

REM Change to src directory and run
cd src
python main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Analysis completed successfully!
) else (
    echo.
    echo ❌ Analysis failed with exit code: %ERRORLEVEL%
)

exit /b %ERRORLEVEL%

