"""Installation script for ZilKit using .reg files.

This script generates and imports .reg files to set up the context menu.
This approach mirrors the working pattern from JJs-MediaCraft.
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
    """Main installation function."""
    console.print(Panel.fit(
        "[bold blue]ZilKit Installation (via .reg files)[/bold blue]",
        border_style="blue"
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
    
    console.print("\n[bold]Step 1: Generating .reg files...[/bold]")
    
    try:
        root_path, submenus_path, uninstall_path = generate_reg_files()
        console.print(f"  Generated: {root_path.name}")
        console.print(f"  Generated: {submenus_path.name}")
        console.print(f"  Generated: {uninstall_path.name}")
    except Exception as e:
        console.print(f"\n[red]Failed to generate .reg files: {e}[/red]")
        sys.exit(1)
    
    console.print("\n[bold]Step 2: Importing root menu...[/bold]")
    if not import_reg_file(root_path):
        console.print("[red]Failed to import root menu[/red]")
        sys.exit(1)
    console.print("  [green]OK[/green]")
    
    console.print("\n[bold]Step 3: Importing submenus and commands...[/bold]")
    if not import_reg_file(submenus_path):
        console.print("[red]Failed to import submenus[/red]")
        sys.exit(1)
    console.print("  [green]OK[/green]")
    
    console.print("\n[green]Installation successful![/green]")
    console.print("\n[bold]You can now:[/bold]")
    console.print("  1. Right-click in any folder (on empty space)")
    console.print("  2. Select 'ZilKit'")
    console.print("  3. You should see: FFmpeg, Utilities, Shortcuts")
    
    console.print("\n[bold yellow]IMPORTANT:[/bold yellow]")
    console.print("[yellow]Restart Windows Explorer for changes to take effect:[/yellow]")
    console.print("[yellow]  - Open Task Manager (Ctrl+Shift+Esc)[/yellow]")
    console.print("[yellow]  - Find 'Windows Explorer' -> Right-click -> Restart[/yellow]")
    
    console.print(f"\n[dim]Generated .reg files are in:[/dim]")
    console.print(f"[dim]  {root_path.parent}[/dim]")
    console.print(f"\n[dim]To uninstall, run: python uninstall_via_reg.py[/dim]")
    
    console.print("\n[dim]Press any key to exit...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
