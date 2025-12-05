"""
list_FileStores.py
List all Gemini File Search Stores with their details.
"""

import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from utils import (
    get_client,
    format_bytes,
    format_timestamp,
    print_success,
    print_error,
    print_info,
    print_warning,
)
from config import MAX_STORES_PER_PROJECT, STORAGE_TIERS

console = Console()


def list_file_stores() -> dict:
    """
    List all File Search Stores.
    
    Returns:
        Dictionary with list of stores or error information.
    """
    client = get_client()
    
    try:
        print_info("Fetching File Search Stores...")
        
        stores = []
        for store in client.file_search_stores.list():
            store_info = {
                "name": store.name,
                "display_name": getattr(store, "display_name", None),
                "create_time": getattr(store, "create_time", None),
                "update_time": getattr(store, "update_time", None),
                "active_documents": getattr(store, "active_documents_count", 0),
                "pending_documents": getattr(store, "pending_documents_count", 0),
                "failed_documents": getattr(store, "failed_documents_count", 0),
                "size_bytes": getattr(store, "size_bytes", None),
            }
            stores.append(store_info)
        
        return {
            "success": True,
            "stores": stores,
            "count": len(stores),
        }
        
    except Exception as e:
        error_message = str(e)
        
        if "PERMISSION_DENIED" in error_message:
            return {
                "success": False,
                "error": "Permission denied. Check your API key permissions.",
            }
        else:
            return {
                "success": False,
                "error": f"Failed to list stores: {error_message}",
            }


def display_stores(stores: list) -> None:
    """Display stores in a formatted table."""
    if not stores:
        print_warning("No File Search Stores found.")
        console.print()
        console.print(
            "[dim]Create a new store using option 1 in the main menu, "
            "or run:[/dim] [cyan]python create_FileStore.py[/cyan]"
        )
        return
    
    # Create table
    table = Table(
        title="File Search Stores",
        show_header=True,
        header_style="bold cyan",
    )
    
    table.add_column("Store Name", style="cyan", no_wrap=True)
    table.add_column("Display Name", style="white")
    table.add_column("Documents", justify="center")
    table.add_column("Size", justify="right")
    table.add_column("Created", style="dim")
    
    for store in stores:
        # Format document counts
        active = store.get("active_documents", 0) or 0
        pending = store.get("pending_documents", 0) or 0
        failed = store.get("failed_documents", 0) or 0
        
        if pending > 0 or failed > 0:
            doc_str = f"{active} [dim](+{pending} pending, {failed} failed)[/dim]"
        else:
            doc_str = str(active)
        
        # Format size
        size_bytes = store.get("size_bytes")
        size_str = format_bytes(size_bytes) if size_bytes else "—"
        
        # Format timestamps
        created = format_timestamp(store.get("create_time"))
        
        table.add_row(
            store["name"],
            store.get("display_name") or "—",
            doc_str,
            size_str,
            created,
        )
    
    console.print(table)


def main():
    """Main function for standalone execution."""
    console.print(
        Panel(
            "[bold cyan]List File Search Stores[/bold cyan]",
            subtitle="Gemini File Search Manager",
        )
    )
    console.print()
    
    # Get the stores
    result = list_file_stores()
    
    if result["success"]:
        console.print()
        display_stores(result["stores"])
        console.print()
        
        # Show summary
        count = result["count"]
        print_success(f"Found {count} store(s)")
        
        if count > 0:
            console.print(
                f"[dim]Store limit: {count}/{MAX_STORES_PER_PROJECT}[/dim]"
            )
        
        console.print()
        
        # Show storage tier info
        console.print("[bold]Storage Limits by Tier:[/bold]")
        for tier, limit in STORAGE_TIERS.items():
            console.print(f"  • {tier}: {limit}")
        console.print()
        
    else:
        console.print()
        print_error(result["error"])
        console.print()
        sys.exit(1)


if __name__ == "__main__":
    main()