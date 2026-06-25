"""任务数据访问层。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cronix.models import Task
from cronix.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """任务数据访问层。

    负责任务表的查询、CRUD 操作和数据映射。
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化任务 Repository。

        Args:
            session: SQLAlchemy 异步会话。
        """
        super().__init__(session)

    async def get_by_id(self, task_id: int) -> Task | None:
        """根据 ID 查询任务。

        Args:
            task_id: 任务 ID。

        Returns:
            任务实例，不存在时返回 None。
        """
        result = await self.session.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Task], int]:
        """分页查询任务列表。

        Args:
            page: 页码（从 1 开始）。
            page_size: 每页大小。
            name: 任务名称过滤（模糊匹配）。
            is_active: 任务状态过滤。

        Returns:
            (任务列表, 总数) 元组。
        """
        query = select(Task)

        # 应用过滤条件
        if name is not None:
            escaped = name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            query = query.where(Task.name.ilike(f"%{escaped}%", escape="\\"))

        if is_active is not None:
            query = query.where(Task.is_active == is_active)

        # 查询总数
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * page_size
        paginated_query = query.order_by(Task.id.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(paginated_query)
        tasks = list(result.scalars().all())

        return tasks, total

    async def create(self, task: Task) -> Task:
        """创建任务。

        Args:
            task: 任务实例。

        Returns:
            已保存的任务实例。
        """
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def update(self, task: Task) -> Task:
        """更新任务。

        Args:
            task: 任务实例。

        Returns:
            更新后的任务实例。
        """
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        """删除任务。

        Args:
            task: 任务实例。
        """
        await self.session.delete(task)
        await self.session.flush()

    async def get_all_active(self) -> list[Task]:
        """查询所有激活的任务。

        Returns:
            激活的任务列表。
        """
        result = await self.session.execute(
            select(Task).where(Task.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get_by_ids(self, task_ids: list[int]) -> list[Task]:
        """根据 ID 列表批量查询任务。

        Args:
            task_ids: 任务 ID 列表。

        Returns:
            任务列表。
        """
        if not task_ids:
            return []

        result = await self.session.execute(
            select(Task).where(Task.id.in_(task_ids))
        )
        return list(result.scalars().all())

    async def get_due_tasks(self, current_time: datetime) -> list[Task]:
        """查询已到达计划运行时间的激活任务。

        Args:
            current_time: 当前时间。

        Returns:
            已到达运行时间的激活任务列表。
        """
        result = await self.session.execute(
            select(Task).where(
                Task.is_active.is_(True),
                Task.next_run_time <= current_time,
            )
        )
        return list(result.scalars().all())

    async def get_active_without_next_run_time(self) -> list[Task]:
        """查询尚未计算下一次运行时间的激活任务。

        Returns:
            缺少 next_run_time 的激活任务列表。
        """
        result = await self.session.execute(
            select(Task).where(
                Task.is_active.is_(True),
                Task.next_run_time.is_(None),
            )
        )
        return list(result.scalars().all())

    async def get_counts(self) -> tuple[int, int]:
        """统计任务总数与激活任务数。

        Returns:
            (任务总数, 激活任务数) 元组。
        """
        result = await self.session.execute(
            select(
                func.count(Task.id).label("total"),
                func.count(case((Task.is_active.is_(True), 1))).label("active"),
            )
        )
        row = result.one()
        return row.total or 0, row.active or 0
