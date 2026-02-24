"""FFmpeg operations for ZilKit.

This module handles image sequence detection and conversion to video using FFmpeg.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pyseq import Sequence, get_sequences

from zilkit.config import get_config
from zilkit.utils.file_utils import walk_directories
from zilkit.utils.logger import get_logger

logger = get_logger(__name__)

# Exclude .exr files as they require special handling
# Exclude movie file extensions - they should be detected separately, not as sequences
EXCLUDED_EXTENSIONS = {".exr", ".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v"}

# Movie file extensions for separate detection
MOVIE_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v", ".mpg", ".mpeg", ".m2v", ".mxf"}


def find_image_sequences(directory: Path) -> List[Sequence]:
    """Find image sequences in a directory using pyseq.
    
    Excludes .exr files as they require special handling.
    Excludes directories - only actual files are included in sequences.
    
    Args:
        directory: Directory to search for image sequences
    
    Returns:
        List of Sequence objects representing found sequences
    
    Example:
        >>> sequences = find_image_sequences(Path("C:\\Images"))
        >>> for seq in sequences:
        ...     print(f"Found sequence: {seq}")
    """
    sequences = []
    
    try:
        # Use pyseq's get_sequences to find all sequences in directory
        all_sequences = get_sequences(str(directory))
        
        for seq in all_sequences:
            # Check if sequence has excluded extension
            # Get extension from first frame
            try:
                first_frame = Path(seq[0])
                ext = first_frame.suffix.lower()
                
                if ext in EXCLUDED_EXTENSIONS:
                    logger.debug(f"Skipping sequence with excluded extension: {seq}")
                    continue
                
                # Verify all items in sequence are actual files, not directories
                all_files = True
                for item in seq:
                    item_path = Path(item)
                    # If path is relative, make it relative to the directory
                    if not item_path.is_absolute():
                        item_path = directory / item_path
                    # Check if it's a file (not a directory)
                    if not item_path.is_file():
                        all_files = False
                        logger.debug(f"Skipping sequence with non-file item: {seq} (contains: {item_path})")
                        break
                
                if not all_files:
                    continue
                    
            except (IndexError, AttributeError):
                continue
            
            # Only include sequences with multiple frames
            if len(seq) > 1:
                sequences.append(seq)
                logger.debug(f"Found image sequence: {seq} ({len(seq)} frames)")
    
    except Exception as e:
        logger.error(f"Error finding sequences in {directory}: {e}")
    
    return sequences


def find_movie_files(directory: Path) -> List[Path]:
    """Find movie files in a directory.
    
    Args:
        directory: Directory to search for movie files
    
    Returns:
        List of Path objects representing found movie files
    
    Example:
        >>> movies = find_movie_files(Path("C:\\Videos"))
        >>> for movie in movies:
        ...     print(f"Found movie: {movie}")
    """
    movies = []
    
    try:
        for file_path in directory.iterdir():
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in MOVIE_EXTENSIONS:
                    movies.append(file_path)
                    logger.debug(f"Found movie file: {file_path}")
    except Exception as e:
        logger.error(f"Error finding movie files in {directory}: {e}")
    
    return movies


def build_ffmpeg_command(
    input_pattern: str,
    output_path: Path,
    start_number: int = 0,
    resolution_scale: float = 1.0,
    crf: int = 23,
    preset: str = "medium",
    pixel_format: str = "yuv420p",
    framerate: Optional[int] = None,
) -> List[str]:
    """Build FFmpeg command for converting image sequence to video.
    
    Args:
        input_pattern: Input pattern for image sequence (e.g., "frame_%04d.png")
        output_path: Output video file path
        resolution_scale: Resolution scale factor (1.0 = full, 0.5 = half, etc.)
        crf: Constant Rate Factor (18-28, lower = higher quality)
        preset: Encoding speed preset (ultrafast, fast, medium, slow, etc.)
        pixel_format: Pixel format (yuv420p, yuv422p, etc.)
        framerate: Output framerate (None = use input framerate)
    
    Returns:
        List of command arguments for subprocess
    
    Example:
        >>> cmd = build_ffmpeg_command("frame_%04d.png", Path("output.mp4"), 0.5, 23)
    """
    config = get_config()
    ffmpeg_path = config.get_ffmpeg_path()
    
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not available")
    
    cmd = [ffmpeg_path, "-y"]  # -y to overwrite output files

    # Input pattern - use start_number to specify where sequence starts
    # The pattern should be the full path with %0Nd format
    # Set input framerate to ensure correct timing
    # Use -f image2 to explicitly tell FFmpeg these are image files
    if framerate:
        cmd.extend(["-framerate", str(framerate)])

    cmd.extend(["-f", "image2", "-start_number", str(start_number), "-i", input_pattern])

    # Build video filter chain for scaling and color handling
    #
    # After experimentation and comparison with Adobe Media Encoder, the
    # combination below matches the expected color/brightness:
    #
    #   zscale=rangein=full:
    #          primariesin=bt709:
    #          transferin=iec61966-2-1:
    #          matrixin=bt709:
    #          range=tv:
    #          primaries=bt709:
    #          transfer=bt709:
    #          matrix=bt709,
    #   format=yuv420p
    #
    # This corresponds to:
    # - Full-range sRGB (IEC61966-2-1) source using Rec.709 primaries
    # - Conversion to TV-range Rec.709 video
    filters = []

    # Optional scaling first (done before color conversion)
    if resolution_scale != 1.0:
        filters.append(f"scale=iw*{resolution_scale}:ih*{resolution_scale}")

    # Color space and range conversion matching the known-good command
    zscale_filter = (
        "zscale="
        "rangein=full:"
        "primariesin=bt709:"
        "transferin=iec61966-2-1:"
        "matrixin=bt709:"
        "range=tv:"
        "primaries=bt709:"
        "transfer=bt709:"
        "matrix=bt709"
    )
    filters.append(zscale_filter)

    # Final output pixel format
    filters.append(f"format={pixel_format}")

    cmd.extend(["-vf", ",".join(filters)])

    # Output framerate (should match input)
    if framerate:
        cmd.extend(["-r", str(framerate)])

    # Video codec and quality settings
    # Align with Media Encoder style defaults where possible
    cmd.extend(
        [
            "-c:v",
            "libx264",
            "-crf",
            str(crf),
            "-preset",
            preset,
            "-profile:v",
            "high",
            "-level",
            "4.2",
            "-pix_fmt",
            pixel_format,
            "-movflags",
            "+faststart",
        ]
    )
    
    # Output file
    cmd.append(str(output_path))
    
    return cmd


def build_ffmpeg_command_from_preset(
    input_pattern: str,
    output_path: Path,
    preset: Dict,
    start_number: int = 0,
    resolution_scale: Optional[float] = None,
    framerate: Optional[int] = None,
    hap_chunk_count: int = 1,
) -> List[str]:
    """Build FFmpeg command from a preset configuration.
    
    Args:
        input_pattern: Input pattern for image sequence (e.g., "frame_%04d.png")
        output_path: Output video file path
        preset: Preset configuration dict from presets.json
        start_number: Starting frame number
        resolution_scale: Optional resolution scale (overrides preset default of 1.0)
        framerate: Optional framerate (overrides preset default of 30fps)
        hap_chunk_count: HAP chunk count (for HAP codecs only)
    
    Returns:
        List of command arguments for subprocess
    
    Example:
        >>> preset = config.get_preset("prores-4444")
        >>> cmd = build_ffmpeg_command_from_preset("frame_%04d.png", Path("out.mov"), preset)
    """
    config = get_config()
    ffmpeg_path = config.get_ffmpeg_path()
    
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not available")
    
    codec = preset.get("codec")
    if not codec:
        raise ValueError("Preset missing 'codec' field")
    
    # Default resolution and framerate (presets default to full res, 30fps)
    if resolution_scale is None:
        resolution_scale = 1.0
    if framerate is None:
        framerate = 30
    
    cmd = [ffmpeg_path, "-y"]  # -y to overwrite output files
    
    # Input pattern
    if framerate:
        cmd.extend(["-framerate", str(framerate)])
    cmd.extend(["-f", "image2", "-start_number", str(start_number), "-i", input_pattern])
    
    # Build video filter chain
    filters = []
    
    # Optional scaling
    if resolution_scale != 1.0:
        filters.append(f"scale=iw*{resolution_scale}:ih*{resolution_scale}")
    
    # Get pixel format from preset
    pixel_format = preset.get("pix_fmt", "yuv420p")
    
    # Color space conversion (for non-HAP codecs)
    if codec != "hap":
        zscale_filter = (
            "zscale="
            "rangein=full:"
            "primariesin=bt709:"
            "transferin=iec61966-2-1:"
            "matrixin=bt709:"
            "range=tv:"
            "primaries=bt709:"
            "transfer=bt709:"
            "matrix=bt709"
        )
        filters.append(zscale_filter)
        filters.append(f"format={pixel_format}")
    
    if filters:
        cmd.extend(["-vf", ",".join(filters)])
    
    # Output framerate
    if framerate:
        cmd.extend(["-r", str(framerate)])
    
    # Codec-specific settings
    if codec == "libx264":
        # H.264 encoding
        cmd.extend([
            "-c:v", "libx264",
            "-crf", "23",  # Default CRF
            "-preset", "medium",  # Default preset
            "-profile:v", "high",
            "-level", "4.2",
            "-pix_fmt", pixel_format,
            "-movflags", "+faststart",
        ])
    elif codec == "prores_ks":
        # ProRes encoding
        profile_v = preset.get("profile_v")
        vendor = preset.get("vendor", "apl0")
        cmd.extend([
            "-c:v", "prores_ks",
            "-profile:v", str(profile_v),
            "-vendor", vendor,
            "-pix_fmt", pixel_format,
        ])
    elif codec == "hap":
        # HAP encoding
        hap_format = preset.get("format", "hap")
        cmd.extend([
            "-c:v", "hap",
            "-format", hap_format,
            "-chunks", str(hap_chunk_count),
        ])
    else:
        raise ValueError(f"Unsupported codec: {codec}")
    
    # Output file
    cmd.append(str(output_path))
    
    return cmd


def convert_sequence_to_video(
    sequence: Sequence,
    output_dir: Optional[Path] = None,
    sequence_directory: Optional[Path] = None,
    resolution_scale: float = 1.0,
    crf: int = 23,
    preset: str = "medium",
    pixel_format: str = "yuv420p",
    framerate: Optional[int] = None,
) -> Tuple[bool, str]:
    """Convert an image sequence to MP4 video.
    
    Args:
        sequence: pyseq.Sequence object representing the image sequence
        output_dir: Output directory (None = same as sequence directory)
        sequence_directory: Directory where sequence files are located (required)
        resolution_scale: Resolution scale factor
        crf: Constant Rate Factor
        preset: Encoding speed preset
        pixel_format: Pixel format
        framerate: Output framerate
    
    Returns:
        Tuple of (success: bool, message: str)
    
    Example:
        >>> seq = find_image_sequences(Path("C:\\Images"))[0]
        >>> success, msg = convert_sequence_to_video(seq, sequence_directory=Path("C:\\Images"))
    """
    try:
        # Get sequence directory - use provided directory or try to resolve from first frame
        if sequence_directory is not None:
            seq_dir = Path(sequence_directory).resolve()
        else:
            # Try to get from first frame path
            first_frame = Path(sequence[0])
            if first_frame.is_absolute():
                seq_dir = first_frame.parent.resolve()
            else:
                # If relative, we need the directory - this shouldn't happen if called correctly
                raise ValueError("sequence_directory must be provided when sequence paths are relative")
        
        # Determine output path
        if output_dir is None:
            output_dir = seq_dir
        
        # Generate output filename from sequence name
        # Use the first frame to extract base name, removing frame number
        import re
        first_frame_name = Path(sequence[0]).name  # Get just the filename, not path
        first_file = Path(first_frame_name)  # Use filename only for name extraction
        stem = first_file.stem
        
        # Remove frame number from stem
        # Handle patterns like: frame_001, frame001, JJ000, etc.
        # Remove trailing digits, and also handle underscore before digits
        base_name = re.sub(r'[_\s]*\d+$', '', stem)  # Remove trailing underscore/digits
        
        # If base_name is empty or too short, use the full stem
        if len(base_name) < 2:
            base_name = stem
        
        output_path = output_dir / f"{base_name}.mp4"
        
        # Build input pattern for FFmpeg
        # pyseq's format() method provides the pattern we need
        import re
        try:
            seq_format = sequence.format()
            # Extract pattern from format string (e.g., "901 2025-12-10_FoldingTotemPromo_v6_JJ%04d.jpg [0-900]")
            # Look for the pattern with %0Nd format
            pattern_match = re.search(r'(\S+%0?\d+d\S+)', seq_format)
            if pattern_match:
                pattern_filename = pattern_match.group(1)
                # Construct full absolute path to pattern
                input_pattern = str((seq_dir / pattern_filename).resolve())
                logger.debug(f"Extracted pattern from format: {input_pattern}")
            else:
                # Fallback: construct pattern manually
                first_file = Path(sequence[0])
                stem = first_file.stem
                suffix = first_file.suffix
                # Find frame number in stem - look for the last sequence of digits
                # This handles cases like "JJ0000" where digits are embedded
                num_matches = list(re.finditer(r'\d+', stem))
                if num_matches:
                    # Use the last (rightmost) number match as it's likely the frame number
                    last_match = num_matches[-1]
                    frame_width = len(last_match.group())
                    # Replace only the last occurrence of digits
                    pattern_stem = stem[:last_match.start()] + f'%0{frame_width}d' + stem[last_match.end():]
                    input_pattern = str(seq_dir / f"{pattern_stem}{suffix}")
                    logger.debug(f"Constructed pattern manually: {input_pattern}")
                else:
                    input_pattern = str(seq_dir / f"frame_%04d{suffix}")
                    logger.warning(f"Could not find frame number, using default pattern: {input_pattern}")
        except Exception as e:
            logger.warning(f"Could not extract pattern from sequence format: {e}")
            # Final fallback
            first_file = Path(sequence[0])
            stem = first_file.stem
            suffix = first_file.suffix
            num_matches = list(re.finditer(r'\d+', stem))
            if num_matches:
                last_match = num_matches[-1]
                frame_width = len(last_match.group())
                pattern_stem = stem[:last_match.start()] + f'%0{frame_width}d' + stem[last_match.end():]
                input_pattern = str(seq_dir / f"{pattern_stem}{suffix}")
            else:
                input_pattern = str(seq_dir / f"frame_%04d{suffix}")
        
        # Get the actual start number from the sequence
        try:
            start_number = sequence.start()
        except (AttributeError, TypeError):
            start_number = 0
        
        # Build FFmpeg command
        cmd = build_ffmpeg_command(
            input_pattern,
            output_path,
            start_number=start_number,
            resolution_scale=resolution_scale,
            crf=crf,
            preset=preset,
            pixel_format=pixel_format,
            framerate=framerate,
        )
        
        logger.info(f"Converting sequence '{sequence}' to {output_path.name}")
        logger.info(f"Input pattern: {input_pattern}")
        logger.info(f"Start number: {start_number}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        # Verify the pattern file exists (check first frame)
        first_frame_name = Path(sequence[0]).name  # Get just filename
        first_frame_path = seq_dir / first_frame_name  # Construct full path
        if not first_frame_path.exists():
            error_msg = f"First frame does not exist: {first_frame_path}"
            logger.error(f"ERROR: {error_msg}")
            return False, error_msg
        
        # Run FFmpeg with real-time output streaming
        # FFmpeg writes progress to stderr, so we need to capture both streams
        import sys
        import threading
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # FFmpeg writes progress to stderr
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
        )
        
        # Stream output in real-time
        output_lines = []
        stderr_lines = []
        last_was_progress = False  # Track if last printed line was a progress line
        
        def read_stdout():
            """Read stdout in a separate thread."""
            try:
                for line in process.stdout:
                    if line:
                        line = line.rstrip()
                        if line:  # Only process non-empty lines
                            output_lines.append(line)
                            # Print non-progress output (FFmpeg usually doesn't write much to stdout)
                            print(f"FFmpeg: {line}", flush=True, file=sys.stdout)
            except Exception:
                pass
        
        def read_stderr():
            """Read stderr (where FFmpeg progress is) in a separate thread."""
            nonlocal last_was_progress
            try:
                for line in process.stderr:
                    if line:
                        line = line.rstrip()
                        if not line:  # Skip empty lines
                            continue
                        stderr_lines.append(line)
                        # FFmpeg progress lines - print on same line with carriage return for live updates
                        is_progress = any(keyword in line.lower() for keyword in ['frame=', 'fps=', 'bitrate=', 'time=', 'speed='])
                        if is_progress:
                            # Progress line - overwrite same line (this creates the live progress effect)
                            print(f"\rFFmpeg: {line}", end="", flush=True, file=sys.stderr)
                            last_was_progress = True
                        else:
                            # Other stderr output (warnings, errors, encoder stats) - print on new line
                            # If last line was progress, we need to add a newline first to move to next line
                            if last_was_progress:
                                print(file=sys.stderr)  # Newline after progress line
                                last_was_progress = False
                            print(f"FFmpeg: {line}", flush=True, file=sys.stderr)
            except Exception:
                pass
        
        # Start threads to read both streams
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        
        try:
            # Wait for process to complete
            returncode = process.wait()
            
            # Wait for threads to finish reading
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
            # Print newline after progress output if needed
            if last_was_progress:
                print(file=sys.stderr)
            
            if returncode == 0:
                logger.info(f"SUCCESS: Successfully converted: {output_path.name}")
                return True, f"Converted {sequence} to {output_path.name}"
            else:
                # Combine stderr and stdout for error message
                all_output = stderr_lines + output_lines
                error_msg = "\n".join(all_output[-20:])  # Last 20 lines for error context
                logger.error(f"ERROR: FFmpeg conversion failed: {error_msg}")
                return False, f"Failed to convert {sequence}: {error_msg[:200]}"
        
        except Exception as e:
            if process.poll() is None:
                process.kill()
            error_msg = f"Error running FFmpeg: {e}"
            logger.error(f"ERROR: {error_msg}")
            return False, error_msg
    
    except subprocess.TimeoutExpired:
        if 'process' in locals() and process.poll() is None:
            process.kill()
        error_msg = "FFmpeg conversion timed out"
        logger.error(f"ERROR: {error_msg}")
        return False, error_msg
    
    except Exception as e:
        error_msg = f"Error converting sequence: {e}"
        logger.error(f"ERROR: {error_msg}")
        return False, error_msg


def generate_output_filename(
    sequence: Sequence,
    preset: Dict,
    custom_text: str = "",
    user_initials: str = "",
    output_dir: Optional[Path] = None,
    sequence_directory: Optional[Path] = None,
) -> Path:
    """Generate output filename according to format: [OriginalSequenceName]_[PresetSuffix]_[CustomText]_[UserInitials].[ext]
    
    Args:
        sequence: pyseq.Sequence object
        preset: Preset configuration dict
        custom_text: Custom text to add to filename (no periods allowed)
        user_initials: User initials to add at the end
        output_dir: Output directory (None = same as sequence directory)
        sequence_directory: Directory where sequence files are located
    
    Returns:
        Path to output file
    """
    import re
    
    # Get sequence directory
    if sequence_directory is not None:
        seq_dir = Path(sequence_directory).resolve()
    else:
        first_frame = Path(sequence[0])
        if first_frame.is_absolute():
            seq_dir = first_frame.parent.resolve()
        else:
            raise ValueError("sequence_directory must be provided when sequence paths are relative")
    
    if output_dir is None:
        output_dir = seq_dir
    
    # Extract base name from sequence (remove frame number)
    first_frame_name = Path(sequence[0]).name
    first_file = Path(first_frame_name)
    stem = first_file.stem
    
    # Remove frame number from stem
    base_name = re.sub(r'[_\s]*\d+$', '', stem)
    if len(base_name) < 2:
        base_name = stem
    
    # Get preset suffix and container extension
    preset_suffix = preset.get("suffix", "")
    container = preset.get("container", "mp4")
    
    # Build filename parts
    parts = [base_name]
    
    if preset_suffix:
        parts.append(preset_suffix)
    
    if custom_text:
        # Remove periods from custom text (safety check)
        custom_text_clean = custom_text.replace(".", "")
        if custom_text_clean:
            parts.append(custom_text_clean)
    
    if user_initials:
        parts.append(user_initials)
    
    # Join parts with underscores
    filename_base = "_".join(parts)
    
    # Add extension
    output_path = output_dir / f"{filename_base}.{container}"
    
    return output_path


def convert_sequence_with_preset(
    sequence: Sequence,
    preset_key: str,
    output_dir: Optional[Path] = None,
    sequence_directory: Optional[Path] = None,
    resolution_scale: Optional[float] = None,
    framerate: Optional[int] = None,
    custom_text: str = "",
    user_initials: str = "",
    hap_chunk_count: int = 1,
) -> Tuple[bool, str]:
    """Convert an image sequence to video using a preset.
    
    Args:
        sequence: pyseq.Sequence object representing the image sequence
        preset_key: Key of the preset to use
        output_dir: Output directory (None = same as sequence directory)
        sequence_directory: Directory where sequence files are located (required)
        resolution_scale: Optional resolution scale (overrides preset default of 1.0)
        framerate: Optional framerate (overrides preset default of 30fps)
        custom_text: Custom text to add to filename
        user_initials: User initials to add to filename
        hap_chunk_count: HAP chunk count (for HAP codecs only)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    config = get_config()
    preset = config.get_preset(preset_key)
    
    if not preset:
        error_msg = f"Preset not found: {preset_key}"
        logger.error(f"ERROR: {error_msg}")
        return False, error_msg
    
    try:
        # Get sequence directory
        if sequence_directory is not None:
            seq_dir = Path(sequence_directory).resolve()
        else:
            first_frame = Path(sequence[0])
            if first_frame.is_absolute():
                seq_dir = first_frame.parent.resolve()
            else:
                raise ValueError("sequence_directory must be provided when sequence paths are relative")
        
        if output_dir is None:
            output_dir = seq_dir
        
        # Generate output filename
        output_path = generate_output_filename(
            sequence,
            preset,
            custom_text=custom_text,
            user_initials=user_initials,
            output_dir=output_dir,
            sequence_directory=seq_dir,
        )
        
        # Build input pattern by finding and using the actual first frame file
        import re
        
        # Find the actual first frame file that exists
        # Try multiple methods to locate the file reliably
        first_frame_path = None
        
        # Method 1: Try sequence[0] directly (might be absolute or relative)
        first_frame_item = sequence[0]
        test_path = Path(first_frame_item)
        if test_path.is_absolute() and test_path.exists():
            first_frame_path = test_path
        else:
            # Method 2: Try just the filename in seq_dir
            filename_only = Path(first_frame_item).name
            test_path = seq_dir / filename_only
            if test_path.exists():
                first_frame_path = test_path
            else:
                # Method 3: Try iterating through sequence items to find one that exists
                for item in sequence[:20]:  # Check first 20 items
                    item_path = Path(item)
                    if item_path.is_absolute() and item_path.exists():
                        first_frame_path = item_path
                        break
                    else:
                        # Try as filename in seq_dir
                        test_path = seq_dir / item_path.name
                        if test_path.exists():
                            first_frame_path = test_path
                            break
        
        if not first_frame_path or not first_frame_path.exists():
            error_msg = f"Could not locate first frame file for sequence '{sequence}' in {seq_dir}"
            logger.error(f"ERROR: {error_msg}")
            logger.debug(f"Sequence[0] was: {sequence[0]}, seq_dir: {seq_dir}")
            # List available files for debugging
            try:
                available_files = [f.name for f in seq_dir.iterdir() if f.is_file() and f.suffix.lower() not in EXCLUDED_EXTENSIONS]
                logger.debug(f"Available files in directory: {available_files[:10]}")
            except Exception:
                pass
            return False, error_msg
        
        # Extract pattern from the actual existing file
        actual_filename = first_frame_path.name
        stem = first_frame_path.stem
        suffix = first_frame_path.suffix
        
        logger.debug(f"Using first frame file: {actual_filename}, stem: '{stem}', suffix: '{suffix}'")
        
        # Find the frame number (last sequence of digits in the stem)
        num_matches = list(re.finditer(r'\d+', stem))
        if num_matches:
            last_match = num_matches[-1]
            frame_width = len(last_match.group())
            frame_number_str = last_match.group()
            # Replace the frame number with the pattern placeholder
            # stem[:last_match.start()] gets everything before the number
            # f'%0{frame_width}d' is the pattern placeholder
            # stem[last_match.end():] gets everything after the number
            pattern_stem = stem[:last_match.start()] + f'%0{frame_width}d' + stem[last_match.end():]
            input_pattern = str(seq_dir / f"{pattern_stem}{suffix}")
            logger.debug(f"Pattern: stem='{stem}', found number '{frame_number_str}' at pos {last_match.start()}-{last_match.end()}, pattern_stem='{pattern_stem}', final='{input_pattern}'")
        else:
            error_msg = f"Could not extract frame number from filename: {actual_filename}"
            logger.error(f"ERROR: {error_msg}")
            return False, error_msg
        
        # Get start number
        try:
            start_number = sequence.start()
        except (AttributeError, TypeError):
            start_number = 0
        
        # Build FFmpeg command from preset
        cmd = build_ffmpeg_command_from_preset(
            input_pattern,
            output_path,
            preset,
            start_number=start_number,
            resolution_scale=resolution_scale,
            framerate=framerate,
            hap_chunk_count=hap_chunk_count,
        )
        
        logger.info(f"Converting sequence '{sequence}' to {output_path.name} using preset '{preset_key}'")
        logger.info(f"Input pattern: {input_pattern}")
        logger.info(f"Start number: {start_number}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        # Run FFmpeg (reuse streaming logic from convert_sequence_to_video)
        import sys
        import threading
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        
        output_lines = []
        stderr_lines = []
        last_was_progress = False
        
        def read_stdout():
            try:
                for line in process.stdout:
                    if line:
                        line = line.rstrip()
                        if line:
                            output_lines.append(line)
                            print(f"FFmpeg: {line}", flush=True, file=sys.stdout)
            except Exception:
                pass
        
        def read_stderr():
            nonlocal last_was_progress
            try:
                for line in process.stderr:
                    if line:
                        line = line.rstrip()
                        if not line:
                            continue
                        stderr_lines.append(line)
                        is_progress = any(keyword in line.lower() for keyword in ['frame=', 'fps=', 'bitrate=', 'time=', 'speed='])
                        if is_progress:
                            print(f"\rFFmpeg: {line}", end="", flush=True, file=sys.stderr)
                            last_was_progress = True
                        else:
                            if last_was_progress:
                                print(file=sys.stderr)
                                last_was_progress = False
                            print(f"FFmpeg: {line}", flush=True, file=sys.stderr)
            except Exception:
                pass
        
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        
        try:
            returncode = process.wait()
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
            if last_was_progress:
                print(file=sys.stderr)
            
            if returncode == 0:
                logger.info(f"SUCCESS: Successfully converted: {output_path.name}")
                return True, f"Converted {sequence} to {output_path.name}"
            else:
                error_msg = "\n".join(stderr_lines[-20:])
                logger.error(f"ERROR: FFmpeg conversion failed: {error_msg}")
                return False, f"Failed to convert {sequence}: {error_msg[:200]}"
        
        except Exception as e:
            if process.poll() is None:
                process.kill()
            error_msg = f"Error running FFmpeg: {e}"
            logger.error(f"ERROR: {error_msg}")
            return False, error_msg
    
    except Exception as e:
        error_msg = f"Error converting sequence: {e}"
        logger.error(f"ERROR: {error_msg}")
        return False, error_msg


def generate_movie_output_filename(
    movie_path: Path,
    preset: Dict,
    custom_text: str = "",
    user_initials: str = "",
    output_dir: Optional[Path] = None,
) -> Path:
    """Generate output filename for movie file conversion.
    
    Format: [OriginalMovieName]_[PresetSuffix]_[CustomText]_[UserInitials].[ext]
    
    Args:
        movie_path: Path to input movie file
        preset: Preset configuration dict
        custom_text: Custom text to add to filename (no periods allowed)
        user_initials: User initials to add at the end
        output_dir: Output directory (None = same as movie directory)
    
    Returns:
        Path to output file
    """
    if output_dir is None:
        output_dir = movie_path.parent
    
    # Get base name (without extension)
    base_name = movie_path.stem
    
    # Get preset suffix and container extension
    preset_suffix = preset.get("suffix", "")
    container = preset.get("container", "mp4")
    
    # Build filename parts
    parts = [base_name]
    
    if preset_suffix:
        parts.append(preset_suffix)
    
    if custom_text:
        # Remove periods from custom text (safety check)
        custom_text_clean = custom_text.replace(".", "")
        if custom_text_clean:
            parts.append(custom_text_clean)
    
    if user_initials:
        parts.append(user_initials)
    
    # Join parts with underscores
    filename_base = "_".join(parts)
    
    # Add extension
    output_path = output_dir / f"{filename_base}.{container}"
    
    return output_path


def build_ffmpeg_command_from_preset_for_movie(
    input_movie: Path,
    output_path: Path,
    preset: Dict,
    resolution_scale: Optional[float] = None,
    framerate: Optional[int] = None,
    hap_chunk_count: int = 1,
) -> List[str]:
    """Build FFmpeg command from a preset configuration for movie file conversion.
    
    Args:
        input_movie: Path to input movie file
        output_path: Output video file path
        preset: Preset configuration dict from presets.json
        resolution_scale: Optional resolution scale (overrides preset default of 1.0)
        framerate: Optional framerate (overrides preset default, None = use input framerate)
        hap_chunk_count: HAP chunk count (for HAP codecs only)
    
    Returns:
        List of command arguments for subprocess
    """
    config = get_config()
    ffmpeg_path = config.get_ffmpeg_path()
    
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not available")
    
    codec = preset.get("codec")
    if not codec:
        raise ValueError("Preset missing 'codec' field")
    
    # Default resolution (presets default to full res)
    if resolution_scale is None:
        resolution_scale = 1.0
    
    cmd = [ffmpeg_path, "-y"]  # -y to overwrite output files
    
    # Input movie file
    cmd.extend(["-i", str(input_movie)])
    
    # Build video filter chain
    filters = []
    
    # Optional scaling
    if resolution_scale != 1.0:
        filters.append(f"scale=iw*{resolution_scale}:ih*{resolution_scale}")
    
    # Get pixel format from preset
    pixel_format = preset.get("pix_fmt", "yuv420p")
    
    # Color space conversion (for non-HAP codecs)
    if codec != "hap":
        zscale_filter = (
            "zscale="
            "rangein=full:"
            "primariesin=bt709:"
            "transferin=iec61966-2-1:"
            "matrixin=bt709:"
            "range=tv:"
            "primaries=bt709:"
            "transfer=bt709:"
            "matrix=bt709"
        )
        filters.append(zscale_filter)
        filters.append(f"format={pixel_format}")
    
    if filters:
        cmd.extend(["-vf", ",".join(filters)])
    
    # Output framerate (only if specified, otherwise use input)
    if framerate:
        cmd.extend(["-r", str(framerate)])
    
    # Codec-specific settings
    if codec == "libx264":
        # H.264 encoding
        cmd.extend([
            "-c:v", "libx264",
            "-crf", "23",  # Default CRF
            "-preset", "medium",  # Default preset
            "-profile:v", "high",
            "-level", "4.2",
            "-pix_fmt", pixel_format,
            "-movflags", "+faststart",
        ])
    elif codec == "prores_ks":
        # ProRes encoding
        profile_v = preset.get("profile_v")
        vendor = preset.get("vendor", "apl0")
        cmd.extend([
            "-c:v", "prores_ks",
            "-profile:v", str(profile_v),
            "-vendor", vendor,
            "-pix_fmt", pixel_format,
        ])
    elif codec == "hap":
        # HAP encoding
        hap_format = preset.get("format", "hap")
        cmd.extend([
            "-c:v", "hap",
            "-format", hap_format,
            "-chunks", str(hap_chunk_count),
        ])
    else:
        raise ValueError(f"Unsupported codec: {codec}")
    
    # Copy audio stream if present
    cmd.extend(["-c:a", "copy"])
    
    # Output file
    cmd.append(str(output_path))
    
    return cmd


def convert_movie_with_preset(
    movie_path: Path,
    preset_key: str,
    output_dir: Optional[Path] = None,
    resolution_scale: Optional[float] = None,
    framerate: Optional[int] = None,
    custom_text: str = "",
    user_initials: str = "",
    hap_chunk_count: int = 1,
) -> Tuple[bool, str]:
    """Convert a movie file using a preset.
    
    Args:
        movie_path: Path to input movie file
        preset_key: Key of the preset to use
        output_dir: Output directory (None = same as movie directory)
        resolution_scale: Optional resolution scale (overrides preset default of 1.0)
        framerate: Optional framerate (overrides preset default, None = use input)
        custom_text: Custom text to add to filename
        user_initials: User initials to add to filename
        hap_chunk_count: HAP chunk count (for HAP codecs only)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    config = get_config()
    preset = config.get_preset(preset_key)
    
    if not preset:
        error_msg = f"Preset not found: {preset_key}"
        logger.error(f"ERROR: {error_msg}")
        return False, error_msg
    
    try:
        if output_dir is None:
            output_dir = movie_path.parent
        
        # Generate output filename
        output_path = generate_movie_output_filename(
            movie_path,
            preset,
            custom_text=custom_text,
            user_initials=user_initials,
            output_dir=output_dir,
        )
        
        # Build FFmpeg command from preset
        cmd = build_ffmpeg_command_from_preset_for_movie(
            movie_path,
            output_path,
            preset,
            resolution_scale=resolution_scale,
            framerate=framerate,
            hap_chunk_count=hap_chunk_count,
        )
        
        logger.info(f"Converting movie '{movie_path.name}' to {output_path.name} using preset '{preset_key}'")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        # Verify input file exists
        if not movie_path.exists():
            error_msg = f"Movie file does not exist: {movie_path}"
            logger.error(f"ERROR: {error_msg}")
            return False, error_msg
        
        # Run FFmpeg (reuse streaming logic from convert_sequence_with_preset)
        import sys
        import threading
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        
        output_lines = []
        stderr_lines = []
        last_was_progress = False
        
        def read_stdout():
            try:
                for line in process.stdout:
                    if line:
                        line = line.rstrip()
                        if line:
                            output_lines.append(line)
                            print(f"FFmpeg: {line}", flush=True, file=sys.stdout)
            except Exception:
                pass
        
        def read_stderr():
            nonlocal last_was_progress
            try:
                for line in process.stderr:
                    if line:
                        line = line.rstrip()
                        if not line:
                            continue
                        stderr_lines.append(line)
                        is_progress = any(keyword in line.lower() for keyword in ['frame=', 'fps=', 'bitrate=', 'time=', 'speed='])
                        if is_progress:
                            print(f"\rFFmpeg: {line}", end="", flush=True, file=sys.stderr)
                            last_was_progress = True
                        else:
                            if last_was_progress:
                                print(file=sys.stderr)
                                last_was_progress = False
                            print(f"FFmpeg: {line}", flush=True, file=sys.stderr)
            except Exception:
                pass
        
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        
        try:
            returncode = process.wait()
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
            if last_was_progress:
                print(file=sys.stderr)
            
            if returncode == 0:
                logger.info(f"SUCCESS: Successfully converted: {output_path.name}")
                return True, f"Converted {movie_path.name} to {output_path.name}"
            else:
                error_msg = "\n".join(stderr_lines[-20:])
                logger.error(f"ERROR: FFmpeg conversion failed: {error_msg}")
                return False, f"Failed to convert {movie_path.name}: {error_msg[:200]}"
        
        except Exception as e:
            if process.poll() is None:
                process.kill()
            error_msg = f"Error running FFmpeg: {e}"
            logger.error(f"ERROR: {error_msg}")
            return False, error_msg
    
    except Exception as e:
        error_msg = f"Error converting movie: {e}"
        logger.error(f"ERROR: {error_msg}")
        return False, error_msg


def convert_sequences_in_directory(
    directory: Path,
    recursive: bool = False,
    use_config_settings: bool = True,
) -> Tuple[int, int]:
    """Convert all image sequences in a directory to MP4 videos.
    
    Args:
        directory: Directory to process
        recursive: If True, process subdirectories recursively
        use_config_settings: If True, use settings from config file
    
    Returns:
        Tuple of (success_count: int, failure_count: int)
    
    Example:
        >>> success, failed = convert_sequences_in_directory(Path("C:\\Images"), recursive=True)
    """
    config = get_config()
    
    if use_config_settings:
        settings = config.get_ffmpeg_encoding_settings()
        resolution_scale = settings["resolution_scale"]
        crf = settings["crf"]
        preset = settings["preset"]
        pixel_format = settings["pixel_format"]
        framerate = settings["framerate"]
    else:
        # Use defaults
        resolution_scale = 1.0
        crf = 23
        preset = "medium"
        pixel_format = "yuv420p"
        framerate = 30  # Default to 30fps
    
    success_count = 0
    failure_count = 0
    
    # Get directories to process
    if recursive:
        directories = list(walk_directories(str(directory), recursive=True))
    else:
        directories = [directory]
    
    logger.info(f"Processing {len(directories)} directory(ies)...")
    
    for dir_path in directories:
        logger.info(f"Scanning directory: {dir_path}")
        
        # Find sequences in this directory
        sequences = find_image_sequences(dir_path)
        
        if not sequences:
            logger.debug(f"No image sequences found in {dir_path}")
            continue
        
        logger.info(f"Found {len(sequences)} sequence(s) in {dir_path}")
        
        # Convert each sequence
        for sequence in sequences:
            success, message = convert_sequence_to_video(
                sequence,
                output_dir=None,  # Output in same directory
                sequence_directory=dir_path,  # Pass the directory where sequence was found
                resolution_scale=resolution_scale,
                crf=crf,
                preset=preset,
                pixel_format=pixel_format,
                framerate=framerate,
            )
            
            if success:
                success_count += 1
            else:
                failure_count += 1
    
    return success_count, failure_count
