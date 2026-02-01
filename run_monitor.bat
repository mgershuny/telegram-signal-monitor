@echo off
echo ========================================
echo 100xclub Channel Monitor
echo ========================================
echo.

cd /d "C:\Users\musag\.openclaw\skills\crypto-trading-assistant\telethon"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

REM Check for required packages
python -c "import telethon" >nul 2>&1
if errorlevel 1 (
    echo Installing Telethon...
    pip install telethon aiohttp
)

echo Starting channel monitor...
echo Press Ctrl+C to stop
echo.

python channel_monitor.py

pause
