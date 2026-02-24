"""Tests for file_utils module."""

import tempfile
from pathlib import Path

import pytest

from zilkit.utils.file_utils import (
    ensure_directory,
    find_files,
    find_image_files,
    format_file_size,
    get_directory_path,
    get_directory_size,
    get_file_size,
    get_relative_path,
    is_safe_path,
    list_files_sorted,
    normalize_path,
    validate_directory,
    walk_directories,
)


def test_normalize_path():
    """Test path normalization."""
    # Test with absolute path
    path = normalize_path("C:\\Users\\Test")
    assert isinstance(path, Path)
    
    # Test with relative path
    path = normalize_path("test")
    assert isinstance(path, Path)


def test_validate_directory(tmp_path):
    """Test directory validation."""
    # Valid directory
    result = validate_directory(str(tmp_path))
    assert result == tmp_path
    
    # Non-existent directory
    with pytest.raises(ValueError, match="does not exist"):
        validate_directory("C:\\NonExistent\\Path\\12345")
    
    # Path that's a file, not a directory
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")
    
    with pytest.raises(ValueError, match="not a directory"):
        validate_directory(str(test_file))


def test_get_directory_path(tmp_path):
    """Test getting directory path."""
    # Without argument (uses current directory)
    result = get_directory_path()
    assert isinstance(result, Path)
    assert result.is_dir()
    
    # With valid directory
    result = get_directory_path(str(tmp_path))
    assert result == tmp_path
    
    # With invalid directory
    with pytest.raises(ValueError):
        get_directory_path("C:\\NonExistent\\Path\\12345")


def test_walk_directories(tmp_path):
    """Test directory walking."""
    # Create test directory structure
    (tmp_path / "subdir1").mkdir()
    (tmp_path / "subdir2").mkdir()
    (tmp_path / "subdir1" / "subsubdir").mkdir()
    
    # Test recursive walk
    dirs = list(walk_directories(str(tmp_path), recursive=True))
    assert len(dirs) >= 3  # root + subdir1 + subdir2 + subsubdir
    
    # Test non-recursive walk
    dirs = list(walk_directories(str(tmp_path), recursive=False))
    assert len(dirs) == 3  # root + subdir1 + subdir2
    
    # Test without including root
    dirs = list(walk_directories(str(tmp_path), recursive=False, include_root=False))
    assert len(dirs) == 2  # subdir1 + subdir2


def test_find_files(tmp_path):
    """Test finding files."""
    # Create test files
    (tmp_path / "file1.txt").write_text("test")
    (tmp_path / "file2.png").write_text("test")
    (tmp_path / "file3.jpg").write_text("test")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file4.txt").write_text("test")
    
    # Find by extension
    files = list(find_files(str(tmp_path), extensions={".txt"}))
    assert len(files) == 1
    
    # Find by pattern
    files = list(find_files(str(tmp_path), pattern="file*.txt"))
    assert len(files) == 1
    
    # Find recursively
    files = list(find_files(str(tmp_path), extensions={".txt"}, recursive=True))
    assert len(files) == 2  # file1.txt and subdir/file4.txt
    
    # Find all files
    files = list(find_files(str(tmp_path), recursive=True))
    assert len(files) == 4


def test_find_image_files(tmp_path):
    """Test finding image files."""
    # Create test files
    (tmp_path / "image1.png").write_text("test")
    (tmp_path / "image2.jpg").write_text("test")
    (tmp_path / "document.txt").write_text("test")
    
    # Find images
    images = list(find_image_files(str(tmp_path)))
    assert len(images) == 2
    
    # Check that only images are found
    extensions = {img.suffix.lower() for img in images}
    assert ".png" in extensions
    assert ".jpg" in extensions
    assert ".txt" not in extensions


def test_get_file_size(tmp_path):
    """Test getting file size."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    size = get_file_size(str(test_file))
    assert size > 0
    
    # Non-existent file
    with pytest.raises(ValueError, match="does not exist"):
        get_file_size(str(tmp_path / "nonexistent.txt"))
    
    # Directory instead of file
    with pytest.raises(ValueError, match="not a file"):
        get_file_size(str(tmp_path))


def test_format_file_size():
    """Test file size formatting."""
    assert format_file_size(0) == "0.0 B"
    assert format_file_size(1024) == "1.0 KB"
    assert format_file_size(1024 * 1024) == "1.0 MB"
    assert format_file_size(1536 * 1024) == "1.5 MB"


def test_ensure_directory(tmp_path):
    """Test ensuring directory exists."""
    new_dir = tmp_path / "new" / "nested" / "directory"
    
    # Directory doesn't exist yet
    assert not new_dir.exists()
    
    # Create it
    result = ensure_directory(str(new_dir))
    assert result == new_dir
    assert new_dir.exists()
    assert new_dir.is_dir()
    
    # Calling again should not raise error
    result = ensure_directory(str(new_dir))
    assert result == new_dir


def test_is_safe_path(tmp_path):
    """Test path safety checking."""
    base = tmp_path / "base"
    base.mkdir()
    
    # Safe paths
    assert is_safe_path("subdir/file.txt", base_dir=str(base))
    assert is_safe_path("file.txt", base_dir=str(base))
    
    # Unsafe paths (directory traversal)
    assert not is_safe_path("../../etc/passwd", base_dir=str(base))
    assert not is_safe_path("..\\..\\windows\\system32", base_dir=str(base))
    
    # Path outside base
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    assert not is_safe_path(str(other_dir), base_dir=str(base))


def test_get_relative_path(tmp_path):
    """Test getting relative path."""
    base = tmp_path / "base"
    base.mkdir()
    target = base / "subdir" / "file.txt"
    target.parent.mkdir()
    target.write_text("test")
    
    relative = get_relative_path(str(target), str(base))
    assert "subdir" in relative
    assert "file.txt" in relative


def test_list_files_sorted(tmp_path):
    """Test listing files sorted."""
    # Create files in non-alphabetical order
    (tmp_path / "zebra.txt").write_text("test")
    (tmp_path / "apple.txt").write_text("test")
    (tmp_path / "banana.txt").write_text("test")
    
    files = list_files_sorted(str(tmp_path), pattern="*.txt")
    
    assert len(files) == 3
    assert files[0].name == "apple.txt"
    assert files[1].name == "banana.txt"
    assert files[2].name == "zebra.txt"


def test_get_directory_size(tmp_path):
    """Test calculating directory size."""
    # Create files with known sizes
    (tmp_path / "file1.txt").write_text("x" * 100)
    (tmp_path / "file2.txt").write_text("y" * 200)
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file3.txt").write_text("z" * 50)
    
    total_size = get_directory_size(str(tmp_path))
    
    # Should be at least the sum of our test files
    assert total_size >= 350  # 100 + 200 + 50

