"""scripts 仓储。"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.script import Script
from app.infrastructure.database.models.task import Task


class ScriptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, script_id: uuid.UUID) -> Script | None:
        return await self._session.get(Script, script_id)

    async def get_by_name(self, name: str) -> Script | None:
        stmt = select(Script).where(Script.name == name)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_paginated(self, page: int, page_size: int) -> tuple[list[Script], int]:
        total = (await self._session.execute(select(func.count()).select_from(Script))).scalar_one()
        stmt = (
            select(Script)
            .order_by(Script.created_at.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows), int(total)

    async def names_by_ids(self, script_ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
        if not script_ids:
            return {}
        rows = await self._session.execute(select(Script.id, Script.name).where(Script.id.in_(script_ids)))
        return {row.id: row.name for row in rows}

    async def count_task_references(self, script_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Task).where(Task.script_id == script_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def add(self, script: Script) -> Script:
        self._session.add(script)
        await self._session.flush()
        return script

    async def delete(self, script: Script) -> None:
        await self._session.delete(script)
