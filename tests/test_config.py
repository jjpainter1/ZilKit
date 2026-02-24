"""Tests for config module."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zilkit.config import Config, get_config, get_config_dir, get_config_file, reset_config


def test_get_config_dir():
    """Test getting config directory."""
    config_dir = get_config_dir()
    assert isinstance(config_dir, Path)
    assert "ZilKit" in str(config_dir)


def test_get_config_file():
    """Test getting config file path."""
    config_file = get_config_file()
    assert isinstance(config_file, Path)
    assert config_file.name == "config.json"


def test_config_load_save(tmp_path):
    """Test loading and saving configuration."""
    config_file = tmp_path / "config.json"
    config = Config(config_file=config_file)
    
    # Set a value
    config.set("test_key", "test_value")
    
    # Create new config instance to test loading
    config2 = Config(config_file=config_file)
    assert config2.get("test_key") == "test_value"


def test_config_get_set(tmp_path):
    """Test getting and setting config values."""
    config_file = tmp_path / "config.json"
    config = Config(config_file=config_file)
    
    # Test default value
    assert config.get("nonexistent", "default") == "default"
    
    # Test setting and getting
    config.set("test", 123)
    assert config.get("test") == 123


def test_config_load_invalid_json(tmp_path):
    """Test loading invalid JSON file."""
    config_file = tmp_path / "config.json"
    config_file.write_text("invalid json {")
    
    # Should not raise, just use defaults
    config = Config(config_file=config_file)
    assert config.get("test", "default") == "default"


def test_config_load_nonexistent():
    """Test loading non-existent config file."""
    config_file = Path("/nonexistent/path/config.json")
    config = Config(config_file=config_file)
    
    # Should use defaults
    assert config.get("test", "default") == "default"


@patch("shutil.which")
def test_find_ffmpeg_in_path(mock_which):
    """Test finding FFmpeg in system PATH."""
    mock_which.return_value = "/usr/bin/ffmpeg"
    
    config = Config()
    ffmpeg_path = config.find_ffmpeg()
    
    assert ffmpeg_path == "/usr/bin/ffmpeg"
    mock_which.assert_called_once_with("ffmpeg")


@patch("os.getenv")
@patch("shutil.which")
def test_find_ffmpeg_env_variable(mock_which, mock_getenv):
    """Test finding FFmpeg via environment variable."""
    mock_getenv.return_value = "/custom/path/ffmpeg.exe"
    
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.is_file", return_value=True):
            with patch("pathlib.Path.resolve", return_value=Path("/custom/path/ffmpeg.exe")):
                config = Config()
                ffmpeg_path = config.find_ffmpeg()
                
                assert ffmpeg_path is not None
                mock_getenv.assert_called_with("ZILKIT_FFMPEG_PATH")


def test_find_ffmpeg_in_config(tmp_path):
    """Test finding FFmpeg path from config file."""
    config_file = tmp_path / "config.json"
    
    # Create a fake FFmpeg executable
    fake_ffmpeg = tmp_path / "ffmpeg.exe"
    fake_ffmpeg.write_text("fake")
    
    config = Config(config_file=config_file)
    config.set("ffmpeg_path", str(fake_ffmpeg))
    
    # Find should use config
    found_path = config.find_ffmpeg()
    assert found_path is not None


@patch("subprocess.run")
def test_validate_ffmpeg_success(mock_run):
    """Test successful FFmpeg validation."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "ffmpeg version 4.4.0\nCopyright..."
    mock_run.return_value = mock_result
    
    config = Config()
    result = config.validate_ffmpeg("/usr/bin/ffmpeg")
    
    assert result is True
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_validate_ffmpeg_failure(mock_run):
    """Test FFmpeg validation failure."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Error: ffmpeg not found"
    mock_run.return_value = mock_result
    
    config = Config()
    result = config.validate_ffmpeg("/usr/bin/ffmpeg")
    
    assert result is False


@patch("subprocess.run")
def test_validate_ffmpeg_timeout(mock_run):
    """Test FFmpeg validation timeout."""
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 5)
    
    config = Config()
    result = config.validate_ffmpeg("/usr/bin/ffmpeg")
    
    assert result is False


def test_set_ffmpeg_path_invalid(tmp_path):
    """Test setting invalid FFmpeg path."""
    config_file = tmp_path / "config.json"
    config = Config(config_file=config_file)
    
    # Non-existent path
    result = config.set_ffmpeg_path("/nonexistent/ffmpeg")
    assert result is False


def test_get_ffmpeg_path():
    """Test getting FFmpeg path."""
    config = Config()
    
    # Mock find_ffmpeg and validate_ffmpeg
    with patch.object(config, "find_ffmpeg", return_value="/usr/bin/ffmpeg"):
        with patch.object(config, "validate_ffmpeg", return_value=True):
            path = config.get_ffmpeg_path()
            assert path == "/usr/bin/ffmpeg"


def test_is_ffmpeg_available():
    """Test checking FFmpeg availability."""
    config = Config()
    
    with patch.object(config, "get_ffmpeg_path", return_value="/usr/bin/ffmpeg"):
        assert config.is_ffmpeg_available() is True
    
    with patch.object(config, "get_ffmpeg_path", return_value=None):
        assert config.is_ffmpeg_available() is False


def test_get_ffmpeg_version():
    """Test getting FFmpeg version."""
    config = Config()
    
    with patch.object(config, "get_ffmpeg_path", return_value="/usr/bin/ffmpeg"):
        with patch.object(config, "validate_ffmpeg", return_value=True):
            config._ffmpeg_version = "ffmpeg version 4.4.0"
            version = config.get_ffmpeg_version()
            assert version == "ffmpeg version 4.4.0"


def test_get_config_singleton():
    """Test that get_config returns a singleton."""
    reset_config()
    config1 = get_config()
    config2 = get_config()
    
    assert config1 is config2


def test_reset_config():
    """Test resetting global config."""
    config1 = get_config()
    reset_config()
    config2 = get_config()
    
    # Should be different instances
    assert config1 is not config2

