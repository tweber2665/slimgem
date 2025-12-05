"""
upload_to_FileStore.py
Upload files or folders to an existing Gemini File Search Store.
"""

import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console, Group
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, ProgressColumn
from rich.table import Table
from rich.live import Live
from rich.text import Text

from utils import (
    get_client,
    get_files_from_path,
    wait_for_operation,
    format_bytes,
    print_success,
    print_error,
    print_info,
    print_warning,
    clean_path_input,
    upload_with_retry,
    is_upload_in_progress,
    get_deduplicated_files,
    init_upload_status,
    update_upload_status,
    get_upload_status_table,
    get_upload_summary_stats,
    clear_upload_statuses,
    extract_file_metadata,
)
from config import (
    DEFAULT_MAX_TOKENS_PER_CHUNK,
    DEFAULT_MAX_OVERLAP_TOKENS,
    MAX_UPLOAD_RETRIES,
    UPLOAD_RETRY_INITIAL_DELAY,
    UPLOAD_RETRY_MAX_DELAY,
)

console = Console()


def upload_file_to_store(
    store_name: str,
    file_path: str,
    display_name: str | None = None,
    max_tokens_per_chunk: int | None = None,
    max_overlap_tokens: int | None = None,
    custom_metadata: list | None = None,
    use_status_tracker: bool = False,
) -> dict:
    """
    Upload a single file to a File Search Store.

    Args:
        store_name: The store name (e.g., 'fileSearchStores/abc123').
        file_path: Path to the file to upload.
        display_name: Display name for the document (defaults to filename).
        max_tokens_per_chunk: Custom chunking - max tokens per chunk.
        max_overlap_tokens: Custom chunking - overlap between chunks.
        custom_metadata: Optional list of metadata dictionaries.
        use_status_tracker: Whether to use status tracker for progress updates.

    Returns:
        Dictionary with upload result or error information.
    """
    client = get_client()

    # Default display name to filename
    if not display_name:
        display_name = Path(file_path).name

    try:
        # Check if upload is already in progress (duplicate prevention)
        if is_upload_in_progress(file_path, store_name):
            return {
                "success": False,
                "file_path": file_path,
                "error": "Upload already in progress for this file",
            }

        # Build configuration
        config: dict[str, object] = {
            "display_name": display_name,
        }

        # Add chunking configuration if specified
        if max_tokens_per_chunk or max_overlap_tokens:
            white_space_config: dict[str, int] = {}
            if max_tokens_per_chunk:
                white_space_config["max_tokens_per_chunk"] = max_tokens_per_chunk
            if max_overlap_tokens:
                white_space_config["max_overlap_tokens"] = max_overlap_tokens
            config["chunking_config"] = {"white_space_config": white_space_config}

        # Add custom metadata - either user-provided or auto-extracted
        if custom_metadata:
            # User provided explicit metadata
            config["custom_metadata"] = custom_metadata
        else:
            # Auto-extract metadata from the file
            extracted_metadata = extract_file_metadata(file_path)
            if extracted_metadata:
                config["custom_metadata"] = extracted_metadata

        # Upload with robust retry logic (handles session termination, exponential backoff, etc.)
        success, message, operation = upload_with_retry(
            client=client,
            file_path=file_path,
            store_name=store_name,
            config=config,  # type: ignore[arg-type]
            max_retries=MAX_UPLOAD_RETRIES,
            initial_delay=UPLOAD_RETRY_INITIAL_DELAY,
            max_delay=UPLOAD_RETRY_MAX_DELAY,
            use_status_tracker=use_status_tracker,
        )

        if success:
            return {
                "success": True,
                "file_path": file_path,
                "display_name": display_name,
                "message": "File uploaded and indexed successfully",
            }
        else:
            return {
                "success": False,
                "file_path": file_path,
                "error": message,
            }
        
    except Exception as e:
        error_message = str(e)
        
        if "NOT_FOUND" in error_message:
            return {
                "success": False,
                "file_path": file_path,
                "error": f"Store not found: {store_name}. Use 'List Stores' to see available stores.",
            }
        elif "PERMISSION_DENIED" in error_message:
            return {
                "success": False,
                "file_path": file_path,
                "error": "Permission denied. Check your API key permissions.",
            }
        elif "INVALID_ARGUMENT" in error_message:
            return {
                "success": False,
                "file_path": file_path,
                "error": f"Invalid argument: {error_message}",
            }
        else:
            return {
                "success": False,
                "file_path": file_path,
                "error": f"Upload failed: {error_message}",
            }


# Default number of concurrent uploads
DEFAULT_MAX_WORKERS = 5


def _create_upload_display() -> Group:
    """Create a combined display with overall progress and status table."""
    total, completed, failed, in_progress = get_upload_summary_stats()

    # Create overall progress bar
    if total > 0:
        percentage = (completed + failed) / total * 100
        done_count = completed + failed

        # Build progress bar visual
        bar_width = 40
        filled = int(bar_width * (done_count / total))
        bar = "█" * filled + "░" * (bar_width - filled)

        # Color based on status
        if failed > 0 and completed == 0:
            bar_color = "red"
        elif failed > 0:
            bar_color = "yellow"
        elif done_count == total:
            bar_color = "green"
        else:
            bar_color = "cyan"

        progress_text = Text()
        progress_text.append("Overall Progress: ", style="bold")
        progress_text.append(f"{done_count}/{total} ", style="white")
        progress_text.append(f"({percentage:.0f}%) ", style="dim")
        progress_text.append(bar, style=bar_color)

        if failed > 0:
            progress_text.append(f" | ", style="dim")
            progress_text.append(f"✓ {completed} ", style="green")
            progress_text.append(f"✗ {failed}", style="red")

    else:
        progress_text = Text("Overall Progress: No files", style="dim")

    # Combine progress bar and table
    return Group(
        progress_text,
        Text(""),  # Blank line
        get_upload_status_table(),
    )


def upload_multiple_files(
    store_name: str,
    file_paths: list,
    max_tokens_per_chunk: int | None = None,
    max_overlap_tokens: int | None = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> dict:
    """
    Upload multiple files to a File Search Store in parallel with live progress display.

    Args:
        store_name: The store name.
        file_paths: List of file paths to upload.
        max_tokens_per_chunk: Custom chunking - max tokens per chunk.
        max_overlap_tokens: Custom chunking - overlap between chunks.
        max_workers: Maximum concurrent uploads (default: 5).

    Returns:
        Dictionary with upload results summary.
    """
    successful = []
    failed = []

    # Clear any previous status tracking
    clear_upload_statuses()

    # Initialize status for all files
    for file_path in file_paths:
        init_upload_status(file_path)

    # Create live display with overall progress and status table
    with Live(
        _create_upload_display(),
        refresh_per_second=4,
        console=console,
    ) as live:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all upload tasks
            future_to_path = {
                executor.submit(
                    upload_file_to_store,
                    store_name=store_name,
                    file_path=file_path,
                    max_tokens_per_chunk=max_tokens_per_chunk,
                    max_overlap_tokens=max_overlap_tokens,
                    use_status_tracker=True,
                ): file_path
                for file_path in file_paths
            }

            # Process completed uploads as they finish
            for future in as_completed(future_to_path):
                file_path = future_to_path[future]

                try:
                    result = future.result()
                    if result["success"]:
                        successful.append(result)
                    else:
                        failed.append(result)
                except Exception as e:
                    failed.append({
                        "success": False,
                        "file_path": file_path,
                        "error": f"Unexpected error: {str(e)}",
                    })

                # Update the live display
                live.update(_create_upload_display())

    return {
        "total": len(file_paths),
        "successful": successful,
        "failed": failed,
    }


def get_chunking_config() -> tuple:
    """
    Prompt user for chunking configuration.
    
    Returns:
        Tuple of (max_tokens_per_chunk, max_overlap_tokens) or (None, None) for defaults.
    """
    console.print()
    console.print("[bold]Chunking Configuration[/bold]")
    console.print(
        f"[dim]Default: {DEFAULT_MAX_TOKENS_PER_CHUNK} tokens per chunk, "
        f"{DEFAULT_MAX_OVERLAP_TOKENS} token overlap[/dim]"
    )
    console.print()
    
    use_custom = Confirm.ask(
        "Would you like to customize chunking settings?",
        default=False,
    )
    
    if not use_custom:
        return None, None
    
    console.print()
    
    # Get chunk size (1-512)
    max_tokens_input = Prompt.ask(
        "Max tokens per chunk (1-512)",
        default=str(DEFAULT_MAX_TOKENS_PER_CHUNK),
    )
    
    try:
        max_tokens = int(max_tokens_input)
        if max_tokens < 1:
            print_warning("Minimum is 1 token. Using 1.")
            max_tokens = 1
        elif max_tokens > 512:
            print_warning("Maximum is 512 tokens. Using 512.")
            max_tokens = 512
    except ValueError:
        print_warning(f"Invalid number. Using default: {DEFAULT_MAX_TOKENS_PER_CHUNK}")
        max_tokens = DEFAULT_MAX_TOKENS_PER_CHUNK
    
    # Calculate max overlap as 25% of chunk size
    max_allowed_overlap = max_tokens // 4
    default_overlap = max(1, max_tokens // 10)
    
    max_overlap_input = Prompt.ask(
        f"Max overlap tokens (0-{max_allowed_overlap}, recommended: ~10%)",
        default=str(default_overlap),
    )
    
    try:
        max_overlap = int(max_overlap_input)
        if max_overlap < 0:
            print_warning("Overlap cannot be negative. Using 0.")
            max_overlap = 0
        elif max_overlap > max_allowed_overlap:
            print_warning(f"Maximum overlap is 25% of chunk size. Using {max_allowed_overlap}.")
            max_overlap = max_allowed_overlap
    except ValueError:
        print_warning(f"Invalid number. Using default: {default_overlap}")
        max_overlap = default_overlap
    
    return max_tokens, max_overlap


def display_upload_results(results: dict) -> None:
    """Display upload results in a formatted way."""
    console.print()
    
    successful = results["successful"]
    failed = results["failed"]
    
    if successful:
        console.print(f"[bold green]✓ Successfully uploaded: {len(successful)} file(s)[/bold green]")
        
        # Create success table
        table = Table(show_header=True, header_style="bold green")
        table.add_column("File", style="cyan")
        table.add_column("Display Name", style="white")
        
        for item in successful:
            table.add_row(
                Path(item["file_path"]).name,
                item["display_name"],
            )
        
        console.print(table)
    
    if failed:
        console.print()
        console.print(f"[bold red]✗ Failed to upload: {len(failed)} file(s)[/bold red]")
        
        # Create failure table
        table = Table(show_header=True, header_style="bold red")
        table.add_column("File", style="cyan")
        table.add_column("Error", style="red")
        
        for item in failed:
            table.add_row(
                Path(item["file_path"]).name,
                item["error"],
            )
        
        console.print(table)


def main():
    """Main function for standalone execution."""
    console.print(
        Panel(
            "[bold cyan]Upload to File Search Store[/bold cyan]",
            subtitle="Gemini File Search Manager",
        )
    )
    console.print()
    
    # Get store name
    store_name = Prompt.ask(
        "[bold]Enter the store name[/bold] (e.g., fileSearchStores/abc123)"
    )
    
    if not store_name.strip():
        print_error("Store name is required.")
        sys.exit(1)
    
    # Ensure proper format
    store_name = store_name.strip()
    if not store_name.startswith("fileSearchStores/"):
        store_name = f"fileSearchStores/{store_name}"
    
    console.print()
    
    # Get path to upload
    path_input = Prompt.ask(
        "[bold]Enter the path to a file or folder[/bold]"
    )
    
    if not path_input.strip():
        print_error("Path is required.")
        sys.exit(1)
    
    path = Path(clean_path_input(path_input)).expanduser().resolve()
    
    if not path.exists():
        print_error(f"Path does not exist: {path}")
        sys.exit(1)
    
    console.print()
    
    # Handle directory - ask about recursive
    recursive = False
    if path.is_dir():
        print_info(f"Directory detected: {path}")
        recursive = Confirm.ask(
            "Include files in subdirectories (recursive)?",
            default=False,
        )
    
    # Get files to upload
    valid_files, skipped_files = get_files_from_path(str(path), recursive=recursive)
    
    if not valid_files:
        print_error("No valid files found to upload.")
        
        if skipped_files:
            console.print()
            console.print("[bold yellow]Skipped files:[/bold yellow]")
            for file_path, reason in skipped_files[:10]:  # Show first 10
                console.print(f"  • {Path(file_path).name}: {reason}")
            
            if len(skipped_files) > 10:
                console.print(f"  ... and {len(skipped_files) - 10} more")
        
        sys.exit(1)
    
    # Show files to be uploaded
    console.print()
    print_info(f"Found {len(valid_files)} valid file(s) to upload")

    if len(valid_files) <= 10:
        for f in valid_files:
            console.print(f"  • {Path(f).name}")
    else:
        for f in valid_files[:5]:
            console.print(f"  • {Path(f).name}")
        console.print(f"  ... and {len(valid_files) - 5} more files")

    # Show skipped files if any
    if skipped_files:
        console.print()
        print_warning(f"Skipping {len(skipped_files)} file(s):")
        for file_path, reason in skipped_files[:5]:
            console.print(f"  • {Path(file_path).name}: [dim]{reason}[/dim]")

        if len(skipped_files) > 5:
            console.print(f"  ... and {len(skipped_files) - 5} more")

    # Detect and handle duplicates
    deduplicated_files, duplicate_groups = get_deduplicated_files(
        valid_files,
        interactive=True
    )

    # Update file list to deduplicated version
    if duplicate_groups:
        skipped_count = len(valid_files) - len(deduplicated_files)
        console.print(f"[green]Deduplicated: {len(deduplicated_files)} unique file(s) to upload[/green]")
        console.print(f"[dim]Skipped {skipped_count} duplicate(s)[/dim]")
        console.print()
        valid_files = deduplicated_files

    # Get chunking configuration
    max_tokens, max_overlap = get_chunking_config()
    
    if max_tokens or max_overlap:
        console.print()
        print_info(f"Using custom chunking: {max_tokens} tokens/chunk, {max_overlap} token overlap")
    
    # Confirm upload
    console.print()
    if not Confirm.ask(
        f"Upload {len(valid_files)} file(s) to [cyan]{store_name}[/cyan]?",
        default=True,
    ):
        print_info("Upload cancelled.")
        sys.exit(0)
    
    console.print()
    
    # Perform upload
    results = upload_multiple_files(
        store_name=store_name,
        file_paths=valid_files,
        max_tokens_per_chunk=max_tokens,
        max_overlap_tokens=max_overlap,
    )
    
    # Display results
    display_upload_results(results)
    
    # Summary
    console.print()
    if results["failed"]:
        print_warning(
            f"Completed with errors: {len(results['successful'])}/{results['total']} successful"
        )
    else:
        print_success(f"All {results['total']} file(s) uploaded successfully!")
    
    console.print()


if __name__ == "__main__":
    main()