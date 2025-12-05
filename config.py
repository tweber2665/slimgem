"""
config.py
Configuration settings for Gemini File Search Manager.
Loads environment variables and defines constants.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# File Upload Limits
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # 100 MB in bytes

# Default Chunking Configuration
DEFAULT_MAX_TOKENS_PER_CHUNK = 512
DEFAULT_MAX_OVERLAP_TOKENS = 128
MAX_TOKENS_PER_CHUNK_LIMIT = 512

# Supported File Extensions (based on Google's documentation)
SUPPORTED_EXTENSIONS = {
    # Documents
    ".pdf", ".docx", ".doc", ".txt", ".rtf", ".md", ".html", ".htm",
    ".odt", ".odp", ".ods",
    # Spreadsheets
    ".csv", ".xlsx", ".xls", ".tsv",
    # Presentations
    ".pptx",
    # Code files
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h",
    ".hpp", ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".r", ".m", ".mm", ".sql", ".sh", ".bash", ".zsh", ".ps1", ".bat",
    ".cmd", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    # Data files
    ".json", ".xml",
    # Other
    ".tex", ".latex", ".ipynb", ".vtt", ".srt",
}

# Storage Tier Limits (for reference/display)
STORAGE_TIERS = {
    "Free": "1 GB",
    "Tier 1 (Billing Enabled)": "10 GB",
    "Tier 2 ($250+ spend)": "100 GB",
    "Tier 3 ($1,000+ spend)": "1 TB",
}

# Maximum stores per project
MAX_STORES_PER_PROJECT = 10

# Recommended maximum store size for optimal performance
RECOMMENDED_MAX_STORE_SIZE_GB = 20

# Failure log file path
FAILURE_LOG_FILE = "upload_failures.json"

# Upload Retry Configuration
# Maximum number of retry attempts for failed uploads
MAX_UPLOAD_RETRIES = 3

# Initial delay in seconds for exponential backoff
UPLOAD_RETRY_INITIAL_DELAY = 1.0

# Maximum delay in seconds between retry attempts
UPLOAD_RETRY_MAX_DELAY = 32.0

# List of error patterns that trigger a retry
RETRYABLE_ERROR_PATTERNS = [
    "already been terminated",
    "503",
    "service unavailable",
    "timeout",
    "deadline exceeded",
    "internal error",
    "temporarily unavailable",
]