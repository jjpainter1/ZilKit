"""System shortcuts menu handler for ZilKit.

This module handles system shortcut actions like empty recycle bin,
restart, and shutdown.
"""

from rich.console import Console
from rich.panel import Panel

from zilkit.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


def empty_recycle_bin() -> None:
    """Empty the Windows recycle bin."""
    console.print(Panel.fit(
        "[bold blue]ZilKit - Empty Recycle Bin[/bold blue]",
        border_style="blue"
    ))
    
    try:
        import win32api
        import win32con
        
        # Empty recycle bin
        win32api.SHEmptyRecycleBin(None, None, win32con.SHERB_NOCONFIRMATION | win32con.SHERB_NOPROGRESSUI)
        console.print("[green]SUCCESS: Recycle bin emptied successfully[/green]")
        logger.info("Recycle bin emptied")
        
    except ImportError:
        console.print("[red]ERROR: pywin32 not installed[/red]")
        console.print("[yellow]Please install pywin32: pip install pywin32[/yellow]")
        logger.error("pywin32 not available")
    except Exception as e:
        console.print(f"[red]ERROR: {str(e)}[/red]")
        logger.exception("Error emptying recycle bin")
    
    console.print("\n[dim]Press any key to close...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


def force_restart() -> None:
    """Force the computer to restart."""
    console.print(Panel.fit(
        "[bold red]ZilKit - Force Restart[/bold red]",
        border_style="red"
    ))
    
    console.print("[yellow]WARNING: This will restart your computer immediately![/yellow]")
    console.print("[yellow]Press Ctrl+C within 5 seconds to cancel...[/yellow]")
    
    try:
        import time
        time.sleep(5)
        
        import os
        os.system("shutdown /r /t 0")
        logger.info("System restart initiated")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Restart cancelled[/yellow]")
        logger.info("Restart cancelled by user")
    except Exception as e:
        console.print(f"[red]ERROR: {str(e)}[/red]")
        logger.exception("Error initiating restart")


def force_shutdown() -> None:
    """Force the computer to shutdown."""
    console.print(Panel.fit(
        "[bold red]ZilKit - Force Shutdown[/bold red]",
        border_style="red"
    ))
    
    console.print("[yellow]WARNING: This will shutdown your computer immediately![/yellow]")
    console.print("[yellow]Press Ctrl+C within 5 seconds to cancel...[/yellow]")
    
    try:
        import time
        time.sleep(5)
        
        import os
        os.system("shutdown /s /t 0")
        logger.info("System shutdown initiated")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutdown cancelled[/yellow]")
        logger.info("Shutdown cancelled by user")
    except Exception as e:
        console.print(f"[red]ERROR: {str(e)}[/red]")
        logger.exception("Error initiating shutdown")
