from fastapi import APIRouter, HTTPException, status, Request
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field
from enum import Enum


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
    """Sanitize filename and ensure correct extension"""
    # Remove any path separators
    name = name.replace("/", "_").replace("\\", "_")

    # Remove extension if present
    for ext in [".py", ".js", ".sh"]:
        if name.endswith(ext):
            name = name[: -len(ext)]
            break

    # Add correct extension
    return name + _get_extension(script_type)


@router.get("/", response_model=List[ScriptListItem])
async def list_scripts(request: Request) -> List[ScriptListItem]:
    """List all scripts in the data/code directory"""
    scripts = []

    for file_path in SCRIPT_DIR.iterdir():
        if file_path.is_file() and file_path.suffix in [".py", ".js", ".sh"]:
            try:
                script_type = _get_script_type(file_path.name)
                scripts.append(
                    ScriptListItem(
                        name=file_path.name,
                        type=script_type,
                        path=str(file_path.relative_to(Path.cwd())),
                    )
                )
            except ValueError:
                continue

    return sorted(scripts, key=lambda x: x.name)


@router.get("/{script_name}", response_model=ScriptResponse)
async def get_script(script_name: str, request: Request) -> ScriptResponse:
    """Get a specific script by name"""
    script_path = SCRIPT_DIR / script_name

    if not script_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script '{script_name}' not found",
        )

    if not script_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{script_name}' is not a file",
        )

    try:
        script_type = _get_script_type(script_name)
        content = script_path.read_text(encoding="utf-8")

        return ScriptResponse(
            name=script_name,
            type=script_type,
            content=content,
            path=str(script_path.relative_to(Path.cwd())),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def create_script(script_data: ScriptSchema, request: Request) -> ScriptResponse:
    """Create a new script"""
    filename = _sanitize_filename(script_data.name, script_data.type)
    script_path = SCRIPT_DIR / filename

    if script_path.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Script '{filename}' already exists",
        )

    script_path.write_text(script_data.content, encoding="utf-8")

    return ScriptResponse(
        name=filename,
        type=script_data.type,
        content=script_data.content,
        path=str(script_path.relative_to(Path.cwd())),
    )


@router.put("/{script_name}", response_model=ScriptResponse)
async def update_script(
    script_name: str, script_data: ScriptSchema, request: Request
) -> ScriptResponse:
    """Update an existing script"""
    script_path = SCRIPT_DIR / script_name

    if not script_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script '{script_name}' not found",
        )

    # Check if renaming
    new_filename = _sanitize_filename(script_data.name, script_data.type)
    if new_filename != script_name:
        new_path = SCRIPT_DIR / new_filename
        if new_path.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Script '{new_filename}' already exists",
            )
        script_path.rename(new_path)
        script_path = new_path

    script_path.write_text(script_data.content, encoding="utf-8")

    return ScriptResponse(
        name=script_path.name,
        type=script_data.type,
        content=script_data.content,
        path=str(script_path.relative_to(Path.cwd())),
    )


@router.delete("/{script_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(script_name: str, request: Request) -> None:
    """Delete a script"""
    script_path = SCRIPT_DIR / script_name

    if not script_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script '{script_name}' not found",
        )

    script_path.unlink()
    return None
