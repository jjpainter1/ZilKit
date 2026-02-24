"""Test script for FFmpeg operations.

This script helps you test the FFmpeg image sequence conversion functionality.
It will:
1. Create test image sequences (or use existing ones)
2. Test sequence detection
3. Test FFmpeg conversion with different settings
4. Show results

Run this script:
    python examples/test_ffmpeg_ops.py
"""

import sys
import tempfile
from pathlib import Path

# Add src to path so we can import zilkit
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zilkit.config import get_config
from zilkit.core.ffmpeg_ops import (
    convert_sequences_in_directory,
    find_image_sequences,
)
from zilkit.utils.logger import get_logger

logger = get_logger(__name__)


def create_test_sequence(directory: Path, name: str, count: int = 5, extension: str = ".png"):
    """Create a test image sequence using ImageMagick or PIL.
    
    Args:
        directory: Directory to create sequence in
        name: Base name for sequence
        count: Number of frames
        extension: File extension
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        directory.mkdir(parents=True, exist_ok=True)
        
        for i in range(1, count + 1):
            # Create a simple test image
            img = Image.new('RGB', (640, 480), color=(50 + i * 10, 100, 150))
            draw = ImageDraw.Draw(img)
            
            # Add frame number text
            try:
                # Try to use a default font
                font = ImageFont.load_default()
            except:
                font = None
            
            text = f"Frame {i}"
            draw.text((10, 10), text, fill=(255, 255, 255), font=font)
            
            # Save with padded frame number
            frame_path = directory / f"{name}_{i:04d}{extension}"
            img.save(frame_path)
            logger.debug(f"Created test frame: {frame_path}")
        
        logger.info(f"Created test sequence: {name} ({count} frames)")
        return True
    
    except ImportError:
        logger.warning("PIL/Pillow not available. Cannot create test images.")
        logger.info("Please install Pillow: pip install Pillow")
        logger.info("Or use an existing directory with image sequences.")
        return False
    except Exception as e:
        logger.error(f"Error creating test sequence: {e}")
        return False


def test_sequence_detection(directory: Path):
    """Test image sequence detection."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 1: Image Sequence Detection")
    logger.info("=" * 60)
    
    logger.info(f"Scanning directory: {directory}")
    
    sequences = find_image_sequences(directory)
    
    if sequences:
        logger.info(f"✓ Found {len(sequences)} image sequence(s):")
        for i, seq in enumerate(sequences, 1):
            logger.info(f"  {i}. {seq} ({len(seq)} frames)")
            logger.info(f"     Format: {seq.format()}")
    else:
        logger.warning("✗ No image sequences found")
        logger.info("This could mean:")
        logger.info("  - No image files in directory")
        logger.info("  - Files don't form sequences (need numbered frames)")
        logger.info("  - Only .exr files (which are excluded)")
    
    return sequences


def test_ffmpeg_conversion(directory: Path, test_actual_conversion: bool = False):
    """Test FFmpeg conversion."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: FFmpeg Conversion")
    logger.info("=" * 60)
    
    # Check FFmpeg availability
    config = get_config()
    if not config.is_ffmpeg_available():
        logger.error("✗ FFmpeg is not available!")
        logger.info("Please ensure FFmpeg is installed and in your PATH")
        logger.info("Or set it in config: config.set_ffmpeg_path('C:\\path\\to\\ffmpeg.exe')")
        return False
    
    ffmpeg_path = config.get_ffmpeg_path()
    logger.info(f"✓ FFmpeg found at: {ffmpeg_path}")
    
    # Show current encoding settings
    settings = config.get_ffmpeg_encoding_settings()
    logger.info("\nCurrent encoding settings:")
    logger.info(f"  Resolution scale: {settings['resolution_scale']} ({'Full' if settings['resolution_scale'] == 1.0 else 'Half' if settings['resolution_scale'] == 0.5 else 'Custom'})")
    logger.info(f"  CRF: {settings['crf']} (lower = higher quality)")
    logger.info(f"  Preset: {settings['preset']}")
    logger.info(f"  Pixel format: {settings['pixel_format']}")
    logger.info(f"  Framerate: {settings['framerate'] or 'Use input framerate'}")
    
    if not test_actual_conversion:
        logger.info("\n⚠ Skipping actual conversion (test_actual_conversion=False)")
        logger.info("Set test_actual_conversion=True to perform real conversions")
        return True
    
    # Find sequences
    sequences = find_image_sequences(directory)
    if not sequences:
        logger.warning("No sequences found to convert")
        return False
    
    logger.info(f"\nConverting {len(sequences)} sequence(s) in current directory...")
    
    # Convert sequences
    success_count, failure_count = convert_sequences_in_directory(
        directory,
        recursive=False,
        use_config_settings=True,
    )
    
    logger.info(f"\n✓ Conversion complete!")
    logger.info(f"  Successful: {success_count}")
    logger.info(f"  Failed: {failure_count}")
    
    # Check for output files
    output_files = list(directory.glob("*.mp4"))
    if output_files:
        logger.info(f"\n✓ Output files created:")
        for output_file in output_files:
            size_mb = output_file.stat().st_size / (1024 * 1024)
            logger.info(f"  - {output_file.name} ({size_mb:.2f} MB)")
    
    return success_count > 0


def test_configuration():
    """Test configuration settings."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Configuration Settings")
    logger.info("=" * 60)
    
    config = get_config()
    
    logger.info("Testing configuration changes...")
    
    # Test full resolution
    logger.info("\n1. Setting to FULL resolution (1.0):")
    config.set_ffmpeg_encoding_settings(resolution_scale=1.0, crf=23)
    settings = config.get_ffmpeg_encoding_settings()
    logger.info(f"   Resolution scale: {settings['resolution_scale']}")
    
    # Test half resolution
    logger.info("\n2. Setting to HALF resolution (0.5):")
    config.set_ffmpeg_encoding_settings(resolution_scale=0.5, crf=23)
    settings = config.get_ffmpeg_encoding_settings()
    logger.info(f"   Resolution scale: {settings['resolution_scale']}")
    
    # Reset to defaults
    logger.info("\n3. Resetting to defaults:")
    config.set_ffmpeg_encoding_settings(resolution_scale=1.0, crf=23, preset="medium")
    settings = config.get_ffmpeg_encoding_settings()
    logger.info(f"   Resolution scale: {settings['resolution_scale']}")
    logger.info(f"   CRF: {settings['crf']}")
    logger.info(f"   Preset: {settings['preset']}")
    
    logger.info("\n✓ Configuration test complete!")
    logger.info("\nYou can change settings anytime:")
    logger.info("  config.set_ffmpeg_encoding_settings(resolution_scale=0.5)")
    logger.info("  config.set_ffmpeg_encoding_settings(crf=18)  # Higher quality")


def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("ZilKit FFmpeg Operations Test")
    logger.info("=" * 60)
    
    # Ask user for test directory
    print("\n" + "=" * 60)
    print("Test Options:")
    print("=" * 60)
    print("1. Use existing directory with image sequences")
    print("2. Create test sequences in temporary directory")
    print("3. Just test configuration (no file operations)")
    print()
    
    choice = input("Enter choice (1-3) [default: 3]: ").strip() or "3"
    
    test_dir = None
    
    if choice == "1":
        # Use existing directory
        dir_path = input("\nEnter directory path with image sequences: ").strip()
        if dir_path:
            test_path = Path(dir_path)
            # If user entered a file path, extract the directory
            if test_path.is_file():
                test_dir = test_path.parent
                logger.info(f"Detected file path, using parent directory: {test_dir}")
            elif test_path.is_dir():
                test_dir = test_path
            elif not test_path.exists():
                logger.error(f"Path does not exist: {test_path}")
                return
            else:
                # Assume it's a directory even if is_dir() returns False
                test_dir = test_path
        else:
            logger.info("No directory provided, using current directory")
            test_dir = Path.cwd()
    
    elif choice == "2":
        # Create test sequences
        logger.info("\nCreating test sequences...")
        test_dir = Path(tempfile.mkdtemp(prefix="zilkit_test_"))
        logger.info(f"Test directory: {test_dir}")
        
        # Create a couple of test sequences
        create_test_sequence(test_dir, "sequence1", count=5, extension=".png")
        create_test_sequence(test_dir, "sequence2", count=3, extension=".jpg")
        
        logger.info(f"\n✓ Test sequences created in: {test_dir}")
        logger.info("You can keep this directory to test with, or it will be cleaned up")
    
    elif choice == "3":
        # Just test configuration
        test_configuration()
        return
    
    if test_dir is None:
        logger.error("No test directory available")
        return
    
    # Run tests
    logger.info(f"\nUsing test directory: {test_dir}")
    
    # Test 1: Sequence detection
    sequences = test_sequence_detection(test_dir)
    
    if not sequences:
        logger.warning("\n⚠ No sequences found. Cannot test conversion.")
        logger.info("Make sure you have image sequences with numbered frames")
        logger.info("Example: frame_001.png, frame_002.png, frame_003.png")
        return
    
    # Test 2: Configuration
    test_configuration()
    
    # Test 3: FFmpeg conversion (ask user)
    if sequences:
        print("\n" + "=" * 60)
        print("FFmpeg Conversion Test")
        print("=" * 60)
        print("This will actually convert sequences to MP4 using FFmpeg.")
        print("This may take a few minutes depending on sequence size.")
        print()
        convert_choice = input("Perform actual conversion? (y/N): ").strip().lower()
        
        if convert_choice == 'y':
            test_ffmpeg_conversion(test_dir, test_actual_conversion=True)
        else:
            logger.info("Skipping actual conversion")
            logger.info("Set test_actual_conversion=True in the code to test conversion")
    
    logger.info("\n" + "=" * 60)
    logger.info("Testing complete!")
    logger.info("=" * 60)
    
    if choice == "2":
        logger.info(f"\nTest directory: {test_dir}")
        logger.info("You can delete this directory when done testing")


if __name__ == "__main__":
    main()

