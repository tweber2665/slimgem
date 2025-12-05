"""
list_Documents.py
List all documents in a File Search Store.
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
    print_success,
    print_warning,
    show_header,
)

console = Console()


def main():
    """List documents in a store."""
    show_header()
    console.print("[bold cyan]Documents in Store[/bold cyan]")
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
        store_display = getattr(selected_store, "display_name", None) or store_name

        console.print()
        print_info(f"Fetching documents from [cyan]{store_display}[/cyan]...")

        # Fetch documents
        documents = list(client.file_search_stores.documents.list(parent=store_name))

        console.print()

        if not documents:
            print_warning("No documents found in this store.")
        else:
            table = Table(
                show_header=True,
                header_style="bold cyan",
                box=box.ROUNDED,
                expand=True,
            )

            table.add_column("#", style="dim", width=3)
            table.add_column("Display Name", style="cyan", overflow="fold")
            table.add_column("State", justify="center")
            table.add_column("Size", justify="right", width=10)
            table.add_column("Created", style="dim")

            for idx, doc in enumerate(documents, 1):
                # Get state and convert to string safely
                state_raw = getattr(doc, "state", None)
                state_str = str(state_raw) if state_raw else "UNKNOWN"

                # Color code state
                if "ACTIVE" in state_str.upper():
                    state_display = "[green]ACTIVE[/green]"
                elif "PENDING" in state_str.upper():
                    state_display = "[yellow]PENDING[/yellow]"
                elif "FAILED" in state_str.upper():
                    state_display = "[red]FAILED[/red]"
                else:
                    state_display = state_str

                # Get size
                size = getattr(doc, "size_bytes", None)
                if size is not None:
                    try:
                        size_str = format_bytes(int(size))
                    except (ValueError, TypeError):
                        size_str = "—"
                else:
                    size_str = "—"

                # Get create time
                create_time = getattr(doc, "create_time", None)
                if create_time is not None:
                    if hasattr(create_time, 'strftime'):
                        created = create_time.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        created = format_timestamp(str(create_time))
                else:
                    created = "—"

                table.add_row(
                    str(idx),
                    getattr(doc, "display_name", None) or "—",
                    state_display,
                    size_str,
                    created,
                )

            console.print(table)
            console.print()
            print_success(f"Found {len(documents)} document(s) in {store_display}")

    except Exception as e:
        error_str = str(e)
        if "NOT_FOUND" in error_str:
            print_error(f"Store not found.")
        else:
            print_error(f"Failed to list documents: {error_str}")

    console.print()
    Prompt.ask("Press Enter to continue")


if __name__ == "__main__":
    main()
