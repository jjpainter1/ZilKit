"""Simple non-interactive test script for FFmpeg operations.

Usage:
    # Test with a specific directory
    python examples/test_ffmpeg_simple.py "C:\\path\\to\\images"
    
    # Test with current directory
    python examples/test_ffmpeg_simple.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zilkit.config import get_config
from zilkit.core.ffmpeg_ops import (
    convert_sequences_in_directory,
    find_image_sequences,
)
from zilkit.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run simple FFmpeg operations test."""
    # Get directory from command line or use current directory
    if len(sys.argv) > 1:
        test_path = Path(sys.argv[1])
        # If user entered a file path, extract the directory
        if test_path.is_file():
            test_dir = test_path.parent
            logger.info(f"Detected file path, using parent directory: {test_dir}")
        else:
            test_dir = test_path
    else:
        test_dir = Path.cwd()
    
    logger.info("=" * 60)
    logger.info("ZilKit FFmpeg Operations - Simple Test")
    logger.info("=" * 60)
    logger.info(f"Test directory: {test_dir}")
    
    # Check FFmpeg
    config = get_config()
    if not config.is_ffmpeg_available():
        logger.error("✗ FFmpeg is not available!")
        logger.info("Please ensure FFmpeg is installed and in your PATH")
        return
    
    logger.info(f"✓ FFmpeg found: {config.get_ffmpeg_path()}")
    
    # Show current settings
    settings = config.get_ffmpeg_encoding_settings()
    logger.info("\nCurrent encoding settings:")
    logger.info(f"  Resolution scale: {settings['resolution_scale']}")
    logger.info(f"  CRF: {settings['crf']}")
    logger.info(f"  Preset: {settings['preset']}")
    
    # Find sequences
    logger.info(f"\nScanning for image sequences in: {test_dir}")
    sequences = find_image_sequences(test_dir)
    
    if not sequences:
        logger.warning("✗ No image sequences found")
        logger.info("\nTo test, you need image sequences like:")
        logger.info("  frame_001.png, frame_002.png, frame_003.png")
        logger.info("  or")
        logger.info("  image.0001.jpg, image.0002.jpg, image.0003.jpg")
        return
    
    logger.info(f"✓ Found {len(sequences)} sequence(s):")
    for i, seq in enumerate(sequences, 1):
        logger.info(f"  {i}. {seq} ({len(seq)} frames)")
    
    # Ask about conversion
    logger.info("\n" + "=" * 60)
    logger.info("To test conversion, uncomment the lines below:")
    logger.info("=" * 60)
    logger.info("\n# Uncomment to perform actual conversion:")
    logger.info("# success, failed = convert_sequences_in_directory(")
    logger.info("#     test_dir,")
    logger.info("#     recursive=False,")
    logger.info("#     use_config_settings=True,")
    logger.info("# )")
    logger.info("# logger.info(f'Success: {success}, Failed: {failed}')")
    
    # Uncomment these lines to actually perform conversion:
    # logger.info("\nConverting sequences...")
    # success, failed = convert_sequences_in_directory(
    #     test_dir,
    #     recursive=False,
    #     use_config_settings=True,
    # )
    # logger.info(f"\n✓ Conversion complete: {success} successful, {failed} failed")


if __name__ == "__main__":
    main()

