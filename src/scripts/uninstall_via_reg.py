"""Uninstallation script for ZilKit using .reg files.

This script generates and imports the uninstall .reg file to remove the context menu.
"""

import ctypes
import sys
from pathlib import Path

# Add parent directory to path to import zilkit
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel

from zilkit.registry_generator import generate_reg_files, import_reg_file
from zilkit.utils.logger import get_logger

console = Console(force_terminal=True)
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
        "[bold red]ZilKit Uninstallation (via .reg files)[/bold red]",
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
    
    console.print("\n[bold]Step 1: Generating uninstall .reg file...[/bold]")
    
    try:
        _, _, uninstall_path = generate_reg_files()
        console.print(f"  Generated: {uninstall_path.name}")
    except Exception as e:
        console.print(f"\n[red]Failed to generate .reg file: {e}[/red]")
        sys.exit(1)
    
    console.print("\n[bold]Step 2: Removing registry entries...[/bold]")
    if not import_reg_file(uninstall_path):
        console.print("[red]Failed to remove registry entries[/red]")
        console.print("[yellow]Some entries may not have existed (this is OK)[/yellow]")
    else:
        console.print("  [green]OK[/green]")
    
    console.print("\n[green]Uninstallation complete![/green]")
    
    console.print("\n[bold yellow]IMPORTANT:[/bold yellow]")
    console.print("[yellow]Restart Windows Explorer for changes to take effect:[/yellow]")
    console.print("[yellow]  - Open Task Manager (Ctrl+Shift+Esc)[/yellow]")
    console.print("[yellow]  - Find 'Windows Explorer' -> Right-click -> Restart[/yellow]")
    
    console.print("\n[dim]Press any key to exit...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
