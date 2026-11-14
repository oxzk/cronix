"""脚本相关模式。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScriptCreate(BaseModel):
    name: str
    description: str | None = None
    content: str


class ScriptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    content: str | None = None


class ScriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    content: str
    created_at: datetime
    updated_at: datetime


class ScriptTestResponse(BaseModel):
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool
