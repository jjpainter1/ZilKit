"""Diagnostic script to check ZilKit registry entries.

This script inspects the actual registry state to help diagnose
context menu issues.
"""

import sys
from pathlib import Path

# Add parent directory to path to import zilkit
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import winreg
except ImportError:
    print("ERROR: winreg module not available (not on Windows?)")
    sys.exit(1)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Use ASCII-safe characters for Windows console compatibility
console = Console(force_terminal=True, legacy_windows=False)


def read_registry_value(hkey, path, value_name=""):
    """Read a registry value, return None if not found."""
    try:
        with winreg.OpenKey(hkey, path, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, value_name)
            return val
    except FileNotFoundError:
        return None
    except Exception as e:
        return f"ERROR: {e}"


def check_key_exists(hkey, path):
    """Check if a registry key exists."""
    try:
        with winreg.OpenKey(hkey, path, 0, winreg.KEY_READ):
            return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def main():
    console.print(Panel.fit(
        "[bold cyan]ZilKit Registry Diagnostic[/bold cyan]",
        border_style="cyan"
    ))
    
    # Check main menu
    console.print("\n[bold]1. MAIN MENU (HKEY_CLASSES_ROOT)[/bold]")
    main_menu_path = r"Directory\Background\shell\ZilKit"
    
    if check_key_exists(winreg.HKEY_CLASSES_ROOT, main_menu_path):
        console.print(f"  [green]OK[/green] Key exists: {main_menu_path}")
        
        muiverb = read_registry_value(winreg.HKEY_CLASSES_ROOT, main_menu_path, "MUIVerb")
        subcommands = read_registry_value(winreg.HKEY_CLASSES_ROOT, main_menu_path, "SubCommands")
        
        console.print(f"    MUIVerb: {muiverb}")
        console.print(f"    SubCommands: {subcommands}")
        
        if subcommands:
            expected_subs = subcommands.split(";")
            console.print(f"    [yellow]Expected submenus: {expected_subs}[/yellow]")
    else:
        console.print(f"  [red]MISSING[/red] Key NOT FOUND: {main_menu_path}")
        console.print("  [red]ZilKit is not installed![/red]")
        return
    
    # Check CommandStore entries
    console.print("\n[bold]2. COMMANDSTORE (HKEY_LOCAL_MACHINE)[/bold]")
    commandstore_base = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell"
    
    # Define what we expect to find
    expected_keys = {
        "ZilKitFFmpeg": {"type": "submenu", "muiverb": "FFmpeg", "subcommands": True},
        "ZilKitFFmpeg1": {"type": "action", "name": "Encode To Movie (Default)"},
        "ZilKitFFmpeg2": {"type": "submenu", "muiverb": "Encode To Movie (Choose Preset)", "subcommands": True},
        "ZilKitFFmpeg3": {"type": "action", "name": "Encode To Movie (Multi-Output)"},
        "ZilKitFFmpeg4": {"type": "action", "name": "Encode To Movie (Recursive)"},
        "ZilKitFFmpeg5": {"type": "action", "name": "Configure Default Settings"},
        "ZilKitUtilities": {"type": "submenu", "muiverb": "Utilities", "subcommands": True},
        "ZilKitUtilities1": {"type": "action", "name": "Remove Frame Padding"},
        "ZilKitShortcuts": {"type": "submenu", "muiverb": "Shortcuts", "subcommands": True},
        "ZilKitShortcuts1": {"type": "action", "name": "Empty Recycle Bin"},
        "ZilKitShortcuts2": {"type": "action", "name": "Force Restart"},
        "ZilKitShortcuts3": {"type": "action", "name": "Force Shutdown"},
    }
    
    table = Table(title="CommandStore Registry Keys")
    table.add_column("Key Name", style="cyan")
    table.add_column("Exists", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Display Name / MUIVerb")
    table.add_column("SubCommands / Command")
    
    for key_name, expected in expected_keys.items():
        full_path = f"{commandstore_base}\\{key_name}"
        exists = check_key_exists(winreg.HKEY_LOCAL_MACHINE, full_path)
        
        if exists:
            exists_str = "[green]YES[/green]"
            
            # Get display name
            if expected["type"] == "submenu":
                display = read_registry_value(winreg.HKEY_LOCAL_MACHINE, full_path, "MUIVerb") or "[red]MISSING![/red]"
                subcmds = read_registry_value(winreg.HKEY_LOCAL_MACHINE, full_path, "SubCommands")
                extra = f"SubCmds: {subcmds}" if subcmds else "[red]SubCommands MISSING![/red]"
            else:
                display = read_registry_value(winreg.HKEY_LOCAL_MACHINE, full_path, "") or "[red]MISSING![/red]"
                # Check command subkey
                cmd_path = f"{full_path}\\command"
                if check_key_exists(winreg.HKEY_LOCAL_MACHINE, cmd_path):
                    cmd = read_registry_value(winreg.HKEY_LOCAL_MACHINE, cmd_path, "")
                    extra = f"[green]Has command[/green]" if cmd else "[red]Command empty![/red]"
                else:
                    extra = "[red]command subkey MISSING![/red]"
        else:
            exists_str = "[red]NO[/red]"
            display = "-"
            extra = "-"
        
        table.add_row(key_name, exists_str, expected["type"], str(display), extra)
    
    console.print(table)
    
    # Summary
    console.print("\n[bold]3. DIAGNOSIS[/bold]")
    
    # Check for common issues
    issues = []
    
    # Check if Utilities submenu has SubCommands
    utils_subcmds = read_registry_value(
        winreg.HKEY_LOCAL_MACHINE, 
        f"{commandstore_base}\\ZilKitUtilities", 
        "SubCommands"
    )
    if not utils_subcmds:
        issues.append("ZilKitUtilities missing SubCommands value")
    
    # Check if Utilities1 exists and has command
    if not check_key_exists(winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\ZilKitUtilities1"):
        issues.append("ZilKitUtilities1 key does not exist")
    elif not check_key_exists(winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\ZilKitUtilities1\\command"):
        issues.append("ZilKitUtilities1\\command subkey does not exist")
    
    # Check if Shortcuts submenu exists
    if not check_key_exists(winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\ZilKitShortcuts"):
        issues.append("ZilKitShortcuts key does not exist")
    
    # Check Shortcuts action keys
    for i in range(1, 4):
        key = f"ZilKitShortcuts{i}"
        if not check_key_exists(winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\{key}"):
            issues.append(f"{key} key does not exist")
    
    if issues:
        console.print("[red]Issues found:[/red]")
        for issue in issues:
            console.print(f"  [red]*[/red] {issue}")
    else:
        console.print("[green]All expected registry keys exist![/green]")
        console.print("\n[yellow]If menus still don't appear, try:[/yellow]")
        console.print("  1. Run uninstall.py as Administrator")
        console.print("  2. Restart Windows Explorer (or log out/in)")
        console.print("  3. Run install.py as Administrator")
        console.print("  4. Restart Windows Explorer again")
    
    console.print("\n[dim]Press any key to exit...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
