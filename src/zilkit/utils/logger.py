"""Logging utilities for ZilKit.

This module provides a centralized logging configuration using Rich for
beautiful console output and file-based logging for debugging.
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def get_log_dir() -> Path:
    """Get the directory for log files.
    
    Returns:
        Path: Path to the log directory (user's AppData/Local/ZilKit/logs)
    """
    # Use Windows AppData Local directory for logs
    appdata_local = os.getenv("LOCALAPPDATA", os.path.expanduser("~"))
    log_dir = Path(appdata_local) / "ZilKit" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_level() -> int:
    """Get the log level from environment variable or default to INFO.
    
    Returns:
        int: Logging level constant
    """
    debug_mode = os.getenv("ZILKIT_DEBUG", "0").lower() in ("1", "true", "yes")
    return logging.DEBUG if debug_mode else logging.INFO


def setup_logger(
    name: str = "zilkit",
    log_file: Optional[str] = None,
    log_level: Optional[int] = None,
    console_output: bool = True,
    file_output: bool = True,
) -> logging.Logger:
    """Configure and return a logger with Rich console and file handlers.
    
    Args:
        name: Logger name (default: "zilkit")
        log_file: Path to log file. If None, uses default location in AppData
        log_level: Logging level. If None, uses environment variable or INFO
        console_output: Whether to enable console output (default: True)
        file_output: Whether to enable file output (default: True)
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        >>> logger = setup_logger()
        >>> logger.info("Application started")
    """
    logger = logging.getLogger(name)
    
    # Don't add handlers if they already exist (prevents duplicate logs)
    if logger.handlers:
        return logger
    
    # Set log level
    if log_level is None:
        log_level = get_log_level()
    logger.setLevel(log_level)
    
    # Console handler with Rich formatting
    if console_output:
        console = Console()
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_output:
        if log_file is None:
            log_dir = get_log_dir()
            log_file = str(log_dir / "zilkit.log")
        
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler (10MB max, 5 backup files)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        
        # File formatter (more detailed than console)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance, creating it if it doesn't exist.
    
    This is a convenience function that returns a logger with default
    configuration. Use this in your modules instead of logging.getLogger().
    
    Args:
        name: Logger name. If None, uses "zilkit"
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        >>> from zilkit.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Module loaded")
    """
    if name is None:
        name = "zilkit"
    
    logger = logging.getLogger(name)
    
    # If logger doesn't have handlers, set it up
    if not logger.handlers:
        setup_logger(name=name)
    
    return logger

