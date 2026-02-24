"""Verify ZilKit registry entries are correctly installed."""

import sys
from pathlib import Path

# Add parent directory to path to import zilkit
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import winreg
except ImportError:
    print("Error: This script requires Windows and the winreg module.")
    sys.exit(1)

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def check_registry_key(hkey, key_path, description):
    """Check if a registry key exists and return its values."""
    try:
        with winreg.OpenKey(hkey, key_path) as key:
            values = {}
            i = 0
            while True:
                try:
                    name, value, reg_type = winreg.EnumValue(key, i)
                    values[name] = value
                    i += 1
                except OSError:
                    break
            
            subkeys = []
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkeys.append(subkey_name)
                    i += 1
                except OSError:
                    break
            
            return True, values, subkeys
    except FileNotFoundError:
        return False, {}, []
    except Exception as e:
        return None, {}, []


def main():
    """Main verification function."""
    console.print(Panel.fit(
        "[bold blue]ZilKit Registry Verification[/bold blue]",
        border_style="blue"
    ))
    
    commandstore_base = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell"
    
    # Keys to check
    checks = [
        # Main menu
        (winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\ZilKit", "Main ZilKit Menu"),
        
        # FFmpeg submenu
        (winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\ZilKit.FFmpeg", "FFmpeg Submenu"),
        (winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\ZilKit.FFmpeg.ConvertCurrent", "FFmpeg: Convert Image Sequence"),
        (winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\ZilKit.FFmpeg.ConvertRecursive", "FFmpeg: Convert All Sequences"),
        
        # Shortcuts submenu
        (winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\ZilKit.Shortcuts", "Shortcuts Submenu"),
        (winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\ZilKit.Shortcuts.EmptyRecycleBin", "Shortcuts: Empty Recycle Bin"),
        (winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\ZilKit.Shortcuts.Restart", "Shortcuts: Force Restart"),
        (winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\ZilKit.Shortcuts.Shutdown", "Shortcuts: Force Shutdown"),
        
        # Utilities submenu
        (winreg.HKEY_LOCAL_MACHINE, f"{commandstore_base}\\ZilKit.Utilities", "Utilities Submenu"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Registry Key", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("MUIVerb", style="yellow")
    table.add_column("SubCommands", style="green")
    table.add_column("Command", style="dim")
    
    all_ok = True
    
    for hkey, key_path, description in checks:
        exists, values, subkeys = check_registry_key(hkey, key_path, description)
        
        if exists is False:
            status = "[red]MISSING[/red]"
            all_ok = False
            muiverb = "-"
            subcommands = "-"
            command = "-"
        elif exists is None:
            status = "[yellow]ERROR[/yellow]"
            all_ok = False
            muiverb = "-"
            subcommands = "-"
            command = "-"
        else:
            status = "[green]OK[/green]"
            muiverb = values.get("MUIVerb", "(default)" if values.get("", "") else "-")
            subcommands = values.get("SubCommands", "-")
            
            # Check for command subkey
            command_path = f"{key_path}\\command"
            cmd_exists, cmd_values, _ = check_registry_key(hkey, command_path, "")
            if cmd_exists:
                command = cmd_values.get("", "-")
            else:
                command = "-"
        
        hkey_name = "HKCR" if hkey == winreg.HKEY_CLASSES_ROOT else "HKLM"
        table.add_row(
            f"{hkey_name}\\{key_path}",
            status,
            muiverb,
            subcommands[:50] + "..." if subcommands and len(subcommands) > 50 else subcommands,
            command[:50] + "..." if command and len(command) > 50 else command
        )
    
    console.print("\n")
    console.print(table)
    
    if all_ok:
        console.print("\n[green]All registry entries are present![/green]")
        console.print("[yellow]If menu items still don't appear, try:[/yellow]")
        console.print("  1. Log out and log back in")
        console.print("  2. Restart your computer")
        console.print("  3. Check if you're running as Administrator")
    else:
        console.print("\n[red]Some registry entries are missing![/red]")
        console.print("[yellow]Please run the install script again as Administrator.[/yellow]")
    
    console.print("\n[dim]Press any key to exit...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
