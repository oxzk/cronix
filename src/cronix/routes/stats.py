"""统计路由。"""

from __future__ import annotations

from fastapi import APIRouter

from cronix.schemas import APIResponse, TaskStatsResponse
from cronix.core.dependencies import StatsServiceDep

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/tasks/summary", response_model=APIResponse[TaskStatsResponse])
async def get_tasks_stats(service: StatsServiceDep):
    """查询任务统计摘要。"""
    data = await service.get_tasks_stats()
    return APIResponse.ok(data)
