from fastapi import APIRouter, Request
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from src.utils import success_response, error_response


router = APIRouter(prefix="/scripts", tags=["scripts"])

# Script storage directory
SCRIPT_DIR = Path("data/code")
SCRIPT_DIR.mkdir(parents=True, exist_ok=True)


class ScriptType(str, Enum):
    PYTHON = "python"
    NODE = "node"
    SHELL = "shell"


class ScriptSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: ScriptType
    content: str


class ScriptResponse(BaseModel):
    name: str
    type: ScriptType
    content: str
    path: str


class ScriptListItem(BaseModel):
    name: str
    type: ScriptType
    path: str


class ScriptTreeNode(BaseModel):
    name: str
    type: str  # "file" or "directory"
    path: str
    script_type: Optional[ScriptType] = None
    children: Optional[List["ScriptTreeNode"]] = None


def _get_extension(script_type: ScriptType) -> str:
    """Get file extension based on script type"""
    extensions = {
        ScriptType.PYTHON: ".py",
        ScriptType.NODE: ".js",
        ScriptType.SHELL: ".sh",
    }
    return extensions[script_type]


def _get_script_type(filename: str) -> ScriptType:
    """Determine script type from filename"""
    if filename.endswith(".py"):
        return ScriptType.PYTHON
    elif filename.endswith(".js"):
        return ScriptType.NODE
    elif filename.endswith(".sh"):
        return ScriptType.SHELL
    else:
        raise ValueError(f"Unknown script type for file: {filename}")


def _sanitize_filename(name: str, script_type: ScriptType) -> str:
    """Sanitize filename and ensure correct extension, supports folder paths"""
    # Normalize path separators to forward slash
    name = name.replace("\\", "/")

    # Split into directory and filename
    parts = name.split("/")
    filename = parts[-1]
    directory = "/".join(parts[:-1]) if len(parts) > 1 else ""

    # Remove extension if present
    for ext in [".py", ".js", ".sh"]:
        if filename.endswith(ext):
            filename = filename[: -len(ext)]
            break

    # Add correct extension
    filename = filename + _get_extension(script_type)

    # Reconstruct full path
    if directory:
        return f"{directory}/{filename}"
    return filename


def _build_tree(directory: Path, base_path: Path) -> List[ScriptTreeNode]:
    """Build tree structure for scripts directory"""
    nodes = []

    try:
        items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    except PermissionError:
        return nodes

    for item in items:
        relative_path = str(item.relative_to(base_path))

        if item.is_dir():
            # Recursively build tree for subdirectories
            children = _build_tree(item, base_path)
            nodes.append(
                ScriptTreeNode(
                    name=item.name,
                    type="directory",
                    path=relative_path,
                    children=children if children else [],
                )
            )
        elif item.is_file() and item.suffix in [".py", ".js", ".sh"]:
            try:
                script_type = _get_script_type(item.name)
                nodes.append(
                    ScriptTreeNode(
                        name=item.name,
                        type="file",
                        path=relative_path,
                        script_type=script_type,
                        children=None,
                    )
                )
            except ValueError:
                continue

    return nodes


@router.get("")
async def list_scripts(request: Request) -> dict:
    """List all scripts in tree structure"""
    tree = _build_tree(SCRIPT_DIR, SCRIPT_DIR)
    return success_response(data=tree)


@router.get("/{script_path:path}")
async def get_script(script_path: str, request: Request):
    """Get a specific script by path, supports folder paths like 'folder/script.py'"""
    full_path = SCRIPT_DIR / script_path

    if not full_path.exists():
        return error_response(message=f"Script '{script_path}' not found", code=404)

    if not full_path.is_file():
        return error_response(message=f"'{script_path}' is not a file", code=400)

    # Verify the path is within SCRIPT_DIR for security
    try:
        full_path.resolve().relative_to(SCRIPT_DIR.resolve())
    except ValueError:
        return error_response(
            message="Access denied: path outside script directory", code=403
        )

    try:
        script_type = _get_script_type(full_path.name)
        content = full_path.read_text(encoding="utf-8")

        script_response = ScriptResponse(
            name=script_path,
            type=script_type,
            content=content,
            path=str(full_path.resolve().relative_to(Path.cwd().resolve())),
        )

        return success_response(data=script_response)
    except ValueError as e:
        return error_response(message=str(e), code=400)


@router.post("")
async def create_script(script_data: ScriptSchema, request: Request):
    """Create a new script, supports folder paths like 'folder/script.py'"""
    filename = _sanitize_filename(script_data.name, script_data.type)
    script_path = SCRIPT_DIR / filename

    if script_path.exists():
        return error_response(message=f"Script '{filename}' already exists", code=409)

    # Create parent directories if they don't exist
    script_path.parent.mkdir(parents=True, exist_ok=True)

    script_path.write_text(script_data.content, encoding="utf-8")

    script_response = ScriptResponse(
        name=filename,
        type=script_data.type,
        content=script_data.content,
        path=str(script_path.resolve().relative_to(Path.cwd().resolve())),
    )

    return success_response(data=script_response, message="Script created successfully")


@router.put("/{script_path:path}")
async def update_script(script_path: str, script_data: ScriptSchema, request: Request):
    """Update an existing script, supports folder paths like 'folder/script.py'"""
    old_path = SCRIPT_DIR / script_path

    if not old_path.exists():
        return error_response(message=f"Script '{script_path}' not found", code=404)

    # Verify the old path is within SCRIPT_DIR for security
    try:
        old_path.resolve().relative_to(SCRIPT_DIR.resolve())
    except ValueError:
        return error_response(
            message="Access denied: path outside script directory", code=403
        )

    # Check if renaming/moving
    new_filename = _sanitize_filename(script_data.name, script_data.type)
    new_path = SCRIPT_DIR / new_filename

    if new_filename != script_path:
        # Verify the new path is within SCRIPT_DIR for security
        try:
            new_path.resolve().relative_to(SCRIPT_DIR.resolve())
        except ValueError:
            return error_response(
                message="Access denied: path outside script directory", code=403
            )

        if new_path.exists():
            return error_response(
                message=f"Script '{new_filename}' already exists", code=409
            )

        # Create parent directories if needed
        new_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.rename(new_path)
        old_path = new_path

    old_path.write_text(script_data.content, encoding="utf-8")

    script_response = ScriptResponse(
        name=new_filename,
        type=script_data.type,
        content=script_data.content,
        path=str(old_path.resolve().relative_to(Path.cwd().resolve())),
    )

    return success_response(data=script_response, message="Script updated successfully")


@router.delete("/{script_path:path}")
async def delete_script(script_path: str, request: Request):
    """Delete a script, supports folder paths like 'folder/script.py'"""
    full_path = SCRIPT_DIR / script_path

    if not full_path.exists():
        return error_response(message=f"Script '{script_path}' not found", code=404)

    # Verify the path is within SCRIPT_DIR for security
    try:
        full_path.resolve().relative_to(SCRIPT_DIR.resolve())
    except ValueError:
        return error_response(
            message="Access denied: path outside script directory", code=403
        )

    if not full_path.is_file():
        return error_response(message=f"'{script_path}' is not a file", code=400)

    # Delete the file
    full_path.unlink()

    # Remove empty parent directories
    parent = full_path.parent
    while parent != SCRIPT_DIR and parent.exists():
        try:
            # Only remove if directory is empty
            if not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
            else:
                break
        except (OSError, PermissionError):
            break

    return success_response(message="Script deleted successfully")
