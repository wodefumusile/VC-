@echo off
title WeChat AI Publisher - Install
cd /d "%~dp0"

echo ============================================
echo   WeChat AI Publisher V2.2.4 - Install
echo ============================================
echo.

echo [1/6] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Python not found! Install Python 3.10+ first.
    echo        Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do echo    [OK] Python %%v

echo [2/6] Checking Python version (>=3.10)...
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo    [FAIL] Python 3.10+ required! Please upgrade.
    pause
    exit /b 1
)
echo    [OK] Version OK

echo [3/6] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo    [OK] Created
) else (
    echo    [OK] Already exists
)

echo [4/6] Installing Python packages...
venv\Scripts\python -m pip install --upgrade pip -q 2>nul
venv\Scripts\pip install -r app\requirements.txt -q 2>nul
if %errorlevel% neq 0 (
    echo    Retrying with mirror...
    venv\Scripts\pip install -r app\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
    if %errorlevel% neq 0 (
        echo    [FAIL] Cannot install packages. Check network.
        pause
        exit /b 1
    )
)
echo    [OK] Packages installed

echo [5/6] Installing browser engine...
venv\Scripts\playwright install chromium 2>nul
if %errorlevel% neq 0 (
    venv\Scripts\python -m playwright install chromium
    if %errorlevel% neq 0 echo    [!] Browser install failed (publish may not work)
)
echo    [OK] Browser ready

echo [6/6] Initializing config...
if not exist "app\.env" (
    copy "app\.env.example" "app\.env" >nul
    echo    [OK] Created app\.env (fill in API keys)
) else (
    echo    [OK] app\.env exists
)
if not exist "app\logs" mkdir app\logs >nul 2>&1
if not exist "logs" mkdir logs >nul 2>&1
echo    [OK] Directories ready

echo.
echo ============================================
echo   INSTALL COMPLETE!
echo ============================================
echo.
echo   1. Edit app\.env and enter your API keys
echo   2. Double-click start.bat to launch
echo   3. Open http://localhost:8000
echo.
echo   Guides: install-guide.docx / user-manual.docx
echo.
pause