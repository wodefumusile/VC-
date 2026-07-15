@echo off
chcp 65001 >nul
title 公众号AI运营系统 - 一键安装
cd /d "%~dp0"

echo.
echo ============================================
echo   公众号AI智能运营系统 V2.2.1 - 安装向导
echo ============================================
echo.

echo [1/6] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] 未检测到 Python！请先安装 Python 3.12+
    echo 下载: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do echo    [OK] Python %%v 已就绪

echo [2/6] 创建 Python 虚拟环境...
if not exist "venv" (
    python -m venv venv
    echo    [OK] 虚拟环境已创建
) else (
    echo    [OK] 虚拟环境已存在
)

echo [3/6] 安装 Python 依赖包（可能需要几分钟）...
venv\Scripts\python -m pip install --upgrade pip -q 2>nul
venv\Scripts\pip install -r app\requirements.txt -q 2>nul
if %errorlevel% neq 0 (
    echo     正在使用清华镜像源重试...
    venv\Scripts\pip install -r app\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
    if %errorlevel% neq 0 (
        echo [X] 依赖安装失败，请检查网络连接后重新运行
        pause
        exit /b 1
    )
)
echo    [OK] Python 依赖安装完成

echo [4/6] 安装浏览器引擎（用于公众号发布）...
venv\Scripts\playwright install chromium 2>nul
if %errorlevel% neq 0 (
    venv\Scripts\python -m playwright install chromium
    if %errorlevel% neq 0 (
        echo [!] Chromium 安装失败（发布功能可能不可用）
    )
)
echo    [OK] 浏览器引擎就绪

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

echo [6/6] 检查 Docker（可选）...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    [!] 未安装 Docker（可选，不影响核心功能）
) else (
    echo    [OK] Docker 已就绪
)

echo.
echo ============================================
echo   安装完成！
echo ============================================
echo.
echo   [重要] 配置 API 密钥：
echo     1. 用记事本打开 app\.env 文件
echo     2. 填入 DeepSeek API Key
echo     3. 如需 AI 生图，填入火山方舟 API Key
echo     4. 保存文件
echo.
echo   [启动] 双击「一键启动.bat」
echo   [访问] http://localhost:8000
echo.
echo   详细教程请查看 docs\\客户安装教程_v2.2.2.md
echo.
pause