"""Windows registry operations for ZilKit context menu integration.

This module handles adding and removing ZilKit entries from the Windows context menu.
"""

import sys
from pathlib import Path
from typing import Optional

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore

from zilkit.config import get_config
from zilkit.utils.logger import get_logger

logger = get_logger(__name__)


def get_python_exe() -> str:
    """Get the path to the Python executable.
    
    Returns:
        Path to python.exe
    """
    return sys.executable


def get_main_script_path() -> Path:
    """Get the path to the main.py script.
    
    Returns:
        Path to main.py
    """
    # Get the directory where this module is located
    zilkit_dir = Path(__file__).parent
    return zilkit_dir / "main.py"


def register_context_menu(
    python_exe: Optional[str] = None,
    script_path: Optional[Path] = None,
) -> bool:
    """Register ZilKit in Windows context menu using CommandStore pattern.
    
    Creates the following structure:
    HKEY_CLASSES_ROOT\Directory\Background\shell\ZilKit
        - SubCommands: ZilKit.FFmpeg;ZilKit.Shortcuts;ZilKit.Utilities
        - MUIVerb: ZilKit
    
    Submenu items are registered in CommandStore to prevent them from
    appearing as separate top-level menu items.
    
    Args:
        python_exe: Path to Python executable (default: sys.executable)
        script_path: Path to main.py script (default: auto-detect)
    
    Returns:
        True if successful, False otherwise
    """
    if winreg is None:
        logger.error("winreg module not available (not on Windows?)")
        return False
    
    try:
        python_exe = python_exe or get_python_exe()
        script_path = script_path or get_main_script_path()
        
        # Ensure script path is absolute
        script_path = script_path.resolve()
        
        if not script_path.exists():
            logger.error(f"Main script not found: {script_path}")
            return False
        
        # Base registry path for Directory Background context menu
        base_key_path = r"Directory\Background\shell\ZilKit"
        
        # Create main ZilKit menu entry
        # Match the pattern: SubCommands uses simple names like "FFmpeg" (not "ZilKitFFmpeg")
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, base_key_path) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "ZilKit")
            # SubCommands uses simple names (matching CommandStore keys exactly)
            # Order: FFmpeg, Utilities, Shortcuts
            winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "ZilKitFFmpeg;ZilKitUtilities;ZilKitShortcuts")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f'"{python_exe}",0')
        
        # Register submenus using CommandStore pattern
        # This prevents them from appearing as separate top-level items
        _register_commandstore_submenus(python_exe, script_path)
        
        logger.info("Successfully registered ZilKit in Windows context menu")
        return True
        
    except Exception as e:
        logger.exception(f"Error registering context menu: {e}")
        return False


def _create_key_with_access(hkey, path):
    """Create a registry key with explicit 64-bit access.
    
    This ensures keys are created in the correct registry view on 64-bit Windows.
    """
    return winreg.CreateKeyEx(
        hkey, 
        path, 
        0, 
        winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
    )


def _register_commandstore_submenus(python_exe: str, script_path: Path) -> None:
    """Register all submenus using CommandStore pattern for proper nesting.
    
    Uses HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell
    to register submenu items. This prevents them from appearing as separate
    top-level menu items.
    
    Also registers in HKEY_CURRENT_USER as a fallback for better compatibility.
    
    Pattern:
    - Main menu references submenu keys in SubCommands (e.g., "ZilKit.FFmpeg")
    - Submenu keys are registered in CommandStore with their own SubCommands
    - Action items are registered in CommandStore with command subkeys
    """
    # CommandStore base path
    commandstore_base = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell"
    
    logger.info("Registering CommandStore submenus...")
    
    # Register in both HKEY_LOCAL_MACHINE and HKEY_CURRENT_USER for maximum compatibility
    hives_to_register = [
        (winreg.HKEY_LOCAL_MACHINE, "HKLM"),
        (winreg.HKEY_CURRENT_USER, "HKCU"),
    ]
    
    for hive, hive_name in hives_to_register:
        logger.info(f"Registering in {hive_name}...")
        try:
            _register_commandstore_in_hive(hive, commandstore_base, python_exe, script_path)
            logger.info(f"Successfully registered in {hive_name}")
        except PermissionError:
            if hive == winreg.HKEY_LOCAL_MACHINE:
                logger.warning(f"Could not write to {hive_name} (admin required), trying HKCU only")
            else:
                raise
        except Exception as e:
            logger.error(f"Failed to register in {hive_name}: {e}")
            if hive == winreg.HKEY_LOCAL_MACHINE:
                logger.info("Continuing with HKCU registration...")
            else:
                raise
    
    logger.info("All CommandStore submenus registered successfully (FFmpeg, Utilities, Shortcuts)")


def _register_commandstore_in_hive(hive, commandstore_base: str, python_exe: str, script_path: Path) -> None:
    """Register all CommandStore entries in a specific registry hive."""
    from zilkit.config import get_config
    
    config = get_config()
    presets = config.get_presets()
    preset_list = list(presets.items())
    
    # Register FFmpeg submenu in CommandStore
    # Menu structure: Default, Choose Preset (submenu), Multi-Output, Recursive, Configure
    try:
        logger.debug("Registering FFmpeg submenu...")
        ffmpeg_key = f"{commandstore_base}\\ZilKitFFmpeg"
        with _create_key_with_access(hive, ffmpeg_key) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "FFmpeg")
            # Build SubCommands list: Default, Choose Preset submenu, Multi-Output, Recursive, Configure
            subcommands = ["ZilKitFFmpeg1", "ZilKitFFmpeg2", "ZilKitFFmpeg3", "ZilKitFFmpeg4", "ZilKitFFmpeg5"]
            winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, ";".join(subcommands))
        logger.debug("FFmpeg submenu registered successfully")
    except PermissionError:
        logger.warning("Could not write to HKEY_LOCAL_MACHINE (admin required)")
        raise
    
    # Register FFmpeg actions in CommandStore
    try:
        logger.debug("Registering FFmpeg actions...")
        
        # ZilKitFFmpeg1: Encode To Movie (Default)
        convert_default_key = f"{commandstore_base}\\ZilKitFFmpeg1"
        with _create_key_with_access(hive, convert_default_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Encode To Movie (Default)")
            with winreg.CreateKey(key, "command") as cmd_key:
                command = f'"{python_exe}" "{script_path}" ffmpeg encode-default'
                winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
        logger.debug("ZilKitFFmpeg1 registered successfully")
        
        # ZilKitFFmpeg2: Encode To Movie (Choose Preset) - this is a submenu
        choose_preset_key = f"{commandstore_base}\\ZilKitFFmpeg2"
        with _create_key_with_access(hive, choose_preset_key) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "Encode To Movie (Choose Preset)")
            # Generate subcommands for each preset
            preset_subcommands = []
            for idx, (preset_key, preset) in enumerate(preset_list, 1):
                preset_action_key = f"ZilKitFFmpeg2Preset{idx}"
                preset_subcommands.append(preset_action_key)
                # Register each preset action
                preset_action_path = f"{commandstore_base}\\{preset_action_key}"
                with _create_key_with_access(hive, preset_action_path) as preset_key_reg:
                    display_name = preset.get("display_name", preset_key)
                    winreg.SetValueEx(preset_key_reg, "", 0, winreg.REG_SZ, display_name)
                    with winreg.CreateKey(preset_key_reg, "command") as preset_cmd_key:
                        # Pass preset key as argument (escape quotes if needed)
                        # Use double quotes around preset key to handle spaces/special chars
                        escaped_preset = preset_key.replace('"', '\\"')
                        command = f'"{python_exe}" "{script_path}" ffmpeg encode-preset "{escaped_preset}"'
                        winreg.SetValueEx(preset_cmd_key, "", 0, winreg.REG_SZ, command)
            winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, ";".join(preset_subcommands))
        logger.debug(f"ZilKitFFmpeg2 registered successfully with {len(preset_list)} presets")
        
        # ZilKitFFmpeg3: Encode To Movie (Multi-Output)
        multi_output_key = f"{commandstore_base}\\ZilKitFFmpeg3"
        with _create_key_with_access(hive, multi_output_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Encode To Movie (Multi-Output)")
            with winreg.CreateKey(key, "command") as cmd_key:
                command = f'"{python_exe}" "{script_path}" ffmpeg encode-multi-output'
                winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
        logger.debug("ZilKitFFmpeg3 registered successfully")
        
        # ZilKitFFmpeg4: Encode To Movie (Recursive)
        recursive_key = f"{commandstore_base}\\ZilKitFFmpeg4"
        with _create_key_with_access(hive, recursive_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Encode To Movie (Recursive)")
            with winreg.CreateKey(key, "command") as cmd_key:
                command = f'"{python_exe}" "{script_path}" ffmpeg encode-recursive'
                winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
        logger.debug("ZilKitFFmpeg4 registered successfully")
        
        # ZilKitFFmpeg5: Configure Default Settings
        configure_key = f"{commandstore_base}\\ZilKitFFmpeg5"
        with _create_key_with_access(hive, configure_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Configure Default Settings")
            with winreg.CreateKey(key, "command") as cmd_key:
                command = f'"{python_exe}" "{script_path}" ffmpeg configure'
                winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
        logger.debug("ZilKitFFmpeg5 registered successfully")
        
        logger.debug("All FFmpeg actions registered successfully")
    except Exception as e:
        logger.error(f"Failed to register FFmpeg actions: {e}")
        raise
    
    # Register Utilities submenu in CommandStore
    try:
        logger.debug("Registering Utilities submenu...")
        utilities_key = f"{commandstore_base}\\ZilKitUtilities"
        with _create_key_with_access(hive, utilities_key) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "Utilities")
            # Build SubCommands list
            subcommands = ["ZilKitUtilities1"]
            winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, ";".join(subcommands))
        logger.debug("Utilities submenu registered successfully")
    except PermissionError:
        logger.warning("Could not write Utilities submenu to HKEY_LOCAL_MACHINE (admin required)")
        raise
    
    # Register Utilities actions in CommandStore
    try:
        logger.debug("Registering Utilities action: ZilKitUtilities1...")
        # ZilKitUtilities1: Remove Frame Padding
        remove_padding_key = f"{commandstore_base}\\ZilKitUtilities1"
        with _create_key_with_access(hive, remove_padding_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Remove Frame Padding")
            with winreg.CreateKey(key, "command") as cmd_key:
                command = f'"{python_exe}" "{script_path}" utilities remove-frame-padding'
                winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
        logger.debug("ZilKitUtilities1 registered successfully")
    except Exception as e:
        logger.error(f"Failed to register Utilities action ZilKitUtilities1: {e}")
        raise
    
    # Register Shortcuts submenu in CommandStore
    try:
        logger.debug("Registering Shortcuts submenu...")
        shortcuts_key = f"{commandstore_base}\\ZilKitShortcuts"
        with _create_key_with_access(hive, shortcuts_key) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "Shortcuts")
            # Build SubCommands list
            subcommands = ["ZilKitShortcuts1", "ZilKitShortcuts2", "ZilKitShortcuts3"]
            winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, ";".join(subcommands))
        logger.debug("Shortcuts submenu registered successfully")
    except PermissionError:
        logger.warning("Could not write Shortcuts submenu to HKEY_LOCAL_MACHINE (admin required)")
        raise
    
    # Register Shortcuts actions in CommandStore
    try:
        logger.debug("Registering Shortcuts actions...")
        # ZilKitShortcuts1: Empty Recycle Bin
        empty_bin_key = f"{commandstore_base}\\ZilKitShortcuts1"
        with _create_key_with_access(hive, empty_bin_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Empty Recycle Bin")
            with winreg.CreateKey(key, "command") as cmd_key:
                command = f'"{python_exe}" "{script_path}" shortcuts empty-recycle-bin'
                winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
        logger.debug("ZilKitShortcuts1 registered successfully")
        
        # ZilKitShortcuts2: Force Restart
        restart_key = f"{commandstore_base}\\ZilKitShortcuts2"
        with _create_key_with_access(hive, restart_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Force Restart")
            with winreg.CreateKey(key, "command") as cmd_key:
                command = f'"{python_exe}" "{script_path}" shortcuts restart'
                winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
        logger.debug("ZilKitShortcuts2 registered successfully")
        
        # ZilKitShortcuts3: Force Shutdown
        shutdown_key = f"{commandstore_base}\\ZilKitShortcuts3"
        with _create_key_with_access(hive, shutdown_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Force Shutdown")
            with winreg.CreateKey(key, "command") as cmd_key:
                command = f'"{python_exe}" "{script_path}" shortcuts shutdown'
                winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
        logger.debug("ZilKitShortcuts3 registered successfully")
        
        logger.debug("All Shortcuts actions registered successfully")
    except Exception as e:
        logger.error(f"Failed to register Shortcuts actions: {e}")
        raise


def _delete_registry_key_recursive(key_path: str, hkey=winreg.HKEY_CLASSES_ROOT) -> bool:
    """Recursively delete a registry key and all its subkeys.
    
    Args:
        key_path: Full registry path to delete
        hkey: Registry hive (HKEY_CLASSES_ROOT or HKEY_LOCAL_MACHINE)
        
    Returns:
        True if successful, False otherwise
    """
    if winreg is None:
        return False
    
    try:
        # Try to open the key to see if it exists and get subkeys
        subkeys = []
        try:
            with winreg.OpenKey(hkey, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                # Get all subkeys
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkeys.append(subkey_name)
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            # Key doesn't exist, that's okay
            return True
        
        # Recursively delete all subkeys first
        for subkey_name in subkeys:
            subkey_path = f"{key_path}\\{subkey_name}"
            _delete_registry_key_recursive(subkey_path, hkey)
        
        # Now delete the key itself
        winreg.DeleteKey(hkey, key_path)
        logger.debug(f"Deleted registry key: {hkey}\\{key_path}")
        return True
        
    except FileNotFoundError:
        # Key doesn't exist, that's okay
        return True
    except Exception as e:
        logger.warning(f"Error deleting registry key {key_path}: {e}")
        return False


def unregister_context_menu() -> bool:
    """Remove ZilKit from Windows context menu.
    
    This function removes ALL ZilKit-related registry entries from both
    HKEY_CLASSES_ROOT and HKEY_LOCAL_MACHINE (CommandStore).
    
    Returns:
        True if successful, False otherwise
    """
    if winreg is None:
        logger.error("winreg module not available (not on Windows?)")
        return False
    
    try:
        deleted_count = 0
        
        # Delete from HKEY_CLASSES_ROOT (main menu)
        hkcr_keys = [
            r"Directory\Background\shell\ZilKit",
        ]
        
        for key_path in hkcr_keys:
            if _delete_registry_key_recursive(key_path, hkey=winreg.HKEY_CLASSES_ROOT):
                deleted_count += 1
        
        # Delete from HKEY_LOCAL_MACHINE CommandStore (submenus and actions)
        # Use simple names to match the registration pattern
        commandstore_base = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell"
        
        # Build dynamic list of preset keys to delete (up to 50 presets)
        preset_keys = [f"{commandstore_base}\\ZilKitFFmpeg2Preset{i}" for i in range(1, 51)]
        
        commandstore_keys = preset_keys + [
            # FFmpeg actions (delete in reverse order)
            f"{commandstore_base}\\ZilKitFFmpeg5",  # Configure Default Settings
            f"{commandstore_base}\\ZilKitFFmpeg4",  # Encode To Movie (Recursive)
            f"{commandstore_base}\\ZilKitFFmpeg3",  # Encode To Movie (Multi-Output)
            f"{commandstore_base}\\ZilKitFFmpeg2",  # Encode To Movie (Choose Preset) - includes preset submenu
            f"{commandstore_base}\\ZilKitFFmpeg1",  # Encode To Movie (Default)
            f"{commandstore_base}\\ZilKitFFmpeg",    # FFmpeg submenu
            # Shortcuts actions (delete in reverse order)
            f"{commandstore_base}\\ZilKitShortcuts3",  # Force Shutdown
            f"{commandstore_base}\\ZilKitShortcuts2",  # Force Restart
            f"{commandstore_base}\\ZilKitShortcuts1",  # Empty Recycle Bin
            f"{commandstore_base}\\ZilKitShortcuts",   # Shortcuts submenu
            # Utilities
            f"{commandstore_base}\\ZilKitUtilities1",  # Remove Frame Padding
            f"{commandstore_base}\\ZilKitUtilities",   # Utilities submenu
            # Also delete old format keys if they exist (for cleanup)
            f"{commandstore_base}\\ZilKit.FFmpeg.ConvertRecursive",
            f"{commandstore_base}\\ZilKit.FFmpeg.ConvertCurrent",
            f"{commandstore_base}\\ZilKit.Shortcuts.Shutdown",
            f"{commandstore_base}\\ZilKit.Shortcuts.Restart",
            f"{commandstore_base}\\ZilKit.Shortcuts.EmptyRecycleBin",
            f"{commandstore_base}\\ZilKit.FFmpeg",
            f"{commandstore_base}\\ZilKit.Shortcuts",
            f"{commandstore_base}\\ZilKit.Utilities",
        ]
        
        # Delete from HKEY_LOCAL_MACHINE (matching registration pattern)
        for key_path in commandstore_keys:
            if _delete_registry_key_recursive(key_path, hkey=winreg.HKEY_LOCAL_MACHINE):
                deleted_count += 1
        
        # Also try to delete from HKEY_CURRENT_USER if any old entries exist there
        for key_path in commandstore_keys:
            _delete_registry_key_recursive(key_path, hkey=winreg.HKEY_CURRENT_USER)
        
        if deleted_count > 0:
            logger.info(f"Successfully removed {deleted_count} ZilKit registry entries")
        else:
            logger.info("No ZilKit registry entries found to remove")
        
        return True
        
    except Exception as e:
        logger.exception(f"Error unregistering context menu: {e}")
        return False


def is_registered() -> bool:
    """Check if ZilKit is registered in the context menu.
    
    Returns:
        True if registered, False otherwise
    """
    if winreg is None:
        return False
    
    try:
        base_key_path = r"Directory\Background\shell\ZilKit"
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, base_key_path):
            return True
    except FileNotFoundError:
        return False
    except Exception:
        return False
