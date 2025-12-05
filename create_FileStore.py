"""
create_FileStore.py
Create a new Gemini File Search Store.
"""

import sys
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from utils import get_client, print_success, print_error, print_info

console = Console()


def create_file_store(display_name: str | None = None) -> dict:
    """
    Create a new File Search Store.

    Args:
        display_name: Optional human-readable name for the store.

    Returns:
        Dictionary with store details or error information.
    """
    client = get_client()

    try:
        print_info("Creating File Search Store...")

        # Create the store
        if display_name:
            store = client.file_search_stores.create(config={"display_name": display_name})
        else:
            store = client.file_search_stores.create()
        
        return {
            "success": True,
            "name": store.name,
            "display_name": getattr(store, "display_name", None),
            "create_time": getattr(store, "create_time", None),
        }
        
    except Exception as e:
        error_message = str(e)
        
        # Parse common errors
        if "PERMISSION_DENIED" in error_message:
            return {
                "success": False,
                "error": "Permission denied. Check your API key permissions.",
            }
        elif "QUOTA_EXCEEDED" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            return {
                "success": False,
                "error": "Quota exceeded. You may have reached the maximum number of stores (10).",
            }
        elif "INVALID_ARGUMENT" in error_message:
            return {
                "success": False,
                "error": f"Invalid argument: {error_message}",
            }
        else:
            return {
                "success": False,
                "error": f"Failed to create store: {error_message}",
            }


def main():
    """Main function for standalone execution."""
    console.print(
        Panel(
            "[bold cyan]Create New File Search Store[/bold cyan]",
            subtitle="Gemini File Search Manager",
        )
    )
    console.print()
    
    # Get display name from user
    display_name = Prompt.ask(
        "[bold]Enter a display name for the store[/bold] (or press Enter to skip)",
        default="",
    )
    
    if not display_name.strip():
        display_name = None
    
    console.print()
    
    # Create the store
    result = create_file_store(display_name)
    
    if result["success"]:
        console.print()
        print_success("File Search Store created successfully!")
        console.print()
        
        # Display store details
        console.print("[bold]Store Details:[/bold]")
        console.print(f"  • Name: [cyan]{result['name']}[/cyan]")
        
        if result.get("display_name"):
            console.print(f"  • Display Name: [cyan]{result['display_name']}[/cyan]")
        
        console.print()
        console.print(
            "[dim]Save the store name above - you'll need it to upload files.[/dim]"
        )
        console.print()
        
    else:
        console.print()
        print_error(result["error"])
        console.print()
        sys.exit(1)


if __name__ == "__main__":
    main()