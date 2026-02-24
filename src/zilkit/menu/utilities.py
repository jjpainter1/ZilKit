"""Utilities menu handler for ZilKit.

This module handles utility actions.
"""

import sys
from pathlib import Path
from typing import List, Tuple
import re

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from zilkit.utils.logger import get_logger

# Configure console for Windows compatibility
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

console = Console(legacy_windows=True)
logger = get_logger(__name__)


def _extract_frame_number_info(filename: str) -> Tuple[bool, int, int, str]:
    """Extract frame number information from a filename using the same logic as FFmpeg pattern detection.
    
    This uses the exact same pattern detection logic as convert_sequence_with_preset.
    
    Args:
        filename: Filename to analyze (without path)
    
    Returns:
        Tuple of (has_frame_number: bool, frame_start: int, frame_width: int, new_name: str)
        If has_frame_number is False, frame_start and frame_width are 0, and new_name is the original filename
    """
    file_path = Path(filename)
    stem = file_path.stem
    suffix = file_path.suffix
    
    # Find the frame number (last sequence of digits in the stem)
    # This matches the logic in convert_sequence_with_preset
    num_matches = list(re.finditer(r'\d+', stem))
    if num_matches:
        last_match = num_matches[-1]
        frame_width = len(last_match.group())
        frame_number_str = last_match.group()
        
        # Remove the frame number from the stem
        # stem[:last_match.start()] gets everything before the number
        # stem[last_match.end():] gets everything after the number
        new_stem = stem[:last_match.start()] + stem[last_match.end():]
        new_name = f"{new_stem}{suffix}"
        
        try:
            frame_number = int(frame_number_str)
        except ValueError:
            return False, 0, 0, filename
        
        return True, frame_number, frame_width, new_name
    else:
        return False, 0, 0, filename


def remove_frame_padding(directory: Path) -> None:
    """Remove frame padding from filenames in a directory.
    
    Uses the same pattern detection logic as FFmpeg to identify frame numbers
    and remove them from filenames.
    
    Args:
        directory: Directory to process
    """
    console.print(Panel.fit(
        "[bold blue]ZilKit - Remove Frame Padding[/bold blue]",
        border_style="blue"
    ))
    
    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]ERROR: Directory does not exist: {directory}[/red]")
        console.print("\n[dim]Press any key to close...[/dim]")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass
        return
    
    console.print(f"\n[bold]Scanning directory:[/bold] [cyan]{directory}[/cyan]")
    
    # Find all files in the directory
    all_files = [f for f in directory.iterdir() if f.is_file()]
    
    # Process each file to find those with frame padding
    files_to_rename = []
    for file_path in all_files:
        has_frame, frame_num, frame_width, new_name = _extract_frame_number_info(file_path.name)
        if has_frame and frame_width > 0:
            new_path = directory / new_name
            files_to_rename.append((file_path, new_path, frame_num, frame_width))
    
    if not files_to_rename:
        console.print("\n[yellow]No files with frame padding found in this directory.[/yellow]")
        console.print("[dim]Frame padding is detected as trailing digits in filenames.[/dim]")
        console.print("\n[dim]Press any key to close...[/dim]")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass
        return
    
    # Display preview
    console.print(f"\n[green]Found [bold]{len(files_to_rename)}[/bold] file(s) with frame padding:[/green]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Current Name", style="cyan", overflow="fold")
    table.add_column("New Name", style="green", overflow="fold")
    table.add_column("Frame #", justify="right")
    table.add_column("Width", justify="right")
    
    for file_path, new_path, frame_num, frame_width in files_to_rename:
        table.add_row(
            file_path.name,
            new_path.name,
            str(frame_num),
            str(frame_width)
        )
    
    console.print(table)
    
    # Ask for confirmation
    if not Confirm.ask(f"\n[bold]Rename {len(files_to_rename)} file(s)?[/bold]", default=True):
        console.print("\n[yellow]Operation cancelled.[/yellow]")
        console.print("\n[dim]Press any key to close...[/dim]")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass
        return
    
    # Perform renaming
    console.print(f"\n[bold]Renaming files...[/bold]")
    
    success_count = 0
    failure_count = 0
    skipped_count = 0
    renamed_files = []
    
    for file_path, new_path, frame_num, frame_width in files_to_rename:
        try:
            # Check if target already exists
            if new_path.exists():
                # Handle conflict by adding suffix
                base_name = new_path.stem
                suffix = new_path.suffix
                counter = 1
                while new_path.exists():
                    new_name = f"{base_name}_{counter}{suffix}"
                    new_path = directory / new_name
                    counter += 1
                    if counter > 1000:  # Safety limit
                        raise ValueError("Too many conflicts, cannot generate unique name")
                
                logger.info(f"Target exists, using: {new_path.name}")
            
            # Rename the file
            file_path.rename(new_path)
            renamed_files.append((file_path.name, new_path.name))
            success_count += 1
            logger.debug(f"Renamed: {file_path.name} -> {new_path.name}")
            
        except Exception as e:
            failure_count += 1
            error_msg = str(e)
            logger.error(f"Failed to rename {file_path.name}: {error_msg}")
            console.print(f"[red]  ERROR: {file_path.name} - {error_msg}[/red]")
    
    # Display results
    console.print("\n" + "=" * 60)
    if success_count > 0:
        console.print(f"[green]SUCCESS: Renamed {success_count} file(s)[/green]")
        if renamed_files:
            console.print("\n[bold]Renamed files:[/bold]")
            for old_name, new_name in renamed_files:
                console.print(f"  [green]✓[/green] {old_name}")
                console.print(f"    [dim]→ {new_name}[/dim]")
    
    if skipped_count > 0:
        console.print(f"[yellow]SKIPPED: {skipped_count} file(s)[/yellow]")
    
    if failure_count > 0:
        console.print(f"[red]FAILED: Could not rename {failure_count} file(s)[/red]")
    
    console.print("\n[dim]Press any key to close...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


def handle_utility_action(action: str) -> None:
    """Handle a utility action.
    
    Args:
        action: Action name
    """
    console.print(Panel.fit(
        "[bold blue]ZilKit - Utilities[/bold blue]",
        border_style="blue"
    ))
    
    console.print(f"[yellow]Utility action '{action}' not yet implemented[/yellow]")
    logger.warning(f"Utility action not implemented: {action}")
    
    console.print("\n[dim]Press any key to close...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass
