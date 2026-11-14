"""系统设置路由: GET 全量(已脱敏) + PUT 更新。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.dependencies import Container
from app.api.schemas.response import SuccessResponse
from app.api.schemas.setting import SystemSettingResponse, SystemSettingUpdate

router = APIRouter(prefix="/system-settings", tags=["system-settings"])


@router.get("", response_model=SuccessResponse[list[SystemSettingResponse]])
async def list_settings(container: Container) -> Any:
    rows = await container.system_settings.list_all()
    return SuccessResponse(data=[SystemSettingResponse.model_validate(row) for row in rows])


@router.put("/{scope}/{key}", response_model=SuccessResponse[SystemSettingResponse])
async def put_setting(scope: str, key: str, body: SystemSettingUpdate, container: Container) -> Any:
    row = await container.system_settings.put(scope, key, body.value)
    return SuccessResponse(data=SystemSettingResponse.model_validate(row))
