@echo off
chcp 65001 >nul
title 关闭公众号AI运营系统
echo 正在关闭系统...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1
echo 系统已关闭。
pause
