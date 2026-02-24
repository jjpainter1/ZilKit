# ZilKit Development Guide

## Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ZilKit.git
cd ZilKit
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -e ".[dev]"  # Include development dependencies
```

### 4. Install Pre-commit Hooks (Optional)
```bash
# If using pre-commit
pre-commit install
```

## Project Structure

See `docs/architecture.md` for detailed architecture documentation.

## Adding New Features

### Adding a New Menu Item

1. **Add to Menu Handler** (`src/zilkit/menu/`)
   - Create or update the appropriate menu handler file
   - Add a new handler function

2. **Implement Core Operation** (`src/zilkit/core/`)
   - Create or update the appropriate core operation file
   - Implement the actual functionality

3. **Update Registry** (`src/zilkit/registry.py`)
   - Add new registry entry for the menu item
   - Update `install.py` to register the new entry

4. **Update Documentation**
   - Add feature description to README.md
   - Update architecture docs if needed

### Adding a New Menu Category

1. **Create Menu Handler** (`src/zilkit/menu/new_category.py`)
2. **Update Main Router** (`src/zilkit/main.py`)
3. **Update Registry** (`src/zilkit/registry.py`)
4. **Update Installation Script** (`src/scripts/install.py`)

## Windows Registry Structure

ZilKit uses the following registry structure:

```
HKEY_CLASSES_ROOT\Directory\Background\shell\ZilKit
├── (Default) = "ZilKit"
├── MUIVerb = "ZilKit"
├── SubCommands = "ZilKit.FFmpeg;ZilKit.Shortcuts;ZilKit.Utilities"
└── Icon = "path\to\icon.ico"

HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ZilKit.FFmpeg
├── (Default) = "FFmpeg Operations"
└── command
    └── (Default) = "python path\to\zilkit\main.py --action ffmpeg --subaction convert-current"

HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ZilKit.Shortcuts
├── (Default) = "System Shortcuts"
└── command
    └── (Default) = "python path\to\zilkit\main.py --action shortcuts --subaction empty-recycle"

HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell\ZilKit.Utilities
├── (Default) = "Utilities"
└── command
    └── (Default) = "python path\to\zilkit\main.py --action utilities"
```

## Testing

### Run Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=zilkit --cov-report=html
```

### Test Context Menu Integration
1. Install ZilKit: `python src/scripts/install.py`
2. Right-click in Windows Explorer
3. Test each menu option
4. Check logs for errors

## Code Style

- Follow PEP 8
- Use Black for formatting: `black src/ tests/`
- Use type hints where appropriate
- Document functions with docstrings

## Building and Distribution

### Create Distribution Package
```bash
python -m build
```

### Create Executable (Future)
Consider using PyInstaller or cx_Freeze to create a standalone executable:
```bash
pyinstaller --onefile --windowed src/zilkit/main.py
```

## Debugging

### Enable Debug Logging
Set environment variable:
```bash
set ZILKIT_DEBUG=1
```

### View Registry Entries
Use `regedit` to inspect registry entries:
- Navigate to `HKEY_CLASSES_ROOT\Directory\Background\shell\ZilKit`

### Test Without Registry
You can test menu handlers directly:
```bash
python src/zilkit/main.py --action ffmpeg --subaction convert-current --path "C:\test\directory"
```

## Common Issues

### Permission Errors
- Registry operations require administrator privileges
- Run installation script as administrator

### Path Issues
- Use absolute paths in registry entries
- Handle spaces in paths correctly
- Use raw strings or proper escaping for Windows paths

### FFmpeg Detection
- Test FFmpeg availability before operations
- Provide clear error messages if not found
- Consider allowing user to specify FFmpeg path in config

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

