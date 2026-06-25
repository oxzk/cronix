"""任务路由。"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from cronix.schemas import APIResponse, PageQuery, PaginatedResponse, TaskResponse, TaskSchema
from cronix.core.dependencies import TaskServiceDep

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=APIResponse[PaginatedResponse[TaskResponse]])
async def list_tasks(
    page_query: Annotated[PageQuery, Depends()],
    service: TaskServiceDep,
    name: Optional[str] = Query(None, description="Filter by task name (partial match)"),
    is_active: Optional[bool] = Query(
        None,
        description="Filter by task status (true=active, false=inactive)",
    ),
):
    """查询任务列表。"""
    data = await service.list_tasks(page_query.page, page_query.page_size, name, is_active)
    return APIResponse.ok(data)


@router.post("", response_model=APIResponse[TaskResponse])
async def create_task(task_data: TaskSchema, service: TaskServiceDep):
    """创建任务。"""
    data = await service.create_task(task_data)
    return APIResponse.ok(data, "Task created successfully")


@router.get("/running/list", response_model=APIResponse[list[int]])
async def list_running_tasks(service: TaskServiceDep):
    """查询正在运行的任务。"""
    data = service.list_running_tasks()
    return APIResponse.ok(data)


@router.get("/{task_id}", response_model=APIResponse[TaskResponse])
async def get_task(task_id: int, service: TaskServiceDep):
    """查询单个任务。"""
    data = await service.get_task(task_id)
    return APIResponse.ok(data)


@router.put("/{task_id}", response_model=APIResponse[TaskResponse])
async def update_task(task_id: int, task_data: TaskSchema, service: TaskServiceDep):
    """更新任务。"""
    data = await service.update_task(task_id, task_data)
    return APIResponse.ok(data, "Task updated successfully")


@router.delete("/{task_id}", response_model=APIResponse[None])
async def delete_task(task_id: int, service: TaskServiceDep):
    """删除任务。"""
    await service.delete_task(task_id)
    return APIResponse.ok(None, "Task deleted successfully")


@router.post("/{task_id}/cancel", response_model=APIResponse[None])
async def cancel_task(task_id: int, service: TaskServiceDep):
    """取消运行中的任务。"""
    await service.cancel_task(task_id)
    return APIResponse.ok(None, f"Task {task_id} cancelled successfully")


@router.post("/{task_id}/execute", response_model=APIResponse[None])
async def execute_task(task_id: int, service: TaskServiceDep):
    """手动执行任务。"""
    await service.execute_task(task_id)
    return APIResponse.ok(None, f"Task {task_id} execution triggered successfully")
