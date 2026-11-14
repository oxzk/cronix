"""tasks 仓储。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.task import Task


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, task_id: uuid.UUID) -> Task | None:
        return await self._session.get(Task, task_id)

    async def list_paginated(self, page: int, page_size: int) -> tuple[list[Task], int]:
        total = (await self._session.execute(select(func.count()).select_from(Task))).scalar_one()
        stmt = select(Task).order_by(Task.created_at.desc()).limit(page_size).offset((page - 1) * page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows), int(total)

    async def list_enabled(self) -> list[Task]:
        stmt = select(Task).where(Task.enabled.is_(True)).order_by(Task.created_at.asc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_due(self, now: datetime) -> list[Task]:
        stmt = (
            select(Task)
            .where(Task.enabled.is_(True), Task.next_run_at.is_not(None), Task.next_run_at <= now)
            .order_by(Task.next_run_at.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def add(self, task: Task) -> Task:
        self._session.add(task)
        await self._session.flush()
        return task

    async def delete(self, task: Task) -> None:
        await self._session.delete(task)
