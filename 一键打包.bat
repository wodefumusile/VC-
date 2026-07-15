@echo off
title Build WeChat AI Publisher EXE
cd /d "%~dp0"

echo ========================================
echo   WeChat AI Publisher - Build EXE
echo ========================================
echo.

echo [1/3] Removing old build files...
if exist "app\dist" rmdir /s /q "app\dist"
if exist "app\build" rmdir /s /q "app\build"

echo [2/3] Building EXE...
echo.
cd /d "%~dp0app"
pyinstaller WeChat_AI_Publisher.spec --noconfirm

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Build failed! Check the output above.
    pause
    exit /b 1
)

echo.
echo [3/3] Copying EXE to project root...
copy /y "dist\WeChat_AI_Publisher.exe" "..\WeChat_AI_Publisher.exe"

echo.
echo ========================================
echo   Build complete!
echo   Output: WeChat_AI_Publisher.exe
echo ========================================
echo.
pause
