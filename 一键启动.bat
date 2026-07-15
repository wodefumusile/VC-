@echo off
chcp 65001 >nul
title 公众号AI运营系统
cd /d "%~dp0"

echo 正在启动公众号AI运营系统...
echo.

cd app
start "公众号AI运营" cmd /c "python -m backend.main"
cd ..

timeout /t 5 >nul

echo.
echo ========================================
echo   系统已启动！
echo ========================================
echo.
echo   工作台: http://localhost:8000
echo.
echo   关闭请运行「一键停止.bat」
echo.
start http://localhost:8000
pause
