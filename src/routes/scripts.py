from fastapi import APIRouter, Request
from src.utils import success_response, error_response
from src.services.scripts import script_service
from src.models.schemas import (
    ScriptSchema,
    ScriptResponse,
    ScriptTreeNode,
    ScriptExecutionRequest,
    ScriptExecutionResponse,
    GitCloneRequest,
    GitCloneResponse,
)


router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.get("")
async def list_scripts(request: Request) -> dict:
    """List all scripts in tree structure"""
    tree = script_service.list_scripts()
    return success_response(data=tree)


@router.get("/{script_path:path}")
async def get_script(script_path: str, request: Request):
    """Get a specific script by path, supports folder paths like 'folder/script.py'"""
    success, error_msg, script_data = script_service.get_script(script_path)

    if not success:
        code = 404 if "not found" in error_msg else 400
        return error_response(message=error_msg, code=code)

    return success_response(data=script_data)


@router.post("")
async def create_script(script_data: ScriptSchema, request: Request):
    """Create a new script, supports folder paths like 'folder/script.py'"""
    success, error_msg, script_response = script_service.create_script(
        script_data.name, script_data.content
    )

    if not success:
        code = 409 if "already exists" in error_msg else 400
        return error_response(message=error_msg, code=code)

    return success_response(data=script_response, message="Script created successfully")


@router.put("/{script_path:path}")
async def update_script(script_path: str, script_data: ScriptSchema, request: Request):
    """Update an existing script, supports folder paths like 'folder/script.py'"""
    success, error_msg, script_response = script_service.update_script(
        script_path, script_data.name, script_data.content
    )

    if not success:
        if "not found" in error_msg:
            code = 404
        elif "already exists" in error_msg:
            code = 409
        elif "Access denied" in error_msg:
            code = 403
        else:
            code = 400
        return error_response(message=error_msg, code=code)

    return success_response(data=script_response, message="Script updated successfully")


@router.delete("/{script_path:path}")
async def delete_script(script_path: str, request: Request):
    """Delete a script, supports folder paths like 'folder/script.py'"""
    success, error_msg = script_service.delete_script(script_path)

    if not success:
        if "not found" in error_msg:
            code = 404
        elif "Access denied" in error_msg:
            code = 403
        else:
            code = 400
        return error_response(message=error_msg, code=code)

    return success_response(message="Script deleted successfully")


@router.post("/{script_path:path}/run")
async def run_script(
    script_path: str, execution_request: ScriptExecutionRequest, request: Request
):
    """Run a script with optional arguments"""
    result = await script_service.run_script(
        script_path, execution_request.args, execution_request.timeout
    )

    if not result.get("success"):
        code = 408 if result["status"] == "timeout" else 500
        return error_response(
            message=result.get("error", "Script execution failed"),
            code=code,
            data=result,
        )

    exit_code = result.get("exit_code", 0)
    return success_response(
        data=result, message=f"Script executed with exit code {exit_code}"
    )


@router.post("/git/clone")
async def clone_git_repo(clone_request: GitCloneRequest, request: Request):
    """Clone a git repository into the scripts directory"""
    result = await script_service.clone_git_repo(
        clone_request.repo_url, clone_request.target_dir, clone_request.branch
    )

    if not result.get("success"):
        return error_response(
            message=result.get("message", "Clone failed"), code=400, data=result
        )

    return success_response(
        data=result, message=result.get("message", "Repository cloned successfully")
    )
