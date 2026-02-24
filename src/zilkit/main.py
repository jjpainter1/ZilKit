"""Main entry point for ZilKit context menu actions.

This module handles command-line arguments from Windows context menu and routes
to appropriate menu handlers.
"""

import sys
from pathlib import Path
from typing import Optional

# Add the src directory to Python path so we can import zilkit
# This is needed when running from context menu
_script_dir = Path(__file__).parent.parent.parent  # Go up from src/zilkit/main.py to project root
_src_dir = _script_dir / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import typer
from rich.console import Console
from rich.panel import Panel

from zilkit.utils.logger import get_logger

# Import menu handlers (will be created)
# from zilkit.menu import ffmpeg, shortcuts, utilities

app = typer.Typer(
    name="zilkit",
    help="ZilKit - Windows context menu tool for FFmpeg operations and utilities",
    add_completion=False,
)

# Use legacy_windows mode for better compatibility with Windows console
console = Console(legacy_windows=True)
logger = get_logger(__name__)


def _pause_before_exit() -> None:
    """Pause before closing the window so user can see any error messages."""
    try:
        console.print("\n[dim]Press any key to close...[/dim]")
        input()
    except (EOFError, KeyboardInterrupt):
        # If input fails (e.g., running in non-interactive mode), just continue
        pass


@app.command()
def ffmpeg(
    action: str = typer.Argument(..., help="FFmpeg action to perform"),
    preset_key: Optional[str] = typer.Argument(None, help="Preset key (for encode-preset action only)"),
    directory: Optional[str] = typer.Option(None, "--dir", "-d", help="Directory path (optional, uses current directory if not provided)"),
) -> None:
    """Handle FFmpeg menu actions.
    
    Args:
        action: Action name (e.g., 'encode-default', 'encode-preset', 'encode-multi-output', 'encode-recursive', 'configure')
        preset_key: Preset key (required for 'encode-preset' action)
        directory: Directory path where user right-clicked (optional, defaults to current working directory)
    """
    try:
        # Import here to avoid circular imports
        from zilkit.menu import ffmpeg as ffmpeg_menu
        
        # Get directory - use provided or current working directory
        # When called from Windows context menu, Windows Explorer sets the working directory
        # to the folder where the user right-clicked
        if directory:
            target_dir = Path(directory)
        else:
            target_dir = Path.cwd()
        
        # Route to appropriate handler
        if action == "encode-default":
            # Validate directory exists
            if not target_dir.exists() or not target_dir.is_dir():
                console.print(f"[red]Error: Directory does not exist: {target_dir}[/red]")
                logger.error(f"Invalid directory: {target_dir}")
                _pause_before_exit()
                sys.exit(1)
            ffmpeg_menu.encode_default(target_dir)
        
        elif action == "encode-preset":
            if not preset_key:
                console.print(f"[red]Error: Preset key required for encode-preset action[/red]")
                logger.error("Preset key missing for encode-preset")
                _pause_before_exit()
                sys.exit(1)
            # Validate directory exists
            if not target_dir.exists() or not target_dir.is_dir():
                console.print(f"[red]Error: Directory does not exist: {target_dir}[/red]")
                logger.error(f"Invalid directory: {target_dir}")
                _pause_before_exit()
                sys.exit(1)
            ffmpeg_menu.encode_with_preset(target_dir, preset_key)
        
        elif action == "encode-multi-output":
            # Validate directory exists
            if not target_dir.exists() or not target_dir.is_dir():
                console.print(f"[red]Error: Directory does not exist: {target_dir}[/red]")
                logger.error(f"Invalid directory: {target_dir}")
                _pause_before_exit()
                sys.exit(1)
            ffmpeg_menu.encode_multi_output(target_dir)
        
        elif action == "encode-recursive":
            # Validate directory exists
            if not target_dir.exists() or not target_dir.is_dir():
                console.print(f"[red]Error: Directory does not exist: {target_dir}[/red]")
                logger.error(f"Invalid directory: {target_dir}")
                _pause_before_exit()
                sys.exit(1)
            ffmpeg_menu.encode_recursive_interactive(target_dir)
        
        elif action == "configure":
            ffmpeg_menu.configure_default_settings()
        
        else:
            console.print(f"[red]Error: Unknown FFmpeg action: {action}[/red]")
            logger.error(f"Unknown action: {action}")
            _pause_before_exit()
            sys.exit(1)
            
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        logger.exception("Error in FFmpeg handler")
        import traceback
        console.print(f"\n[dim]Traceback:[/dim]")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        _pause_before_exit()
        sys.exit(1)


@app.command()
def utilities(
    action: str = typer.Argument(..., help="Utility action to perform"),
    directory: Optional[str] = typer.Option(None, "--dir", "-d", help="Directory path (optional, uses current directory if not provided)"),
) -> None:
    """Handle utility menu actions.
    
    Args:
        action: Action name (e.g., 'remove-frame-padding')
        directory: Directory path where user right-clicked (optional, defaults to current working directory)
    """
    try:
        # Import here to avoid circular imports
        from zilkit.menu import utilities as utilities_menu
        
        # Get directory - use provided or current working directory
        if directory:
            target_dir = Path(directory)
        else:
            target_dir = Path.cwd()
        
        # Route to appropriate handler
        if action == "remove-frame-padding":
            # Validate directory exists
            if not target_dir.exists() or not target_dir.is_dir():
                console.print(f"[red]Error: Directory does not exist: {target_dir}[/red]")
                logger.error(f"Invalid directory: {target_dir}")
                _pause_before_exit()
                sys.exit(1)
            utilities_menu.remove_frame_padding(target_dir)
        else:
            console.print(f"[red]Error: Unknown utility action: {action}[/red]")
            logger.error(f"Unknown action: {action}")
            _pause_before_exit()
            sys.exit(1)
            
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        logger.exception("Error in utilities handler")
        import traceback
        console.print(f"\n[dim]Traceback:[/dim]")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        _pause_before_exit()
        sys.exit(1)


@app.command()
def shortcuts(
    action: str = typer.Argument(..., help="Shortcut action to perform"),
) -> None:
    """Handle system shortcuts menu actions.
    
    Args:
        action: Action name (e.g., 'empty-recycle-bin', 'restart', 'shutdown')
    """
    try:
        # Import here to avoid circular imports
        from zilkit.menu import shortcuts as shortcuts_menu
        
        # Route to appropriate handler
        if action == "empty-recycle-bin":
            shortcuts_menu.empty_recycle_bin()
        elif action == "restart":
            shortcuts_menu.force_restart()
        elif action == "shutdown":
            shortcuts_menu.force_shutdown()
        else:
            console.print(f"[red]Error: Unknown shortcut action: {action}[/red]")
            logger.error(f"Unknown action: {action}")
            _pause_before_exit()
            sys.exit(1)
            
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        logger.exception("Error in shortcuts handler")
        import traceback
        console.print(f"\n[dim]Traceback:[/dim]")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        _pause_before_exit()
        sys.exit(1)


def main() -> None:
    """Main entry point for ZilKit."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        _pause_before_exit()
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {str(e)}[/red]")
        logger.exception("Fatal error in main")
        import traceback
        console.print(f"\n[dim]Traceback:[/dim]")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        _pause_before_exit()
        sys.exit(1)


if __name__ == "__main__":
    main()
