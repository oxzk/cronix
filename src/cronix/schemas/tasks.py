"""任务相关数据结构。"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from croniter import croniter
from pydantic import BaseModel, ConfigDict, Field, field_validator

from cronix.schemas.notifications import NotificationResponse, NotifyStrategy


class TaskSchema(BaseModel):
    """任务请求数据。"""

    name: str
    description: Optional[str] = None
    cron_expression: str
    command: str
    is_active: bool = True
    timeout: int = Field(default=300, ge=1, le=3600)
    retry_count: int = Field(default=0, ge=0, le=5)
    retry_interval: int = Field(default=60, ge=1, le=600)
    notification_ids: Optional[List[int]] = None
    notify_strategy: NotifyStrategy = Field(default=NotifyStrategy.NEVER)

    @field_validator("cron_expression")
    @classmethod
    def validate_cron_expression(cls, v: str) -> str:
        """校验 5 段 cron 表达式。"""
        parts = v.strip().split()
        if len(parts) != 5:
            raise ValueError(
                "Cron expression must have 5 fields: minute hour day month weekday"
            )
        try:
            croniter(v)
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid cron expression: {str(e)}")
        return v


class TaskResponse(BaseModel):
    """任务响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    cron_expression: str
    command: str
    is_active: bool
    timeout: int
    retry_count: int
    retry_interval: int
    notification_ids: Optional[List[int]] = None
    notifications: Optional[List[NotificationResponse]] = None
    notify_strategy: NotifyStrategy
    next_run_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
