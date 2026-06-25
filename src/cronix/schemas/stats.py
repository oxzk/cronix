"""统计相关数据结构。"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class TaskStatsResponse(BaseModel):
    """任务统计响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    total_tasks: int
    active_tasks: int
    inactive_tasks: int
    total_executions: int
    success_executions: int
    failed_executions: int
    running_executions: int
    success_rate: Optional[float] = None
