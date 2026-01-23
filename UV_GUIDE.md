# UV Package Manager Guide

This project supports [uv](https://github.com/astral-sh/uv), a fast Python package installer and resolver.

## Installation

### Install uv

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pip
pip install uv
```

## Usage

### Create Virtual Environment

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
# On Windows
.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate
```

### Install Dependencies

```bash
# Install all dependencies from pyproject.toml
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"

# Or sync from pyproject.toml (recommended)
uv sync

# Sync with dev dependencies
uv sync --extra dev
```

### Add New Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Add with version constraint
uv add "package-name>=1.0.0"
```

### Remove Dependencies

```bash
# Remove a dependency
uv remove package-name
```

### Run Commands

```bash
# Run the application
uv run python main.py

# Run with uvicorn
uv run uvicorn main:app --reload

# Run tests
uv run pytest

# Run ruff linter
uv run ruff check .

# Format code with ruff
uv run ruff format .
```

### Update Dependencies

```bash
# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package package-name
```

### Export Requirements

```bash
# Export to requirements.txt
uv pip compile pyproject.toml -o requirements.txt

# Export with dev dependencies
uv pip compile pyproject.toml --extra dev -o requirements-dev.txt
```

## Benefits of Using uv

- **Fast**: 10-100x faster than pip
- **Reliable**: Consistent dependency resolution
- **Compatible**: Works with existing pip and requirements.txt
- **Modern**: Built in Rust for performance

## Migration from pip

If you're currently using `requirements.txt`, you can continue using it alongside `pyproject.toml`:

```bash
# Install from requirements.txt
uv pip install -r requirements.txt

# Or migrate to pyproject.toml
uv pip install -e .
```

## Common Commands Comparison

| Task | pip | uv |
|------|-----|-----|
| Install dependencies | `pip install -r requirements.txt` | `uv sync` |
| Add package | `pip install package` | `uv add package` |
| Remove package | `pip uninstall package` | `uv remove package` |
| Create venv | `python -m venv .venv` | `uv venv` |
| Run script | `python script.py` | `uv run python script.py` |

## Troubleshooting

### uv not found after installation

Make sure uv is in your PATH. Restart your terminal or run:

```bash
# On Windows
$env:PATH += ";$HOME\.cargo\bin"

# On macOS/Linux
export PATH="$HOME/.cargo/bin:$PATH"
```

### Lock file conflicts

If you encounter lock file issues:

```bash
# Remove lock file and regenerate
rm uv.lock
uv lock
```

## Learn More

- [uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub Repository](https://github.com/astral-sh/uv)
