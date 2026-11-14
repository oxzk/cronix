"""task_runs 仓储。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.task import Task
from app.infrastructure.database.models.task_run import TaskRun


class TaskRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, run_id: uuid.UUID) -> TaskRun | None:
        return await self._session.get(TaskRun, run_id)

    def _list_stmt(
        self,
        task_id: uuid.UUID | None,
        status: int | None,
        trigger: int | None,
        limit: int,
        offset: int,
    ) -> Select:
        stmt = select(TaskRun).order_by(TaskRun.created_at.desc(), TaskRun.id.desc())
        if task_id is not None:
            stmt = stmt.where(TaskRun.task_id == task_id)
        if status is not None:
            stmt = stmt.where(TaskRun.status == status)
        if trigger is not None:
            stmt = stmt.where(TaskRun.trigger == trigger)
        return stmt.limit(limit).offset(offset)

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        *,
        task_id: uuid.UUID | None = None,
        status: int | None = None,
        trigger: int | None = None,
    ) -> tuple[list[tuple[TaskRun, str | None]], int]:
        base = select(TaskRun)
        if task_id is not None:
            base = base.where(TaskRun.task_id == task_id)
        if status is not None:
            base = base.where(TaskRun.status == status)
        if trigger is not None:
            base = base.where(TaskRun.trigger == trigger)
        total = (await self._session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        stmt = self._list_stmt(task_id, status, trigger, page_size, (page - 1) * page_size)
        rows = (await self._session.execute(stmt)).scalars().all()

        task_ids = {run.task_id for run in rows}
        names: dict[uuid.UUID, str] = {}
        if task_ids:
            name_rows = await self._session.execute(
                select(Task.id, Task.name).where(Task.id.in_(task_ids))
            )
            names = {row.id: row.name for row in name_rows}
        return [(run, names.get(run.task_id)) for run in rows], int(total)

    async def add(self, run: TaskRun) -> TaskRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def delete(self, run: TaskRun) -> None:
        await self._session.delete(run)

    async def set_running(self, run_id: uuid.UUID, started_at: datetime) -> None:
        await self._session.execute(
            update(TaskRun)
            .where(TaskRun.id == run_id)
            .values(status=1, started_at=started_at)
        )

    async def set_terminal(self, run_id: uuid.UUID, values: dict) -> bool:
        result = await self._session.execute(
            update(TaskRun).where(TaskRun.id == run_id).values(**values)
        )
        return result.rowcount > 0

    async def recover_interrupted(self) -> int:
        """启动恢复: RUNNING → failed_interrupted。"""
        result = await self._session.execute(
            update(TaskRun)
            .where(TaskRun.status == 1)
            .values(
                status=3,
                completed_at=func.now(),
                error_code="interrupted",
                error_message="进程重启, 执行中断",
            )
        )
        return result.rowcount

    async def cancel_pending_all(self) -> int:
        result = await self._session.execute(
            update(TaskRun)
            .where(TaskRun.status == 0)
            .values(status=4, error_code="cancelled", error_message="进程重启, 排队任务已取消")
        )
        return result.rowcount

    async def count_by_status_since(self, since: datetime) -> dict[int, int]:
        stmt = (
            select(TaskRun.status, func.count())
            .where(TaskRun.created_at >= since)
            .group_by(TaskRun.status)
        )
        rows = (await self._session.execute(stmt)).all()
        return {int(row[0]): int(row[1]) for row in rows}

    async def count_active_by_task(self, task_ids: set[uuid.UUID]) -> dict[uuid.UUID, int]:
        if not task_ids:
            return {}
        stmt = (
            select(TaskRun.task_id, func.count())
            .where(TaskRun.task_id.in_(task_ids), TaskRun.status.in_((0, 1)))
            .group_by(TaskRun.task_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: int(row[1]) for row in rows}

    async def cleanup_before(self, before: datetime, *, include_active: bool = True) -> int:
        stmt = delete(TaskRun).where(TaskRun.created_at < before)
        if not include_active:
            stmt = stmt.where(TaskRun.status.not_in((0, 1)))
        result = await self._session.execute(stmt)
        return result.rowcount

    async def count_running(self) -> int:
        return int(
            (
                await self._session.execute(
                    select(func.count()).select_from(TaskRun).where(TaskRun.status == 1)
                )
            ).scalar_one()
        )
