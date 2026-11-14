"""任务路由: 零逻辑, 委托 TaskService。"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter

from app.api.dependencies import Container
from app.api.schemas.response import PageResponse, SuccessResponse
from app.api.schemas.run import RunResponse
from app.api.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.application.pagination import parse_pagination

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _task_response(task: Any, script_name: str | None, running_count: int = 0) -> TaskResponse:
    item = TaskResponse.model_validate(task)
    item.script_name = script_name
    item.running_count = running_count
    return item


@router.get("", response_model=SuccessResponse[PageResponse[TaskResponse]])
async def list_tasks(container: Container, page: int = 1, page_size: int = 20) -> Any:
    page, page_size = parse_pagination(page, page_size)
    rows, total = await container.tasks.list_paginated(page, page_size)
    return SuccessResponse(
        data=PageResponse(
            items=[_task_response(task, script_name, running_count) for task, script_name, running_count in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("", response_model=SuccessResponse[TaskResponse], status_code=201)
async def create_task(body: TaskCreate, container: Container) -> Any:
    values = body.model_dump(mode="json", exclude_none=True)
    task, script_name, running_count = await container.tasks.create(values)
    return SuccessResponse(data=_task_response(task, script_name, running_count))


@router.get("/{task_id}", response_model=SuccessResponse[TaskResponse])
async def get_task(task_id: uuid.UUID, container: Container) -> Any:
    task, script_name, running_count = await container.tasks.get(task_id)
    return SuccessResponse(data=_task_response(task, script_name, running_count))


@router.patch("/{task_id}", response_model=SuccessResponse[TaskResponse])
async def update_task(task_id: uuid.UUID, body: TaskUpdate, container: Container) -> Any:
    values = body.model_dump(mode="json", exclude_unset=True)
    task, script_name, running_count = await container.tasks.update(task_id, values)
    return SuccessResponse(data=_task_response(task, script_name, running_count))


@router.delete("/{task_id}", response_model=SuccessResponse[bool])
async def delete_task(task_id: uuid.UUID, container: Container) -> Any:
    await container.tasks.delete(task_id)
    return SuccessResponse(data=True)


@router.post("/{task_id}/run", response_model=SuccessResponse[RunResponse], status_code=202)
async def run_task(task_id: uuid.UUID, container: Container) -> Any:
    run = await container.tasks.run_now(task_id)
    return SuccessResponse(data=RunResponse.model_validate(run))


@router.post("/{task_id}/cancel", response_model=SuccessResponse[int])
async def cancel_task(task_id: uuid.UUID, container: Container) -> Any:
    cancelled = await container.tasks.cancel(task_id)
    return SuccessResponse(data=cancelled)
