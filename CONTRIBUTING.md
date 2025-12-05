# Contributing to Slimgem

Thank you for your interest in contributing to Slimgem! We welcome contributions from the community and are excited to see what you'll bring to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors. Please:

- Be respectful and considerate in your communication
- Welcome newcomers and help them get started
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- A Google Gemini API key
- Basic understanding of terminal/command-line interfaces

### Development Setup

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then clone your fork
   git clone https://github.com/tweber2665/slimgem.git
   cd slimgem
   ```

2. **Set up the development environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Set up environment variables
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## How to Contribute

### Types of Contributions

We welcome several types of contributions:

1. **Bug fixes** - Fix issues in existing code
2. **New features** - Implement planned features from the roadmap
3. **Documentation** - Improve README, docstrings, or guides
4. **Performance improvements** - Optimize existing code
5. **Tests** - Add or improve test coverage
6. **UI/UX enhancements** - Improve terminal interface and user experience

### Before You Start

1. **Check existing issues** - See if someone is already working on it
2. **Create an issue** - Discuss your idea before investing significant time
3. **Wait for feedback** - Get maintainer approval for major changes
4. **Keep it focused** - One feature or fix per pull request

---

## Coding Standards

### Python Style Guide

We follow **PEP 8** with these project-specific conventions:

#### Naming Conventions (STRICT)

```python
# Variables and functions: snake_case
user_id = 123
document_count = 0

def get_user_details():
    pass

# Classes: PascalCase
class DocumentProcessor:
    pass

# Constants: SCREAMING_SNAKE_CASE
MAX_FILE_SIZE = 100
DEFAULT_TIMEOUT = 30

# Private members: Single underscore prefix
_internal_cache = {}

def _helper_function():
    pass
```

#### Type Hints

Always include type hints for function parameters and return values:

```python
def upload_file(
    file_path: str,
    store_name: str,
    metadata: Optional[dict] = None
) -> Tuple[bool, str]:
    """
    Upload a file to a store.

    Args:
        file_path: Path to the file.
        store_name: Name of the target store.
        metadata: Optional metadata dictionary.

    Returns:
        Tuple of (success, message).
    """
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def process_documents(docs: List[str], max_size: int = 100) -> dict:
    """
    Process a list of documents.

    This function validates and processes documents, extracting
    metadata and preparing them for upload.

    Args:
        docs: List of document paths.
        max_size: Maximum file size in MB (default: 100).

    Returns:
        Dictionary with processing results:
            - valid: List of valid document paths
            - invalid: List of (path, error) tuples

    Raises:
        ValueError: If docs list is empty.

    Example:
        >>> result = process_documents(['file1.pdf', 'file2.txt'])
        >>> print(result['valid'])
        ['file1.pdf', 'file2.txt']
    """
    pass
```

#### Code Organization

- **One class per file** (unless tightly related)
- **Functions before classes** in modules
- **Imports at the top**, grouped:
  1. Standard library
  2. Third-party packages
  3. Local imports

```python
# Standard library
import os
import sys
from pathlib import Path
from typing import List, Optional

# Third-party
from rich.console import Console
from rich.table import Table

# Local
from utils import get_client, print_error
from config import MAX_FILE_SIZE
```

#### Error Handling

- Use specific exceptions, not bare `except:`
- Always provide helpful error messages
- Log errors appropriately

```python
try:
    result = upload_file(path)
except FileNotFoundError:
    print_error(f"File not found: {path}")
except PermissionError:
    print_error(f"Permission denied: {path}")
except Exception as e:
    print_error(f"Unexpected error: {e}")
```

### Project Structure

When adding new features:

- **Utility functions** → `utils/helpers.py`
- **New menu options** → Create dedicated script (e.g., `batch_delete.py`)
- **Configuration** → Add to `config.py`
- **Shared logic** → Extract to `utils/` and export in `utils/__init__.py`

---

## Pull Request Process

### 1. Prepare Your Changes

```bash
# Make sure you're on your feature branch
git checkout feature/your-feature-name

# Make your changes
# ... edit files ...

# Test your changes
python main.py
# Manually test the affected features

# Commit your changes
git add .
git commit -m "Add feature: brief description"
```

### 2. Commit Message Format

Use clear, descriptive commit messages:

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Build/tooling changes

**Examples:**

```bash
feat: add batch delete for file stores

Implements batch deletion workflow allowing users to select
and delete multiple stores at once with confirmation.

Closes #42
```

```bash
fix: handle empty metadata gracefully in document view

Previously crashed when documents had no custom metadata.
Now displays "No custom metadata" message.

Fixes #38
```

### 3. Push and Create PR

```bash
# Push your branch
git push origin feature/your-feature-name

# Go to GitHub and create a Pull Request
# Fill out the PR template
```

### 4. PR Checklist

Before submitting, ensure:

- [ ] Code follows style guidelines
- [ ] All functions have type hints and docstrings
- [ ] No unnecessary imports or commented-out code
- [ ] Tested manually on your local setup
- [ ] No new errors or warnings
- [ ] Updated README if adding new features
- [ ] Added entry to Future Improvements if incomplete

### 5. Code Review Process

1. **Automated checks** - Wait for any CI checks to pass
2. **Maintainer review** - Address feedback from maintainers
3. **Make changes** - Push additional commits if requested
4. **Approval** - Get approval from at least one maintainer
5. **Merge** - Maintainer will merge your PR

---

## Reporting Bugs

Found a bug? Please create a detailed bug report.

### Before Reporting

1. **Check existing issues** - Your bug might already be reported
2. **Update to latest** - Ensure you're on the latest version
3. **Reproduce** - Confirm the bug is reproducible

### Bug Report Template

Use the bug report template on GitHub Issues. Include:

- **Environment**: OS, Python version, terminal
- **Steps to reproduce**: Exact steps to trigger the bug
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Error messages**: Full error output
- **Screenshots**: If applicable

---

## Suggesting Features

We love feature suggestions! Here's how to propose one:

### Before Suggesting

1. **Check the roadmap** - Feature might already be planned
2. **Search existing issues** - Someone might have suggested it
3. **Consider scope** - Is it aligned with project goals?

### Feature Request Template

Use the feature request template on GitHub Issues. Include:

- **Problem**: What problem does this solve?
- **Solution**: Your proposed solution
- **Alternatives**: Other solutions you considered
- **Use cases**: Real-world examples
- **Mockups**: Screenshots or diagrams if applicable

---

## Development Tips

### Debugging

```python
# Use Rich's print for debugging (auto-removes in production)
from rich import print as rprint
rprint(f"Debug: {variable}")

# Use console.log for persistent debug messages
console.log("Processing file", file_path)
```

### Testing Your Changes

```bash
# Test with different file types
python main.py
# Try: PDFs, DOCX, PPTX, TXT

# Test error handling
# Try: Invalid paths, missing API key, network errors

# Test edge cases
# Try: Empty folders, duplicate files, large files
```

### Common Pitfalls

1. **Don't commit `.env`** - Contains your API key
2. **Don't commit `upload_failures.json`** - User-specific data
3. **Use virtual environment** - Prevents dependency conflicts
4. **Test on clean install** - Ensure all dependencies are in requirements.txt
5. **Follow naming conventions** - Snake case for functions, Pascal case for classes

---

## Getting Help

Stuck? Here are some resources:

- **GitHub Issues**: Ask questions or report problems
- **Discussions**: Join community discussions on GitHub
- **Code Comments**: Read existing code for examples
- **README**: Review the main documentation

---

## Recognition

Contributors will be recognized in:

- **README.md** - Contributors section
- **Release notes** - For significant contributions
- **Git history** - Your commits are permanent record

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Slimgem! 🎉**

Your efforts help make this project better for everyone.
