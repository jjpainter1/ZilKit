"""File and directory utility functions for ZilKit.

This module provides utilities for path validation, directory traversal,
and file pattern matching.
"""

import os
from pathlib import Path
from typing import Iterator, List, Optional, Set


# Common image file extensions (for image sequence detection)
IMAGE_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".exr", ".dpx",
    ".bmp", ".gif", ".webp", ".tga", ".hdr", ".pic", ".sgi",
}


def normalize_path(path: str) -> Path:
    """Normalize a path string to a Path object.
    
    Handles Windows paths, expands user directory, and resolves relative paths.
    
    Args:
        path: Path string (can be relative or absolute)
    
    Returns:
        Path: Normalized Path object
    
    Example:
        >>> normalize_path("C:\\Users\\Test")
        WindowsPath('C:/Users/Test')
        >>> normalize_path("~/Documents")
        WindowsPath('C:/Users/Username/Documents')
    """
    return Path(path).expanduser().resolve()


def validate_directory(path: str) -> Path:
    """Validate that a path exists and is a directory.
    
    Args:
        path: Path string to validate
    
    Returns:
        Path: Validated Path object
    
    Raises:
        ValueError: If path doesn't exist or is not a directory
    
    Example:
        >>> validate_directory("C:\\Users")
        WindowsPath('C:/Users')
    """
    normalized = normalize_path(path)
    
    if not normalized.exists():
        raise ValueError(f"Path does not exist: {path}")
    
    if not normalized.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    
    return normalized


def get_directory_path(path: Optional[str] = None) -> Path:
    """Get the current working directory or validate a provided path.
    
    This is useful for getting the directory where the user right-clicked
    in Windows Explorer.
    
    Args:
        path: Optional directory path. If None, uses current working directory
    
    Returns:
        Path: Directory path
    
    Raises:
        ValueError: If provided path is invalid
    
    Example:
        >>> get_directory_path()  # Uses current directory
        >>> get_directory_path("C:\\Users\\Documents")
    """
    if path is None:
        return Path.cwd()
    
    return validate_directory(path)


def walk_directories(
    root_dir: str,
    recursive: bool = True,
    include_root: bool = True,
) -> Iterator[Path]:
    """Walk through directories, optionally recursively.
    
    Args:
        root_dir: Root directory to start from
        recursive: If True, walk subdirectories recursively
        include_root: If True, include the root directory in results
    
    Yields:
        Path: Directory paths
    
    Example:
        >>> for dir_path in walk_directories("C:\\Users", recursive=True):
        ...     print(dir_path)
    """
    root = validate_directory(root_dir)
    
    if include_root:
        yield root
    
    if recursive:
        for dirpath in root.rglob("*"):
            if dirpath.is_dir():
                yield dirpath
    else:
        for item in root.iterdir():
            if item.is_dir():
                yield item


def find_files(
    directory: str,
    pattern: Optional[str] = None,
    recursive: bool = False,
    extensions: Optional[Set[str]] = None,
) -> Iterator[Path]:
    """Find files in a directory matching a pattern or extensions.
    
    Args:
        directory: Directory to search
        pattern: Glob pattern (e.g., "*.png", "frame_*.jpg")
        recursive: If True, search subdirectories recursively
        extensions: Set of file extensions to match (e.g., {".png", ".jpg"})
    
    Yields:
        Path: Matching file paths
    
    Example:
        >>> # Find all PNG files
        >>> for file in find_files("C:\\Images", extensions={".png"}):
        ...     print(file)
        
        >>> # Find files matching pattern
        >>> for file in find_files("C:\\Images", pattern="frame_*.png"):
        ...     print(file)
    """
    root = validate_directory(directory)
    
    if pattern:
        if recursive:
            files = root.rglob(pattern)
        else:
            files = root.glob(pattern)
        
        for file_path in files:
            if file_path.is_file():
                yield file_path
    
    elif extensions:
        if recursive:
            all_files = root.rglob("*")
        else:
            all_files = root.glob("*")
        
        for file_path in all_files:
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                yield file_path
    
    else:
        # No filter, return all files
        if recursive:
            all_files = root.rglob("*")
        else:
            all_files = root.glob("*")
        
        for file_path in all_files:
            if file_path.is_file():
                yield file_path


def find_image_files(
    directory: str,
    recursive: bool = False,
    extensions: Optional[Set[str]] = None,
) -> Iterator[Path]:
    """Find image files in a directory.
    
    Convenience function for finding image files with common extensions.
    
    Args:
        directory: Directory to search
        recursive: If True, search subdirectories recursively
        extensions: Optional set of extensions. If None, uses IMAGE_EXTENSIONS
    
    Yields:
        Path: Image file paths
    
    Example:
        >>> for img in find_image_files("C:\\Images", recursive=True):
        ...     print(img)
    """
    if extensions is None:
        extensions = IMAGE_EXTENSIONS
    
    yield from find_files(directory, extensions=extensions, recursive=recursive)


def get_file_size(path: str) -> int:
    """Get file size in bytes.
    
    Args:
        path: File path
    
    Returns:
        int: File size in bytes
    
    Raises:
        ValueError: If path doesn't exist or is not a file
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise ValueError(f"File does not exist: {path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    
    return file_path.stat().st_size


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        str: Formatted size string (e.g., "1.5 MB")
    
    Example:
        >>> format_file_size(1572864)
        '1.5 MB'
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"


def ensure_directory(path: str) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
    
    Returns:
        Path: Path object for the directory
    
    Example:
        >>> ensure_directory("C:\\Users\\ZilKit\\output")
    """
    dir_path = normalize_path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def is_safe_path(path: str, base_dir: Optional[str] = None) -> bool:
    """Check if a path is safe (doesn't escape base directory).
    
    Useful for preventing directory traversal attacks.
    
    Args:
        path: Path to check
        base_dir: Base directory. If None, uses current working directory
    
    Returns:
        bool: True if path is safe, False otherwise
    
    Example:
        >>> is_safe_path("subdir/file.txt", base_dir="C:\\Users")
        True
        >>> is_safe_path("..\\..\\etc\\passwd", base_dir="C:\\Users")
        False
    """
    try:
        normalized_path = normalize_path(path)
        
        if base_dir:
            base = normalize_path(base_dir)
        else:
            base = Path.cwd()
        
        # Check if the normalized path is within the base directory
        try:
            normalized_path.relative_to(base)
            return True
        except ValueError:
            return False
    
    except Exception:
        return False


def get_relative_path(path: str, base_dir: str) -> str:
    """Get relative path from a base directory.
    
    Args:
        path: Target path
        base_dir: Base directory
    
    Returns:
        str: Relative path string
    
    Example:
        >>> get_relative_path("C:\\Users\\Test\\file.txt", "C:\\Users")
        'Test\\file.txt'
    """
    target = normalize_path(path)
    base = normalize_path(base_dir)
    
    try:
        return str(target.relative_to(base))
    except ValueError:
        return str(target)


def list_files_sorted(
    directory: str,
    pattern: Optional[str] = None,
    recursive: bool = False,
) -> List[Path]:
    """List files sorted by name.
    
    Args:
        directory: Directory to list
        pattern: Optional glob pattern
        recursive: If True, search recursively
    
    Returns:
        List[Path]: Sorted list of file paths
    
    Example:
        >>> files = list_files_sorted("C:\\Images", pattern="*.png")
    """
    files = list(find_files(directory, pattern=pattern, recursive=recursive))
    return sorted(files)


def get_directory_size(directory: str) -> int:
    """Calculate total size of all files in a directory.
    
    Args:
        directory: Directory path
    
    Returns:
        int: Total size in bytes
    
    Example:
        >>> size = get_directory_size("C:\\Users\\Documents")
        >>> print(format_file_size(size))
    """
    total_size = 0
    root = validate_directory(directory)
    
    for file_path in root.rglob("*"):
        if file_path.is_file():
            try:
                total_size += file_path.stat().st_size
            except (OSError, PermissionError):
                # Skip files we can't access
                continue
    
    return total_size

