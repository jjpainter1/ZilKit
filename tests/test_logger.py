"""Tests for logger module."""

import logging
import os
import tempfile
from pathlib import Path

import pytest

from zilkit.utils.logger import get_log_dir, get_log_level, get_logger, setup_logger


def test_get_log_dir():
    """Test that log directory is created correctly."""
    log_dir = get_log_dir()
    assert isinstance(log_dir, Path)
    assert log_dir.exists()
    assert log_dir.is_dir()


def test_get_log_level():
    """Test log level detection from environment."""
    # Test default (no env var)
    original = os.environ.pop("ZILKIT_DEBUG", None)
    level = get_log_level()
    assert level in (logging.DEBUG, logging.INFO)
    
    # Test debug mode enabled
    os.environ["ZILKIT_DEBUG"] = "1"
    level = get_log_level()
    assert level == logging.DEBUG
    
    # Test debug mode disabled
    os.environ["ZILKIT_DEBUG"] = "0"
    level = get_log_level()
    assert level == logging.INFO
    
    # Restore original
    if original:
        os.environ["ZILKIT_DEBUG"] = original
    elif "ZILKIT_DEBUG" in os.environ:
        del os.environ["ZILKIT_DEBUG"]


def test_setup_logger_console_only():
    """Test logger setup with console output only."""
    logger = setup_logger(name="test_console", console_output=True, file_output=False)
    assert logger.name == "test_console"
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.Handler)


def test_setup_logger_file_only(tmp_path):
    """Test logger setup with file output only."""
    log_file = str(tmp_path / "test.log")
    logger = setup_logger(
        name="test_file",
        log_file=log_file,
        console_output=False,
        file_output=True,
    )
    assert logger.name == "test_file"
    assert len(logger.handlers) == 1
    
    # Test that logging works
    logger.info("Test message")
    assert Path(log_file).exists()
    assert "Test message" in Path(log_file).read_text()


def test_setup_logger_both(tmp_path):
    """Test logger setup with both console and file output."""
    log_file = str(tmp_path / "test.log")
    logger = setup_logger(
        name="test_both",
        log_file=log_file,
        console_output=True,
        file_output=True,
    )
    assert logger.name == "test_both"
    assert len(logger.handlers) == 2
    
    # Test that logging works
    logger.info("Test message")
    assert Path(log_file).exists()
    assert "Test message" in Path(log_file).read_text()


def test_get_logger():
    """Test get_logger convenience function."""
    logger = get_logger("test_module")
    assert logger.name == "test_module"
    assert len(logger.handlers) > 0


def test_logger_no_duplicate_handlers():
    """Test that calling setup_logger twice doesn't create duplicate handlers."""
    logger1 = setup_logger(name="test_dup", console_output=True, file_output=False)
    handler_count_1 = len(logger1.handlers)
    
    logger2 = setup_logger(name="test_dup", console_output=True, file_output=False)
    handler_count_2 = len(logger2.handlers)
    
    # Should be the same logger instance
    assert logger1 is logger2
    # Should not have duplicate handlers
    assert handler_count_1 == handler_count_2


def test_logger_levels():
    """Test that different log levels work correctly."""
    logger = setup_logger(name="test_levels", console_output=False, file_output=False)
    logger.setLevel(logging.DEBUG)
    
    # All these should work without raising exceptions
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

