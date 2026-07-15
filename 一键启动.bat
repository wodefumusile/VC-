@echo off
title WeChat AI Publisher
cd /d "%~dp0"

echo Starting WeChat AI Publisher...
echo.

start "WeChat AI Publisher" /d "%~dp0app" cmd /c "python -m backend.main"

timeout /t 5 >nul

echo.
echo ========================================
echo   System started!
echo ========================================
echo.
echo   Dashboard will open in Chrome window
echo.
echo   Run Stop.bat to shut down
echo.
pause
