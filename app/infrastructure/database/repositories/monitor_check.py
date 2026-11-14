"""monitor_checks 仓储。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.monitor_check import MonitorCheck


class MonitorCheckRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, check: MonitorCheck) -> MonitorCheck:
        self._session.add(check)
        await self._session.flush()
        return check

    async def list_paginated(
        self, monitor_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[MonitorCheck], int]:
        base = select(MonitorCheck).where(MonitorCheck.monitor_id == monitor_id)
        total = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        stmt = (
            base.order_by(MonitorCheck.checked_at.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows), int(total)

    async def uptime_since(self, since: datetime) -> dict[uuid.UUID, tuple[int, int]]:
        """返回 {monitor_id: (总检查数, up 数)}。"""
        up_expr = func.sum(case((MonitorCheck.status == 1, 1), else_=0))
        stmt = (
            select(MonitorCheck.monitor_id, func.count(), up_expr)
            .where(MonitorCheck.checked_at >= since)
            .group_by(MonitorCheck.monitor_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: (int(row[1]), int(row[2] or 0)) for row in rows}

    async def recent_checks(self, limit: int = 30) -> dict[uuid.UUID, list[dict]]:
        """每个 monitor 最近 N 条检查明细, 按时间升序(旧→新)。"""
        rn = func.row_number().over(
            partition_by=MonitorCheck.monitor_id, order_by=MonitorCheck.checked_at.desc()
        ).label("rn")
        sub = select(
            MonitorCheck.monitor_id,
            MonitorCheck.status,
            MonitorCheck.checked_at,
            MonitorCheck.latency_ms,
            MonitorCheck.error_message,
            rn,
        ).subquery()
        stmt = (
            select(
                sub.c.monitor_id,
                sub.c.status,
                sub.c.checked_at,
                sub.c.latency_ms,
                sub.c.error_message,
            )
            .where(sub.c.rn <= limit)
            .order_by(sub.c.monitor_id, sub.c.checked_at.asc())
        )
        rows = (await self._session.execute(stmt)).all()
        result: dict[uuid.UUID, list[dict]] = {}
        for row in rows:
            result.setdefault(row[0], []).append(
                {
                    "status": int(row[1]),
                    "checked_at": row[2],
                    "latency_ms": row[3],
                    "error_message": row[4],
                }
            )
        return result

    async def cleanup_before(self, before: datetime) -> int:
        result = await self._session.execute(
            delete(MonitorCheck).where(MonitorCheck.checked_at < before)
        )
        return result.rowcount
