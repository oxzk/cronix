"""任务执行记录路由。"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from cronix.schemas import (
    APIResponse,
    ExecutionStatus,
    PageQuery,
    PaginatedResponse,
    TaskExecutionDetailResponse,
)
from cronix.core.dependencies import ExecutionServiceDep

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=APIResponse[PaginatedResponse[TaskExecutionDetailResponse]])
async def list_executions(
    page_query: Annotated[PageQuery, Depends()],
    service: ExecutionServiceDep,
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    status: Optional[ExecutionStatus] = Query(None, description="Filter by status"),
):
    """查询任务执行记录列表。"""
    data = await service.list_executions(
        task_id,
        status,
        page_query.page,
        page_query.page_size,
    )
    return APIResponse.ok(data)


@router.get("/{execution_id}", response_model=APIResponse[TaskExecutionDetailResponse])
async def get_execution(execution_id: int, service: ExecutionServiceDep):
    """查询任务执行记录详情。"""
    data = await service.get_execution(execution_id)
    return APIResponse.ok(data)
