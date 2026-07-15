@echo off
title WeChat AI Publisher
cd /d "%~dp0"

echo Starting WeChat AI Publisher...
echo.

if not exist "venv\Scripts\python.exe" (
    echo [FAIL] Not installed! Run install.bat first.
    pause
    exit /b 1
)

start "WeChat AI Publisher" /d "%~dp0app" cmd /c "..\venv\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

timeout /t 5 >nul

echo.
echo ============================================
echo   Server started!
echo ============================================
echo.
echo   Open: http://localhost:8000
echo   Stop: run stop.bat
echo.
start http://localhost:8000
pause