"""Simple demo script to test the logger functionality.

Run this script to see the logger in action:
    python examples/test_logger_demo.py

Or with debug mode enabled:
    set ZILKIT_DEBUG=1
    python examples/test_logger_demo.py
"""

import sys
from pathlib import Path

# Add src to path so we can import zilkit
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zilkit.utils.logger import get_logger

# Get a logger instance
logger = get_logger(__name__)


def main():
    """Demonstrate logger functionality."""
    logger.info("Starting logger demo...")
    logger.debug("This is a debug message (only visible if ZILKIT_DEBUG=1)")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    try:
        # Simulate an error with traceback
        result = 1 / 0
    except ZeroDivisionError:
        logger.exception("Caught an exception (this will show a traceback)")
    
    logger.info("Logger demo completed!")
    logger.info(f"Log file location: {Path.home() / 'AppData' / 'Local' / 'ZilKit' / 'logs' / 'zilkit.log'}")


if __name__ == "__main__":
    main()

