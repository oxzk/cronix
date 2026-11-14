"""任务相关模式(命令可内联或引用脚本)。"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class NotificationConfig(BaseModel):
    enabled: bool = False
    events: list[str] = []


class TaskCreate(BaseModel):
    name: str
    command: str | None = None
    script_id: uuid.UUID | None = None
    cron: str
    enabled: bool = True
    timeout: int | None = None
    max_retries: int = 0
    retry_delay: int = 5
    notification_config: NotificationConfig = NotificationConfig()


class TaskUpdate(BaseModel):
    name: str | None = None
    command: str | None = None
    script_id: uuid.UUID | None = None
    cron: str | None = None
    enabled: bool | None = None
    timeout: int | None = None
    max_retries: int | None = None
    retry_delay: int | None = None
    notification_config: NotificationConfig | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    command: str | None
    script_id: uuid.UUID | None
    script_name: str | None = None
    cron: str
    enabled: bool
    timeout: int | None
    max_retries: int
    retry_delay: int
    running_count: int = 0
    notification_config: dict[str, Any]
    next_run_at: datetime | None
    last_run_at: datetime | None
    last_status: int | None
    created_at: datetime
    updated_at: datetime
