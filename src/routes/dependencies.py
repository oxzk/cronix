from fastapi import APIRouter, Request, Query
from typing import Optional
from src.utils import success_response, error_response
from src.services.dependencies import dependency_service
from src.models.schemas import DependencySchema


router = APIRouter(prefix="/dependencies", tags=["dependencies"])


@router.get("")
async def list_dependencies(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=200, description="Items per page"),
    dependency_type: Optional[str] = Query(
        None, description="Filter by type: python or node"
    ),
    status: Optional[str] = Query(
        None, description="Filter by status: pending, installing, installed, failed"
    ),
):
    """List all dependencies with pagination"""
    result = await dependency_service.list_dependencies(
        dependency_type, status, page, page_size
    )
    return success_response(data=result)


@router.post("")
async def create_and_install_dependency(dep_data: DependencySchema, request: Request):
    """Create and install a dependency"""
    # Install the dependency (will create or update record)
    result = await dependency_service.install_dependency(
        dep_data.dependency_type,
        dep_data.package_name,
        dep_data.version,
        timeout=300,
    )

    if not result.get("success"):
        code = 408 if result["status"] == "timeout" else 500
        return error_response(
            message=result.get("error", "Installation failed"), code=code, data=result
        )

    return success_response(
        data=result,
        message=f"Dependency '{dep_data.package_name}' installed successfully",
    )
