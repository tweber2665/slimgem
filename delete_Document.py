"""
delete_Document.py
Delete a document from a File Search Store.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

from utils import (
    get_client,
    format_bytes,
    print_error,
    print_info,
    print_success,
    print_warning,
    show_header,
)

console = Console()


def main():
    """Delete a document from a File Search Store."""
    show_header()
    console.print("[bold cyan]Delete a Document[/bold cyan]")
    console.print()
    console.print("[bold red]⚠ WARNING: This action cannot be undone![/bold red]")
    console.print()

    # Fetch stores first
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

        # Get store selection
        store_selection = Prompt.ask("Select a store (enter number or name)")

        if not store_selection.strip():
            print_error("Selection is required.")
            Prompt.ask("Press Enter to continue")
            return

        store_selection = store_selection.strip()
        selected_store = None

        # Try to match by number
        try:
            idx = int(store_selection)
            if 1 <= idx <= len(stores):
                selected_store = stores[idx - 1]
        except ValueError:
            pass

        # Try to match by display name or store name
        if selected_store is None:
            for store in stores:
                display_name = getattr(store, "display_name", "") or ""
                if store_selection.lower() == display_name.lower():
                    selected_store = store
                    break
                if store.name and (store_selection == store.name or store_selection == store.name.replace("fileSearchStores/", "")):
                    selected_store = store
                    break

        if selected_store is None:
            print_error(f"No store found matching: {store_selection}")
            Prompt.ask("Press Enter to continue")
            return

        store_name = selected_store.name
        assert store_name is not None, "Store name should not be None"
        store_display = getattr(selected_store, "display_name", None) or store_name

        console.print()
        print_info(f"Fetching documents from [cyan]{store_display}[/cyan]...")

        # Fetch documents
        documents = list(client.file_search_stores.documents.list(parent=store_name))

        if not documents:
            print_warning("No documents found in this store.")
            Prompt.ask("Press Enter to continue")
            return

        console.print()

        # Display documents
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
        )

        table.add_column("#", style="dim", width=3)
        table.add_column("Display Name", style="cyan", overflow="fold")
        table.add_column("State", justify="center")
        table.add_column("Size", justify="right", width=10)

        for idx, doc in enumerate(documents, 1):
            # Get state
            state_raw = getattr(doc, "state", None)
            state_str = str(state_raw) if state_raw else "UNKNOWN"

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

            table.add_row(
                str(idx),
                getattr(doc, "display_name", None) or "—",
                state_display,
                size_str,
            )

        console.print(table)
        console.print()

        # Get document selection
        doc_selection = Prompt.ask("Select a document to delete (enter number or name)")

        if not doc_selection.strip():
            print_error("Selection is required.")
            Prompt.ask("Press Enter to continue")
            return

        doc_selection = doc_selection.strip()
        selected_doc = None

        # Try to match by number
        try:
            idx = int(doc_selection)
            if 1 <= idx <= len(documents):
                selected_doc = documents[idx - 1]
        except ValueError:
            pass

        # Try to match by display name
        if selected_doc is None:
            for doc in documents:
                display_name = getattr(doc, "display_name", "") or ""
                if doc_selection.lower() == display_name.lower():
                    selected_doc = doc
                    break

        if selected_doc is None:
            print_error(f"No document found matching: {doc_selection}")
            Prompt.ask("Press Enter to continue")
            return

        doc_name = selected_doc.name
        assert doc_name is not None, "Document name should not be None"
        doc_display = getattr(selected_doc, "display_name", None) or doc_name

        console.print()

        # Confirm deletion
        if not Confirm.ask(
            f"Delete document [cyan]{doc_display}[/cyan]?",
            default=False,
        ):
            print_info("Deletion cancelled.")
            Prompt.ask("Press Enter to continue")
            return

        console.print()

        force = Confirm.ask(
            "Force delete including all chunks?",
            default=True,
        )

        console.print()
        print_info("Deleting document...")

        if force:
            client.file_search_stores.documents.delete(name=doc_name, config={"force": True})
        else:
            client.file_search_stores.documents.delete(name=doc_name)

        console.print()
        print_success(f"Document deleted: {doc_display}")

    except Exception as e:
        error_str = str(e)
        if "NOT_FOUND" in error_str:
            print_error("Document not found.")
        elif "FAILED_PRECONDITION" in error_str:
            print_error("Document contains chunks. Use 'force delete' option.")
        else:
            print_error(f"Failed to delete document: {error_str}")

    console.print()
    Prompt.ask("Press Enter to continue")


if __name__ == "__main__":
    main()
