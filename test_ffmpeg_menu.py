"""Quick test script to verify FFmpeg menu functionality works."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from zilkit.menu import ffmpeg

# Test with current directory or a test directory
test_dir = Path.cwd()
if len(sys.argv) > 1:
    test_dir = Path(sys.argv[1])

print(f"Testing FFmpeg menu with directory: {test_dir}")
print("=" * 60)

# Test the convert_current_directory function
try:
    ffmpeg.convert_current_directory(test_dir)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
