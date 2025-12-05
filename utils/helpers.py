"""
utils/helpers.py
Helper functions for file validation, formatting, and operation polling.
"""

import json
import os
import time
import random
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Set, Dict
from threading import Lock
from enum import Enum

from rich.console import Console
from rich.table import Table

# Metadata extraction libraries
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    from pptx import Presentation
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

from config import (
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    SUPPORTED_EXTENSIONS,
    FAILURE_LOG_FILE,
    MAX_UPLOAD_RETRIES,
    UPLOAD_RETRY_INITIAL_DELAY,
    UPLOAD_RETRY_MAX_DELAY,
    RETRYABLE_ERROR_PATTERNS,
)

console = Console()

# Global set to track active upload sessions (prevent duplicates)
_active_uploads: Set[str] = set()
_upload_lock = Lock()


# Upload status tracking
class UploadStatus(Enum):
    """Status states for file uploads."""
    PENDING = "pending"
    UPLOADING = "uploading"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"


# Global upload status tracker
_upload_statuses: Dict[str, Dict] = {}
_status_lock = Lock()


def init_upload_status(file_path: str) -> None:
    """Initialize status tracking for a file upload."""
    with _status_lock:
        _upload_statuses[file_path] = {
            "status": UploadStatus.PENDING,
            "attempt": 0,
            "max_retries": 0,
            "message": "",
        }


def update_upload_status(
    file_path: str,
    status: UploadStatus,
    attempt: int = 0,
    max_retries: int = 0,
    message: str = "",
) -> None:
    """Update the status of a file upload."""
    with _status_lock:
        if file_path in _upload_statuses:
            _upload_statuses[file_path].update({
                "status": status,
                "attempt": attempt,
                "max_retries": max_retries,
                "message": message,
            })


def get_upload_status_table() -> Table:
    """
    Generate a Rich Table showing current upload statuses.

    Returns:
        Rich Table with file upload statuses.
    """
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("File", style="white", no_wrap=False)
    table.add_column("Status", style="cyan", width=12)
    table.add_column("Progress", style="yellow", no_wrap=False)

    with _status_lock:
        for file_path, info in _upload_statuses.items():
            filename = Path(file_path).name
            status = info["status"]
            attempt = info["attempt"]
            max_retries = info["max_retries"]
            message = info.get("message", "")

            # Status icon and text
            if status == UploadStatus.PENDING:
                status_icon = "⋯"
                status_text = "Pending"
                status_style = "dim"
            elif status == UploadStatus.UPLOADING:
                status_icon = "⏳"
                status_text = "Uploading"
                status_style = "cyan"
            elif status == UploadStatus.RETRYING:
                status_icon = "↻"
                status_text = "Retrying"
                status_style = "yellow"
            elif status == UploadStatus.COMPLETED:
                status_icon = "✓"
                status_text = "Done"
                status_style = "green"
            elif status == UploadStatus.FAILED:
                status_icon = "✗"
                status_text = "Failed"
                status_style = "red"
            else:
                status_icon = "?"
                status_text = "Unknown"
                status_style = "dim"

            # Progress indicator
            if status == UploadStatus.RETRYING and max_retries > 0 and attempt > 0:
                # Show attempt count and brief error
                error_brief = message[:40] + "..." if len(message) > 40 else message
                progress = f"[yellow]Retry {attempt}/{max_retries + 1}:[/yellow] {error_brief}"
            elif status == UploadStatus.UPLOADING:
                progress = "▓▓▓░░░░░░░"
            elif status == UploadStatus.COMPLETED:
                progress = "▓▓▓▓▓▓▓▓▓▓ 100%"
            elif status == UploadStatus.FAILED:
                # Show brief error for failed uploads
                error_brief = message[:50] + "..." if len(message) > 50 else message
                progress = f"[red]✗ {error_brief}[/red]"
            else:
                progress = "░░░░░░░░░░"

            table.add_row(
                filename,
                f"[{status_style}]{status_icon} {status_text}[/{status_style}]",
                progress,
            )

    return table


def get_upload_summary_stats() -> tuple[int, int, int, int]:
    """
    Get summary statistics of upload statuses.

    Returns:
        Tuple of (total, completed, failed, in_progress).
    """
    with _status_lock:
        total = len(_upload_statuses)
        completed = sum(1 for info in _upload_statuses.values() if info["status"] == UploadStatus.COMPLETED)
        failed = sum(1 for info in _upload_statuses.values() if info["status"] == UploadStatus.FAILED)
        in_progress = sum(1 for info in _upload_statuses.values()
                         if info["status"] in [UploadStatus.UPLOADING, UploadStatus.RETRYING])
        return total, completed, failed, in_progress


def clear_upload_statuses() -> None:
    """Clear all upload status tracking."""
    with _status_lock:
        _upload_statuses.clear()


def print_success(message: str) -> None:
    """Print a success message with green checkmark."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str) -> None:
    """Print an error message with red X."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message with yellow exclamation."""
    console.print(f"[bold yellow]![/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message with blue arrow."""
    console.print(f"[bold blue]→[/bold blue] {message}")

def clean_path_input(path_input: str) -> str:
    """
    Clean a path string from drag-and-drop input.
    
    macOS Terminal adds quotes or escape characters when you drag/drop files.
    This function removes those so the path works correctly.
    
    Args:
        path_input: Raw path string from user input.
        
    Returns:
        Cleaned path string.
    """
    path = path_input.strip()
    
    # Remove surrounding quotes (single or double)
    if (path.startswith('"') and path.endswith('"')) or \
       (path.startswith("'") and path.endswith("'")):
        path = path[1:-1]
    
    # Remove backslash escapes (e.g., "My\ Folder" -> "My Folder")
    path = path.replace("\\ ", " ")
    path = path.replace("\\(", "(")
    path = path.replace("\\)", ")")
    path = path.replace("\\&", "&")
    path = path.replace("\\'", "'")
    
    return path

def format_bytes(size_bytes) -> str:
    """
    Convert bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Human-readable size string (e.g., "1.5 MB").
    """
    if size_bytes is None:
        return "Unknown"
    
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_timestamp(timestamp_str: Optional[str]) -> str:
    """
    Format an ISO timestamp to a readable format.
    
    Args:
        timestamp_str: ISO format timestamp string.
        
    Returns:
        Formatted date/time string.
    """
    if not timestamp_str:
        return "Unknown"
    
    try:
        # Handle various timestamp formats
        if "." in timestamp_str:
            # Has microseconds
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return timestamp_str


def validate_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate a file for upload.
    
    Checks:
    - File exists
    - File is not empty
    - File size is under 100MB
    - File extension is supported
    
    Args:
        file_path: Path to the file to validate.
        
    Returns:
        Tuple of (is_valid, message).
    """
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        return False, f"File not found: {file_path}"
    
    # Check if it's actually a file (not a directory)
    if not path.is_file():
        return False, f"Not a file: {file_path}"
    
    # Check file size
    file_size = path.stat().st_size
    if file_size == 0:
        return False, f"File is empty: {file_path}"
    
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, (
            f"File too large: {format_bytes(file_size)}. "
            f"Maximum allowed: {MAX_FILE_SIZE_MB} MB"
        )
    
    # Check file extension
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        return False, (
            f"Unsupported file type: {extension}. "
            f"See Google's documentation for supported formats."
        )
    
    return True, f"Valid file: {path.name} ({format_bytes(file_size)})"


def get_files_from_path(
    path: str,
    recursive: bool = False
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Get list of valid files from a path (file or directory).
    
    Args:
        path: Path to a file or directory.
        recursive: If True and path is a directory, include subdirectories.
        
    Returns:
        Tuple of (valid_files, skipped_files).
        - valid_files: List of valid file paths.
        - skipped_files: List of (file_path, reason) tuples for skipped files.
    """
    valid_files = []
    skipped_files = []
    
    target_path = Path(path)
    
    if not target_path.exists():
        return [], [(path, "Path does not exist")]
    
    # If it's a single file
    if target_path.is_file():
        is_valid, message = validate_file(str(target_path))
        if is_valid:
            valid_files.append(str(target_path))
        else:
            skipped_files.append((str(target_path), message))
        return valid_files, skipped_files
    
    # If it's a directory
    if target_path.is_dir():
        if recursive:
            # Get all files recursively
            file_iterator = target_path.rglob("*")
        else:
            # Get only top-level files
            file_iterator = target_path.glob("*")
        
        for item in file_iterator:
            if item.is_file():
                # Skip hidden files
                if item.name.startswith("."):
                    skipped_files.append((str(item), "Hidden file"))
                    continue
                
                is_valid, message = validate_file(str(item))
                if is_valid:
                    valid_files.append(str(item))
                else:
                    skipped_files.append((str(item), message))
        
        return valid_files, skipped_files
    
    return [], [(path, "Not a file or directory")]


def wait_for_operation(
    client,
    operation,
    timeout_seconds: int = 300,
    poll_interval: int = 2
) -> Tuple[bool, str]:
    """
    Wait for a long-running operation to complete.
    
    Args:
        client: The GenAI client instance.
        operation: The operation object to poll.
        timeout_seconds: Maximum time to wait (default: 5 minutes).
        poll_interval: Seconds between status checks (default: 2).
        
    Returns:
        Tuple of (success, message).
    """
    start_time = time.time()
    
    while not operation.done:
        elapsed = time.time() - start_time
        
        if elapsed > timeout_seconds:
            return False, (
                f"Operation timed out after {timeout_seconds} seconds. "
                "The file may still be processing. Check back later."
            )
        
        time.sleep(poll_interval)
        
        try:
            operation = client.operations.get(operation)
        except Exception as e:
            return False, f"Error checking operation status: {str(e)}"
    
    # Check if operation completed successfully
    if hasattr(operation, "error") and operation.error:
        return False, f"Operation failed: {operation.error}"
    
    return True, "Operation completed successfully"

def log_upload_failure(filename: str, store_name: str, error: str) -> None:
    """
    Log a failed upload to the failure log file.
    
    Args:
        filename: Name of the file that failed.
        store_name: Name of the target store.
        error: Error message.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "filename": filename,
        "store_name": store_name,
        "error": error
    }
    
    # Load existing log or create new
    try:
        with open(FAILURE_LOG_FILE, "r") as f:
            log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log = []
    
    log.append(entry)
    
    with open(FAILURE_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def get_failure_log() -> list:
    """
    Get all entries from the failure log.
    
    Returns:
        List of failure log entries.
    """
    try:
        with open(FAILURE_LOG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def clear_failure_log() -> None:
    """Clear the failure log."""
    with open(FAILURE_LOG_FILE, "w") as f:
        json.dump([], f)


def upload_with_retry(
    client,
    file_path: str,
    store_name: str,
    config: dict,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 32.0,
    use_status_tracker: bool = False,
) -> Tuple[bool, str, Optional[object]]:
    """
    Upload a file with robust retry logic and session management.

    Implements:
    1. Fresh session creation on retry (no reuse of terminated sessions)
    2. Session status checks before retrying
    3. Exponential backoff with jitter
    4. Duplicate upload prevention

    Args:
        client: The GenAI client instance.
        file_path: Path to the file to upload.
        store_name: The file search store name.
        config: Upload configuration dictionary.
        max_retries: Maximum number of retry attempts (default: 3).
        initial_delay: Initial delay in seconds for exponential backoff (default: 1.0).
        max_delay: Maximum delay in seconds between retries (default: 32.0).
        use_status_tracker: Whether to update global status tracker instead of printing (default: False).

    Returns:
        Tuple of (success, message, operation).
    """
    # Solution 4: Check for duplicate uploads (prevent concurrent uploads of same file)
    upload_key = f"{store_name}:{file_path}"

    with _upload_lock:
        if upload_key in _active_uploads:
            if use_status_tracker:
                update_upload_status(
                    file_path,
                    UploadStatus.FAILED,
                    message="Upload already in progress for this file to this store"
                )
            return (
                False,
                "Upload already in progress for this file to this store",
                None
            )
        _active_uploads.add(upload_key)

    try:
        last_error = None
        attempt = 0

        while attempt <= max_retries:
            try:
                # Update status to uploading on first attempt, retrying on subsequent
                if use_status_tracker:
                    if attempt == 0:
                        update_upload_status(
                            file_path,
                            UploadStatus.UPLOADING,
                            attempt=attempt,
                            max_retries=max_retries
                        )
                    else:
                        update_upload_status(
                            file_path,
                            UploadStatus.RETRYING,
                            attempt=attempt,
                            max_retries=max_retries,
                            message=f"Retrying after error: {last_error[:50]}..."
                        )

                # Solution 1: Create a fresh upload session for each attempt
                # (never reuse a terminated session)
                operation = client.file_search_stores.upload_to_file_search_store(
                    file=file_path,
                    file_search_store_name=store_name,
                    config=config,
                )

                # Wait for operation to complete
                success, message = wait_for_operation(client, operation)

                if success:
                    if use_status_tracker:
                        update_upload_status(
                            file_path,
                            UploadStatus.COMPLETED,
                            message="Upload successful"
                        )
                    return True, message, operation

                # Check if error indicates terminated session
                if "already been terminated" in message.lower():
                    last_error = message
                    # Don't retry with same session - will create new one in next iteration
                else:
                    # Other error - might not be retryable
                    if use_status_tracker:
                        update_upload_status(
                            file_path,
                            UploadStatus.FAILED,
                            message=message
                        )
                    return False, message, None

            except Exception as e:
                error_str = str(e)
                last_error = error_str

                # Check if it's a retryable error
                if any(err in error_str.lower() for err in RETRYABLE_ERROR_PATTERNS):
                    # Retryable error - continue to backoff and retry
                    pass
                else:
                    # Non-retryable error
                    if use_status_tracker:
                        update_upload_status(
                            file_path,
                            UploadStatus.FAILED,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            message=f"Upload failed: {error_str[:80]}"
                        )
                    return False, f"Upload failed: {error_str}", None

            # If we get here, we need to retry
            attempt += 1

            if attempt <= max_retries:
                # Solution 3: Implement exponential backoff with jitter
                delay = min(initial_delay * (2 ** (attempt - 1)), max_delay)
                # Add jitter (random variation of ±25%)
                jitter = delay * 0.25 * (2 * random.random() - 1)
                actual_delay = max(0.1, delay + jitter)

                # Update status to retrying BEFORE the sleep
                if use_status_tracker:
                    error_preview = str(last_error)[:80] if last_error else "Unknown error"
                    update_upload_status(
                        file_path,
                        UploadStatus.RETRYING,
                        attempt=attempt,
                        max_retries=max_retries,
                        message=f"{error_preview}"
                    )

                if not use_status_tracker:
                    console.print(
                        f"[yellow]Upload attempt {attempt} failed. "
                        f"Retrying in {actual_delay:.1f}s...[/yellow]"
                    )
                time.sleep(actual_delay)

        # Max retries exhausted
        final_message = f"Upload failed after {max_retries + 1} attempts. Last error: {last_error}"
        if use_status_tracker:
            update_upload_status(
                file_path,
                UploadStatus.FAILED,
                attempt=max_retries + 1,
                max_retries=max_retries,
                message=final_message
            )
        return (
            False,
            final_message,
            None
        )

    finally:
        # Solution 4: Always remove from active uploads when done
        with _upload_lock:
            _active_uploads.discard(upload_key)


def is_upload_in_progress(file_path: str, store_name: str) -> bool:
    """
    Check if an upload is currently in progress for a file.

    Args:
        file_path: Path to the file.
        store_name: The file search store name.

    Returns:
        True if upload is in progress, False otherwise.
    """
    upload_key = f"{store_name}:{file_path}"
    with _upload_lock:
        return upload_key in _active_uploads


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a file's contents.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal hash string.
    """
    hash_obj = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def detect_duplicate_files(file_paths: List[str]) -> Dict[str, List[str]]:
    """
    Detect duplicate files based on content hash.

    Args:
        file_paths: List of file paths to check for duplicates.

    Returns:
        Dictionary mapping hash to list of file paths with that hash.
        Only includes hashes that have 2+ files (actual duplicates).
    """
    hash_to_files: Dict[str, List[str]] = {}

    for file_path in file_paths:
        try:
            file_hash = calculate_file_hash(file_path)

            if file_hash not in hash_to_files:
                hash_to_files[file_hash] = []

            hash_to_files[file_hash].append(file_path)
        except Exception as e:
            # If we can't hash a file, skip it
            console.print(f"[yellow]Warning: Could not hash {Path(file_path).name}: {e}[/yellow]")

    # Return only groups with 2+ files (actual duplicates)
    duplicates = {
        hash_val: files
        for hash_val, files in hash_to_files.items()
        if len(files) > 1
    }

    return duplicates


def get_deduplicated_files(
    file_paths: List[str],
    interactive: bool = True
) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Detect duplicates and get user selection for which files to keep.

    Args:
        file_paths: List of file paths to deduplicate.
        interactive: If True, prompt user to select files (default: True).

    Returns:
        Tuple of (files_to_upload, duplicate_groups).
        - files_to_upload: List of files after deduplication
        - duplicate_groups: Dict of hash to list of duplicate file paths
    """
    from rich.prompt import Prompt
    from rich.table import Table
    from rich import box

    duplicates = detect_duplicate_files(file_paths)

    if not duplicates:
        # No duplicates found, return all files
        return file_paths, {}

    # Build list of files to keep
    files_to_keep = []
    all_duplicate_files = set()

    # Track all files that are duplicates
    for files in duplicates.values():
        all_duplicate_files.update(files)

    # Add non-duplicate files first
    for file_path in file_paths:
        if file_path not in all_duplicate_files:
            files_to_keep.append(file_path)

    if interactive:
        console.print()
        console.print("[bold yellow]⚠ Duplicate Files Detected[/bold yellow]")
        console.print()
        console.print(
            f"Found {len(duplicates)} group(s) of duplicate files "
            f"({sum(len(files) for files in duplicates.values())} total duplicates)"
        )
        console.print()

        # Process each duplicate group
        for group_num, (hash_val, dup_files) in enumerate(duplicates.items(), 1):
            console.print(f"[bold cyan]Duplicate Group {group_num}[/bold cyan] (same content):")
            console.print()

            # Create table for this group
            table = Table(
                show_header=True,
                header_style="bold cyan",
                box=box.ROUNDED,
            )
            table.add_column("#", style="dim", width=3)
            table.add_column("Filename", style="white")
            table.add_column("Size", justify="right", width=12)

            for idx, file_path in enumerate(dup_files, 1):
                file_size = Path(file_path).stat().st_size
                table.add_row(
                    str(idx),
                    Path(file_path).name,
                    format_bytes(file_size),
                )

            console.print(table)
            console.print()

            # Get user selection
            console.print("[dim]Enter the number of the file to upload (or 'all' to upload all)[/dim]")
            selection = Prompt.ask(
                f"Which file from group {group_num} do you want to upload?",
                default="1",
            )

            if selection.lower() == "all":
                # Upload all files in this group
                files_to_keep.extend(dup_files)
            else:
                try:
                    idx = int(selection)
                    if 1 <= idx <= len(dup_files):
                        files_to_keep.append(dup_files[idx - 1])
                    else:
                        # Invalid selection, default to first file
                        console.print("[yellow]Invalid selection. Using first file.[/yellow]")
                        files_to_keep.append(dup_files[0])
                except ValueError:
                    # Invalid input, default to first file
                    console.print("[yellow]Invalid input. Using first file.[/yellow]")
                    files_to_keep.append(dup_files[0])

            console.print()
    else:
        # Non-interactive mode: keep first file from each duplicate group
        for dup_files in duplicates.values():
            files_to_keep.append(dup_files[0])

    return files_to_keep, duplicates


def extract_file_metadata(file_path: str) -> List[Dict[str, any]]:
    """
    Extract metadata from a file based on its type.

    Supports:
    - PDF files: Title, author, subject, keywords, creator, creation date, modification date
    - DOCX files: Title, author, subject, keywords, created, modified, last_modified_by
    - PPTX files: Title, author, subject, keywords, created, modified, last_modified_by
    - All files: File extension, file size, upload timestamp

    Args:
        file_path: Path to the file.

    Returns:
        List of metadata dictionaries in Google Gemini CustomMetadata format.
        Each dict has 'key' and one of: 'string_value', 'numeric_value', 'string_list_value'.
        Maximum 20 entries will be returned (API limitation).
    """
    metadata = []
    path = Path(file_path)
    extension = path.suffix.lower()

    # Extract file-type specific metadata
    if extension == ".pdf" and HAS_PYMUPDF:
        metadata.extend(_extract_pdf_metadata(file_path))
    elif extension == ".docx" and HAS_DOCX:
        metadata.extend(_extract_docx_metadata(file_path))
    elif extension in [".pptx", ".ppt"] and HAS_PPTX:
        metadata.extend(_extract_pptx_metadata(file_path))

    # Extract universal file properties
    metadata.extend(_extract_file_properties(file_path))

    # Parse filename for structured metadata (e.g., "Report_2024_Q1.pdf")
    metadata.extend(_parse_filename_metadata(path.name))

    # Limit to 20 entries (Google API constraint)
    return metadata[:20]


def _extract_pdf_metadata(file_path: str) -> List[Dict[str, any]]:
    """
    Extract metadata from a PDF file using PyMuPDF.

    Args:
        file_path: Path to PDF file.

    Returns:
        List of metadata dictionaries.
    """
    metadata = []

    try:
        doc = fitz.open(file_path)
        pdf_metadata = doc.metadata

        # Map PDF metadata fields to custom metadata
        field_mapping = {
            "title": "pdf_title",
            "author": "pdf_author",
            "subject": "pdf_subject",
            "keywords": "pdf_keywords",
            "creator": "pdf_creator",
            "producer": "pdf_producer",
        }

        for pdf_key, custom_key in field_mapping.items():
            value = pdf_metadata.get(pdf_key, "").strip()
            if value:
                metadata.append({
                    "key": custom_key,
                    "string_value": value
                })

        # Add page count
        metadata.append({
            "key": "pdf_page_count",
            "numeric_value": float(doc.page_count)
        })

        # Extract dates if available
        creation_date = pdf_metadata.get("creationDate", "")
        if creation_date:
            metadata.append({
                "key": "pdf_creation_date",
                "string_value": creation_date
            })

        mod_date = pdf_metadata.get("modDate", "")
        if mod_date:
            metadata.append({
                "key": "pdf_modification_date",
                "string_value": mod_date
            })

        doc.close()

    except Exception as e:
        # If extraction fails, log but continue
        console.print(f"[dim yellow]Could not extract PDF metadata: {e}[/dim yellow]")

    return metadata


def _extract_docx_metadata(file_path: str) -> List[Dict[str, any]]:
    """
    Extract metadata from a DOCX file using python-docx.

    Args:
        file_path: Path to DOCX file.

    Returns:
        List of metadata dictionaries.
    """
    metadata = []

    try:
        doc = Document(file_path)
        props = doc.core_properties

        # Extract text properties
        if props.title:
            metadata.append({"key": "docx_title", "string_value": props.title})
        if props.author:
            metadata.append({"key": "docx_author", "string_value": props.author})
        if props.subject:
            metadata.append({"key": "docx_subject", "string_value": props.subject})
        if props.keywords:
            metadata.append({"key": "docx_keywords", "string_value": props.keywords})
        if props.comments:
            metadata.append({"key": "docx_comments", "string_value": props.comments})
        if props.last_modified_by:
            metadata.append({"key": "docx_last_modified_by", "string_value": props.last_modified_by})

        # Extract dates
        if props.created:
            metadata.append({
                "key": "docx_created",
                "string_value": props.created.isoformat()
            })
        if props.modified:
            metadata.append({
                "key": "docx_modified",
                "string_value": props.modified.isoformat()
            })

        # Add paragraph count
        para_count = len(doc.paragraphs)
        metadata.append({
            "key": "docx_paragraph_count",
            "numeric_value": float(para_count)
        })

    except Exception as e:
        console.print(f"[dim yellow]Could not extract DOCX metadata: {e}[/dim yellow]")

    return metadata


def _extract_pptx_metadata(file_path: str) -> List[Dict[str, any]]:
    """
    Extract metadata from a PPTX file using python-pptx.

    Args:
        file_path: Path to PPTX file.

    Returns:
        List of metadata dictionaries.
    """
    metadata = []

    try:
        prs = Presentation(file_path)
        props = prs.core_properties

        # Extract text properties
        if props.title:
            metadata.append({"key": "pptx_title", "string_value": props.title})
        if props.author:
            metadata.append({"key": "pptx_author", "string_value": props.author})
        if props.subject:
            metadata.append({"key": "pptx_subject", "string_value": props.subject})
        if props.keywords:
            metadata.append({"key": "pptx_keywords", "string_value": props.keywords})
        if props.comments:
            metadata.append({"key": "pptx_comments", "string_value": props.comments})
        if props.last_modified_by:
            metadata.append({"key": "pptx_last_modified_by", "string_value": props.last_modified_by})

        # Extract dates
        if props.created:
            metadata.append({
                "key": "pptx_created",
                "string_value": props.created.isoformat()
            })
        if props.modified:
            metadata.append({
                "key": "pptx_modified",
                "string_value": props.modified.isoformat()
            })

        # Add slide count
        slide_count = len(prs.slides)
        metadata.append({
            "key": "pptx_slide_count",
            "numeric_value": float(slide_count)
        })

    except Exception as e:
        console.print(f"[dim yellow]Could not extract PPTX metadata: {e}[/dim yellow]")

    return metadata


def _extract_file_properties(file_path: str) -> List[Dict[str, any]]:
    """
    Extract universal file properties (extension, size, upload timestamp).

    Args:
        file_path: Path to file.

    Returns:
        List of metadata dictionaries.
    """
    metadata = []
    path = Path(file_path)

    try:
        # File extension
        extension = path.suffix.lower()
        if extension:
            metadata.append({
                "key": "file_extension",
                "string_value": extension
            })

        # File size in MB
        size_bytes = path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        metadata.append({
            "key": "file_size_mb",
            "numeric_value": round(size_mb, 2)
        })

        # Upload timestamp
        metadata.append({
            "key": "upload_timestamp",
            "string_value": datetime.now().isoformat()
        })

        # File modification time
        mod_time = datetime.fromtimestamp(path.stat().st_mtime)
        metadata.append({
            "key": "file_modified",
            "string_value": mod_time.isoformat()
        })

    except Exception as e:
        console.print(f"[dim yellow]Could not extract file properties: {e}[/dim yellow]")

    return metadata


def _parse_filename_metadata(filename: str) -> List[Dict[str, any]]:
    """
    Parse filename for structured metadata patterns.

    Common patterns:
    - "Report_2024_Q1.pdf" -> year: 2024, quarter: Q1
    - "Invoice_12345.pdf" -> invoice_number: 12345
    - "Meeting_Notes_2024-01-15.docx" -> date: 2024-01-15

    Args:
        filename: Name of the file.

    Returns:
        List of metadata dictionaries.
    """
    metadata = []

    try:
        # Remove extension for parsing
        name_without_ext = Path(filename).stem

        # Extract year (4 digits)
        import re
        year_match = re.search(r'\b(20\d{2})\b', name_without_ext)
        if year_match:
            metadata.append({
                "key": "filename_year",
                "string_value": year_match.group(1)
            })

        # Extract quarter (Q1, Q2, Q3, Q4)
        quarter_match = re.search(r'\b(Q[1-4])\b', name_without_ext, re.IGNORECASE)
        if quarter_match:
            metadata.append({
                "key": "filename_quarter",
                "string_value": quarter_match.group(1).upper()
            })

        # Extract date (YYYY-MM-DD format)
        date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', name_without_ext)
        if date_match:
            metadata.append({
                "key": "filename_date",
                "string_value": date_match.group(1)
            })

        # Extract version (v1.0, v2.3, version-1.0, etc.)
        version_match = re.search(r'\b[vV]?ersion[_-]?(\d+\.?\d*)\b', name_without_ext)
        if not version_match:
            version_match = re.search(r'\b[vV](\d+\.?\d*)\b', name_without_ext)
        if version_match:
            metadata.append({
                "key": "filename_version",
                "string_value": version_match.group(1)
            })

        # Extract document type from prefix (common patterns)
        doc_type_patterns = {
            r'^(invoice|receipt|bill)': "invoice",
            r'^(report|summary)': "report",
            r'^(contract|agreement)': "contract",
            r'^(proposal)': "proposal",
            r'^(meeting|minutes)': "meeting_notes",
            r'^(presentation|slides)': "presentation",
        }

        for pattern, doc_type in doc_type_patterns.items():
            if re.search(pattern, name_without_ext, re.IGNORECASE):
                metadata.append({
                    "key": "filename_document_type",
                    "string_value": doc_type
                })
                break

    except Exception as e:
        # Filename parsing is best-effort, don't fail on errors
        pass

    return metadata


def show_header() -> None:
    """
    Display the standard application header.

    Clears console and shows styled header panel with app name.
    """
    from rich import box
    from rich.panel import Panel

    console.clear()
    console.print(
        Panel(
            "[bold cyan]Gemini File Search Manager[/bold cyan]\n"
            "[dim]Manage your Google Gemini File Search Stores[/dim]",
            box=box.DOUBLE,
            padding=(1, 2),
        )
    )
    console.print()


def select_item_from_list(
    items: list,
    item_type: str = "item",
    get_display_name: callable = lambda x: str(x),
    get_identifier: callable = lambda x: str(x),
) -> any:
    """
    Generic function to select an item from a list by number, name, or identifier.

    Args:
        items: List of items to select from.
        item_type: Type of item for display messages (e.g., "store", "document").
        get_display_name: Function to extract display name from item.
        get_identifier: Function to extract unique identifier from item.

    Returns:
        Selected item or None if no match found or cancelled.

    Example:
        store = select_item_from_list(
            items=stores,
            item_type="store",
            get_display_name=lambda s: getattr(s, "display_name", "") or s.name,
            get_identifier=lambda s: s.name
        )
    """
    from rich.prompt import Prompt

    if not items:
        print_warning(f"No {item_type}s available.")
        return None

    # Get user selection
    selection = Prompt.ask(f"Enter the number, name, or ID of the {item_type}").strip()

    if not selection:
        print_warning("No selection provided.")
        return None

    # Try to match by number first
    if selection.isdigit():
        idx = int(selection) - 1
        if 0 <= idx < len(items):
            return items[idx]

    # Try to match by display name or identifier
    selection_lower = selection.lower()
    for item in items:
        display_name = get_display_name(item)
        identifier = get_identifier(item)

        # Match display name (case-insensitive)
        if display_name and selection_lower == display_name.lower():
            return item

        # Match full identifier
        if identifier and selection == identifier:
            return item

        # Match identifier without prefix (e.g., "abc123" matches "fileSearchStores/abc123")
        if identifier and "/" in identifier:
            short_id = identifier.split("/")[-1]
            if selection == short_id:
                return item

    print_error(f"No {item_type} found matching: {selection}")
    return None