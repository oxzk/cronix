"""任务执行记录业务服务。"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from cronix.core.exceptions import NotFoundError
from cronix.repositories import ExecutionRepository, NotificationRepository
from cronix.schemas import (
    ExecutionStatus,
    PaginatedResponse,
    TaskExecutionDetailResponse,
)


class ExecutionService:
    """任务执行记录查询服务。

    Attributes:
        session: SQLAlchemy 异步会话。
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化执行记录服务。

        Args:
            session: SQLAlchemy 异步会话，由外层依赖注入并管理事务边界。
        """
        self._execution_repo = ExecutionRepository(session)
        self._notification_repo = NotificationRepository(session)
        self._session = session

    async def list_executions(
        self,
        task_id: Optional[int],
        status: Optional[ExecutionStatus],
        page: int,
        page_size: int,
    ) -> PaginatedResponse[TaskExecutionDetailResponse]:
        """分页查询任务执行记录。

        Args:
            task_id: 任务 ID 过滤条件。
            status: 状态过滤条件。
            page: 页码。
            page_size: 每页大小。

        Returns:
            分页后的执行记录列表。
        """
        # 使用 Repository 获取分页数据
        executions, total = await self._execution_repo.list_paginated(
            page, page_size, task_id, status.value if status else None
        )

        return PaginatedResponse(
            items=executions,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_execution(self, execution_id: int) -> TaskExecutionDetailResponse:
        """查询单条任务执行记录详情。

        Args:
            execution_id: 执行记录 ID。

        Returns:
            执行记录详情。

        Raises:
            NotFoundError: 执行记录不存在。
        """
        # 使用 Repository 获取执行记录
        execution = await self._execution_repo.get_by_id(execution_id)
        if not execution:
            raise NotFoundError("Execution not found")

        if execution.task and execution.task.notification_ids:
            execution.task.notifications = await self._notification_repo.get_by_ids(
                execution.task.notification_ids
            )

        return TaskExecutionDetailResponse.model_validate(execution)
