# ZilKit Architecture

## Overview

ZilKit is a Windows context menu integration tool that provides quick access to FFmpeg operations, system shortcuts, and utilities directly from the Windows Explorer right-click menu.

## System Architecture

### Windows Context Menu Integration

The Windows context menu is integrated through registry entries:

```
HKEY_CLASSES_ROOT\Directory\Background\shell\ZilKit
├── (Default) = "ZilKit"
├── MUIVerb = "ZilKit"
├── SubCommands = "ZilKit.FFmpeg;ZilKit.Shortcuts;ZilKit.Utilities"
└── Icon = "path\to\zilkit\icon.ico"
```

Each submenu item points to a Python script handler that:
1. Receives the directory path where the user right-clicked
2. Processes the selected action
3. Provides user feedback via Rich console output

### Module Structure

#### `zilkit/main.py`
- Entry point for all context menu actions
- Parses command-line arguments from Windows registry
- Routes to appropriate menu handler based on action type

#### `zilkit/config.py`
- Manages configuration settings
- Handles FFmpeg path detection
- Stores user preferences

#### `zilkit/registry.py`
- Windows registry operations
- Functions to add/remove context menu entries
- Registry key management

#### `zilkit/menu/`
Menu handlers that receive context menu actions and delegate to core operations:

- **`ffmpeg.py`**: Handles FFmpeg menu actions
  - Convert image sequence in current directory
  - Convert all image sequences recursively

- **`shortcuts.py`**: Handles system shortcut actions
  - Empty recycle bin
  - Force restart
  - Force shutdown

- **`utilities.py`**: Handles utility actions
  - (To be defined)

#### `zilkit/core/`
Core operation implementations:

- **`ffmpeg_ops.py`**: FFmpeg operation implementations
  - Image sequence detection using `pyseq`
  - FFmpeg command construction
  - Video encoding operations

- **`system_ops.py`**: System operation implementations
  - Windows API calls for system operations
  - Recycle bin management
  - System shutdown/restart

#### `zilkit/utils/`
Shared utilities:

- **`file_utils.py`**: File and directory operations
  - Path validation
  - Directory traversal
  - File pattern matching

- **`logger.py`**: Logging utilities
  - Structured logging setup
  - Log file management

## Data Flow

1. **User Action**: User right-clicks in Windows Explorer and selects a ZilKit option
2. **Registry Invocation**: Windows executes the registered Python script with arguments
3. **Main Handler**: `main.py` receives the action type and context (directory path)
4. **Menu Router**: Routes to appropriate menu handler (`menu/ffmpeg.py`, etc.)
5. **Core Operation**: Menu handler calls core operation (`core/ffmpeg_ops.py`, etc.)
6. **Execution**: Core operation performs the actual work
7. **Feedback**: Rich console output provides user feedback

## Dependencies

### External Tools
- **FFmpeg**: Must be installed and available in system PATH
  - Used for video encoding operations
  - Detected at runtime via `config.py`

### Python Packages
- **pyseq**: Image sequence detection and parsing
- **typer**: CLI argument parsing and command structure
- **rich**: Beautiful terminal output and progress bars
- **openimageio**: Image I/O operations (if needed for advanced image handling)

## Installation Flow

1. User runs `install.py`
2. Script validates Python installation
3. Script validates FFmpeg availability
4. Script creates registry entries for context menu
5. Script creates necessary directory structure
6. Script verifies installation

## Uninstallation Flow

1. User runs `uninstall.py`
2. Script removes all registry entries
3. Script optionally removes installed files
4. Script verifies removal

## Error Handling

- All operations should provide clear error messages via Rich
- Logging to file for debugging
- Graceful handling of missing dependencies (FFmpeg, etc.)
- User-friendly error messages for common issues

## Future Considerations

- Configuration file for user preferences
- Plugin system for extensibility
- Update mechanism
- Logging and analytics (optional)
- Multi-language support

