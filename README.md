# ZilKit

A Windows 10/11 context menu tool for FFmpeg operations, system shortcuts, and utilities.

## Overview

ZilKit integrates into the Windows right-click context menu, providing quick access to:
- **FFmpeg**: Image sequence to video conversion tools
- **Shortcuts**: System operations (empty recycle bin, restart, shutdown)
- **Utilities**: Additional helper tools

## Project Structure

```
ZilKit/
├── src/
│   ├── zilkit/
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point for context menu handlers
│   │   ├── config.py            # Configuration management
│   │   ├── registry.py          # Windows registry operations for context menu
│   │   ├── menu/
│   │   │   ├── __init__.py
│   │   │   ├── ffmpeg.py        # FFmpeg menu handlers
│   │   │   ├── shortcuts.py     # Shortcuts menu handlers
│   │   │   └── utilities.py     # Utilities menu handlers
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── ffmpeg_ops.py    # FFmpeg operation implementations
│   │   │   └── system_ops.py    # System operation implementations
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_utils.py    # File/directory utilities
│   │       └── logger.py        # Logging utilities
│   └── scripts/
│       ├── install.py           # Installation script (registers context menu)
│       └── uninstall.py         # Uninstallation script (removes registry entries)
├── tests/
│   ├── __init__.py
│   ├── test_ffmpeg_ops.py
│   ├── test_system_ops.py
│   └── test_file_utils.py
├── docs/
│   ├── installation.md
│   ├── development.md
│   └── architecture.md
├── .gitignore
├── LICENSE
├── requirements.txt
├── pyproject.toml              # Modern Python project configuration
├── setup.py                    # Package setup (optional, for pip install)
└── README.md
```

## Features

### FFmpeg Menu
- Convert image sequence to video in current directory
- Convert all image sequences in all subdirectories

### Shortcuts Menu
- Empty Recycle Bin
- Force Computer to Restart
- Force Computer to Shutdown

### Utilities Menu
- (To be defined)

## Requirements

- Python 3.8+
- FFmpeg (must be installed and available in PATH)
- Windows 10/11

## Installation

**Easiest:** Double-click `install.bat` in the ZilKit folder. It will check for Python and FFmpeg, install them via WinGet if needed, and add ZilKit to your context menu. See [INSTALL_GUIDE.md](INSTALL_GUIDE.md) for details.

**Manual:**
1. Clone the repository
2. Install Python dependencies: `pip install -r requirements.txt`
3. Install FFmpeg and ensure it's in your system PATH
4. Run the installation script (as Administrator): `python src/scripts/install.py`

## Uninstallation

Run: `python src/scripts/uninstall.py`

## Development

### Dependencies

- `pyseq`: Image sequence detection and parsing
- `typer`: CLI framework for command-line interface
- `rich`: Rich text and beautiful formatting in terminal
- `openimageio`: Image I/O operations

### Architecture

The project follows a modular structure:
- **Menu handlers** (`menu/`): Handle context menu actions and route to core operations
- **Core operations** (`core/`): Implement the actual functionality
- **Utilities** (`utils/`): Shared helper functions
- **Registry** (`registry.py`): Windows registry integration for context menu

### Windows Context Menu Integration

ZilKit integrates with Windows by:
1. Adding registry entries under `HKEY_CLASSES_ROOT\Directory\Background\shell\ZilKit`
2. Creating submenu entries for FFmpeg, Shortcuts, and Utilities
3. Each menu item points to a Python script handler that processes the action

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

