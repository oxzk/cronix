"""数据结构包。"""

from __future__ import annotations

from cronix.schemas.auth import (
    LoginSchema,
    TokenResponse,
    UserResponse,
)
from cronix.schemas.executions import (
    ExecutionStatus,
    TaskExecutionResponse,
    TaskExecutionDetailResponse,
)
from cronix.schemas.notifications import (
    NotificationSchema,
    NotificationResponse,
    NotifyStrategy,
    NotifyType,
)
from cronix.schemas.response import APIResponse, PageQuery, PaginatedResponse
from cronix.schemas.settings import (
    SettingsUserCreateSchema,
    SettingsUserResponse,
    SettingsUserUpdateSchema,
)
from cronix.schemas.stats import (
    TaskStatsResponse,
)
from cronix.schemas.tasks import (
    TaskSchema,
    TaskResponse,
)

__all__ = [
    "APIResponse",
    "PageQuery",
    "PaginatedResponse",
    "LoginSchema",
    "TokenResponse",
    "UserResponse",
    "ExecutionStatus",
    "NotifyStrategy",
    "NotifyType",
    "TaskSchema",
    "TaskResponse",
    "TaskExecutionResponse",
    "TaskExecutionDetailResponse",
    "NotificationSchema",
    "NotificationResponse",
    "SettingsUserCreateSchema",
    "SettingsUserResponse",
    "SettingsUserUpdateSchema",
    "TaskStatsResponse",
]
