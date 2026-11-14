"""系统设置相关模式。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SystemSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scope: str
    key: str
    type: str
    value: dict[str, Any]
    is_complete: bool
    description: str | None
    updated_at: datetime


class SystemSettingUpdate(BaseModel):
    value: dict[str, Any]
