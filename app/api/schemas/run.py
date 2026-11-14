"""执行记录相关模式。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    task_name: str | None = None
    trigger: int
    status: int
    attempt: int
    scheduled_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    exit_code: int | None
    error_code: str | None
    error_message: str | None
    created_at: datetime


class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str


class LogsResponse(BaseModel):
    run_id: str
    persisted: bool
    logs: list[LogEntry]
