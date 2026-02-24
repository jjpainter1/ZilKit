@echo off
setlocal enabledelayedexpansion
title ZilKit Uninstaller

:: Always run from the folder where this script lives
cd /d "%~dp0"

:: Verify we're in the ZilKit project folder
if not exist "src\scripts\uninstall.py" (
    echo ERROR: Please run this from the ZilKit folder.
    echo This script should be next to requirements.txt
    pause
    exit /b 1
)

:: ============================================================
:: Request Administrator privileges (needed for registry removal)
:: ============================================================
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ZilKit uninstall needs Administrator rights to remove the context menu.
    echo A new window will open - please approve the prompt.
    echo.
    set "INSTALL_DIR=%~dp0"
    set "INSTALL_DIR=!INSTALL_DIR:~0,-1!"
    (
        echo $dir = '!INSTALL_DIR!'
        echo $bat = Join-Path $dir 'uninstall.bat'
        echo Start-Process cmd -ArgumentList '/k', "cd /d ^`"$dir^`" ^^&^^& ^`"$bat^`"" -Verb RunAs -WorkingDirectory $dir
    ) > "%TEMP%\zilkit-elevate.ps1"
    powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\zilkit-elevate.ps1"
    del "%TEMP%\zilkit-elevate.ps1" 2>nul
    exit /b
)

:: ============================================================
:: Welcome
:: ============================================================
echo.
echo  ============================================
echo    ZilKit Uninstaller
echo  ============================================
echo.
echo  This will remove ZilKit from your right-click context menu.
echo  Python, FFmpeg, and pip packages will NOT be uninstalled.
echo.

:: ============================================================
:: Find Python
:: ============================================================
set "PYTHON_CMD="
python --version >nul 2>&1
if %errorlevel% equ 0 set "PYTHON_CMD=python"
if "!PYTHON_CMD!"=="" (
    py --version >nul 2>&1
    if %errorlevel% equ 0 set "PYTHON_CMD=py"
)

if "!PYTHON_CMD!"=="" (
    echo  X Python not found. ZilKit uninstall requires Python.
    echo.
    echo  If you already removed Python, you can manually delete the
    echo  registry keys. See INSTALL_GUIDE.md for details.
    goto :pause_exit
)

:: ============================================================
:: Run uninstall
:: ============================================================
echo  Removing ZilKit from context menu...
echo.

!PYTHON_CMD! src\scripts\uninstall.py
if %errorlevel% neq 0 (
    echo.
    echo  X Uninstall failed.
    goto :pause_exit
)

echo.
echo  ============================================
echo    Uninstall complete!
echo  ============================================
echo.
echo  ZilKit has been removed from your right-click menu.
echo.
echo  You can safely delete the ZilKit folder if you no longer need it.
echo  Python, FFmpeg, and pip packages were left installed.
echo.
goto :pause_exit

:pause_exit
echo.
pause
exit /b
