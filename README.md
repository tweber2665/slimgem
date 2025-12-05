# Slimgem

**A Terminal Manager for Gemini File Search Stores**

Slimgem is a powerful, user-friendly command-line interface for managing Google Gemini File Search Stores. Upload documents, manage metadata, and organize your knowledge base—all from your terminal.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

### 📁 File Search Store Management
- **Create** new File Search Stores with custom display names
- **List** all stores with document counts and metadata
- **View** detailed store information (size, documents, creation date)
- **Delete** stores with force option for non-empty stores

### 📄 Document Operations
- **Upload** single files or entire folders (with recursive option)
- **Parallel uploads** with live progress tracking
- **Duplicate detection** - Automatically detect and handle duplicate files by content hash
- **Custom chunking** - Configure token limits and overlap for optimal search performance
- **List documents** in any store with detailed metadata
- **View document details** - Full metadata, size, state, and parent store info
- **Delete documents** with confirmation prompts

### 🏷️ Automatic Metadata Extraction
- **PDF metadata**: Title, author, subject, keywords, creator, page count, creation/modification dates
- **DOCX metadata**: Document properties, paragraph count, author information
- **PPTX metadata**: Presentation properties, slide count, author details
- **Universal properties**: File extension, size, upload timestamp, modification time
- **Smart filename parsing**: Automatically extract years, quarters, dates, versions, document types

### 🔄 Robust Upload System
- **Retry logic** with exponential backoff for failed uploads
- **Session management** - Fresh upload sessions prevent termination errors
- **Real-time progress display** - Track multiple uploads simultaneously
- **Failure logging** - View and clear upload failure history
- **Error handling** - Graceful recovery from API errors

### 🎨 Beautiful Terminal UI
- **Rich terminal interface** with colors, tables, and progress bars
- **Interactive menus** - Number, name, or ID-based selection
- **Live status updates** - Real-time upload progress for multiple files
- **Formatted displays** - Human-readable file sizes, timestamps, and metadata

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/tweber2665/slimgem.git
   cd slimgem
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

### First Run

```bash
python main.py
```

You'll see the main menu with all available options:

```
╔═════════════════════════════════════════════════════════╗
║           Gemini File Search Manager                    ║
║     Manage your Google Gemini File Search Stores        ║
╚═════════════════════════════════════════════════════════╝

Main Menu

  1  Create new File Search Store
  2  Upload files to existing File Search Store
  3  List existing File Search Stores
  4  View existing File Search Store Details
  5  Delete existing File Search Store
  6  List Documents in File Search Store
  7  View Document Details
  8  Delete Document
  9  View Upload Failure Log
  0  Exit
```

---

## 📖 Usage Guide

### Creating a File Search Store

```bash
# From main menu, select option 1
1

# Enter a display name (or press Enter to skip)
Enter a display name for the store: My Research Documents
```

### Uploading Files

```bash
# From main menu, select option 2
2

# Enter store name (supports tab completion)
Enter the store name: fileSearchStores/abc123

# Add files or folders one at a time
Drag & drop file or folder: /path/to/document.pdf
✓ Added: document.pdf

Add another file or folder? [y/n]: y
Drag & drop file or folder: /path/to/folder/
✓ Added: folder

# Configure chunking (optional)
Would you like to customize chunking settings? [y/n]: n

# Confirm and upload
Upload 15 file(s) to fileSearchStores/abc123? [Y/n]: Y

Overall Progress: 15/15 (100%) ████████████████████████████████████████
┌─────────────────────┬──────────┬─────────────────────────────────┐
│ File                │ Status   │ Progress                        │
├─────────────────────┼──────────┼─────────────────────────────────┤
│ document1.pdf       │ ✓ Done   │ ▓▓▓▓▓▓▓▓▓▓ 100%                 │
│ document2.docx      │ ✓ Done   │ ▓▓▓▓▓▓▓▓▓▓ 100%                 │
│ presentation.pptx   │ ✓ Done   │ ▓▓▓▓▓▓▓▓▓▓ 100%                 │
└─────────────────────┴──────────┴─────────────────────────────────┘
```

### Viewing Document Metadata

```bash
# From main menu, select option 7
7

# Select store by number or name
Select store: 1

# Select document
Select document: 1

# View extracted metadata
Document Details:

  • Name: fileSearchStores/abc123/documents/xyz789
  • Display Name: Report_2024_Q1.pdf
  • State: ACTIVE
  • Size: 2.45 MB
  • MIME Type: application/pdf
  • Created: 2024-01-15 10:30:00
  • Updated: 2024-01-15 10:30:00

Custom Metadata:
  • pdf_title: Quarterly Financial Report
  • pdf_author: John Doe
  • pdf_page_count: 42
  • filename_year: 2024
  • filename_quarter: Q1
  • filename_document_type: report
  • file_size_mb: 2.45
  • upload_timestamp: 2024-01-15T10:30:00
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required: Your Google Gemini API key
GEMINI_API_KEY=your_api_key_here
```

### Upload Configuration

Edit `config.py` to customize:

```python
# File size limits
MAX_FILE_SIZE_MB = 100

# Chunking defaults
DEFAULT_MAX_TOKENS_PER_CHUNK = 512
DEFAULT_MAX_OVERLAP_TOKENS = 128

# Retry configuration
MAX_UPLOAD_RETRIES = 3
UPLOAD_RETRY_INITIAL_DELAY = 1.0
UPLOAD_RETRY_MAX_DELAY = 32.0
```

### Supported File Types

Slimgem supports all file types compatible with Google Gemini File Search:

- **Documents**: PDF, DOCX, DOC, TXT, RTF, MD, HTML, ODT
- **Spreadsheets**: CSV, XLSX, XLS, TSV
- **Presentations**: PPTX, ODP
- **Code**: PY, JS, TS, JAVA, C, CPP, GO, RS, and more
- **Data**: JSON, XML, YAML, TOML
- **Other**: TEX, IPYNB, VTT, SRT

---

## 🏗️ Project Structure

```
Slimgem/
├── main.py                      # Main menu and application entry
├── config.py                    # Configuration settings
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── upload_failures.json         # Upload failure log
│
├── utils/                       # Shared utilities
│   ├── __init__.py             # Package exports
│   ├── api_client.py           # Google Gemini API client
│   └── helpers.py              # Helper functions (validation, formatting, metadata)
│
├── create_FileStore.py         # Create new stores
├── upload_to_FileStore.py      # Upload files with parallel processing
├── list_FileStores.py          # List all stores
├── view_FileStore_details.py   # View store details
├── delete_FileStore.py         # Delete stores
├── list_Documents.py           # List documents in store
├── view_Document_details.py    # View document metadata
├── delete_Document.py          # Delete documents
└── view_failurelog.py          # View upload failures
```

---

## 🔮 Future Improvements

### Planned Features

#### v2.0 - Batch Operations
- [ ] **Batch delete file stores** - Delete multiple stores at once
- [ ] **Batch delete documents** - Remove multiple documents simultaneously
- [ ] **Batch uploads to multiple stores** - Upload files to several stores in parallel

#### v2.1 - Search & Discovery
- [ ] **Search documents by metadata** - Filter by author, date, keywords, etc.
- [ ] **Advanced filtering** - Combine multiple metadata criteria
- [ ] **Full-text search integration** - Search document contents (when available)

#### v2.2 - Metadata Management
- [ ] **Bulk metadata editing** - Update metadata across multiple documents
- [ ] **Custom metadata templates** - Predefined schemas for different document types
- [ ] **Metadata import/export** - CSV or JSON format for bulk operations

#### v2.3 - Analytics & Insights
- [ ] **Store statistics dashboard** - Visual analytics on usage, size, document types
- [ ] **Document analytics** - Most accessed, largest files, upload trends
- [ ] **Storage usage reports** - Track quota and storage tiers

#### v2.4 - Advanced Features
- [ ] **Document preview** - View PDF/text content before/after upload
- [ ] **Store backup/restore** - Export entire stores for backup
- [ ] **Configuration import/export** - Share store configurations
- [ ] **Scheduled uploads** - Cron-like automated uploads
- [ ] **Document versioning** - Track document history and changes

#### v2.5 - Developer Experience
- [ ] **CLI arguments mode** - Non-interactive command-line usage
- [ ] **JSON output mode** - Machine-readable output for scripting
- [ ] **Plugin system** - Custom metadata extractors and processors
- [ ] **Advanced retry strategies** - Configurable per file type or error
- [ ] **Web UI** - Optional browser-based interface

---

## 🛠️ Development

### Running from Source

```bash
# Activate virtual environment
source .venv/bin/activate

# Run main application
python main.py

# Or run individual modules
python create_FileStore.py
python upload_to_FileStore.py
```

### Code Quality

The codebase follows strict Python conventions:
- **Snake case** for variables and functions
- **Pascal case** for classes
- **Type hints** throughout
- **Modular architecture** with single-responsibility modules
- **DRY principles** with shared utility functions

### Testing

```bash
# Run tests (coming soon)
pytest tests/ -v --cov=src
```

---

## 📝 API Limits & Quotas

Slimgem respects Google Gemini API limits:

| Tier | Storage Limit | Max Stores |
|------|---------------|------------|
| Free | 1 GB | 10 |
| Tier 1 (Billing Enabled) | 10 GB | 10 |
| Tier 2 ($250+ spend) | 100 GB | 10 |
| Tier 3 ($1,000+ spend) | 1 TB | 10 |

- **Max file size**: 100 MB per file
- **Max chunk size**: 512 tokens
- **Max metadata entries**: 20 per document

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal UI
- Uses [Google Gemini API](https://ai.google.dev/gemini-api/docs) for file search capabilities
- PDF metadata extraction via [PyMuPDF](https://pymupdf.readthedocs.io/)
- Office document support from [python-docx](https://python-docx.readthedocs.io/) and [python-pptx](https://python-pptx.readthedocs.io/)

---

## 📧 Support

For issues, questions, or suggestions:
- **Issues**: [GitHub Issues](https://github.com/tweber2665/slimgem/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tweber2665/slimgem/discussions)

---

**Made with ❤️ for developers who love their terminals**
