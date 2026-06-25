"""任务执行记录数据访问层。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cronix.models import TaskExecution
from cronix.repositories.base import BaseRepository
from cronix.schemas import ExecutionStatus


class ExecutionRepository(BaseRepository[TaskExecution]):
    """任务执行记录数据访问层。

    负责任务执行记录表的查询、CRUD 操作和数据映射。
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化执行记录 Repository。

        Args:
            session: SQLAlchemy 异步会话。
        """
        super().__init__(session)

    async def get_by_id(self, execution_id: int) -> TaskExecution | None:
        """根据 ID 查询执行记录。

        Args:
            execution_id: 执行记录 ID。

        Returns:
            执行记录实例，不存在时返回 None。
        """
        result = await self.session.execute(
            select(TaskExecution)
            .options(selectinload(TaskExecution.task))
            .where(TaskExecution.id == execution_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        task_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> tuple[list[TaskExecution], int]:
        """分页查询执行记录列表。

        Args:
            page: 页码（从 1 开始）。
            page_size: 每页大小。
            task_id: 任务 ID 过滤。
            status: 执行状态过滤。

        Returns:
            (执行记录列表, 总数) 元组。
        """
        query = select(TaskExecution).options(selectinload(TaskExecution.task))

        # 应用过滤条件
        if task_id is not None:
            query = query.where(TaskExecution.task_id == task_id)

        if status is not None:
            query = query.where(TaskExecution.status == status)

        # 查询总数
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # 分页查询（按开始时间倒序）
        offset = (page - 1) * page_size
        paginated_query = (
            query.order_by(TaskExecution.started_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(paginated_query)
        executions = list(result.scalars().all())

        return executions, total

    async def create(self, execution: TaskExecution) -> TaskExecution:
        """创建执行记录。

        Args:
            execution: 执行记录实例。

        Returns:
            已保存的执行记录实例。
        """
        self.session.add(execution)
        await self.session.flush()
        await self.session.refresh(execution)
        return execution

    async def update(self, execution: TaskExecution) -> TaskExecution:
        """更新执行记录。

        Args:
            execution: 执行记录实例。

        Returns:
            更新后的执行记录实例。
        """
        await self.session.flush()
        await self.session.refresh(execution)
        return execution

    async def get_latest_by_task_id(
        self, task_id: int, limit: int = 10
    ) -> list[TaskExecution]:
        """查询指定任务的最新执行记录。

        Args:
            task_id: 任务 ID。
            limit: 返回记录数量限制。

        Returns:
            最新的执行记录列表。
        """
        result = await self.session.execute(
            select(TaskExecution)
            .where(TaskExecution.task_id == task_id)
            .order_by(TaskExecution.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_task_id(self, task_id: int) -> int:
        """统计指定任务的执行记录总数。

        Args:
            task_id: 任务 ID。

        Returns:
            执行记录总数。
        """
        result = await self.session.execute(
            select(func.count()).where(TaskExecution.task_id == task_id)
        )
        return result.scalar() or 0

    async def count_by_status(self, status: str) -> int:
        """统计指定状态的执行记录总数。

        Args:
            status: 执行状态。

        Returns:
            执行记录总数。
        """
        result = await self.session.execute(
            select(func.count()).where(TaskExecution.status == status)
        )
        return result.scalar() or 0

    async def count_group_by_status(self) -> dict[str, int]:
        """按状态分组统计执行记录数量。

        Returns:
            以状态为键、记录数为值的字典。
        """
        result = await self.session.execute(
            select(
                TaskExecution.status,
                func.count(TaskExecution.id).label("cnt"),
            ).group_by(TaskExecution.status)
        )
        return {row.status: row.cnt for row in result.all()}

    async def cancel_orphan_running(
        self, finished_at: datetime, error: str
    ) -> None:
        """将所有 RUNNING 状态的执行记录批量标记为 CANCELLED。

        用于服务重启时清理状态未知的遗留执行记录。

        Args:
            finished_at: 标记的结束时间。
            error: 取消原因描述。
        """
        await self.session.execute(
            update(TaskExecution)
            .where(TaskExecution.status == ExecutionStatus.RUNNING.value)
            .values(
                status=ExecutionStatus.CANCELLED.value,
                finished_at=finished_at,
                error=error,
            )
        )
