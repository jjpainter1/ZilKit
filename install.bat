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

:: Track if we install anything that requires a PATH refresh (restart needed)
set "NEED_RESTART=0"

:: ============================================================
:: Step 1: Verify WinGet is installed and up to date
:: ============================================================
echo  [Step 1/6] Checking WinGet...
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
set "UPDATE_WINGET="
set /p "UPDATE_WINGET=  Update WinGet package list? (y/n, default y): "
if /i "!UPDATE_WINGET!"=="" set "UPDATE_WINGET=y"
if /i "!UPDATE_WINGET!"=="y" (
    echo  Updating package list...
    winget source update >nul 2>&1
    echo  + Package list updated.
) else (
    echo  Skipping WinGet update.
)
echo.

:: ============================================================
:: Step 2: Check Python
:: ============================================================
echo  [Step 2/6] Checking Python...
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
    set "INSTALL_PYTHON="
    set /p "INSTALL_PYTHON=  Install Python 3.14 via WinGet? (y/n, default y): "
    if /i "!INSTALL_PYTHON!"=="" set "INSTALL_PYTHON=y"
    if /i "!INSTALL_PYTHON!" neq "y" (
        echo.
        echo  Python is required. Install manually from python.org and run this installer again.
        goto :pause_exit
    )
    echo.
    echo  Installing Python 3.14 via WinGet...
    echo.
    winget install -e --id Python.Python.3.14 --scope machine --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo.
        echo  X Installation failed. You may need to install Python manually from python.org
        goto :pause_exit
    )
    set "NEED_RESTART=1"
)

if "!PYTHON_CMD!" neq "" (
    echo  + Python is installed.
) else (
    echo  + Python installed.
)
echo.

:: ============================================================
:: Step 3: Check FFmpeg
:: ============================================================
echo  [Step 3/6] Checking FFmpeg...
echo.

ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo  X FFmpeg is not installed.
    echo.
    set "INSTALL_FFMPEG="
    set /p "INSTALL_FFMPEG=  Install FFmpeg (full build) via WinGet? (y/n, default y): "
    if /i "!INSTALL_FFMPEG!"=="" set "INSTALL_FFMPEG=y"
    if /i "!INSTALL_FFMPEG!" neq "y" (
        echo.
        echo  FFmpeg is required. Install manually from ffmpeg.org and run this installer again.
        goto :pause_exit
    )
    echo.
    echo  Installing FFmpeg via WinGet...
    echo.
    winget install -e --id Gyan.FFmpeg --scope machine --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo.
        echo  X Installation failed. You may need to install FFmpeg manually from ffmpeg.org
        goto :pause_exit
    )
    set "NEED_RESTART=1"
    echo  + FFmpeg installed.
) else (
    echo  + FFmpeg is installed.
)
echo.

if "!NEED_RESTART!"=="1" (
    echo.
    echo  ============================================
    echo    IMPORTANT - Please read this
    echo  ============================================
    echo.
    echo  Python and/or FFmpeg were just installed. Windows needs to refresh
    echo  its settings before we can continue with the rest of the setup.
    echo.
    echo  Please:
    echo    1. CLOSE this window completely
    echo    2. Run install.bat as Administrator again to finish
    echo.
    goto :pause_exit
)

:: ============================================================
:: Step 4: Install Python dependencies
:: ============================================================
echo  [Step 4/6] Installing ZilKit dependencies...
echo.
echo  ZilKit requires the following Python packages:
echo    - pyseq, typer, rich, openimageio, pywin32
echo.
set "INSTALL_DEPS="
set /p "INSTALL_DEPS=  Install all pip dependencies now? (y/n, default y): "
if /i "!INSTALL_DEPS!"=="" set "INSTALL_DEPS=y"
if /i "!INSTALL_DEPS!" neq "y" (
    echo.
    echo  Dependencies are required. Run install.bat again when ready.
    goto :pause_exit
)
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
:: Step 5: Windows 11 classic context menu (do BEFORE registering ZilKit)
:: ============================================================
echo  [Step 5/6] Checking Windows 11 context menu...
echo.
set "WIN_BUILD=0"
for /f "tokens=3" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentBuild 2^>nul ^| findstr CurrentBuild') do set "WIN_BUILD=%%a"
if !WIN_BUILD! GEQ 22000 (
    :: Windows 11 - check if classic context menu is enabled
    reg query "HKCU\SOFTWARE\CLASSES\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" >nul 2>&1
    if !errorlevel! neq 0 (
        echo  [Windows 11] ZilKit requires the classic right-click context menu.
        echo  Windows 11's new menu hides third-party entries like ZilKit.
        echo.
        set "SWITCH_MENU="
        set /p "SWITCH_MENU=  Switch to classic context menu now? (y/n, default y): "
        if /i "!SWITCH_MENU!"=="" set "SWITCH_MENU=y"
        if /i "!SWITCH_MENU!"=="y" (
            echo.
            echo  Applying classic context menu...
            reg add "HKCU\SOFTWARE\CLASSES\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /ve /f >nul 2>&1
            reg add "HKCU\Software\Classes\CLSID\{d93ed569-3b3e-4bff-8355-3c44f6a52bb5}\InprocServer32" /f /ve >nul 2>&1
            echo  Restarting Windows Explorer...
            taskkill /f /im explorer.exe >nul 2>&1
            start explorer.exe
            echo  + Classic context menu enabled.
        ) else (
            echo.
            echo  You can switch later by running these commands as Administrator:
            echo    reg add "HKCU\SOFTWARE\CLASSES\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /ve /f
            echo    reg add "HKCU\Software\Classes\CLSID\{d93ed569-3b3e-4bff-8355-3c44f6a52bb5}\InprocServer32" /f /ve
            echo    taskkill /f /im explorer.exe ^& start explorer.exe
        )
    ) else (
        echo  + Classic context menu already enabled.
    )
) else (
    echo  + Windows 10 - no context menu change needed.
)
echo.

:: ============================================================
:: Step 6: Register ZilKit in context menu
:: ============================================================
echo  [Step 6/6] Adding ZilKit to your right-click menu...
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
echo  Note: If you don't see ZilKit, restart Windows Explorer
echo  (Task Manager -^> find "Windows Explorer" -^> Right-click -^> Restart).
echo.
goto :pause_exit

:pause_exit
echo.
pause
exit /b
