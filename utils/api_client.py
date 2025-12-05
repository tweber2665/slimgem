"""
utils/api_client.py
Handles initialization of the Google GenAI client with proper error handling.
"""

from google import genai
from rich.console import Console

from config import GEMINI_API_KEY

console = Console()

# Global client instance (singleton pattern)
_client = None


def get_client():
    """
    Get or create the GenAI client instance.
    
    Returns:
        genai.Client: The initialized client.
        
    Raises:
        SystemExit: If API key is not configured.
    """
    global _client
    
    if _client is not None:
        return _client
    
    # Check if API key is configured
    if not GEMINI_API_KEY:
        console.print(
            "\n[bold red]ERROR:[/bold red] GEMINI_API_KEY not found!\n",
            style="red"
        )
        console.print(
            "Please follow these steps to fix this:\n"
            "1. Open the [cyan].env[/cyan] file in your project folder\n"
            "2. Add your API key: [cyan]GEMINI_API_KEY=your-key-here[/cyan]\n"
            "3. Save the file and restart this application\n\n"
            "To get an API key, visit: [link]https://aistudio.google.com/apikey[/link]\n"
        )
        raise SystemExit(1)
    
    try:
        _client = genai.Client(api_key=GEMINI_API_KEY)
        return _client
    except Exception as e:
        console.print(
            f"\n[bold red]ERROR:[/bold red] Failed to initialize API client.\n",
            style="red"
        )
        console.print(f"Details: {str(e)}\n")
        raise SystemExit(1)