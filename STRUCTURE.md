# ZilKit Project Structure

## Quick Reference

```
ZilKit/
│
├── 📄 README.md                    # Main project documentation
├── 📄 LICENSE                      # MIT License
├── 📄 .gitignore                   # Git ignore rules
├── 📄 requirements.txt             # Python dependencies
├── 📄 pyproject.toml               # Modern Python project config
├── 📄 PROJECT_PLAN.md              # Detailed project plan
├── 📄 STRUCTURE.md                 # This file
│
├── 📁 src/                         # Source code
│   ├── 📁 zilkit/                 # Main package
│   │   ├── 📄 __init__.py         # Package initialization
│   │   ├── 📄 main.py             # Entry point (TO BE CREATED)
│   │   ├── 📄 config.py           # Configuration (TO BE CREATED)
│   │   ├── 📄 registry.py         # Registry operations (TO BE CREATED)
│   │   │
│   │   ├── 📁 menu/               # Menu handlers (routing layer)
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 ffmpeg.py       # FFmpeg menu handler (TO BE CREATED)
│   │   │   ├── 📄 shortcuts.py    # Shortcuts menu handler (TO BE CREATED)
│   │   │   └── 📄 utilities.py   # Utilities menu handler (TO BE CREATED)
│   │   │
│   │   ├── 📁 core/               # Core operations (business logic)
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 ffmpeg_ops.py   # FFmpeg operations (TO BE CREATED)
│   │   │   └── 📄 system_ops.py   # System operations (TO BE CREATED)
│   │   │
│   │   └── 📁 utils/              # Shared utilities
│   │       ├── 📄 __init__.py
│   │       ├── 📄 file_utils.py   # File utilities (TO BE CREATED)
│   │       └── 📄 logger.py       # Logging utilities (TO BE CREATED)
│   │
│   └── 📁 scripts/                # Installation scripts
│       ├── 📄 install.py          # Installation script (TO BE CREATED)
│       └── 📄 uninstall.py        # Uninstallation script (TO BE CREATED)
│
├── 📁 tests/                      # Test suite
│   ├── 📄 __init__.py
│   ├── 📄 test_ffmpeg_ops.py      # FFmpeg tests (TO BE CREATED)
│   ├── 📄 test_system_ops.py      # System tests (TO BE CREATED)
│   └── 📄 test_file_utils.py      # Utility tests (TO BE CREATED)
│
└── 📁 docs/                       # Documentation
    ├── 📄 architecture.md         # Architecture documentation
    ├── 📄 installation.md         # Installation guide
    └── 📄 development.md          # Development guide
```

## Module Flow

### Context Menu Action Flow
```
User Right-Clicks → Windows Registry → main.py → Menu Handler → Core Operation → Result
```

### Example: Convert Image Sequence
```
1. User: Right-click → ZilKit → FFmpeg → Convert Image Sequence
2. Windows: Executes python main.py --action ffmpeg --subaction convert-current --path "C:\directory"
3. main.py: Parses arguments, routes to menu/ffmpeg.py
4. menu/ffmpeg.py: Validates, calls core/ffmpeg_ops.py
5. core/ffmpeg_ops.py: Detects sequence (pyseq), runs FFmpeg, returns result
6. menu/ffmpeg.py: Displays result via Rich
```

## Key Design Principles

1. **Separation of Concerns**
   - Menu handlers: Routing and user interaction
   - Core operations: Business logic
   - Utils: Reusable functions

2. **Modularity**
   - Each menu category is independent
   - Easy to add new features
   - Clear boundaries between modules

3. **Maintainability**
   - Well-documented code
   - Comprehensive tests
   - Clear project structure

4. **User Experience**
   - Rich terminal output
   - Clear error messages
   - Progress indicators

## Next Steps

1. Implement `main.py` - Entry point with Typer
2. Implement `config.py` - Configuration management
3. Implement `registry.py` - Windows registry operations
4. Implement core operations (ffmpeg_ops.py, system_ops.py)
5. Implement menu handlers
6. Create installation/uninstallation scripts
7. Write tests
8. Test end-to-end functionality

