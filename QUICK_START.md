# ZilKit Quick Start Guide

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install ZilKit in Windows context menu:**
   ```bash
   python src/scripts/install.py
   ```

3. **Restart Windows Explorer** (required for changes to take effect):
   - Open Task Manager (Ctrl+Shift+Esc)
   - Find "Windows Explorer" process
   - Right-click and select "Restart"
   - Or simply log out and log back in

## Usage

1. **Right-click in any folder** (in the background, not on a file)
2. Select **ZilKit** > **FFmpeg** > **Convert Image Sequence**
3. The script will:
   - Scan for image sequences in the current directory
   - Show you what sequences were found
   - Convert them to MP4 video files

## Testing

### Test the Installation

After installing, you can test if the context menu is registered:

```bash
python -c "from zilkit.registry import is_registered; print('Registered!' if is_registered() else 'Not registered')"
```

### Test FFmpeg Conversion

You can test the FFmpeg conversion directly from command line:

```bash
# Test with current directory
python src/zilkit/main.py ffmpeg convert-current

# Test with specific directory
python src/zilkit/main.py ffmpeg convert-current --dir "C:\path\to\your\images"
```

### Test with Example Images

If you have the test images in `tests/TestImageSeq/`:

```bash
python src/zilkit/main.py ffmpeg convert-current --dir "tests/TestImageSeq"
```

## Uninstallation

To remove ZilKit from the context menu:

```bash
python src/scripts/uninstall.py
```

Then restart Windows Explorer (same as installation).

## Troubleshooting

### Context Menu Doesn't Appear

1. Make sure you installed: `python src/scripts/install.py`
2. Restart Windows Explorer (see Installation step 3)
3. Try logging out and back in
4. Check if it's registered: `python -c "from zilkit.registry import is_registered; print(is_registered())"`

### FFmpeg Not Found

1. Install FFmpeg: Download from https://ffmpeg.org/download.html
2. Add FFmpeg to your system PATH
3. Verify: `ffmpeg -version` should work in command prompt
4. Or set manually in ZilKit config (see config.py)

### No Sequences Found

- Make sure your image files are numbered sequentially (e.g., `frame_001.png`, `frame_002.png`)
- Files must be in the same directory
- At least 2 frames are required to form a sequence
- `.exr` files are excluded

## Configuration

Settings are stored in: `%LOCALAPPDATA%\ZilKit\config.json`

You can modify encoding settings programmatically or edit the JSON file directly.
