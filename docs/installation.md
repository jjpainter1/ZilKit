# ZilKit Installation Guide

## Prerequisites

### 1. Python 3.8 or Higher
- Download from [python.org](https://www.python.org/downloads/)
- Ensure Python is added to your system PATH during installation
- Verify installation: `python --version`

### 2. FFmpeg
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Or use a package manager like Chocolatey: `choco install ffmpeg`
- Ensure FFmpeg is in your system PATH
- Verify installation: `ffmpeg -version`

## Installation Steps

### 1. Clone or Download ZilKit
```bash
git clone https://github.com/yourusername/ZilKit.git
cd ZilKit
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Or install in development mode:
```bash
pip install -e ".[dev]"
```

### 3. Install ZilKit to Context Menu
```bash
python src/scripts/install.py
```

This script will:
- Verify Python and FFmpeg are available
- Create necessary registry entries
- Register ZilKit in the Windows context menu
- Set up the menu structure (FFmpeg, Shortcuts, Utilities)

### 4. Verify Installation
- Right-click in any Windows Explorer window
- You should see "ZilKit" in the context menu
- Hovering over it should show submenus: FFmpeg, Shortcuts, Utilities

## Uninstallation

To remove ZilKit from your system:

```bash
python src/scripts/uninstall.py
```

This will:
- Remove all registry entries
- Clean up context menu integration
- Optionally remove installed files

## Troubleshooting

### ZilKit doesn't appear in context menu
- Ensure you ran `install.py` with administrator privileges
- Check that registry entries were created successfully
- Try restarting Windows Explorer or your computer

### FFmpeg not found
- Verify FFmpeg is installed: `ffmpeg -version`
- Ensure FFmpeg is in your system PATH
- You may need to restart your terminal/command prompt after adding to PATH

### Python not found
- Verify Python is installed: `python --version`
- Ensure Python is in your system PATH
- Try using `py` instead of `python` on Windows

## Manual Installation (Advanced)

If the automated installation script doesn't work, you can manually create registry entries. See `docs/development.md` for registry key details.

