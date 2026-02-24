"""Installation script for ZilKit.

This script registers ZilKit in the Windows context menu.
"""

import ctypes
import sys
from pathlib import Path

# Add parent directory to path to import zilkit
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel

from zilkit.registry import is_registered, register_context_menu, unregister_context_menu
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
    """Main installation function."""
    console.print(Panel.fit(
        "[bold blue]ZilKit Installation[/bold blue]",
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
    
    # Check if already installed
    if is_registered():
        console.print("[yellow]ZilKit is already registered in the context menu.[/yellow]")
        response = input("Do you want to reinstall? (y/n): ").strip().lower()
        if response != 'y':
            console.print("[yellow]Installation cancelled.[/yellow]")
            return
        else:
            # Uninstall first to clean up any old entries
            console.print("[yellow]Uninstalling existing entries...[/yellow]")
            unregister_context_menu()
    
    console.print("\n[bold]Registering ZilKit in Windows context menu...[/bold]")
    
    # Register context menu
    success = register_context_menu()
    
    if success:
        console.print("\n[green]Installation successful![/green]")
        console.print("\n[bold]You can now:[/bold]")
        console.print("  1. Right-click in any folder")
        console.print("  2. Select 'ZilKit' > 'FFmpeg'")
        console.print("  3. Choose 'Convert Image Sequence' to convert sequences")
        console.print("\n[yellow]Note: You may need to restart Windows Explorer for changes to take effect.[/yellow]")
        console.print("[yellow]You can do this by:[/yellow]")
        console.print("[yellow]  - Logging out and back in[/yellow]")
        console.print("[yellow]  - Or restarting explorer.exe in Task Manager[/yellow]")
    else:
        console.print("\n[red]Installation failed![/red]")
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
