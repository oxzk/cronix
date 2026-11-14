"""监控路由: 零逻辑, 委托 MonitorService。"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter

from app.api.dependencies import Container
from app.api.schemas.monitor import (
    MonitorCardResponse,
    MonitorCheckResponse,
    MonitorCreate,
    MonitorResponse,
    MonitorUpdate,
)
from app.api.schemas.response import PageResponse, SuccessResponse
from app.application.pagination import parse_pagination
from app.core.monitoring import redact_config

router = APIRouter(prefix="/monitors", tags=["monitors"])


def _monitor_response(monitor: Any) -> MonitorResponse:
    data = MonitorResponse.model_validate(monitor)
    data.config = redact_config(monitor.kind, monitor.config)
    return data


@router.get("", response_model=SuccessResponse[list[MonitorCardResponse]])
async def list_monitors(container: Container) -> Any:
    cards = await container.monitors.list_cards()
    items = [
        MonitorCardResponse(**{**card, "config": redact_config(card["kind"], card["config"])})
        for card in cards
    ]
    return SuccessResponse(data=items)


@router.post("", response_model=SuccessResponse[MonitorResponse], status_code=201)
async def create_monitor(body: MonitorCreate, container: Container) -> Any:
    values = body.model_dump(mode="json", exclude_none=True)
    monitor = await container.monitors.create(values)
    return SuccessResponse(data=_monitor_response(monitor))


@router.get("/{monitor_id}", response_model=SuccessResponse[MonitorResponse])
async def get_monitor(monitor_id: uuid.UUID, container: Container) -> Any:
    monitor = await container.monitors.get(monitor_id)
    return SuccessResponse(data=_monitor_response(monitor))


@router.patch("/{monitor_id}", response_model=SuccessResponse[MonitorResponse])
async def update_monitor(monitor_id: uuid.UUID, body: MonitorUpdate, container: Container) -> Any:
    values = body.model_dump(mode="json", exclude_unset=True)
    monitor = await container.monitors.update(monitor_id, values)
    return SuccessResponse(data=_monitor_response(monitor))


@router.delete("/{monitor_id}", response_model=SuccessResponse[bool])
async def delete_monitor(monitor_id: uuid.UUID, container: Container) -> Any:
    await container.monitors.delete(monitor_id)
    return SuccessResponse(data=True)


@router.post("/{monitor_id}/check", response_model=SuccessResponse[MonitorCheckResponse])
async def check_monitor(monitor_id: uuid.UUID, container: Container) -> Any:
    result = await container.monitors.check_now(monitor_id)
    return SuccessResponse(data=MonitorCheckResponse(**result))


@router.get("/{monitor_id}/checks", response_model=SuccessResponse[PageResponse[MonitorCheckResponse]])
async def list_monitor_checks(
    monitor_id: uuid.UUID, container: Container, page: int = 1, page_size: int = 20
) -> Any:
    page, page_size = parse_pagination(page, page_size)
    rows, total = await container.monitors.list_checks(monitor_id, page, page_size)
    return SuccessResponse(
        data=PageResponse(
            items=[MonitorCheckResponse.model_validate(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
    )
