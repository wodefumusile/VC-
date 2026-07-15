@echo off
chcp 65001 >nul
title 公众号AI运营系统
cd /d "%~dp0"

echo 正在启动公众号AI运营系统...
echo.

REM Activate virtual environment
if not exist "venv\Scripts\python.exe" (
    echo [X] 未安装！请先运行 一键安装.bat
    pause
    exit /b 1
)

cd app
start "公众号AI运营" cmd /c "..\venv\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
cd ..

timeout /t 5 >nul

echo.
echo ============================================
echo   系统已启动！
echo ============================================
echo.
echo   工作台: http://localhost:8000
echo   关闭请运行「一键停止.bat」
echo.
start http://localhost:8000
pause