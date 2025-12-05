"""
view_FileStore_details.py
View detailed information about a specific File Search Store.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import box

from utils import (
    get_client,
    format_bytes,
    format_timestamp,
    print_error,
    print_info,
    print_warning,
    show_header,
)

console = Console()


def main():
    """View details of a specific store."""
    show_header()
    console.print("[bold cyan]Store Details[/bold cyan]")
    console.print()

    # Fetch stores first so user can pick by number or name
    print_info("Fetching stores...")

    try:
        client = get_client()
        stores = list(client.file_search_stores.list())

        if not stores:
            print_warning("No File Search Stores found.")
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

        for idx, store in enumerate(stores, 1):
            active_docs = getattr(store, "active_documents_count", 0) or 0
            table.add_row(
                str(idx),
                getattr(store, "display_name", None) or store.name,
                str(active_docs),
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

        # Fetch fresh details
        console.print()
        print_info("Fetching store details...")

        store = client.file_search_stores.get(name=store_name)

        console.print()
        console.print(Panel(f"[bold cyan]{getattr(store, 'display_name', None) or store.name}[/bold cyan]"))
        console.print()

        # Get create time
        create_time = getattr(store, "create_time", None)
        if create_time is not None:
            if hasattr(create_time, 'strftime'):
                created = create_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created = format_timestamp(str(create_time))
        else:
            created = "—"

        # Get update time
        update_time = getattr(store, "update_time", None)
        if update_time is not None:
            if hasattr(update_time, 'strftime'):
                updated = update_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                updated = format_timestamp(str(update_time))
        else:
            updated = "—"

        # Get size
        size_bytes = getattr(store, "size_bytes", None)
        if size_bytes is not None:
            try:
                size_str = format_bytes(int(size_bytes))
            except (ValueError, TypeError):
                size_str = "—"
        else:
            size_str = "—"

        # Display details
        details = [
            ("Store Name", store.name),
            ("Display Name", getattr(store, "display_name", None) or "—"),
            ("Active Documents", str(getattr(store, "active_documents_count", 0) or 0)),
            ("Pending Documents", str(getattr(store, "pending_documents_count", 0) or 0)),
            ("Failed Documents", str(getattr(store, "failed_documents_count", 0) or 0)),
            ("Size", size_str),
            ("Created", created),
            ("Updated", updated),
        ]

        for label, value in details:
            console.print(f"  [bold]{label}:[/bold] {value}")

    except Exception as e:
        error_str = str(e)
        if "NOT_FOUND" in error_str:
            print_error("Store not found.")
        else:
            print_error(f"Failed to get store details: {error_str}")

    console.print()
    Prompt.ask("Press Enter to continue")


if __name__ == "__main__":
    main()
