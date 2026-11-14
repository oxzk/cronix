"""StatsService: 仪表盘统计。"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select

from app.core.utils import utc_now
from app.infrastructure.database.models.task import Task
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.runtime.enums import ExecutionStatus


class StatsService:
    def __init__(self, session_factory) -> None:  # type: ignore[no-untyped-def]
        self._session_factory = session_factory

    async def get(self) -> dict:  # type: ignore[type-arg]
        since = utc_now() - timedelta(hours=24)
        async with UnitOfWork(self._session_factory) as uow:
            session = uow.session
            tasks_total = (
                await session.execute(select(func.count()).select_from(Task))
            ).scalar_one()
            tasks_enabled = (
                await session.execute(
                    select(func.count()).select_from(Task).where(Task.enabled.is_(True))
                )
            ).scalar_one()
            runs_running = await uow.task_runs.count_running()
            status_counts = await uow.task_runs.count_by_status_since(since)
            next_rows = (
                await session.execute(
                    select(Task.id, Task.name, Task.cron, Task.next_run_at)
                    .where(Task.enabled.is_(True), Task.next_run_at.is_not(None))
                    .order_by(Task.next_run_at.asc())
                    .limit(10)
                )
            ).all()

        def count(status: ExecutionStatus) -> int:
            return status_counts.get(int(status), 0)

        return {
            "tasks_total": int(tasks_total),
            "tasks_enabled": int(tasks_enabled),
            "runs_running": runs_running,
            "runs_24h": {
                "total": sum(status_counts.values()),
                "completed": count(ExecutionStatus.COMPLETED),
                "failed": count(ExecutionStatus.FAILED),
                "timeout": count(ExecutionStatus.TIMEOUT),
                "cancelled": count(ExecutionStatus.CANCELLED),
            },
            "next_runs": [
                {
                    "task_id": str(row.id),
                    "task_name": row.name,
                    "cron": row.cron,
                    "next_run_at": row.next_run_at.isoformat() if row.next_run_at else None,
                }
                for row in next_rows
            ],
        }
