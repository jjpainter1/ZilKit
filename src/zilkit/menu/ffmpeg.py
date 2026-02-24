"""FFmpeg menu handler for ZilKit.

This module handles FFmpeg-related context menu actions and provides
user feedback via Rich console output.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table

from zilkit.config import get_config
from zilkit.core.ffmpeg_ops import (
    convert_movie_with_preset,
    convert_sequence_with_preset,
    find_image_sequences,
    find_movie_files,
)
from zilkit.utils.file_utils import walk_directories
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


def _get_resolution_scale(resolution: str) -> float:
    """Convert resolution string to scale factor.
    
    Args:
        resolution: "full", "half", "quarter", or custom float string
    
    Returns:
        Resolution scale factor (1.0, 0.5, 0.25, or custom value)
    """
    resolution_lower = resolution.lower().strip()
    if resolution_lower == "full":
        return 1.0
    elif resolution_lower == "half":
        return 0.5
    elif resolution_lower == "quarter":
        return 0.25
    elif "x" in resolution_lower:
        # Custom resolution like "1920x1080" - return 1.0 and let FFmpeg handle explicit resolution
        return 1.0
    else:
        try:
            return float(resolution)
        except ValueError:
            return 1.0


def _prompt_resolution(current_value: Optional[str] = None, allow_clear: bool = False) -> Optional[str]:
    """Reusable function to prompt for resolution.
    
    Shows Full/Half/Quarter/Custom options, and prompts for XxY if Custom is selected.
    This ensures consistent resolution prompts throughout the application.
    
    Args:
        current_value: Current resolution value (for display)
        allow_clear: If True, adds option to clear override
    
    Returns:
        Resolution string ("full", "half", "quarter", "1920x1080", etc.) or None to clear
    """
    console.print("\n[bold cyan]Resolution[/bold cyan]")
    console.print("  1. Full (use source resolution)")
    console.print("  2. Half (50% of source)")
    console.print("  3. Quarter (25% of source)")
    console.print("  4. Custom (enter width x height)")
    if allow_clear:
        console.print("  5. Clear override")
    
    choices = ["1", "2", "3", "4", "5"] if allow_clear else ["1", "2", "3", "4"]
    default = "5" if allow_clear else "1"
    
    res_choice = Prompt.ask("Select resolution", choices=choices, default=default)
    
    if res_choice == "1":
        return "full"
    elif res_choice == "2":
        return "half"
    elif res_choice == "3":
        return "quarter"
    elif res_choice == "4":
        # Prompt for custom resolution - ask for width and height separately
        # This avoids Rich interpreting "0x1080" as a hex color code
        console.print("\nEnter custom resolution dimensions:")
        try:
            width_str = Prompt.ask("Width (pixels)", default="")
            if not width_str:
                return current_value
            width = int(width_str)
            if width <= 0:
                console.print("[yellow]Invalid width (must be positive number).[/yellow]")
                return current_value
            
            height_str = Prompt.ask("Height (pixels)", default="")
            if not height_str:
                return current_value
            height = int(height_str)
            if height <= 0:
                console.print("[yellow]Invalid height (must be positive number).[/yellow]")
                return current_value
            
            # Return as string format "widthxheight" for internal use
            return f"{width}x{height}"
        except ValueError:
            console.print("[yellow]Invalid resolution format (must be numbers).[/yellow]")
            return current_value
    elif res_choice == "5" and allow_clear:
        return None  # Signal to clear override
    else:
        return current_value


def encode_default(directory: Path) -> None:
    """Encode using default preset (non-interactive).
    
    Args:
        directory: Directory to process
    """
    console.print(Panel.fit(
        "[bold blue]ZilKit - Encode To Movie (Default)[/bold blue]",
        border_style="blue"
    ))
    
    config = get_config()
    if not config.is_ffmpeg_available():
        console.print("[red]ERROR: FFmpeg is not available![/red]")
        return
    
    default_preset_key = config.get_default_preset()
    if not default_preset_key:
        console.print("[red]ERROR: No default preset configured![/red]")
        console.print("[yellow]Please configure default settings first.[/yellow]")
        return
    
    preset = config.get_preset(default_preset_key)
    if not preset:
        console.print(f"[red]ERROR: Default preset '{default_preset_key}' not found![/red]")
        return
    
    console.print(f"[green]Using preset:[/green] [cyan]{preset.get('display_name', default_preset_key)}[/cyan]")
    
    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]ERROR: Directory does not exist: {directory}[/red]")
        return
    
    console.print(f"\n[bold]Scanning directory:[/bold] [cyan]{directory}[/cyan]")
    sequences = find_image_sequences(directory)
    movies = find_movie_files(directory)
    
    if not sequences and not movies:
        console.print("[yellow]WARNING: No image sequences or movie files found.[/yellow]")
        return
    
    total_items = len(sequences) + len(movies)
    console.print(f"\n[green]Found [bold]{len(sequences)}[/bold] image sequence(s) and [bold]{len(movies)}[/bold] movie file(s):[/green]")
    
    if sequences:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Sequence", style="cyan")
        table.add_column("Frames", justify="right")
        for seq in sequences:
            table.add_row(str(seq), str(len(seq)))
        console.print(table)
    
    if movies:
        if sequences:
            console.print("\n[bold]Movie Files:[/bold]")
        for movie in movies:
            console.print(f"  [cyan]- {movie.name}[/cyan]")
    
    console.print(f"\n[bold]Converting {total_items} item(s)...[/bold]")
    console.print("[dim]FFmpeg progress will be shown below:[/dim]\n")
    
    success_count = 0
    failure_count = 0
    failed_items = []
    
    # Convert sequences
    for seq in sequences:
        success, msg = convert_sequence_with_preset(
            seq,
            default_preset_key,
            sequence_directory=directory,
        )
        if success:
            success_count += 1
        else:
            failure_count += 1
            failed_items.append((f"Sequence: {str(seq)}", msg))
    
    # Convert movies
    for movie in movies:
        success, msg = convert_movie_with_preset(
            movie,
            default_preset_key,
        )
        if success:
            success_count += 1
        else:
            failure_count += 1
            failed_items.append((f"Movie: {movie.name}", msg))
    
    console.print("\n" + "=" * 60)
    if success_count > 0:
        console.print(f"[green]SUCCESS: Converted {success_count} item(s)[/green]")
    if failure_count > 0:
        console.print(f"[red]FAILED: Could not convert {failure_count} item(s)[/red]")
        for item_name, error in failed_items:
            console.print(f"  [red]- {item_name}: {error[:100]}[/red]")
    
    console.print("\n[dim]Press any key to close...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


def encode_with_preset(directory: Path, preset_key: str) -> None:
    """Encode using a specific preset (non-interactive).
    
    Args:
        directory: Directory to process
        preset_key: Key of the preset to use
    """
    console.print(Panel.fit(
        "[bold blue]ZilKit - Encode To Movie (Choose Preset)[/bold blue]",
        border_style="blue"
    ))
    
    config = get_config()
    if not config.is_ffmpeg_available():
        console.print("[red]ERROR: FFmpeg is not available![/red]")
        return
    
    preset = config.get_preset(preset_key)
    if not preset:
        console.print(f"[red]ERROR: Preset '{preset_key}' not found![/red]")
        return
    
    console.print(f"[green]Using preset:[/green] [cyan]{preset.get('display_name', preset_key)}[/cyan]")
    
    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]ERROR: Directory does not exist: {directory}[/red]")
        return
    
    console.print(f"\n[bold]Scanning directory:[/bold] [cyan]{directory}[/cyan]")
    sequences = find_image_sequences(directory)
    movies = find_movie_files(directory)
    
    if not sequences and not movies:
        console.print("[yellow]WARNING: No image sequences or movie files found.[/yellow]")
        return
    
    total_items = len(sequences) + len(movies)
    console.print(f"\n[green]Found [bold]{len(sequences)}[/bold] image sequence(s) and [bold]{len(movies)}[/bold] movie file(s):[/green]")
    
    if sequences:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Sequence", style="cyan")
        table.add_column("Frames", justify="right")
        for seq in sequences:
            table.add_row(str(seq), str(len(seq)))
        console.print(table)
    
    if movies:
        if sequences:
            console.print("\n[bold]Movie Files:[/bold]")
        for movie in movies:
            console.print(f"  [cyan]- {movie.name}[/cyan]")
    
    console.print(f"\n[bold]Converting {total_items} item(s)...[/bold]")
    console.print("[dim]FFmpeg progress will be shown below:[/dim]\n")
    
    success_count = 0
    failure_count = 0
    failed_items = []
    
    # Convert sequences
    for seq in sequences:
        success, msg = convert_sequence_with_preset(
            seq,
            preset_key,
            sequence_directory=directory,
        )
        if success:
            success_count += 1
        else:
            failure_count += 1
            failed_items.append((f"Sequence: {str(seq)}", msg))
    
    # Convert movies
    for movie in movies:
        success, msg = convert_movie_with_preset(
            movie,
            preset_key,
        )
        if success:
            success_count += 1
        else:
            failure_count += 1
            failed_items.append((f"Movie: {movie.name}", msg))
    
    console.print("\n" + "=" * 60)
    if success_count > 0:
        console.print(f"[green]SUCCESS: Converted {success_count} item(s)[/green]")
    if failure_count > 0:
        console.print(f"[red]FAILED: Could not convert {failure_count} item(s)[/red]")
        for item_name, error in failed_items:
            console.print(f"  [red]- {item_name}: {error[:100]}[/red]")
    
    console.print("\n[dim]Press any key to close...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass

def encode_multi_output(directory: Path) -> None:
    """Encode using multi-output configuration (non-interactive).
    
    Args:
        directory: Directory to process
    """
    console.print(Panel.fit(
        "[bold blue]ZilKit - Encode To Movie (Multi-Output)[/bold blue]",
        border_style="blue"
    ))
    
    config = get_config()
    if not config.is_ffmpeg_available():
        console.print("[red]ERROR: FFmpeg is not available![/red]")
        return
    
    multi_config = config.get_default_multi_output_config()
    if not multi_config:
        console.print("[red]ERROR: Multi-output configuration not set![/red]")
        console.print("[yellow]Please configure default settings first.[/yellow]")
        console.print("\n[dim]Press any key to close...[/dim]")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass
        return
    
    conversions = multi_config.get("conversions", [])
    if not conversions:
        console.print("[red]ERROR: No conversions configured in multi-output setup![/red]")
        return
    
    user_initials = multi_config.get("user_initials", "")
    hap_chunk_count = config.get_hap_chunk_count()
    
    console.print(f"[green]Multi-output configuration:[/green] [cyan]{len(conversions)} conversion(s)[/cyan]")
    if user_initials:
        console.print(f"[green]User initials:[/green] [cyan]{user_initials}[/cyan]")
    
    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]ERROR: Directory does not exist: {directory}[/red]")
        return
    
    console.print(f"\n[bold]Scanning directory:[/bold] [cyan]{directory}[/cyan]")
    sequences = find_image_sequences(directory)
    movies = find_movie_files(directory)
    
    if not sequences and not movies:
        console.print("[yellow]WARNING: No image sequences or movie files found.[/yellow]")
        return
    
    total_items = len(sequences) + len(movies)
    console.print(f"\n[green]Found [bold]{len(sequences)}[/bold] image sequence(s) and [bold]{len(movies)}[/bold] movie file(s):[/green]")
    
    if sequences:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Sequence", style="cyan")
        table.add_column("Frames", justify="right")
        for seq in sequences:
            table.add_row(str(seq), str(len(seq)))
        console.print(table)
    
    if movies:
        if sequences:
            console.print("\n[bold]Movie Files:[/bold]")
        for movie in movies:
            console.print(f"  [cyan]- {movie.name}[/cyan]")
    
    # Display preview of what will be converted
    console.print(f"\n[bold]Conversion Preview:[/bold]")
    console.print(f"[green]Items to convert:[/green] [cyan]{total_items}[/cyan] (sequences: {len(sequences)}, movies: {len(movies)})")
    console.print(f"[green]Outputs per item:[/green] [cyan]{len(conversions)}[/cyan]")
    console.print(f"[green]Total conversions:[/green] [cyan]{total_items * len(conversions)}[/cyan]")
    
    console.print(f"\n[bold]Configured Conversions:[/bold]")
    for conv_idx, conversion in enumerate(conversions, 1):
        preset_key = conversion.get("preset")
        preset = config.get_preset(preset_key) if preset_key else None
        preset_name = preset.get("display_name", preset_key) if preset else "Unknown"
        resolution = conversion.get("resolution", "full")
        framerate = conversion.get("framerate", 30)
        custom_text = conversion.get("filename_suffix", "")
        
        console.print(f"\n  [bold]Conversion {conv_idx}:[/bold]")
        console.print(f"    Preset: [cyan]{preset_name}[/cyan]")
        console.print(f"    Resolution: [cyan]{resolution}[/cyan]")
        console.print(f"    Framerate: [cyan]{framerate} fps[/cyan]")
        if custom_text:
            console.print(f"    Filename suffix: [cyan]{custom_text}[/cyan]")
        if user_initials:
            console.print(f"    User initials: [cyan]{user_initials}[/cyan]")
    
    # Generate output paths for preview
    from zilkit.core.ffmpeg_ops import generate_output_filename, generate_movie_output_filename
    preview_outputs = []
    
    for seq in sequences:
        for conv_idx, conversion in enumerate(conversions, 1):
            preset_key = conversion.get("preset")
            if not preset_key:
                continue
            preset = config.get_preset(preset_key)
            if not preset:
                continue
            custom_text = conversion.get("filename_suffix", "")
            output_path = generate_output_filename(
                seq,
                preset,
                custom_text=custom_text,
                user_initials=user_initials,
                sequence_directory=directory,
            )
            preset_name = preset.get("display_name", preset_key)
            preview_outputs.append((f"Sequence: {str(seq)}", output_path, f"Conversion {conv_idx}", preset_name))
    
    for movie in movies:
        for conv_idx, conversion in enumerate(conversions, 1):
            preset_key = conversion.get("preset")
            if not preset_key:
                continue
            preset = config.get_preset(preset_key)
            if not preset:
                continue
            custom_text = conversion.get("filename_suffix", "")
            output_path = generate_movie_output_filename(
                movie,
                preset,
                custom_text=custom_text,
                user_initials=user_initials,
            )
            preset_name = preset.get("display_name", preset_key)
            preview_outputs.append((f"Movie: {movie.name}", output_path, f"Conversion {conv_idx}", preset_name))
    
    # Display preview of output files
    if preview_outputs:
        console.print(f"\n[bold]Output Files Preview:[/bold]")
        for item_name, output_path, conv_info, preset_name in preview_outputs:
            console.print(f"  {item_name} ({conv_info} - {preset_name})")
            console.print(f"    [dim]→ {output_path.resolve()}[/dim]")
    
    console.print(f"\n[yellow]Press any key to continue with conversion...[/yellow]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        console.print("\n[yellow]Conversion cancelled by user.[/yellow]")
        return
    
    console.print(f"\n[bold]Converting {total_items} item(s) with {len(conversions)} output(s) each...[/bold]")
    console.print("[dim]FFmpeg progress will be shown below:[/dim]\n")
    
    total_success = 0
    total_failure = 0
    failed_conversions = []
    successful_outputs = []  # Track successful conversions with full paths
    
    # Convert sequences
    for seq in sequences:
        for conv_idx, conversion in enumerate(conversions, 1):
            preset_key = conversion.get("preset")
            if not preset_key:
                logger.error(f"Conversion {conv_idx} missing preset")
                continue
            
            preset = config.get_preset(preset_key)
            if not preset:
                error_msg = f"Preset '{preset_key}' not found for conversion {conv_idx}"
                logger.error(error_msg)
                total_failure += 1
                failed_conversions.append((f"Sequence: {str(seq)}", f"Conversion {conv_idx}: {error_msg}"))
                continue
            
            resolution_str = conversion.get("resolution", "full")
            resolution_scale = _get_resolution_scale(resolution_str)
            framerate = conversion.get("framerate", 30)
            custom_text = conversion.get("filename_suffix", "")
            
            # Get HAP chunk count if this is a HAP codec
            chunk_count = hap_chunk_count if preset.get("codec") == "hap" else 1
            
            console.print(f"\n[bold]Conversion {conv_idx}/{len(conversions)}:[/bold] [cyan]{preset.get('display_name', preset_key)}[/cyan]")
            
            success, msg = convert_sequence_with_preset(
                seq,
                preset_key,
                sequence_directory=directory,
                resolution_scale=resolution_scale,
                framerate=framerate,
                custom_text=custom_text,
                user_initials=user_initials,
                hap_chunk_count=chunk_count,
            )
            
            if success:
                total_success += 1
                # Generate output path to track it
                output_path = generate_output_filename(
                    seq,
                    preset,
                    custom_text=custom_text,
                    user_initials=user_initials,
                    sequence_directory=directory,
                )
                successful_outputs.append((f"Sequence: {str(seq)}", str(output_path.resolve()), f"Conversion {conv_idx}"))
            else:
                total_failure += 1
                failed_conversions.append((f"Sequence: {str(seq)}", f"Conversion {conv_idx}: {msg}"))
    
    # Convert movies
    for movie in movies:
        for conv_idx, conversion in enumerate(conversions, 1):
            preset_key = conversion.get("preset")
            if not preset_key:
                logger.error(f"Conversion {conv_idx} missing preset")
                continue
            
            preset = config.get_preset(preset_key)
            if not preset:
                error_msg = f"Preset '{preset_key}' not found for conversion {conv_idx}"
                logger.error(error_msg)
                total_failure += 1
                failed_conversions.append((f"Movie: {movie.name}", f"Conversion {conv_idx}: {error_msg}"))
                continue
            
            resolution_str = conversion.get("resolution", "full")
            resolution_scale = _get_resolution_scale(resolution_str)
            framerate = conversion.get("framerate", 30)
            custom_text = conversion.get("filename_suffix", "")
            
            # Get HAP chunk count if this is a HAP codec
            chunk_count = hap_chunk_count if preset.get("codec") == "hap" else 1
            
            console.print(f"\n[bold]Conversion {conv_idx}/{len(conversions)}:[/bold] [cyan]{preset.get('display_name', preset_key)}[/cyan]")
            
            success, msg = convert_movie_with_preset(
                movie,
                preset_key,
                resolution_scale=resolution_scale,
                framerate=framerate,
                custom_text=custom_text,
                user_initials=user_initials,
                hap_chunk_count=chunk_count,
            )
            
            if success:
                total_success += 1
                # Generate output path to track it
                output_path = generate_movie_output_filename(
                    movie,
                    preset,
                    custom_text=custom_text,
                    user_initials=user_initials,
                )
                successful_outputs.append((f"Movie: {movie.name}", str(output_path.resolve()), f"Conversion {conv_idx}"))
            else:
                total_failure += 1
                failed_conversions.append((f"Movie: {movie.name}", f"Conversion {conv_idx}: {msg}"))
    
    console.print("\n" + "=" * 60)
    if total_success > 0:
        console.print(f"[green]SUCCESS: {total_success} conversion(s) completed[/green]")
        console.print(f"\n[bold]Output Files:[/bold]")
        for item_name, output_path, conv_info in successful_outputs:
            console.print(f"  [green]✓[/green] {item_name} ({conv_info})")
            console.print(f"    [dim]{output_path}[/dim]")
    if total_failure > 0:
        console.print(f"\n[red]FAILED: {total_failure} conversion(s) failed[/red]")
        for item_name, error in failed_conversions:
            console.print(f"  [red]✗ {item_name}: {error[:100]}[/red]")
    
    console.print("\n[dim]Press any key to close...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


def encode_recursive_interactive(directory: Path) -> None:
    """Encode recursively with interactive preset selection.
    
    Args:
        directory: Root directory to process
    """
    console.print(Panel.fit(
        "[bold blue]ZilKit - Encode To Movie (Recursive)[/bold blue]",
        border_style="blue"
    ))
    
    config = get_config()
    if not config.is_ffmpeg_available():
        console.print("[red]ERROR: FFmpeg is not available![/red]")
        return
    
    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]ERROR: Directory does not exist: {directory}[/red]")
        return
    
    console.print(f"\n[bold]Scanning directory recursively:[/bold] [cyan]{directory}[/cyan]")
    
    # Find all directories with sequences or movies
    all_directories = list(walk_directories(str(directory), recursive=True))
    directories_with_items = []
    
    for dir_path in all_directories:
        sequences = find_image_sequences(Path(dir_path))
        movies = find_movie_files(Path(dir_path))
        if sequences or movies:
            directories_with_items.append((Path(dir_path), sequences, movies))
    
    if not directories_with_items:
        console.print("[yellow]WARNING: No image sequences or movie files found in any subdirectory.[/yellow]")
        return
    
    # Display found items grouped by directory
    console.print(f"\n[green]Found [bold]{len(directories_with_items)}[/bold] directory(ies) with items:[/green]")
    for idx, (dir_path, sequences, movies) in enumerate(directories_with_items, 1):
        console.print(f"\n[bold]{idx}. {dir_path}[/bold]")
        for seq in sequences:
            console.print(f"   - {seq} ({len(seq)} frames)")
        for movie in movies:
            console.print(f"   - {movie.name} (movie file)")
    
    # Interactive preset selection
    console.print("\n[bold]Preset Selection Options:[/bold]")
    console.print("[1] Use same preset for all")
    console.print("[2] Select preset for each directory")
    console.print("[3] Use default preset for all")
    
    choice = Prompt.ask("\nEnter your choice", choices=["1", "2", "3"], default="3")
    
    presets = config.get_presets()
    preset_list = sorted(list(presets.items()))  # Sort for consistent ordering
    
    selected_presets = {}
    
    if choice == "1":
        # Same preset for all
        console.print("\n[bold]Available Presets:[/bold]")
        for idx, (key, preset) in enumerate(preset_list, 1):
            console.print(f"  {idx}. {preset.get('display_name', key)}")
        
        preset_idx = IntPrompt.ask("Select preset number", default=1)
        if 1 <= preset_idx <= len(preset_list):
            selected_key = preset_list[preset_idx - 1][0]
        for dir_path, _, _ in directories_with_items:
            selected_presets[dir_path] = selected_key
        else:
            console.print("[red]Invalid preset selection![/red]")
            return
    
    elif choice == "2":
        # Select preset for each directory
        for dir_path, sequences, movies in directories_with_items:
            console.print(f"\n[bold]Directory: {dir_path}[/bold]")
            if sequences:
                console.print(f"  Sequences: {len(sequences)}")
            if movies:
                console.print(f"  Movies: {len(movies)}")
            console.print("Available Presets:")
            for idx, (key, preset) in enumerate(preset_list, 1):
                console.print(f"  {idx}. {preset.get('display_name', key)}")
            
            preset_idx = IntPrompt.ask(f"Select preset for {dir_path.name}", default=1)
            if 1 <= preset_idx <= len(preset_list):
                selected_presets[dir_path] = preset_list[preset_idx - 1][0]
            else:
                console.print(f"[yellow]Invalid selection, using default preset for {dir_path.name}[/yellow]")
                default_preset = config.get_default_preset()
                if default_preset:
                    selected_presets[dir_path] = default_preset
    
    elif choice == "3":
        # Default preset for all
        default_preset = config.get_default_preset()
        if not default_preset:
            console.print("[red]ERROR: No default preset configured![/red]")
            return
        for dir_path, _, _ in directories_with_items:
            selected_presets[dir_path] = default_preset
    
    # Perform conversions
    console.print(f"\n[bold]Converting items...[/bold]")
    console.print("[dim]FFmpeg progress will be shown below:[/dim]\n")
    
    total_success = 0
    total_failure = 0
    failed_items = []
    
    for dir_path, sequences, movies in directories_with_items:
        preset_key = selected_presets.get(dir_path)
        if not preset_key:
            continue
        
        preset = config.get_preset(preset_key)
        console.print(f"\n[bold]Processing: {dir_path}[/bold] ([cyan]{preset.get('display_name', preset_key)}[/cyan])")
        
        # Convert sequences
        for seq in sequences:
            success, msg = convert_sequence_with_preset(
                seq,
                preset_key,
                sequence_directory=dir_path,
            )
            if success:
                total_success += 1
            else:
                total_failure += 1
                failed_items.append((f"{dir_path.name}/Sequence: {str(seq)}", msg))
        
        # Convert movies
        for movie in movies:
            success, msg = convert_movie_with_preset(
                movie,
                preset_key,
            )
            if success:
                total_success += 1
            else:
                total_failure += 1
                failed_items.append((f"{dir_path.name}/Movie: {movie.name}", msg))
    
    console.print("\n" + "=" * 60)
    if total_success > 0:
        console.print(f"[green]SUCCESS: Converted {total_success} item(s)[/green]")
    if total_failure > 0:
        console.print(f"[red]FAILED: Could not convert {total_failure} item(s)[/red]")
        for item_name, error in failed_items:
            console.print(f"  [red]- {item_name}: {error[:100]}[/red]")
    
    console.print("\n[dim]Press any key to close...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


def configure_default_settings() -> None:
    """Interactive wizard to configure default settings with main menu."""
    console.print(Panel.fit(
        "[bold blue]ZilKit - Configure Default Settings[/bold blue]",
        border_style="blue"
    ))
    
    config = get_config()
    presets = config.get_presets()
    preset_list = sorted(list(presets.items()))  # Sort for consistent ordering
    
    if not preset_list:
        console.print("[red]ERROR: No presets available![/red]")
        return
    
    # Main menu loop
    while True:
        console.print("\n[bold]Main Menu[/bold]")
        console.print("  1. Set Default Preset")
        console.print("  2. Multi-Output Configuration")
        console.print("  3. Advanced Settings")
        console.print("\n[dim]Close this window to exit (all changes are saved automatically)[/dim]")
        
        choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3"], default="1")
        
        if choice == "1":
            _configure_default_preset(config, preset_list, presets)
        elif choice == "2":
            _configure_multi_output(config, preset_list)
        elif choice == "3":
            _configure_preset_settings(config, preset_list, presets)
    
    console.print("\n[dim]Press any key to close...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


def _configure_default_preset(config, preset_list, presets) -> None:
    """Configure the default preset."""
    console.print("\n[bold]Set Default Preset[/bold]\n")
    console.print("Available presets:")
    
    current_default_key = config.get_default_preset()
    current_default_idx = None
    
    for idx, (key, preset) in enumerate(preset_list, 1):
        current = " (current default)" if key == current_default_key else ""
        console.print(f"  {idx}. {preset.get('display_name', key)}{current}")
        if key == current_default_key:
            current_default_idx = idx
    
    console.print()  # Blank line for readability
    
    # Use current default as the default value, or 1 if no default set
    default_value = current_default_idx if current_default_idx else 1
    preset_idx = IntPrompt.ask(f"Select default preset number (currently: {presets[current_default_key].get('display_name', current_default_key) if current_default_key else 'none'})", default=default_value)
    
    if 1 <= preset_idx <= len(preset_list):
        default_preset_key = preset_list[preset_idx - 1][0]
        config.set_default_preset(default_preset_key)
        console.print(f"\n[green]Default preset set to: {presets[default_preset_key].get('display_name', default_preset_key)}[/green]\n")
    else:
        console.print("\n[yellow]Invalid selection, keeping current default.[/yellow]\n")


def _configure_multi_output(config, preset_list) -> None:
    """Configure multi-output settings."""
    console.print("\n[bold]Multi-Output Configuration[/bold]")
    
    existing_config = config.get_default_multi_output_config()
    if existing_config:
        console.print("[yellow]Current configuration exists. This will replace it.[/yellow]")
        console.print("\n[bold]Current Configuration:[/bold]")
        
        user_initials = existing_config.get("user_initials", "")
        hap_chunk_count = existing_config.get("hap_chunk_count", 1)
        conversions = existing_config.get("conversions", [])
        
        if user_initials:
            console.print(f"  - User initials: {user_initials}")
        console.print(f"  - HAP chunk count: {hap_chunk_count}")
        console.print(f"  - Number of conversions: {len(conversions)}")
        
        if conversions:
            console.print("\n  [bold]Conversions:[/bold]")
            for idx, conversion in enumerate(conversions, 1):
                preset_key = conversion.get("preset")
                preset = config.get_preset(preset_key) if preset_key else None
                preset_name = preset.get("display_name", preset_key) if preset else "Unknown"
                resolution = conversion.get("resolution", "full")
                framerate = conversion.get("framerate", 30)
                custom_text = conversion.get("filename_suffix", "")
                
                console.print(f"\n    [bold]Conversion {idx}:[/bold]")
                console.print(f"      Preset: {preset_name}")
                console.print(f"      Resolution: {resolution}")
                console.print(f"      Framerate: {framerate} fps")
                if custom_text:
                    console.print(f"      Filename suffix: {custom_text}")
        
        if not Confirm.ask("\nContinue?", default=True):
            return
    
    # User initials
    console.print("\n[bold]User Initials[/bold]")
    user_initials = Prompt.ask("Enter your initials (will be added to all filenames)", default="")
    if user_initials:
        # Remove periods and spaces
        user_initials = user_initials.replace(".", "").replace(" ", "").upper()
    
    # HAP chunk count
    console.print("\n[bold]HAP Chunk Count[/bold]")
    hap_chunk_count = IntPrompt.ask("Enter HAP chunk count (for HAP codecs)", default=1)
    if hap_chunk_count < 1:
        hap_chunk_count = 1
    
    # Number of conversions
    console.print("\n[bold]Number of Conversions[/bold]")
    num_conversions = IntPrompt.ask("How many conversions per sequence?", default=2)
    if num_conversions < 1:
        num_conversions = 1
    
    conversions = []
    
    for conv_num in range(1, num_conversions + 1):
        console.print(f"\n[bold]Conversion {conv_num}/{num_conversions}[/bold]")
        
        # Preset selection
        console.print("Available presets:")
        for idx, (key, preset) in enumerate(preset_list, 1):
            console.print(f"  {idx}. {preset.get('display_name', key)}")
        
        preset_idx = IntPrompt.ask(f"Select preset for conversion {conv_num}", default=1)
        if 1 <= preset_idx <= len(preset_list):
            preset_key = preset_list[preset_idx - 1][0]
        else:
            console.print("[yellow]Invalid selection, using default preset.[/yellow]")
            preset_key = config.get_default_preset() or preset_list[0][0]
        
        # Resolution - use reusable function
        resolution = _prompt_resolution("full", allow_clear=False) or "full"
        
        # Framerate
        framerate = IntPrompt.ask("Enter framerate (fps)", default=30)
        if framerate < 1:
            framerate = 30
        
        # Custom text
        custom_text = Prompt.ask("Enter custom text for filename (optional, no periods)", default="")
        if custom_text:
            # Remove periods
            custom_text = custom_text.replace(".", "")
        
        conversions.append({
            "preset": preset_key,
            "resolution": resolution,
            "framerate": framerate,
            "filename_suffix": custom_text,
        })
    
    # Check if any conversion uses HAP codec - only then prompt for HAP chunk count
    uses_hap = False
    for conv in conversions:
        preset_key = conv.get("preset")
        preset = config.get_preset(preset_key)
        if preset and preset.get("codec") == "hap":
            uses_hap = True
            break
    
    if uses_hap:
        console.print("\n[bold]HAP Chunk Count[/bold]")
        hap_chunk_count = IntPrompt.ask("Enter HAP chunk count (for HAP codecs)", default=1)
        if hap_chunk_count < 1:
            hap_chunk_count = 1
    else:
        hap_chunk_count = 1  # Default if no HAP codecs used
    
    # Save multi-output configuration
    multi_config = {
        "user_initials": user_initials,
        "hap_chunk_count": hap_chunk_count,
        "conversions": conversions,
    }
    config.set_default_multi_output_config(multi_config)
    console.print(f"\n[green]Multi-output configuration saved![/green]")
    console.print(f"  - User initials: {user_initials or '(none)'}")
    console.print(f"  - HAP chunk count: {hap_chunk_count}")
    console.print(f"  - Conversions: {len(conversions)}")


def _configure_preset_settings(config, preset_list, presets) -> None:
    """Configure preset settings and global overrides."""
    console.print("\n[bold]Advanced Settings[/bold]")
    console.print("  1. Configure Individual Preset")
    console.print("  2. Configure Global Overrides")
    console.print("  3. Reset Individual Preset to Defaults")
    console.print("  4. Reset All Individual Presets to Defaults")
    console.print("  5. Reset Global Overrides to Defaults")
    console.print("  0. Back to Main Menu")
    
    choice = Prompt.ask("\nSelect an option", choices=["0", "1", "2", "3", "4", "5"], default="0")
    
    if choice == "0":
        return
    elif choice == "1":
        _configure_individual_preset(config, preset_list, presets)
    elif choice == "2":
        _configure_global_overrides(config)
    elif choice == "3":
        _reset_individual_preset(config, preset_list, presets)
    elif choice == "4":
        _reset_all_individual_presets(config, preset_list)
    elif choice == "5":
        _reset_global_overrides(config)


def _configure_individual_preset(config, preset_list, presets) -> None:
    """Configure settings for an individual preset."""
    console.print("\n[bold]Select Preset to Configure[/bold]")
    for idx, (key, preset) in enumerate(preset_list, 1):
        console.print(f"  {idx}. {preset.get('display_name', key)}")
    
    console.print()  # Blank line for readability
    preset_idx = IntPrompt.ask("Select preset number", default=1)
    if not (1 <= preset_idx <= len(preset_list)):
        console.print("[yellow]Invalid selection.[/yellow]")
        return
    
    preset_key = preset_list[preset_idx - 1][0]
    preset = presets[preset_key]
    current_overrides = config.get_preset_override(preset_key) or {}
    
    console.print(f"\n[bold]Configuring: {preset.get('display_name', preset_key)}[/bold]")
    console.print("[dim]Leave blank to keep current/default value[/dim]")
    
    overrides = {}
    
    # Framerate
    current_framerate = current_overrides.get("framerate", preset.get("framerate", 30))
    console.print()  # Blank line for readability
    framerate_str = Prompt.ask("Framerate (fps)", default=str(current_framerate) if current_framerate else "")
    if framerate_str:
        try:
            overrides["framerate"] = int(framerate_str)
        except ValueError:
            console.print("[yellow]Invalid framerate, keeping current.[/yellow]")
    
    # Resolution - use reusable function
    current_resolution = current_overrides.get("resolution", "full")
    res_result = _prompt_resolution(current_resolution, allow_clear=False)
    if res_result:
        overrides["resolution"] = res_result
    
    # Codec-specific settings
    codec = preset.get("codec")
    
    # CRF for H.264
    if codec == "libx264":
        current_crf = current_overrides.get("crf", 23)
        crf_str = Prompt.ask("CRF (Constant Rate Factor, 18-28, lower = higher quality)", default=str(current_crf))
        if crf_str:
            try:
                crf = int(crf_str)
                if 18 <= crf <= 28:
                    overrides["crf"] = crf
                else:
                    console.print("[yellow]Invalid CRF (must be 18-28), keeping current.[/yellow]")
            except ValueError:
                console.print("[yellow]Invalid CRF, keeping current.[/yellow]")
    
    elif codec == "hap":
        # HAP Chunk Count
        current_chunk_count = current_overrides.get("hap_chunk_count", 1)
        chunk_count_str = Prompt.ask("HAP Chunk Count (1-8)", default=str(current_chunk_count))
        if chunk_count_str:
            try:
                chunk_count = int(chunk_count_str)
                if 1 <= chunk_count <= 8:
                    overrides["hap_chunk_count"] = chunk_count
                else:
                    console.print("[yellow]Invalid chunk count (must be 1-8), keeping current.[/yellow]")
            except ValueError:
                console.print("[yellow]Invalid chunk count, keeping current.[/yellow]")
    
    # Alpha channel (for HAP and ProRes 4444)
    if codec == "hap" or (codec == "prores_ks" and preset.get("profile_v") in ["4", "5"]):
        current_alpha = current_overrides.get("alpha", None)
        if current_alpha is None:
            # Check if format/profile already indicates alpha
            if codec == "hap":
                current_alpha = preset.get("format", "hap") == "hap_alpha"
            else:
                current_alpha = preset.get("pix_fmt", "").startswith("yuva")
        
        alpha_enabled = Confirm.ask("Enable alpha channel?", default=current_alpha)
        overrides["alpha"] = alpha_enabled
        
        # Update format/pixel format based on alpha setting
        if codec == "hap":
            if alpha_enabled:
                # If format is hap (not hap_q), change to hap_alpha
                current_format = overrides.get("format", preset.get("format", "hap"))
                if current_format == "hap":
                    overrides["format"] = "hap_alpha"
                # If format is hap_q, keep it (HAP Q doesn't have separate alpha format)
        elif codec == "prores_ks":
            if alpha_enabled:
                overrides["pix_fmt"] = "yuva444p10le"
            else:
                overrides["pix_fmt"] = "yuv444p10le"
    
    # Save overrides
    if overrides:
        config.set_preset_override(preset_key, overrides)
        console.print(f"\n[green]Overrides saved for {preset.get('display_name', preset_key)}![/green]\n")
    else:
        console.print("\n[yellow]No changes made.[/yellow]\n")
    
    # Return to Advanced Settings menu (not Main Menu)
    _configure_preset_settings(config, preset_list, presets)


def _configure_global_overrides(config) -> None:
    """Configure global override settings."""
    console.print("\n[bold]Global Overrides[/bold]")
    console.print("[yellow]Note: Global overrides apply to all presets (except multi-output)[/yellow]")
    console.print("[dim]Leave blank to keep current/default value[/dim]")
    
    current_overrides = config.get_global_overrides()
    overrides = {}
    
    # Framerate
    current_framerate = current_overrides.get("framerate")
    framerate_str = Prompt.ask("Framerate (fps)", default=str(current_framerate) if current_framerate else "")
    if framerate_str:
        try:
            overrides["framerate"] = int(framerate_str)
        except ValueError:
            console.print("[yellow]Invalid framerate.[/yellow]")
    
    # Resolution - use reusable function
    current_resolution = current_overrides.get("resolution")
    res_result = _prompt_resolution(current_resolution, allow_clear=True)
    if res_result is not None:
        if res_result:  # Not empty string
            overrides["resolution"] = res_result
        # If res_result is None, we want to clear it, so don't set it
    
    # Alpha channel (global - applies to HAP and ProRes 4444)
    current_alpha = current_overrides.get("alpha")
    if current_alpha is not None:
        alpha_enabled = Confirm.ask("Enable alpha channel globally?", default=current_alpha)
        overrides["alpha"] = alpha_enabled
    else:
        alpha_enabled = Confirm.ask("Enable alpha channel globally?", default=False)
        if alpha_enabled:
            overrides["alpha"] = True
    
    # HAP Chunk Count (global - applies to all HAP codecs)
    current_hap_chunk = current_overrides.get("hap_chunk_count")
    if current_hap_chunk is not None:
        hap_chunk_str = Prompt.ask("HAP Chunk Count (1-8, global)", default=str(current_hap_chunk))
    else:
        hap_chunk_str = Prompt.ask("HAP Chunk Count (1-8, global)", default="")
    if hap_chunk_str:
        try:
            hap_chunk = int(hap_chunk_str)
            if 1 <= hap_chunk <= 8:
                overrides["hap_chunk_count"] = hap_chunk
            else:
                console.print("[yellow]Invalid chunk count (must be 1-8).[/yellow]")
        except ValueError:
            console.print("[yellow]Invalid chunk count.[/yellow]")
    
    # CRF for H.264 (global)
    current_crf = current_overrides.get("crf")
    if current_crf is not None:
        crf_str = Prompt.ask("CRF for H.264 (18-28, lower = higher quality, global)", default=str(current_crf))
    else:
        crf_str = Prompt.ask("CRF for H.264 (18-28, lower = higher quality, global)", default="")
    if crf_str:
        try:
            crf = int(crf_str)
            if 18 <= crf <= 28:
                overrides["crf"] = crf
            else:
                console.print("[yellow]Invalid CRF (must be 18-28).[/yellow]")
        except ValueError:
            console.print("[yellow]Invalid CRF.[/yellow]")
    
    # Save global overrides
    config.set_global_overrides(overrides)
    console.print(f"\n[green]Global overrides saved![/green]")


def _reset_individual_preset(config, preset_list, presets) -> None:
    """Reset an individual preset to defaults."""
    console.print("\n[bold]Select Preset to Reset[/bold]")
    presets_with_overrides = []
    for idx, (key, preset) in enumerate(preset_list, 1):
        has_overrides = config.get_preset_override(key) is not None
        if has_overrides:
            presets_with_overrides.append((idx, key, preset))
        override_indicator = " (has overrides)" if has_overrides else ""
        console.print(f"  {idx}. {preset.get('display_name', key)}{override_indicator}")
    
    console.print("  0. Back to Advanced Settings menu")
    
    if not presets_with_overrides:
        console.print("[yellow]No presets have overrides to reset.[/yellow]")
        preset_idx = IntPrompt.ask("\nSelect an option", default=0)
        if preset_idx == 0:
            return
        return
    
    preset_idx = IntPrompt.ask("\nSelect preset number (or 0 to go back)", default=1)
    if preset_idx == 0:
        return
    if not (1 <= preset_idx <= len(preset_list)):
        console.print("[yellow]Invalid selection.[/yellow]")
        return
    
    preset_key = preset_list[preset_idx - 1][0]
    preset = config.get_preset(preset_key)
    
    if config.get_preset_override(preset_key):
        if Confirm.ask(f"Reset '{preset.get('display_name', preset_key)}' to defaults?", default=True):
            config.clear_preset_override(preset_key)
            console.print(f"[green]Preset '{preset.get('display_name', preset_key)}' reset to defaults![/green]")
        else:
            console.print("[yellow]Reset cancelled.[/yellow]")
    else:
        console.print("[yellow]This preset has no overrides to reset.[/yellow]")


def _reset_all_individual_presets(config, preset_list) -> None:
    """Reset all individual presets to defaults."""
    presets_with_overrides = []
    for key, preset in preset_list:
        if config.get_preset_override(key):
            presets_with_overrides.append((key, preset))
    
    if not presets_with_overrides:
        console.print("[yellow]No presets have overrides to reset.[/yellow]")
        return
    
    console.print(f"\n[bold]Found {len(presets_with_overrides)} preset(s) with overrides:[/bold]")
    for key, preset in presets_with_overrides:
        console.print(f"  - {preset.get('display_name', key)}")
    
    if Confirm.ask(f"\nReset all {len(presets_with_overrides)} preset(s) to defaults?", default=False):
        for key, preset in presets_with_overrides:
            config.clear_preset_override(key)
        console.print(f"[green]Reset {len(presets_with_overrides)} preset(s) to defaults![/green]")
    else:
        console.print("[yellow]Reset cancelled.[/yellow]")


def _reset_global_overrides(config) -> None:
    """Reset global overrides to defaults with confirmation."""
    current_overrides = config.get_global_overrides()
    
    if not current_overrides:
        console.print("[yellow]No global overrides to reset.[/yellow]")
        return
    
    console.print("\n[bold]Current Global Overrides:[/bold]")
    for key, value in current_overrides.items():
        if value is not None:
            # Format resolution values to avoid Rich hex color interpretation
            if key == "resolution" and isinstance(value, str) and "x" in str(value):
                # Display resolution with spaces around 'x' to prevent Rich hex color interpretation
                # Convert "1920x1080" to "1920 x 1080" for display
                try:
                    parts = str(value).split("x")
                    if len(parts) == 2:
                        display_value = f"{parts[0]} x {parts[1]}"
                        console.print(f"  - {key}: {display_value}")
                    else:
                        console.print(f"  - {key}: {value}")
                except Exception:
                    console.print(f"  - {key}: {value}")
            else:
                console.print(f"  - {key}: {value}")
    
    if Confirm.ask("\nReset all global overrides to defaults?", default=False):
        config.clear_global_overrides()
        console.print("[green]Global overrides cleared![/green]")
    else:
        console.print("[yellow]Reset cancelled.[/yellow]")

