"""Force cleanup of all ZilKit registry entries.

This script attempts to remove all ZilKit registry entries, even if they
are locked by Windows Explorer. Run as Administrator for best results.
"""

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
from rich.panel import Panel

console = Console()


def force_delete_key(key_path: str, hkey=winreg.HKEY_CLASSES_ROOT) -> bool:
    """Force delete a registry key, handling access denied errors."""
    try:
        # Try to delete recursively
        try:
            with winreg.OpenKey(hkey, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                # Get all subkeys
                subkeys = []
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkeys.append(subkey_name)
                        i += 1
                    except OSError:
                        break
                
                # Delete subkeys first
                for subkey_name in subkeys:
                    subkey_path = f"{key_path}\\{subkey_name}"
                    force_delete_key(subkey_path, hkey)
        except FileNotFoundError:
            return True
        except PermissionError:
            console.print(f"[red]Access denied: {hkey}\\{key_path}[/red]")
            console.print("[yellow]Try running as Administrator or close Windows Explorer first[/yellow]")
            return False
        
        # Delete the key itself
        winreg.DeleteKey(hkey, key_path)
        console.print(f"[green]Deleted: {key_path}[/green]")
        return True
        
    except FileNotFoundError:
        return True
    except PermissionError as e:
        console.print(f"[red]Access denied: {hkey}\\{key_path}[/red]")
        return False
    except Exception as e:
        console.print(f"[yellow]Warning: {hkey}\\{key_path} - {e}[/yellow]")
        return False


def main() -> None:
    """Main cleanup function."""
    console.print(Panel.fit(
        "[bold red]ZilKit Registry Cleanup[/bold red]",
        border_style="red"
    ))
    
    console.print("\n[bold]This script will attempt to remove ALL ZilKit registry entries.[/bold]")
    console.print("[yellow]If you get 'Access Denied' errors, please:[/yellow]")
    console.print("[yellow]  1. Run this script as Administrator, OR[/yellow]")
    console.print("[yellow]  2. Close Windows Explorer first[/yellow]")
    console.print()
    
    response = input("Continue? (y/n): ").strip().lower()
    if response != 'y':
        console.print("[yellow]Cancelled.[/yellow]")
        return
    
    # List of all ZilKit-related keys in HKEY_CLASSES_ROOT
    hkcr_keys = [
        r"Directory\Background\shell\ZilKit",
    ]
    
    # List of all ZilKit-related keys in HKEY_LOCAL_MACHINE CommandStore
    commandstore_base = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell"
    hklm_keys = [
        f"{commandstore_base}\\ZilKit.FFmpeg.ConvertRecursive",
        f"{commandstore_base}\\ZilKit.FFmpeg.ConvertCurrent",
        f"{commandstore_base}\\ZilKit.Shortcuts.Shutdown",
        f"{commandstore_base}\\ZilKit.Shortcuts.Restart",
        f"{commandstore_base}\\ZilKit.Shortcuts.EmptyRecycleBin",
        f"{commandstore_base}\\ZilKit.FFmpeg",
        f"{commandstore_base}\\ZilKit.Shortcuts",
        f"{commandstore_base}\\ZilKit.Utilities",
    ]
    
    keys_to_delete = [(key, winreg.HKEY_CLASSES_ROOT) for key in hkcr_keys] + \
                     [(key, winreg.HKEY_LOCAL_MACHINE) for key in hklm_keys]
    
    console.print("\n[bold]Deleting registry keys...[/bold]")
    deleted = 0
    failed = 0
    
    for key_path, hkey in keys_to_delete:
        if force_delete_key(key_path, hkey):
            deleted += 1
        else:
            failed += 1
    
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"[green]Deleted: {deleted}[/green]")
    if failed > 0:
        console.print(f"[red]Failed: {failed}[/red]")
        console.print("\n[yellow]Some keys could not be deleted due to access restrictions.[/yellow]")
        console.print("[yellow]Please run as Administrator or close Windows Explorer and try again.[/yellow]")
    else:
        console.print("\n[green]All registry entries removed successfully![/green]")
        console.print("[yellow]Restart Windows Explorer to see the changes.[/yellow]")
    
    console.print("\n[dim]Press any key to exit...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
