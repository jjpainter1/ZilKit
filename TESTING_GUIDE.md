# Testing Guide for ZilKit FFmpeg Operations

This guide walks you through testing the FFmpeg image sequence conversion functionality.

## Prerequisites

1. **FFmpeg installed** - Verify with: `ffmpeg -version`
2. **Python dependencies** - Install with: `pip install -r requirements.txt`
3. **Test image sequences** - You'll need some image sequences to test with

## Quick Test

### Option 1: Simple Test Script (Recommended)

```bash
# Test with a specific directory
python examples/test_ffmpeg_simple.py "C:\path\to\your\images"

# Or test with current directory
python examples/test_ffmpeg_simple.py
```

This will:
- Check if FFmpeg is available
- Show current encoding settings
- Scan for image sequences
- Show what sequences were found

### Option 2: Interactive Test Script

```bash
python examples/test_ffmpeg_ops.py
```

This provides an interactive menu to:
- Use existing directories
- Create test sequences
- Test configuration
- Perform actual conversions

## Manual Testing Steps

### Step 1: Prepare Test Data

You need image sequences with numbered frames. Examples:
- `frame_001.png`, `frame_002.png`, `frame_003.png`
- `image.0001.jpg`, `image.0002.jpg`, `image.0003.jpg`
- `render_01.tif`, `render_02.tif`, `render_03.tif`

**Note:** `.exr` files are excluded and will not be processed.

### Step 2: Check FFmpeg Availability

```python
from zilkit.config import get_config

config = get_config()
if config.is_ffmpeg_available():
    print(f"FFmpeg found: {config.get_ffmpeg_path()}")
else:
    print("FFmpeg not found!")
```

### Step 3: Test Sequence Detection

```python
from pathlib import Path
from zilkit.core.ffmpeg_ops import find_image_sequences

test_dir = Path("C:\\path\\to\\your\\images")
sequences = find_image_sequences(test_dir)

print(f"Found {len(sequences)} sequences:")
for seq in sequences:
    print(f"  - {seq} ({len(seq)} frames)")
```

### Step 4: Configure Encoding Settings

```python
from zilkit.config import get_config

config = get_config()

# Set to full resolution
config.set_ffmpeg_encoding_settings(
    resolution_scale=1.0,  # Full resolution
    crf=23,                 # Quality (18-28, lower = higher quality)
    preset="medium"         # Encoding speed
)

# Or set to half resolution
config.set_ffmpeg_encoding_settings(
    resolution_scale=0.5,  # Half resolution
    crf=23,
    preset="medium"
)
```

### Step 5: Test Conversion (Current Directory)

```python
from pathlib import Path
from zilkit.core.ffmpeg_ops import convert_sequences_in_directory

test_dir = Path("C:\\path\\to\\your\\images")

# Convert sequences in current directory only
success, failed = convert_sequences_in_directory(
    test_dir,
    recursive=False,  # Only current directory
    use_config_settings=True  # Use settings from config
)

print(f"Success: {success}, Failed: {failed}")
```

### Step 6: Test Recursive Conversion

```python
# Convert sequences in all subdirectories
success, failed = convert_sequences_in_directory(
    test_dir,
    recursive=True,  # All subdirectories
    use_config_settings=True
)

print(f"Success: {success}, Failed: {failed}")
```

## Testing Different Configurations

### Test Full Resolution

```python
from zilkit.config import get_config

config = get_config()
config.set_ffmpeg_encoding_settings(
    resolution_scale=1.0,  # Full resolution
    crf=23,
    preset="medium"
)

# Then run conversion...
```

### Test Half Resolution

```python
config.set_ffmpeg_encoding_settings(
    resolution_scale=0.5,  # Half resolution
    crf=23,
    preset="medium"
)

# Then run conversion...
```

### Test High Quality

```python
config.set_ffmpeg_encoding_settings(
    resolution_scale=1.0,
    crf=18,  # Lower CRF = higher quality
    preset="slow"  # Slower encoding = better compression
)
```

### Test Fast Encoding

```python
config.set_ffmpeg_encoding_settings(
    resolution_scale=1.0,
    crf=23,
    preset="fast"  # Faster encoding
)
```

## Expected Results

After conversion, you should see:
- `.mp4` files created in the same directory as the sequences
- Files named after the sequence (e.g., `frame_1-100.mp4`)
- Video files playable in any media player

## Troubleshooting

### No Sequences Found

**Problem:** `find_image_sequences()` returns empty list

**Solutions:**
- Ensure files are numbered sequentially (frame_001.png, frame_002.png, etc.)
- Check that files are in the same directory
- Verify files are not `.exr` format (these are excluded)
- Make sure files form a sequence (at least 2 frames)

### FFmpeg Not Found

**Problem:** `config.is_ffmpeg_available()` returns False

**Solutions:**
- Install FFmpeg: `choco install ffmpeg` (Chocolatey) or download from ffmpeg.org
- Add FFmpeg to system PATH
- Or set manually: `config.set_ffmpeg_path("C:\\path\\to\\ffmpeg.exe")`

### Conversion Fails

**Problem:** `convert_sequences_in_directory()` returns failures

**Solutions:**
- Check FFmpeg is working: `ffmpeg -version`
- Verify image files are valid and readable
- Check disk space
- Review log files in `%LOCALAPPDATA%\ZilKit\logs\`

### Wrong Resolution

**Problem:** Output video has unexpected resolution

**Solutions:**
- Check `config.get_ffmpeg_encoding_settings()` to see current settings
- Adjust `resolution_scale` (1.0 = full, 0.5 = half, etc.)
- Re-run conversion

## Configuration File Location

Settings are saved in:
```
%LOCALAPPDATA%\ZilKit\config.json
```

You can edit this file directly or use the Python API:
```python
config.set_ffmpeg_encoding_settings(resolution_scale=0.5)
```

## Example Test Workflow

1. **Prepare test directory** with image sequences
2. **Run simple test**: `python examples/test_ffmpeg_simple.py "C:\test\images"`
3. **Verify sequences found** - Should show your sequences
4. **Set configuration** for desired output (full/half resolution)
5. **Run conversion** - Uncomment conversion code in test script
6. **Check output** - Verify `.mp4` files created
7. **Test different settings** - Change config and re-run

## Next Steps

Once testing is successful:
- Create menu handlers to call these functions
- Integrate with Windows context menu
- Add progress indicators
- Add error handling UI

