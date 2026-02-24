"""Configuration management for ZilKit.

This module handles configuration settings, FFmpeg detection, and user preferences.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from zilkit.utils.logger import get_logger

logger = get_logger(__name__)


def get_config_dir() -> Path:
    """Get the directory for configuration files.
    
    Returns:
        Path: Path to the config directory (user's AppData/Local/ZilKit)
    """
    appdata_local = os.getenv("LOCALAPPDATA", os.path.expanduser("~"))
    config_dir = Path(appdata_local) / "ZilKit"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    """Get the path to the configuration file.
    
    Returns:
        Path: Path to config.json
    """
    return get_config_dir() / "config.json"


def get_presets_file() -> Path:
    """Get the path to the presets file.
    
    Returns:
        Path: Path to presets.json (in package directory)
    """
    # Get the package directory (src/zilkit)
    package_dir = Path(__file__).parent
    return package_dir / "presets.json"


class Config:
    """Configuration manager for ZilKit.
    
    Handles FFmpeg detection, validation, and user preferences.
    """
    
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_file: Optional path to config file. If None, uses default location.
        """
        self.config_file = config_file or get_config_file()
        self._config: Dict = {}
        self._presets: Dict = {}
        self._ffmpeg_path: Optional[str] = None
        self._ffmpeg_version: Optional[str] = None
        self.load()
        self.load_presets()
    
    def load(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                logger.debug(f"Loaded configuration from {self.config_file}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config file: {e}. Using defaults.")
                self._config = {}
        else:
            self._config = {}
            logger.debug("No config file found, using defaults")
    
    def load_presets(self) -> None:
        """Load presets from presets.json file."""
        presets_file = get_presets_file()
        if presets_file.exists():
            try:
                with open(presets_file, "r", encoding="utf-8") as f:
                    presets_data = json.load(f)
                    self._presets = presets_data.get("presets", {})
                logger.debug(f"Loaded {len(self._presets)} presets from {presets_file}")
                
                # Set default preset to h264-mp4 if not already set
                if not self.get("default_preset") and "h264-mp4" in self._presets:
                    self.set("default_preset", "h264-mp4")
                    logger.debug("Set default preset to h264-mp4")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load presets file: {e}. Using empty presets.")
                self._presets = {}
        else:
            logger.warning(f"Presets file not found: {presets_file}")
            self._presets = {}
    
    def save(self) -> None:
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2)
            logger.debug(f"Saved configuration to {self.config_file}")
        except IOError as e:
            logger.error(f"Failed to save config file: {e}")
    
    def get(self, key: str, default=None):
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
        
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value (must be JSON serializable)
        """
        self._config[key] = value
        self.save()
    
    def find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable in system PATH or configured path.
        
        Checks in this order:
        1. Environment variable ZILKIT_FFMPEG_PATH
        2. Config file setting 'ffmpeg_path'
        3. System PATH
        
        Returns:
            Path to FFmpeg executable, or None if not found
        """
        # Check environment variable first
        env_path = os.getenv("ZILKIT_FFMPEG_PATH")
        if env_path:
            ffmpeg_path = Path(env_path)
            if ffmpeg_path.exists() and ffmpeg_path.is_file():
                logger.debug(f"Found FFmpeg via environment variable: {ffmpeg_path}")
                return str(ffmpeg_path.resolve())
        
        # Check config file
        config_path = self.get("ffmpeg_path")
        if config_path:
            ffmpeg_path = Path(config_path)
            if ffmpeg_path.exists() and ffmpeg_path.is_file():
                logger.debug(f"Found FFmpeg via config file: {ffmpeg_path}")
                return str(ffmpeg_path.resolve())
        
        # Check system PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            logger.debug(f"Found FFmpeg in system PATH: {ffmpeg_path}")
            return ffmpeg_path
        
        logger.warning("FFmpeg not found in PATH or configuration")
        return None
    
    def validate_ffmpeg(self, ffmpeg_path: Optional[str] = None) -> bool:
        """Validate that FFmpeg is working correctly.
        
        Args:
            ffmpeg_path: Optional path to FFmpeg. If None, uses find_ffmpeg()
        
        Returns:
            True if FFmpeg is valid, False otherwise
        """
        if ffmpeg_path is None:
            ffmpeg_path = self.find_ffmpeg()
        
        if not ffmpeg_path:
            return False
        
        try:
            # Run ffmpeg -version to validate
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                # Extract version from output
                version_line = result.stdout.split("\n")[0]
                self._ffmpeg_version = version_line
                logger.debug(f"FFmpeg validated: {version_line}")
                return True
            else:
                logger.warning(f"FFmpeg validation failed: {result.stderr}")
                return False
        
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.warning(f"FFmpeg validation error: {e}")
            return False
    
    def get_ffmpeg_path(self) -> Optional[str]:
        """Get the FFmpeg executable path, validating it if necessary.
        
        Returns:
            Path to FFmpeg executable, or None if not found/valid
        """
        if self._ffmpeg_path is None:
            ffmpeg_path = self.find_ffmpeg()
            if ffmpeg_path and self.validate_ffmpeg(ffmpeg_path):
                self._ffmpeg_path = ffmpeg_path
            else:
                self._ffmpeg_path = None
        
        return self._ffmpeg_path
    
    def set_ffmpeg_path(self, path: str) -> bool:
        """Set the FFmpeg path in configuration.
        
        Args:
            path: Path to FFmpeg executable
        
        Returns:
            True if path is valid and was set, False otherwise
        """
        ffmpeg_path = Path(path)
        
        if not ffmpeg_path.exists():
            logger.error(f"FFmpeg path does not exist: {path}")
            return False
        
        if not ffmpeg_path.is_file():
            logger.error(f"FFmpeg path is not a file: {path}")
            return False
        
        if not self.validate_ffmpeg(str(ffmpeg_path.resolve())):
            logger.error(f"FFmpeg validation failed for: {path}")
            return False
        
        self.set("ffmpeg_path", str(ffmpeg_path.resolve()))
        self._ffmpeg_path = str(ffmpeg_path.resolve())
        logger.info(f"FFmpeg path set to: {self._ffmpeg_path}")
        return True
    
    def get_ffmpeg_version(self) -> Optional[str]:
        """Get FFmpeg version string.
        
        Returns:
            FFmpeg version string, or None if not available
        """
        if self._ffmpeg_version is None:
            ffmpeg_path = self.get_ffmpeg_path()
            if ffmpeg_path:
                self.validate_ffmpeg(ffmpeg_path)
        
        return self._ffmpeg_version
    
    def is_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available and valid.
        
        Returns:
            True if FFmpeg is available, False otherwise
        """
        return self.get_ffmpeg_path() is not None
    
    def get_ffmpeg_encoding_settings(self) -> Dict:
        """Get FFmpeg encoding settings from config.
        
        Returns:
            Dict with encoding settings:
            - resolution_scale: float (1.0 = full res, 0.5 = half res, etc.)
            - crf: int (Constant Rate Factor, 18-28 recommended, lower = higher quality)
            - preset: str (encoding speed preset: ultrafast, fast, medium, slow, etc.)
            - pixel_format: str (pixel format, default: yuv420p)
            - framerate: Optional[int] (output framerate, default: 30fps, None = use input)
        
        Example:
            >>> settings = config.get_ffmpeg_encoding_settings()
            >>> # Use settings['resolution_scale'] to scale resolution
        """
        return {
            "resolution_scale": self.get("ffmpeg_resolution_scale", 1.0),
            "crf": self.get("ffmpeg_crf", 23),
            "preset": self.get("ffmpeg_preset", "medium"),
            "pixel_format": self.get("ffmpeg_pixel_format", "yuv420p"),
            "framerate": self.get("ffmpeg_framerate", 30),  # Default to 30fps
        }
    
    def set_ffmpeg_encoding_settings(
        self,
        resolution_scale: Optional[float] = None,
        crf: Optional[int] = None,
        preset: Optional[str] = None,
        pixel_format: Optional[str] = None,
        framerate: Optional[int] = None,
    ) -> None:
        """Set FFmpeg encoding settings.
        
        Args:
            resolution_scale: Resolution scale factor (1.0 = full, 0.5 = half, etc.)
            crf: Constant Rate Factor (18-28, lower = higher quality)
            preset: Encoding speed preset (ultrafast, fast, medium, slow, etc.)
            pixel_format: Pixel format (yuv420p, yuv422p, etc.)
            framerate: Output framerate (None = use input framerate)
        """
        if resolution_scale is not None:
            self.set("ffmpeg_resolution_scale", float(resolution_scale))
        if crf is not None:
            self.set("ffmpeg_crf", int(crf))
        if preset is not None:
            self.set("ffmpeg_preset", str(preset))
        if pixel_format is not None:
            self.set("ffmpeg_pixel_format", str(pixel_format))
        if framerate is not None:
            self.set("ffmpeg_framerate", int(framerate))
    
    def get_presets(self) -> Dict:
        """Get all available presets.
        
        Returns:
            Dict of preset key -> preset configuration
        """
        return self._presets.copy()
    
    def get_preset(self, preset_key: str) -> Optional[Dict]:
        """Get a specific preset by key.
        
        Args:
            preset_key: Key of the preset to retrieve
        
        Returns:
            Preset configuration dict, or None if not found
        """
        return self._presets.get(preset_key)
    
    def get_default_preset(self) -> Optional[str]:
        """Get the default preset key.
        
        Returns:
            Preset key string, or None if not set
        """
        return self.get("default_preset")
    
    def set_default_preset(self, preset_key: str) -> bool:
        """Set the default preset.
        
        Args:
            preset_key: Key of the preset to set as default
        
        Returns:
            True if preset exists and was set, False otherwise
        """
        if preset_key not in self._presets:
            logger.error(f"Preset not found: {preset_key}")
            return False
        self.set("default_preset", preset_key)
        logger.info(f"Default preset set to: {preset_key}")
        return True
    
    def get_default_multi_output_config(self) -> Optional[Dict]:
        """Get the default multi-output configuration.
        
        Returns:
            Dict with multi-output configuration, or None if not configured:
            - user_initials: str
            - hap_chunk_count: int (for HAP codecs)
            - conversions: List[Dict] with:
              - preset: str (preset key)
              - resolution: str (full, half, quarter, or custom float)
              - framerate: int
              - filename_suffix: str
        """
        return self.get("default_multi_output_config")
    
    def set_default_multi_output_config(self, config: Dict) -> None:
        """Set the default multi-output configuration.
        
        Args:
            config: Dict with multi-output configuration
        """
        self.set("default_multi_output_config", config)
        logger.info("Default multi-output configuration updated")
    
    def get_user_initials(self) -> Optional[str]:
        """Get user initials from multi-output config.
        
        Returns:
            User initials string, or None if not set
        """
        multi_config = self.get_default_multi_output_config()
        if multi_config:
            return multi_config.get("user_initials")
        return None
    
    def get_hap_chunk_count(self) -> int:
        """Get HAP chunk count setting.
        
        Returns:
            HAP chunk count (default: 1)
        """
        multi_config = self.get_default_multi_output_config()
        if multi_config:
            return multi_config.get("hap_chunk_count", 1)
        return 1
    
    def get_preset_overrides(self) -> Dict:
        """Get preset-specific overrides.
        
        Returns:
            Dict mapping preset_key -> override settings (framerate, resolution, etc.)
        """
        return self.get("preset_overrides", {})
    
    def set_preset_override(self, preset_key: str, overrides: Dict) -> None:
        """Set overrides for a specific preset.
        
        Args:
            preset_key: Key of the preset to override
            overrides: Dict with override settings (framerate, resolution, alpha, etc.)
        """
        preset_overrides = self.get_preset_overrides()
        preset_overrides[preset_key] = overrides
        self.set("preset_overrides", preset_overrides)
        logger.info(f"Set overrides for preset '{preset_key}'")
    
    def get_preset_override(self, preset_key: str) -> Optional[Dict]:
        """Get overrides for a specific preset.
        
        Args:
            preset_key: Key of the preset
        
        Returns:
            Dict with override settings, or None if no overrides
        """
        preset_overrides = self.get_preset_overrides()
        return preset_overrides.get(preset_key)
    
    def clear_preset_override(self, preset_key: str) -> None:
        """Clear overrides for a specific preset.
        
        Args:
            preset_key: Key of the preset
        """
        preset_overrides = self.get_preset_overrides()
        if preset_key in preset_overrides:
            del preset_overrides[preset_key]
            self.set("preset_overrides", preset_overrides)
            logger.info(f"Cleared overrides for preset '{preset_key}'")
    
    def get_global_overrides(self) -> Dict:
        """Get global override settings (applies to all presets except multi-output).
        
        Returns:
            Dict with global override settings (framerate, resolution, alpha, etc.)
        """
        return self.get("global_overrides", {})
    
    def set_global_overrides(self, overrides: Dict) -> None:
        """Set global override settings.
        
        Args:
            overrides: Dict with global override settings
        """
        self.set("global_overrides", overrides)
        logger.info("Set global override settings")
    
    def clear_global_overrides(self) -> None:
        """Clear all global override settings."""
        self.set("global_overrides", {})
        logger.info("Cleared global override settings")
    
    def get_effective_preset_settings(self, preset_key: str, for_multi_output: bool = False) -> Dict:
        """Get effective settings for a preset, applying overrides.
        
        Priority: global override > preset override > preset defaults
        (Global overrides can override individual preset overrides)
        
        Args:
            preset_key: Key of the preset
            for_multi_output: If True, global overrides are NOT applied
        
        Returns:
            Dict with effective settings
        """
        preset = self.get_preset(preset_key)
        if not preset:
            return {}
        
        # Start with preset defaults
        effective = preset.copy()
        
        # Apply preset-specific overrides first
        preset_overrides = self.get_preset_override(preset_key)
        if preset_overrides:
            for key, value in preset_overrides.items():
                if value is not None:  # Only apply if value is set
                    effective[key] = value
        
        # Apply global overrides (unless multi-output) - these override preset overrides
        if not for_multi_output:
            global_overrides = self.get_global_overrides()
            for key, value in global_overrides.items():
                if value is not None:  # Only apply if value is set
                    effective[key] = value
        
        return effective


# Global config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.
    
    Returns:
        Config: Global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reset_config() -> None:
    """Reset the global configuration instance (useful for testing)."""
    global _config_instance
    _config_instance = None
