@echo off
title WeChat AI Publisher - Stop
echo Stopping WeChat AI Publisher...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1
echo Done.
pause