# ZilKit Project Plan

## Overview
ZilKit is a Windows 10/11 context menu integration tool that provides quick access to FFmpeg operations, system shortcuts, and utilities directly from the Windows Explorer right-click menu.

## Project Structure

### Directory Organization
```
ZilKit/
├── src/                    # Source code
│   ├── zilkit/            # Main package
│   │   ├── menu/          # Menu handlers (routing layer)
│   │   ├── core/          # Core operations (business logic)
│   │   └── utils/         # Shared utilities
│   └── scripts/           # Installation/uninstallation scripts
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
└── [config files]         # Project configuration
```

### Module Responsibilities

#### Menu Layer (`src/zilkit/menu/`)
- **Purpose**: Handle context menu actions, route to core operations
- **Files**:
  - `ffmpeg.py`: FFmpeg menu actions
  - `shortcuts.py`: System shortcuts menu actions
  - `utilities.py`: Utilities menu actions
- **Responsibilities**:
  - Parse action parameters
  - Validate inputs
  - Call core operations
  - Provide user feedback via Rich

#### Core Layer (`src/zilkit/core/`)
- **Purpose**: Implement actual functionality
- **Files**:
  - `ffmpeg_ops.py`: FFmpeg operations
    - Image sequence detection (using pyseq)
    - FFmpeg command construction
    - Video encoding (ProRes, HAP, H.264 presets)
  - *Note*: System operations (recycle bin, restart, shutdown) are implemented inline in `menu/shortcuts.py` using pywin32
- **Responsibilities**:
  - Business logic implementation
  - External tool integration (FFmpeg)
  - System API calls

#### Utilities Layer (`src/zilkit/utils/`)
- **Purpose**: Shared helper functions
- **Files**:
  - `file_utils.py`: File/directory operations
  - `logger.py`: Logging setup
- **Responsibilities**:
  - Reusable utility functions
  - Cross-cutting concerns

#### Configuration (`src/zilkit/config.py`)
- **Purpose**: Configuration management
- **Responsibilities**:
  - FFmpeg path detection
  - User preferences
  - Settings persistence

#### Registry (`src/zilkit/registry.py`)
- **Purpose**: Windows registry operations
- **Responsibilities**:
  - Add/remove context menu entries
  - Registry key management
  - Installation/uninstallation support

#### Main Entry Point (`src/zilkit/main.py`)
- **Purpose**: Entry point for all context menu actions
- **Responsibilities**:
  - Parse command-line arguments (using Typer)
  - Route to appropriate menu handler
  - Initialize Rich console
  - Error handling

## Implementation Phases

### Phase 1: Foundation
- [x] Project structure setup
- [x] Documentation (README, architecture, installation)
- [x] Dependency management (requirements.txt, pyproject.toml)
- [x] Basic module stubs
- [x] Configuration management
- [x] Logging setup

### Phase 2: Registry Integration
- [x] Registry operations module
- [x] Installation script
- [x] Uninstallation script
- [x] Context menu registration
- [ ] Testing registry operations

### Phase 3: Core Operations
- [x] FFmpeg operations
  - [x] Image sequence detection (pyseq)
  - [x] Convert single sequence
  - [x] Convert all sequences recursively
- [x] System operations
  - [x] Empty recycle bin
  - [x] Force restart
  - [x] Force shutdown

### Phase 4: Menu Handlers
- [x] FFmpeg menu handler
- [x] Shortcuts menu handler
- [x] Utilities menu handler
- [x] Main router

### Phase 5: User Experience
- [x] Rich console output
- [x] Progress indicators
- [x] Error messages
- [x] Success feedback

### Phase 6: Testing & Polish
- [x] Unit tests (config, file_utils, logger)
- [ ] Integration tests
- [ ] End-to-end testing
- [ ] Documentation updates
- [x] Error handling improvements

## Technical Decisions

### Windows Context Menu Integration
- **Method**: Windows Registry entries
- **Location**: `HKEY_CLASSES_ROOT\Directory\Background\shell\ZilKit`
- **Submenus**: Using CommandStore for submenu items
- **Icon**: Optional icon file for visual identification

### Command-Line Interface
- **Framework**: Typer (modern, type-safe CLI framework)
- **Arguments**: Action type, subaction, directory path
- **Example**: `python main.py --action ffmpeg --subaction convert-current --path "C:\directory"`

### User Feedback
- **Framework**: Rich (beautiful terminal output)
- **Features**: Progress bars, colored output, formatted messages
- **Logging**: File-based logging for debugging

### Image Sequence Detection
- **Library**: pyseq (detects image sequences like frame_001.png, frame_002.png)
- **Integration**: Use pyseq to identify sequences before FFmpeg conversion

### FFmpeg Integration
- **Detection**: Check system PATH for FFmpeg
- **Validation**: Verify FFmpeg availability at startup
- **Commands**: Construct FFmpeg commands programmatically
- **Error Handling**: Capture and display FFmpeg errors

## Dependencies

### Required
- `pyseq>=0.9.0`: Image sequence detection
- `typer>=0.20.0`: CLI framework
- `rich>=14.2.0`: Terminal formatting
- `openimageio>=3.1.8.0`: Image I/O
- `pywin32`: Windows API (recycle bin, system operations)

### External Tools
- **FFmpeg**: Must be installed and in PATH
- **Python 3.8+**: Runtime requirement

## Future Enhancements

### Potential Features
- Configuration file for user preferences (implemented: `%LOCALAPPDATA%\ZilKit\config.json`)
- Plugin system for extensibility
- Additional FFmpeg operations
- Batch operations
- Progress tracking for long operations
- Update mechanism
- Multi-language support

### Distribution
- Consider creating a standalone executable (PyInstaller)
- Windows installer (NSIS or InnoSetup)
- Auto-update mechanism
- Chocolatey package

## Maintenance Plan

### Version Control
- Use Git with semantic versioning
- Feature branches for new functionality
- Pull requests for code review

### Documentation
- Keep README.md updated
- Maintain architecture documentation
- Update installation guide as needed
- Code comments and docstrings

### Testing
- Unit tests for core operations
- Integration tests for menu handlers
- Manual testing for registry integration
- Test on Windows 10 and 11

### Updates
- Regular dependency updates
- Security patches
- Feature additions based on user feedback
- Bug fixes and improvements

## Success Criteria

1. ✅ Project structure is well-organized and maintainable
2. ✅ Documentation is comprehensive
3. ✅ Context menu integration works reliably
4. ✅ All menu options function correctly
5. ✅ User experience is smooth with clear feedback
6. ⏳ Code is testable and tested (unit tests exist; integration/e2e pending)
7. ✅ Installation/uninstallation is straightforward
8. ⏳ Project is ready for GitHub publication

