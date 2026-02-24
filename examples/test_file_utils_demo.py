"""Simple demo script to test the file_utils functionality.

Run this script to see file utilities in action:
    python examples/test_file_utils_demo.py
"""

import sys
import tempfile
from pathlib import Path

# Add src to path so we can import zilkit
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zilkit.utils.file_utils import (
    ensure_directory,
    find_image_files,
    format_file_size,
    get_directory_size,
    get_file_size,
    list_files_sorted,
    normalize_path,
    validate_directory,
    walk_directories,
)
from zilkit.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Demonstrate file_utils functionality."""
    logger.info("Starting file_utils demo...")
    
    # Create a temporary directory structure for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Created temporary directory: {temp_dir}")
        
        # Create test structure
        test_dir = Path(temp_dir) / "test_structure"
        test_dir.mkdir()
        
        # Create subdirectories
        (test_dir / "images").mkdir()
        (test_dir / "documents").mkdir()
        (test_dir / "images" / "subfolder").mkdir()
        
        # Create test files
        (test_dir / "file1.txt").write_text("Test content 1")
        (test_dir / "file2.txt").write_text("Test content 2")
        (test_dir / "images" / "image1.png").write_text("fake png")
        (test_dir / "images" / "image2.jpg").write_text("fake jpg")
        (test_dir / "images" / "subfolder" / "image3.png").write_text("fake png")
        (test_dir / "documents" / "doc1.pdf").write_text("fake pdf")
        
        logger.info("\n=== Path Normalization ===")
        normalized = normalize_path(str(test_dir))
        logger.info(f"Normalized path: {normalized}")
        
        logger.info("\n=== Directory Validation ===")
        validated = validate_directory(str(test_dir))
        logger.info(f"Validated directory: {validated}")
        
        logger.info("\n=== Walking Directories ===")
        logger.info("Directories found (recursive):")
        for dir_path in walk_directories(str(test_dir), recursive=True):
            logger.info(f"  - {dir_path.name}")
        
        logger.info("\n=== Finding Image Files ===")
        logger.info("Image files found (non-recursive):")
        for img_file in find_image_files(str(test_dir), recursive=False):
            logger.info(f"  - {img_file.relative_to(test_dir)}")
        
        logger.info("\n=== Finding Image Files (Recursive) ===")
        logger.info("Image files found (recursive):")
        for img_file in find_image_files(str(test_dir), recursive=True):
            logger.info(f"  - {img_file.relative_to(test_dir)}")
        
        logger.info("\n=== Listing Files Sorted ===")
        files = list_files_sorted(str(test_dir), pattern="*.txt")
        logger.info("Text files (sorted):")
        for file_path in files:
            logger.info(f"  - {file_path.name}")
        
        logger.info("\n=== File Size Operations ===")
        test_file = test_dir / "file1.txt"
        size = get_file_size(str(test_file))
        logger.info(f"Size of {test_file.name}: {format_file_size(size)}")
        
        logger.info("\n=== Directory Size ===")
        total_size = get_directory_size(str(test_dir))
        logger.info(f"Total directory size: {format_file_size(total_size)}")
        
        logger.info("\n=== Ensure Directory ===")
        new_dir = test_dir / "new" / "nested" / "path"
        ensured = ensure_directory(str(new_dir))
        logger.info(f"Created directory: {ensured}")
        logger.info(f"Directory exists: {ensured.exists()}")
    
    logger.info("\n=== Demo completed! ===")


if __name__ == "__main__":
    main()

