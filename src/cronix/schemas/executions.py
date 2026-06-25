"""任务执行记录相关数据结构。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict

from cronix.schemas.tasks import TaskResponse


class ExecutionStatus(str, Enum):
    """任务执行状态。"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskExecutionResponse(BaseModel):
    """任务执行记录响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    started_at: datetime
    finished_at: Optional[datetime]
    status: ExecutionStatus
    output: Optional[str]
    error: Optional[str]
    retry_attempt: int
    duration: Optional[int] = None


class TaskExecutionDetailResponse(BaseModel):
    """任务执行记录详情响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    task: Optional[TaskResponse]
    started_at: datetime
    finished_at: Optional[datetime]
    status: ExecutionStatus
    output: Optional[str]
    error: Optional[str]
    retry_attempt: int
    duration: Optional[int] = None
