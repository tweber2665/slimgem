"""
main.py
Main Terminal UI for Gemini File Search Manager.
Provides a menu-driven interface for managing File Search Stores.
"""

import sys
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

from utils import (
    get_client,
    get_files_from_path,
    format_bytes,
    format_timestamp,
    print_success,
    print_error,
    print_info,
    print_warning,
    clean_path_input,
    log_upload_failure,
    get_failure_log,
    clear_failure_log,
    get_deduplicated_files,
    show_header,
)
from config import (
    DEFAULT_MAX_TOKENS_PER_CHUNK,
    DEFAULT_MAX_OVERLAP_TOKENS,
    MAX_STORES_PER_PROJECT,
)
from upload_to_FileStore import upload_multiple_files, display_upload_results
import view_FileStore_details
import delete_FileStore
import list_Documents
import view_Document_details
import delete_Document
import view_failurelog

console = Console()


def show_menu():
    """Display the main menu and return user choice."""
    console.print("[bold]Main Menu[/bold]")
    console.print()
    console.print("  [cyan]1[/cyan]  Create new File Search Store")
    console.print("  [cyan]2[/cyan]  Upload files to existing File Search Store")
    console.print("  [cyan]3[/cyan]  List existing File Search Stores")
    console.print("  [cyan]4[/cyan]  View existing File Search Store Details")
    console.print("  [cyan]5[/cyan]  Delete existing File Search Store")
    console.print("  [cyan]6[/cyan]  List existing Documents in File Search Store")
    console.print("  [cyan]7[/cyan]  View existing Document Details")
    console.print("  [cyan]8[/cyan]  Delete existing Document")
    console.print("  [cyan]9[/cyan]  View Upload Failure Log")
    console.print()
    console.print("  [cyan]0[/cyan]  Exit")
    console.print()
    
    choice = Prompt.ask(
        "Enter your choice",
        choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
        default="0",
    )
    
    return choice


def create_store():
    """Create a new File Search Store."""
    show_header()
    console.print("[bold cyan]Create New File Search Store[/bold cyan]")
    console.print()
    
    display_name = Prompt.ask(
        "Enter a display name (or press Enter to skip)",
        default="",
    )
    
    if not display_name.strip():
        display_name = None
    
    console.print()
    print_info("Creating store...")
    
    try:
        client = get_client()
        
        if display_name:
            store = client.file_search_stores.create(config={"display_name": display_name})
        else:
            store = client.file_search_stores.create()
        
        console.print()
        print_success("Store created successfully!")
        console.print()
        console.print("[bold]Store Details:[/bold]")
        console.print(f"  • Name: [cyan]{store.name}[/cyan]")
        
        if hasattr(store, "display_name") and store.display_name:
            console.print(f"  • Display Name: {store.display_name}")
        
        console.print()
        console.print(
            "[dim]Copy the store name above - you'll need it to upload files.[/dim]"
        )
        
    except Exception as e:
        console.print()
        print_error(f"Failed to create store: {str(e)}")
    
    console.print()
    Prompt.ask("Press Enter to continue")


def list_stores():
    """List all File Search Stores."""
    show_header()
    console.print("[bold cyan]File Search Stores[/bold cyan]")
    console.print()
    
    print_info("Fetching stores...")
    
    try:
        client = get_client()
        stores = list(client.file_search_stores.list())
        
        console.print()
        
        if not stores:
            print_warning("No File Search Stores found.")
            console.print()
            console.print("[dim]Create a new store using option 1 from the main menu.[/dim]")
        else:
            # Create table
            table = Table(
                show_header=True,
                header_style="bold cyan",
                box=box.ROUNDED,
                show_lines=True,
                expand=True,
            )
            
            table.add_column("#", style="dim", width=3)
            table.add_column("Store Name", style="cyan", overflow="fold")
            table.add_column("Display Name", overflow="fold")
            table.add_column("Docs", justify="center", width=6)
            table.add_column("Size", justify="right", width=10)
            
            for idx, store in enumerate(stores, 1):
                active_docs = getattr(store, "active_documents_count", 0) or 0
                pending_docs = getattr(store, "pending_documents_count", 0) or 0
                
                if pending_docs > 0:
                    doc_str = f"{active_docs} (+{pending_docs})"
                else:
                    doc_str = str(active_docs)
                
                size_bytes = getattr(store, "size_bytes", None)
                size_str = format_bytes(size_bytes) if size_bytes else "—"
                
                table.add_row(
                    str(idx),
                    store.name,
                    getattr(store, "display_name", None) or "—",
                    doc_str,
                    size_str,
                )
            
            console.print(table)
            console.print()
            print_success(f"Found {len(stores)} store(s)")
            console.print(f"[dim]Store limit: {len(stores)}/{MAX_STORES_PER_PROJECT}[/dim]")
        
    except Exception as e:
        console.print()
        print_error(f"Failed to list stores: {str(e)}")
    
    console.print()
    Prompt.ask("Press Enter to continue")


def upload_files():
    """Upload files to a File Search Store."""
    show_header()
    console.print("[bold cyan]Upload Files to Store[/bold cyan]")
    console.print()
    
    # Fetch stores first so user can pick by number or name
    print_info("Fetching stores...")
    
    try:
        client = get_client()
        stores = list(client.file_search_stores.list())
        
        if not stores:
            print_warning("No File Search Stores found. Create one first using option 1.")
            Prompt.ask("Press Enter to continue")
            return
        
        console.print()
        
        # Display stores with numbers
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
        )
        
        table.add_column("#", style="dim", width=3)
        table.add_column("Display Name", style="cyan")
        table.add_column("Docs", justify="center", width=6)
        table.add_column("Size", justify="right", width=10)
        
        for idx, store in enumerate(stores, 1):
            active_docs = getattr(store, "active_documents_count", 0) or 0
            size_bytes = getattr(store, "size_bytes", None)
            if size_bytes is not None:
                try:
                    size_str = format_bytes(int(size_bytes))
                except (ValueError, TypeError):
                    size_str = "—"
            else:
                size_str = "—"
            
            table.add_row(
                str(idx),
                getattr(store, "display_name", None) or store.name,
                str(active_docs),
                size_str,
            )
        
        console.print(table)
        console.print()
        
        # Get user selection
        selection = Prompt.ask("Select a store (enter number or name)")
        
        if not selection.strip():
            print_error("Selection is required.")
            Prompt.ask("Press Enter to continue")
            return
        
        selection = selection.strip()
        selected_store = None
        
        # Try to match by number first
        try:
            idx = int(selection)
            if 1 <= idx <= len(stores):
                selected_store = stores[idx - 1]
        except ValueError:
            pass
        
        # Try to match by display name or store name
        if selected_store is None:
            for store in stores:
                display_name = getattr(store, "display_name", "") or ""
                if selection.lower() == display_name.lower():
                    selected_store = store
                    break
                if store.name and (selection == store.name or selection == store.name.replace("fileSearchStores/", "")):
                    selected_store = store
                    break
        
        if selected_store is None:
            print_error(f"No store found matching: {selection}")
            Prompt.ask("Press Enter to continue")
            return
        
        store_name = selected_store.name
        assert store_name is not None, "Store name should not be None"
        store_display = getattr(selected_store, "display_name", None) or store_name

        console.print()
        console.print(f"Uploading to: [cyan]{store_display}[/cyan]")
        console.print()
        
        # Get path(s) - allow adding multiple files/folders through a loop
        # (Terminal can only accept 1 drag at a time)
        paths = []

        while True:
            if paths:
                console.print(f"\n[dim]Added {len(paths)} file(s)/folder(s) so far[/dim]")
                if not Confirm.ask("Add another file or folder?", default=False):
                    break
                console.print()

            path_input = Prompt.ask("Drag & drop file or folder (or press Enter if done)")

            if not path_input.strip():
                if paths:
                    # User pressed Enter with existing paths - done adding
                    break
                else:
                    print_error("At least one path is required.")
                    Prompt.ask("Press Enter to continue")
                    return

            # Clean and resolve path
            cleaned = clean_path_input(path_input)
            resolved = Path(cleaned).expanduser().resolve()

            if resolved.exists():
                if resolved not in paths:
                    paths.append(resolved)
                    console.print(f"[green]✓ Added: {resolved.name}[/green]")
                else:
                    print_warning(f"Already added: {resolved.name}")
            else:
                print_error(f"Path does not exist: {resolved}")

        if not paths:
            print_error("No valid paths provided.")
            Prompt.ask("Press Enter to continue")
            return

        console.print()

        # Handle multiple paths
        valid_files = []
        skipped_files = []
        recursive = False

        # If any path is a directory, ask about recursion
        has_directory = any(p.is_dir() for p in paths)
        if has_directory:
            print_info(f"Directory detected in paths")
            recursive = Confirm.ask("Include subdirectories (recursive)?", default=False)

        # Get files from all paths
        for path in paths:
            files, skipped = get_files_from_path(str(path), recursive=recursive)
            valid_files.extend(files)
            skipped_files.extend(skipped)
        
        if not valid_files:
            print_error("No valid files found to upload.")
            Prompt.ask("Press Enter to continue")
            return
        
        console.print()
        print_info(f"Found {len(valid_files)} valid file(s)")

        # Show preview
        for f in valid_files[:5]:
            console.print(f"  • {Path(f).name}")
        if len(valid_files) > 5:
            console.print(f"  ... and {len(valid_files) - 5} more")

        if skipped_files:
            console.print()
            print_warning(f"Skipping {len(skipped_files)} invalid file(s)")

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

        # Chunking configuration
        console.print()
        console.print("[bold]Chunking Configuration[/bold]")
        console.print(
            f"[dim]Default: {DEFAULT_MAX_TOKENS_PER_CHUNK} tokens/chunk, "
            f"{DEFAULT_MAX_OVERLAP_TOKENS} token overlap[/dim]"
        )
        
        use_custom = Confirm.ask("Customize chunking settings?", default=False)
        
        max_tokens = None
        max_overlap = None
        
        if use_custom:
            console.print()
            
            # Get chunk size (1-512)
            tokens_input = Prompt.ask(
                "Max tokens per chunk (1-512)",
                default=str(DEFAULT_MAX_TOKENS_PER_CHUNK),
            )
            try:
                max_tokens = max(1, min(512, int(tokens_input)))
            except ValueError:
                max_tokens = DEFAULT_MAX_TOKENS_PER_CHUNK
            
            # Calculate max overlap as 25% of chunk size
            max_allowed_overlap = max_tokens // 4
            
            overlap_input = Prompt.ask(
                f"Max overlap tokens (0-{max_allowed_overlap}, recommended: ~10%)",
                default=str(max(1, max_tokens // 10)),
            )
            try:
                max_overlap = max(0, min(max_allowed_overlap, int(overlap_input)))
            except ValueError:
                max_overlap = max(1, max_tokens // 10)
            
            print_info(f"Using: {max_tokens} tokens/chunk, {max_overlap} token overlap")
        
        # Confirm
        console.print()
        if not Confirm.ask(f"Upload {len(valid_files)} file(s) to [cyan]{store_display}[/cyan]?", default=True):
            print_info("Upload cancelled.")
            Prompt.ask("Press Enter to continue")
            return
        
        console.print()

        # Upload files in parallel
        results = upload_multiple_files(
            store_name=store_name,
            file_paths=valid_files,
            max_tokens_per_chunk=max_tokens,
            max_overlap_tokens=max_overlap,
        )

        # Display results
        display_upload_results(results)

        # Log any failures
        for item in results["failed"]:
            log_upload_failure(
                Path(item["file_path"]).name,
                store_name,
                item.get("error", "Unknown error"),
            )

        console.print()

        if results["failed"]:
            print_warning(
                f"Completed: {len(results['successful'])} successful, {len(results['failed'])} failed"
            )
        else:
            print_success(f"All {results['total']} file(s) uploaded successfully!")
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
    
    console.print()
    Prompt.ask("Press Enter to continue")


def main():
    """Main application entry point."""
    # Verify API client can be initialized
    try:
        get_client()
    except SystemExit:
        return
    
    while True:
        show_header()
        choice = show_menu()
        
        if choice == "0":
            console.print()
            console.print("[dim]Goodbye![/dim]")
            console.print()
            break
        elif choice == "1":
            create_store()
        elif choice == "2":
            upload_files()
        elif choice == "3":
            list_stores()
        elif choice == "4":
            view_FileStore_details.main()
        elif choice == "5":
            delete_FileStore.main()
        elif choice == "6":
            list_Documents.main()
        elif choice == "7":
            view_Document_details.main()
        elif choice == "8":
            delete_Document.main()
        elif choice == "9":
            view_failurelog.main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print()
        console.print("[dim]Interrupted. Goodbye![/dim]")
        console.print()
        sys.exit(0)
