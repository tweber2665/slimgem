"""
view_failurelog.py
View the upload failure log.
"""

from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich import box

from utils import (
    get_failure_log,
    clear_failure_log,
    print_info,
    print_success,
    show_header,
)

console = Console()


def main():
    """View the upload failure log."""
    show_header()
    console.print("[bold]Upload Failure Log[/bold]\n")

    log = get_failure_log()

    if not log:
        print_info("No upload failures recorded.")
        console.print()
        Prompt.ask("Press Enter to continue")
        return

    table = Table(
        show_header=True,
        header_style="bold cyan",
        expand=True,
        show_lines=True
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Timestamp", width=20)
    table.add_column("Filename", overflow="fold")
    table.add_column("Store", overflow="fold")
    table.add_column("Error", overflow="fold")

    for i, entry in enumerate(log, 1):
        # Format timestamp
        try:
            ts = datetime.fromisoformat(entry["timestamp"])
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, KeyError):
            ts_str = entry.get("timestamp", "Unknown")

        # Extract store display name from full path
        store = entry.get("store_name", "Unknown")
        if "/" in store:
            store = store.split("/")[-1]

        table.add_row(
            str(i),
            ts_str,
            entry.get("filename", "Unknown"),
            store,
            entry.get("error", "Unknown error")
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(log)} failure(s)[/dim]\n")

    # Offer to clear the log
    if Confirm.ask("Clear the failure log?", default=False):
        clear_failure_log()
        print_success("Failure log cleared.")
        console.print()

    Prompt.ask("Press Enter to continue")


if __name__ == "__main__":
    main()
