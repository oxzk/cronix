"""健康检查(公开)。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.api.dependencies import Container
from app.infrastructure.database.unit_of_work import UnitOfWork

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health(container: Container) -> Any:
    database = True
    try:
        async with UnitOfWork(container.session_factory) as uow:
            await uow.session.execute(text("SELECT 1"))
    except Exception:
        database = False
    return {"status": "ok", "database": database}
