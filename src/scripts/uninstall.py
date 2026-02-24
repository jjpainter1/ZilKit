"""Uninstallation script for ZilKit.

This script removes ZilKit from the Windows context menu.
"""

import ctypes
import sys
from pathlib import Path

# Add parent directory to path to import zilkit
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel

from zilkit.registry import is_registered, unregister_context_menu
from zilkit.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


def is_admin() -> bool:
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def main() -> None:
    """Main uninstallation function."""
    console.print(Panel.fit(
        "[bold red]ZilKit Uninstallation[/bold red]",
        border_style="red"
    ))
    
    # Check for admin privileges
    if not is_admin():
        console.print("\n[bold red]ERROR: Administrator privileges required![/bold red]")
        console.print("[yellow]Please right-click and 'Run as administrator'[/yellow]")
        console.print("\n[dim]Press any key to exit...[/dim]")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass
        sys.exit(1)
    
    console.print("\n[bold]Removing ALL ZilKit entries from Windows context menu...[/bold]")
    console.print("[yellow]This will remove:[/yellow]")
    console.print("  - ZilKit main menu")
    console.print("  - FFmpeg submenu and all actions")
    console.print("  - Shortcuts submenu and all actions")
    console.print("  - Utilities submenu")
    console.print("\n[yellow]Note: If you get 'Access Denied' errors, you may need to:[/yellow]")
    console.print("[yellow]  1. Run this script as Administrator, OR[/yellow]")
    console.print("[yellow]  2. Close Windows Explorer first (restart it after)[/yellow]")
    
    # Always try to unregister, even if is_registered() returns False
    # This ensures we clean up any leftover entries
    success = unregister_context_menu()
    
    if success:
        console.print("\n[green]Uninstallation successful![/green]")
        console.print("\n[bold yellow]IMPORTANT:[/bold yellow]")
        console.print("[yellow]You MUST restart Windows Explorer for changes to take effect.[/yellow]")
        console.print("\n[yellow]To restart Windows Explorer:[/yellow]")
        console.print("[yellow]  1. Press Ctrl+Shift+Esc to open Task Manager[/yellow]")
        console.print("[yellow]  2. Find 'Windows Explorer' in the list[/yellow]")
        console.print("[yellow]  3. Right-click and select 'Restart'[/yellow]")
        console.print("\n[yellow]Or simply log out and log back in.[/yellow]")
    else:
        console.print("\n[red]Uninstallation failed![/red]")
        console.print("[yellow]Please check the logs for more information.[/yellow]")
        console.print("[yellow]Logs are located in: %LOCALAPPDATA%\\ZilKit\\logs\\[/yellow]")
        sys.exit(1)
    
    console.print("\n[dim]Press any key to exit...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
