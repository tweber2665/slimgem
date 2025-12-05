"""
view_Document_details.py
View detailed information about a specific document.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import box

from utils import (
    get_client,
    format_bytes,
    print_error,
    print_warning,
    show_header,
)

console = Console()


def main():
    """View detailed information about a specific document."""
    show_header()
    console.print("[bold]View Document Details[/bold]\n")

    try:
        client = get_client()

        # Get and display stores
        stores = list(client.file_search_stores.list())

        if not stores:
            print_warning("No File Search Stores found.")
            Prompt.ask("Press Enter to continue")
            return

        # Display stores table for selection
        table = Table(
            show_header=True,
            header_style="bold cyan",
            expand=True,
            show_lines=True
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Display Name", overflow="fold")
        table.add_column("Store Name", overflow="fold")
        table.add_column("Docs", justify="right", width=6)

        for i, store in enumerate(stores, 1):
            doc_count = int(getattr(store, 'active_documents_count', 0) or 0)
            table.add_row(
                str(i),
                store.display_name or "(no name)",
                store.name,
                str(doc_count)
            )

        console.print(table)
        console.print()

        # Select store
        store_input = console.input("[bold]Select store (number, Display Name, or Store Name): [/bold]").strip()

        if not store_input:
            print_warning("No store selected.")
            Prompt.ask("Press Enter to continue")
            return

        # Find the selected store
        selected_store = None

        # Try by number first
        if store_input.isdigit():
            idx = int(store_input) - 1
            if 0 <= idx < len(stores):
                selected_store = stores[idx]

        # Try by name if not found
        if not selected_store:
            for store in stores:
                if (store_input.lower() == (store.display_name or "").lower() or
                    (store.name and (store_input == store.name or store_input == store.name.split("/")[-1]))):
                    selected_store = store
                    break

        if not selected_store:
            print_error(f"Store not found: {store_input}")
            Prompt.ask("Press Enter to continue")
            return

        assert selected_store.name is not None, "Store name should not be None"

        # List documents in the selected store
        documents = list(client.file_search_stores.documents.list(parent=selected_store.name))

        if not documents:
            print_warning(f"No documents in store '{selected_store.display_name or selected_store.name}'")
            Prompt.ask("Press Enter to continue")
            return

        # Display documents table
        doc_table = Table(
            show_header=True,
            header_style="bold cyan",
            expand=True,
            show_lines=True
        )
        doc_table.add_column("#", style="dim", width=4)
        doc_table.add_column("Display Name", overflow="fold")
        doc_table.add_column("State", width=10)
        doc_table.add_column("Size", justify="right", width=12)

        for i, doc in enumerate(documents, 1):
            state_str = str(getattr(doc, 'state', 'UNKNOWN'))
            if 'ACTIVE' in state_str:
                state_display = "[green]ACTIVE[/green]"
            elif 'PENDING' in state_str:
                state_display = "[yellow]PENDING[/yellow]"
            elif 'FAILED' in state_str:
                state_display = "[red]FAILED[/red]"
            else:
                state_display = state_str

            size = format_bytes(int(getattr(doc, 'size_bytes', 0) or 0))

            doc_table.add_row(
                str(i),
                doc.display_name or "(no name)",
                state_display,
                size
            )

        console.print(doc_table)
        console.print()

        # Select document
        doc_input = console.input("[bold]Select document (number or Display Name): [/bold]").strip()

        if not doc_input:
            print_warning("No document selected.")
            Prompt.ask("Press Enter to continue")
            return

        # Find the selected document
        selected_doc = None

        if doc_input.isdigit():
            idx = int(doc_input) - 1
            if 0 <= idx < len(documents):
                selected_doc = documents[idx]

        if not selected_doc:
            for doc in documents:
                if doc_input.lower() == (doc.display_name or "").lower() or doc_input == doc.name:
                    selected_doc = doc
                    break

        if not selected_doc:
            print_error(f"Document not found: {doc_input}")
            Prompt.ask("Press Enter to continue")
            return

        assert selected_doc.name is not None, "Document name should not be None"

        # Get full document details using .get()
        doc_details = client.file_search_stores.documents.get(name=selected_doc.name)

        # Display detailed information
        console.print("\n[bold cyan]═══ Document Details ═══[/bold cyan]\n")

        # Document name/ID
        console.print(f"[bold]Document Name:[/bold] {doc_details.name}")
        console.print(f"[bold]Display Name:[/bold]  {doc_details.display_name or '(not set)'}")

        # State with color
        state_str = str(getattr(doc_details, 'state', 'UNKNOWN'))
        if 'ACTIVE' in state_str:
            console.print(f"[bold]State:[/bold]         [green]{state_str}[/green]")
        elif 'PENDING' in state_str:
            console.print(f"[bold]State:[/bold]         [yellow]{state_str}[/yellow]")
        elif 'FAILED' in state_str:
            console.print(f"[bold]State:[/bold]         [red]{state_str}[/red]")
        else:
            console.print(f"[bold]State:[/bold]         {state_str}")

        # Size
        size_bytes = int(getattr(doc_details, 'size_bytes', 0) or 0)
        console.print(f"[bold]Size:[/bold]          {format_bytes(size_bytes)} ({size_bytes:,} bytes)")

        # MIME type
        mime_type = getattr(doc_details, 'mime_type', None)
        if mime_type:
            console.print(f"[bold]MIME Type:[/bold]     {mime_type}")

        # Timestamps
        create_time = getattr(doc_details, 'create_time', None)
        if create_time:
            if hasattr(create_time, 'strftime'):
                create_str = create_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                create_str = str(create_time)
            console.print(f"[bold]Created:[/bold]       {create_str}")

        update_time = getattr(doc_details, 'update_time', None)
        if update_time:
            if hasattr(update_time, 'strftime'):
                update_str = update_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                update_str = str(update_time)
            console.print(f"[bold]Updated:[/bold]       {update_str}")

        # Custom metadata
        custom_metadata = getattr(doc_details, 'custom_metadata', None)
        if custom_metadata:
            console.print(f"\n[bold]Custom Metadata:[/bold]")
            for meta in custom_metadata:
                key = getattr(meta, 'key', 'unknown')
                # Check for different value types
                if hasattr(meta, 'string_value') and meta.string_value:
                    value = meta.string_value
                elif hasattr(meta, 'numeric_value') and meta.numeric_value is not None:
                    value = str(meta.numeric_value)
                elif hasattr(meta, 'string_list_value') and meta.string_list_value:
                    value = ', '.join(meta.string_list_value.values)
                else:
                    value = str(meta)
                console.print(f"  • {key}: {value}")
        else:
            console.print(f"\n[dim]No custom metadata[/dim]")

        # Parent store info
        console.print(f"\n[bold]Parent Store:[/bold]  {selected_store.display_name or selected_store.name}")

        console.print()

        # Wait for user to continue
        Prompt.ask("Press Enter to continue")

    except Exception as e:
        error_msg = str(e)
        if "PERMISSION_DENIED" in error_msg:
            print_error("Permission denied. Check your API key.")
        elif "NOT_FOUND" in error_msg:
            print_error("Document not found. It may have been deleted.")
        else:
            print_error(f"Error viewing document: {error_msg}")
        Prompt.ask("Press Enter to continue")


if __name__ == "__main__":
    main()
