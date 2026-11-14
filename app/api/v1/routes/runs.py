"""执行记录路由: 零逻辑, 委托 ExecutionService。"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter

from app.api.dependencies import Container
from app.api.schemas.response import PageResponse, SuccessResponse
from app.api.schemas.run import LogsResponse, RunResponse
from app.application.pagination import parse_pagination

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=SuccessResponse[PageResponse[RunResponse]])
async def list_runs(
    container: Container,
    page: int = 1,
    page_size: int = 20,
    task_id: uuid.UUID | None = None,
    status: int | None = None,
    trigger: int | None = None,
) -> Any:
    page, page_size = parse_pagination(page, page_size)
    rows, total = await container.executions.list_runs(
        page, page_size, task_id=task_id, status=status, trigger=trigger
    )
    items: list[RunResponse] = []
    for run, task_name in rows:
        item = RunResponse.model_validate(run)
        item.task_name = task_name
        items.append(item)
    return SuccessResponse(
        data=PageResponse(items=items, total=total, page=page, page_size=page_size)
    )


@router.get("/{run_id}", response_model=SuccessResponse[RunResponse])
async def get_run(run_id: uuid.UUID, container: Container) -> Any:
    run, task_name = await container.executions.get_run(run_id)
    item = RunResponse.model_validate(run)
    item.task_name = task_name
    return SuccessResponse(data=item)


@router.get("/{run_id}/logs", response_model=SuccessResponse[LogsResponse])
async def get_run_logs(run_id: uuid.UUID, container: Container) -> Any:
    data = await container.executions.get_logs(run_id)
    return SuccessResponse(data=LogsResponse(**data))


@router.post("/{run_id}/cancel", response_model=SuccessResponse[bool])
async def cancel_run(run_id: uuid.UUID, container: Container) -> Any:
    await container.executions.cancel(run_id)
    return SuccessResponse(data=True)


@router.delete("/{run_id}", response_model=SuccessResponse[bool])
async def delete_run(run_id: uuid.UUID, container: Container) -> Any:
    await container.executions.delete_run(run_id)
    return SuccessResponse(data=True)
