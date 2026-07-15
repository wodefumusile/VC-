@echo off
chcp 65001 >nul
title 公众号AI运营系统 - 一键安装
cd /d "%~dp0"

echo.
echo ============================================
echo   公众号AI智能运营系统 V2.2 - 安装向导
echo ============================================
echo.

REM ==== Step 1: Check Python ====
echo [1/6] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [X] 未检测到 Python！
    echo.
    echo 请先安装 Python 3.12：
    echo   1. 打开 https://www.python.org/downloads/
    echo   2. 下载 Python 3.12.x
    echo   3. 安装时务必勾选 "Add Python to PATH"
    echo   4. 安装完成后重新运行本脚本
    echo.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do echo    [OK] Python %%v 已就绪

REM ==== Step 2: Check pip ====
echo [2/6] 检查 pip 包管理器...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] pip 不可用，请重新安装 Python
    pause
    exit /b 1
)
echo    [OK] pip 可用

REM ==== Step 3: Install Python dependencies ====
echo [3/6] 安装 Python 依赖包（可能需要几分钟）...
echo     （如遇到网络问题，自动切换国内镜像源）
pip install -r app\requirements.txt -q 2>nul
if %errorlevel% neq 0 (
    echo     正在使用清华镜像源重试...
    pip install -r app\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
    if %errorlevel% neq 0 (
        echo [X] 依赖安装失败，请检查网络连接后重新运行
        pause
        exit /b 1
    )
)
echo    [OK] Python 依赖安装完成

REM ==== Step 4: Install Playwright browser ====
echo [4/6] 安装浏览器引擎（用于公众号发布）...
playwright install chromium 2>nul
if %errorlevel% neq 0 (
    echo     首次安装可能较慢，正在重试...
    python -m playwright install chromium
    if %errorlevel% neq 0 (
        echo [!] Chromium 安装失败（发布功能可能不可用）
        echo     可稍后手动运行: playwright install chromium
    )
)
echo    [OK] 浏览器引擎就绪

REM ==== Step 5: Initialize config ====
echo [5/6] 初始化配置文件...
if not exist "app\.env" (
    copy "app\.env.example" "app\.env" >nul
    echo    [OK] .env 配置文件已创建（请稍后填入 API Key）
) else (
    echo    [OK] .env 配置文件已存在（跳过）
)
if not exist "logs" mkdir logs >nul 2>&1
if not exist "data" mkdir data >nul 2>&1
if not exist "backup" mkdir backup >nul 2>&1
if not exist "app\logs" mkdir app\logs >nul 2>&1
echo    [OK] 目录结构就绪

REM ==== Step 6: Check Docker (optional) ====
echo [6/6] 检查 Docker（可选）...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    [!] 未安装 Docker（自动化工作流引擎不可用）
    echo        如需 n8n 工作流编排，请安装 Docker Desktop
    echo        下载: https://www.docker.com/products/docker-desktop/
) else (
    echo    [OK] Docker 已就绪
)

echo.
echo ============================================
echo   安装完成！请按以下步骤继续：
echo ============================================
echo.
echo   [重要] 配置 API 密钥：
echo     1. 用记事本打开 app\.env 文件
echo     2. 填入 DeepSeek API Key（AI 写文章用）
echo     3. 如需 AI 生图，填入火山方舟 API Key
echo     4. 保存文件
echo.
echo   [启动] 双击「一键启动.bat」即可运行
echo   [访问] 浏览器打开 http://localhost:8000
echo   [关闭] 双击「一键停止.bat」停止系统
echo.
echo   详细教程请查看 docs\客户安装教程_v2.2.md
echo.
pause
