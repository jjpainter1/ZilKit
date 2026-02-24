@echo off
setlocal enabledelayedexpansion
title ZilKit Installer

:: Always run from the folder where this script lives
cd /d "%~dp0"

:: Verify we're in the ZilKit project folder
if not exist "requirements.txt" (
    echo ERROR: Please run this from the ZilKit folder.
    echo This script should be next to requirements.txt
    pause
    exit /b 1
)
if not exist "src\scripts\install.py" (
    echo ERROR: ZilKit files not found. Make sure you have the complete project.
    pause
    exit /b 1
)

:: ============================================================
:: Request Administrator privileges (needed for context menu)
:: ============================================================
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ZilKit needs Administrator rights to add itself to the context menu.
    echo A new window will open - please approve the prompt.
    echo.
    :: Use cmd /k to keep the elevated window open (otherwise it closes immediately)
    :: Write a small helper script to avoid batch/PowerShell quoting nightmares
    set "INSTALL_DIR=%~dp0"
    set "INSTALL_DIR=!INSTALL_DIR:~0,-1!"
    (
        echo $dir = '!INSTALL_DIR!'
        echo $bat = Join-Path $dir 'install.bat'
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
echo    ZilKit Installer
echo  ============================================
echo.
echo  This will install ZilKit and add it to your right-click context menu.
echo  We'll check for required tools and install them if needed.
echo.

:: ============================================================
:: Step 1: Verify WinGet is installed and up to date
:: ============================================================
echo  [Step 1/5] Checking WinGet...
echo.

winget --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  X WinGet is not installed.
    echo.
    echo  WinGet is Microsoft's package manager for Windows.
    echo  Install it from: https://aka.ms/getwinget
    echo.
    echo  Or install "App Installer" from the Microsoft Store.
    echo.
    goto :pause_exit
)

echo  + WinGet is installed.
echo.

:: Update WinGet package sources (ensures we get latest versions)
echo  Updating package list...
winget source update >nul 2>&1
echo  + Package list updated.
echo.

:: ============================================================
:: Step 2: Check Python
:: ============================================================
echo  [Step 2/5] Checking Python...
echo.

set "PYTHON_CMD="
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
)
if "!PYTHON_CMD!"=="" (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=py"
    )
)

if "!PYTHON_CMD!"=="" (
    echo  X Python is not installed.
    echo.
    echo  Installing Python 3.12 via WinGet...
    echo.
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo.
        echo  X Installation failed. You may need to install Python manually from python.org
        goto :pause_exit
    )
    echo.
    echo  ============================================
    echo    IMPORTANT - Please read this
    echo  ============================================
    echo.
    echo  Python was just installed. Windows needs to refresh its settings
    echo  before we can continue.
    echo.
    echo  Please:
    echo    1. CLOSE this window completely
    echo    2. Double-click install.bat again to continue
    echo.
    goto :pause_exit
)

echo  + Python is installed.
echo.

:: ============================================================
:: Step 3: Check FFmpeg
:: ============================================================
echo  [Step 3/5] Checking FFmpeg...
echo.

ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo  X FFmpeg is not installed.
    echo.
    echo  Installing FFmpeg via WinGet...
    echo.
    winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo.
        echo  X Installation failed. You may need to install FFmpeg manually from ffmpeg.org
        goto :pause_exit
    )
    echo.
    echo  ============================================
    echo    IMPORTANT - Please read this
    echo  ============================================
    echo.
    echo  FFmpeg was just installed. Windows needs to refresh its settings
    echo  before we can continue.
    echo.
    echo  Please:
    echo    1. CLOSE this window completely
    echo    2. Double-click install.bat again to continue
    echo.
    goto :pause_exit
)

echo  + FFmpeg is installed.
echo.

:: ============================================================
:: Step 4: Install Python dependencies
:: ============================================================
echo  [Step 4/5] Installing ZilKit dependencies...
echo.

!PYTHON_CMD! -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo  X Failed to install dependencies.
    echo.
    echo  Try running: !PYTHON_CMD! -m pip install -r requirements.txt
    goto :pause_exit
)

echo  + Dependencies installed.
echo.

:: ============================================================
:: Step 5: Register ZilKit in context menu
:: ============================================================
echo  [Step 5/5] Adding ZilKit to your right-click menu...
echo.

!PYTHON_CMD! src\scripts\install.py
if %errorlevel% neq 0 (
    echo.
    echo  X Failed to register context menu.
    goto :pause_exit
)

:: ============================================================
:: Success
:: ============================================================
echo.
echo  ============================================
echo    Installation complete!
echo  ============================================
echo.
echo  ZilKit is now installed. You can:
echo.
echo    - Right-click in any folder
echo    - Select "ZilKit" from the menu
echo    - Choose FFmpeg, Shortcuts, or Utilities
echo.
echo  Note: You may need to restart Windows Explorer for the
echo  menu to appear. In Task Manager, find "Windows Explorer",
echo  right-click it, and select "Restart".
echo.
goto :pause_exit

:pause_exit
echo.
pause
exit /b
