"""系统设置相关数据结构。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SettingsUserCreateSchema(BaseModel):
    """系统设置用户创建请求数据。"""

    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class SettingsUserUpdateSchema(BaseModel):
    """系统设置用户更新请求数据。"""

    username: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="用户名",
    )
    password: str | None = Field(
        default=None,
        min_length=6,
        max_length=128,
        description="密码",
    )


class SettingsUserResponse(BaseModel):
    """系统设置用户响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime
    updated_at: datetime
