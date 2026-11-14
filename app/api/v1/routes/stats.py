"""仪表盘统计路由。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.dependencies import Container
from app.api.schemas.response import SuccessResponse
from app.api.schemas.stats import StatsResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=SuccessResponse[StatsResponse])
async def get_stats(container: Container) -> Any:
    return SuccessResponse(data=StatsResponse(**(await container.stats.get())))
