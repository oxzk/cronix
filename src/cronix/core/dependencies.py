"""业务服务依赖提供器。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from cronix.core.database import db
from cronix.core.exceptions import AppError
from cronix.models import User
from cronix.services.auth import AuthService
from cronix.services.executions import ExecutionService
from cronix.services.notifier import NotifierService, notifier_service
from cronix.services.scheduler import SchedulerService, scheduler_service
from cronix.services.settings import SettingsService
from cronix.services.stats import StatsService
from cronix.services.tasks import TaskService


async def get_database() -> AsyncIterator[AsyncSession]:
    """获取 SQLAlchemy 异步会话。

    Yields:
        AsyncSession: SQLAlchemy 异步会话。
    """
    async for session in db.get_session():
        yield session


def get_current_user(request: Request) -> User:
    """获取当前已认证用户。

    用户由 ``AuthMiddleware`` 在校验令牌后写入 ``request.state``。

    Args:
        request: FastAPI 请求对象。

    Returns:
        当前已认证用户。

    Raises:
        AppError: 请求未经过认证。
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise AppError("Not authenticated", status_code=401)
    return user


class ServiceDependencyProvider:
    """业务服务依赖提供器。"""

    @staticmethod
    def get_auth_service(session: AsyncSession = Depends(get_database)) -> AuthService:
        """创建认证服务。

        Args:
            session: 数据库会话（自动注入）。

        Returns:
            认证服务实例。
        """
        return AuthService(session)

    @staticmethod
    def get_notifier_service() -> NotifierService:
        """获取全局通知服务。"""
        return notifier_service

    @staticmethod
    def get_scheduler_service() -> SchedulerService:
        """获取全局调度服务。"""
        return scheduler_service

    @staticmethod
    def get_task_service(
        session: AsyncSession = Depends(get_database),
    ) -> TaskService:
        """创建任务服务。

        Args:
            request: FastAPI 请求对象。
            session: 数据库会话（自动注入）。

        Returns:
            任务服务实例。
        """
        return TaskService(
            session=session,
            scheduler_service=ServiceDependencyProvider.get_scheduler_service(),
        )

    @staticmethod
    def get_execution_service(session: AsyncSession = Depends(get_database)) -> ExecutionService:
        """创建执行记录服务。

        Args:
            session: 数据库会话（自动注入）。

        Returns:
            执行记录服务实例。
        """
        return ExecutionService(session)

    @staticmethod
    def get_settings_service(session: AsyncSession = Depends(get_database)) -> SettingsService:
        """创建设置服务。

        Args:
            session: 数据库会话（自动注入）。

        Returns:
            设置服务实例。
        """
        return SettingsService(session)

    @staticmethod
    def get_stats_service(session: AsyncSession = Depends(get_database)) -> StatsService:
        """创建统计服务。

        Args:
            session: 数据库会话（自动注入）。

        Returns:
            统计服务实例。
        """
        return StatsService(session)


DatabaseDep = Annotated[AsyncSession, Depends(get_database)]
"""直接数据库会话依赖。

注意：在大多数情况下，应该使用服务层依赖（如 ExecutionServiceDep、TaskServiceDep 等）
而不是直接注入数据库会话。DatabaseDep 主要用于需要直接数据库访问的特殊场景，
例如复杂的跨表事务操作。参见 examples/route_with_database_session.py 了解使用示例。
"""
NotifierServiceDep = Annotated[
    NotifierService,
    Depends(ServiceDependencyProvider.get_notifier_service),
]
AuthServiceDep = Annotated[
    AuthService,
    Depends(ServiceDependencyProvider.get_auth_service),
]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
SchedulerServiceDep = Annotated[
    SchedulerService,
    Depends(ServiceDependencyProvider.get_scheduler_service),
]
TaskServiceDep = Annotated[
    TaskService,
    Depends(ServiceDependencyProvider.get_task_service),
]
ExecutionServiceDep = Annotated[
    ExecutionService,
    Depends(ServiceDependencyProvider.get_execution_service),
]
SettingsServiceDep = Annotated[
    SettingsService,
    Depends(ServiceDependencyProvider.get_settings_service),
]
StatsServiceDep = Annotated[
    StatsService,
    Depends(ServiceDependencyProvider.get_stats_service),
]
