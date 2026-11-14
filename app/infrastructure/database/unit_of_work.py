"""事务边界: 一个 UoW 绑定一个 session 与全部仓储, 干净退出提交, 异常回滚。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.database.repositories.monitor import MonitorRepository
from app.infrastructure.database.repositories.monitor_check import MonitorCheckRepository
from app.infrastructure.database.repositories.script import ScriptRepository
from app.infrastructure.database.repositories.system_setting import SystemSettingRepository
from app.infrastructure.database.repositories.task import TaskRepository
from app.infrastructure.database.repositories.task_run import TaskRunRepository


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork 未进入上下文")
        return self._session

    async def __aenter__(self) -> "UnitOfWork":
        self._session = self._session_factory()
        self.tasks = TaskRepository(self._session)
        self.task_runs = TaskRunRepository(self._session)
        self.system_settings = SystemSettingRepository(self._session)
        self.scripts = ScriptRepository(self._session)
        self.monitors = MonitorRepository(self._session)
        self.monitor_checks = MonitorCheckRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        try:
            if exc_type is not None:
                await self._session.rollback()
            else:
                await self._session.commit()
        finally:
            await self._session.close()
            self._session = None
