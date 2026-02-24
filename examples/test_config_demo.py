"""Simple demo script to test the config functionality.

Run this script to see config in action:
    python examples/test_config_demo.py
"""

import sys
from pathlib import Path

# Add src to path so we can import zilkit
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zilkit.config import get_config, get_config_dir, get_config_file
from zilkit.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Demonstrate config functionality."""
    logger.info("Starting config demo...")
    
    logger.info("\n=== Configuration File Location ===")
    config_dir = get_config_dir()
    config_file = get_config_file()
    logger.info(f"Config directory: {config_dir}")
    logger.info(f"Config file: {config_file}")
    
    logger.info("\n=== Getting Config Instance ===")
    config = get_config()
    logger.info("Config instance created")
    
    logger.info("\n=== Testing Configuration Values ===")
    # Set some test values
    config.set("test_string", "Hello, ZilKit!")
    config.set("test_number", 42)
    config.set("test_bool", True)
    
    logger.info(f"test_string: {config.get('test_string')}")
    logger.info(f"test_number: {config.get('test_number')}")
    logger.info(f"test_bool: {config.get('test_bool')}")
    logger.info(f"nonexistent (with default): {config.get('nonexistent', 'default_value')}")
    
    logger.info("\n=== FFmpeg Detection ===")
    logger.info("Searching for FFmpeg...")
    
    # Find FFmpeg
    ffmpeg_path = config.find_ffmpeg()
    
    if ffmpeg_path:
        logger.info(f"✓ FFmpeg found at: {ffmpeg_path}")
        
        # Validate FFmpeg
        logger.info("Validating FFmpeg...")
        is_valid = config.validate_ffmpeg(ffmpeg_path)
        
        if is_valid:
            logger.info("✓ FFmpeg is valid and working")
            
            # Get version
            version = config.get_ffmpeg_version()
            if version:
                logger.info(f"FFmpeg version: {version}")
            
            # Check availability
            if config.is_ffmpeg_available():
                logger.info("✓ FFmpeg is available for use")
        else:
            logger.warning("✗ FFmpeg validation failed")
    else:
        logger.warning("✗ FFmpeg not found")
        logger.info("\nTo set FFmpeg path manually:")
        logger.info("  config.set_ffmpeg_path('C:\\path\\to\\ffmpeg.exe')")
        logger.info("\nOr set environment variable:")
        logger.info("  set ZILKIT_FFMPEG_PATH=C:\\path\\to\\ffmpeg.exe")
    
    logger.info("\n=== Configuration Persistence ===")
    logger.info("Configuration is saved to:")
    logger.info(f"  {config_file}")
    logger.info("\nYou can edit this file directly or use config.set() to modify values")
    
    logger.info("\n=== Demo completed! ===")


if __name__ == "__main__":
    main()

