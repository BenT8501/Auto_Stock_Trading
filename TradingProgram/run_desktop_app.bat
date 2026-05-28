@echo off
setlocal
cd /d "%~dp0"

echo [TradingProgram] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not available. Install Python and add it to PATH.
    pause
    exit /b 1
)

echo [TradingProgram] Installing/updating required packages...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements.
    pause
    exit /b 1
)

echo [TradingProgram] Starting desktop app...
python desktop_app.py
pause
