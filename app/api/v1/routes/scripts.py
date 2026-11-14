"""脚本路由: 零逻辑, 委托 ScriptService。"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter

from app.api.dependencies import Container
from app.api.schemas.response import PageResponse, SuccessResponse
from app.api.schemas.script import ScriptCreate, ScriptResponse, ScriptTestResponse, ScriptUpdate
from app.application.pagination import parse_pagination

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.get("", response_model=SuccessResponse[PageResponse[ScriptResponse]])
async def list_scripts(container: Container, page: int = 1, page_size: int = 20) -> Any:
    page, page_size = parse_pagination(page, page_size)
    scripts, total = await container.scripts.list_paginated(page, page_size)
    return SuccessResponse(
        data=PageResponse(
            items=[ScriptResponse.model_validate(script) for script in scripts],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("", response_model=SuccessResponse[ScriptResponse], status_code=201)
async def create_script(body: ScriptCreate, container: Container) -> Any:
    values = body.model_dump(mode="json", exclude_none=True)
    script = await container.scripts.create(values)
    return SuccessResponse(data=ScriptResponse.model_validate(script))


@router.get("/{script_id}", response_model=SuccessResponse[ScriptResponse])
async def get_script(script_id: uuid.UUID, container: Container) -> Any:
    script = await container.scripts.get(script_id)
    return SuccessResponse(data=ScriptResponse.model_validate(script))


@router.patch("/{script_id}", response_model=SuccessResponse[ScriptResponse])
async def update_script(script_id: uuid.UUID, body: ScriptUpdate, container: Container) -> Any:
    values = body.model_dump(mode="json", exclude_unset=True)
    script = await container.scripts.update(script_id, values)
    return SuccessResponse(data=ScriptResponse.model_validate(script))


@router.delete("/{script_id}", response_model=SuccessResponse[bool])
async def delete_script(script_id: uuid.UUID, container: Container) -> Any:
    await container.scripts.delete(script_id)
    return SuccessResponse(data=True)


@router.post("/{script_id}/test", response_model=SuccessResponse[ScriptTestResponse])
async def test_script(script_id: uuid.UUID, container: Container) -> Any:
    result = await container.scripts.test_run(script_id)
    return SuccessResponse(data=ScriptTestResponse(**result))
