"""
delete_FileStore.py
Delete a File Search Store.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

from utils import (
    get_client,
    print_error,
    print_info,
    print_success,
    print_warning,
    show_header,
)

console = Console()


def main():
    """Delete a File Search Store."""
    show_header()
    console.print("[bold cyan]Delete File Search Store[/bold cyan]")
    console.print()
    console.print("[bold red]⚠ WARNING: This action cannot be undone![/bold red]")
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
        table.add_column("Store Name", style="dim", overflow="fold")

        for idx, store in enumerate(stores, 1):
            table.add_row(
                str(idx),
                getattr(store, "display_name", None) or "—",
                store.name,
            )

        console.print(table)
        console.print()

        # Get user selection
        selection = Prompt.ask(
            "Enter the number, Display Name, or Store Name to delete"
        )

        if not selection.strip():
            print_error("Selection is required.")
            Prompt.ask("Press Enter to continue")
            return

        selection = selection.strip()
        store_to_delete = None

        # Try to match by number first
        try:
            idx = int(selection)
            if 1 <= idx <= len(stores):
                store_to_delete = stores[idx - 1]
        except ValueError:
            pass

        # Try to match by display name or store name
        if store_to_delete is None:
            for store in stores:
                display_name = getattr(store, "display_name", "") or ""
                if selection.lower() == display_name.lower():
                    store_to_delete = store
                    break
                if store.name and (selection == store.name or selection == store.name.replace("fileSearchStores/", "")):
                    store_to_delete = store
                    break

        if store_to_delete is None:
            print_error(f"No store found matching: {selection}")
            Prompt.ask("Press Enter to continue")
            return

        store_name = store_to_delete.name
        assert store_name is not None, "Store name should not be None"
        display_name = getattr(store_to_delete, "display_name", None) or store_name

        console.print()

        # Confirm deletion
        if not Confirm.ask(
            f"Delete store [cyan]{display_name}[/cyan]?",
            default=False,
        ):
            print_info("Deletion cancelled.")
            Prompt.ask("Press Enter to continue")
            return

        console.print()

        force = Confirm.ask(
            "Force delete even if store contains documents?",
            default=False,
        )

        console.print()
        print_info("Deleting store...")

        if force:
            client.file_search_stores.delete(name=store_name, config={"force": True})
        else:
            client.file_search_stores.delete(name=store_name)

        console.print()
        print_success(f"Store deleted: {display_name}")

    except Exception as e:
        error_str = str(e)
        if "NOT_FOUND" in error_str:
            print_error("Store not found.")
        elif "FAILED_PRECONDITION" in error_str:
            print_error("Store contains documents. Use 'force delete' option.")
        else:
            print_error(f"Failed to delete store: {error_str}")

    console.print()
    Prompt.ask("Press Enter to continue")


if __name__ == "__main__":
    main()
