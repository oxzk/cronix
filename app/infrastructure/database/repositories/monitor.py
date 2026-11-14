"""monitors 仓储。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.monitor import Monitor


class MonitorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, monitor_id: uuid.UUID) -> Monitor | None:
        return await self._session.get(Monitor, monitor_id)

    async def list_all(self) -> list[Monitor]:
        stmt = select(Monitor).order_by(Monitor.created_at.asc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_enabled(self) -> list[Monitor]:
        stmt = select(Monitor).where(Monitor.enabled.is_(True)).order_by(Monitor.created_at.asc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_due(self, now: datetime) -> list[Monitor]:
        stmt = (
            select(Monitor)
            .where(
                Monitor.enabled.is_(True),
                Monitor.next_check_at.is_not(None),
                Monitor.next_check_at <= now,
            )
            .order_by(Monitor.next_check_at.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def add(self, monitor: Monitor) -> Monitor:
        self._session.add(monitor)
        await self._session.flush()
        return monitor

    async def delete(self, monitor: Monitor) -> None:
        await self._session.delete(monitor)
