"""
utils package
Shared utilities for Gemini File Search Manager.
"""

from .api_client import get_client
from .helpers import (
    validate_file,
    format_bytes,
    format_timestamp,
    wait_for_operation,
    get_files_from_path,
    print_success,
    print_error,
    print_warning,
    print_info,
    clean_path_input,
    log_upload_failure,
    get_failure_log,
    clear_failure_log,
    upload_with_retry,
    is_upload_in_progress,
    calculate_file_hash,
    detect_duplicate_files,
    get_deduplicated_files,
    UploadStatus,
    init_upload_status,
    update_upload_status,
    get_upload_status_table,
    get_upload_summary_stats,
    clear_upload_statuses,
    extract_file_metadata,
    show_header,
    select_item_from_list,
)