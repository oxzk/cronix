"""监控相关模式。"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MonitorNotificationConfig(BaseModel):
    enabled: bool = False
    events: list[str] = []


class MonitorCreate(BaseModel):
    name: str
    kind: str
    config: dict[str, Any] = Field(default_factory=dict)
    interval_seconds: int = 60
    timeout_seconds: int = 10
    enabled: bool = True
    notification_config: MonitorNotificationConfig = MonitorNotificationConfig()


class MonitorUpdate(BaseModel):
    name: str | None = None
    kind: str | None = None
    config: dict[str, Any] | None = None
    interval_seconds: int | None = None
    timeout_seconds: int | None = None
    enabled: bool | None = None
    notification_config: MonitorNotificationConfig | None = None


class MonitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    kind: str
    config: dict[str, Any]
    interval_seconds: int
    timeout_seconds: int
    enabled: bool
    notification_config: dict[str, Any]
    next_check_at: datetime | None
    last_status: int | None
    last_latency_ms: int | None
    last_checked_at: datetime | None
    last_issue_at: datetime | None
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime


class MonitorRecentCheck(BaseModel):
    status: int
    checked_at: datetime
    latency_ms: int | None = None
    error_message: str | None = None


class MonitorCardResponse(MonitorResponse):
    uptime_24h: float | None = None
    recent_checks: list[MonitorRecentCheck] = []


class MonitorCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    monitor_id: uuid.UUID
    status: int
    latency_ms: int | None
    error_code: str | None
    error_message: str | None
    checked_at: datetime
