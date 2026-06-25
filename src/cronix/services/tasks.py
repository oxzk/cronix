"""任务业务服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from croniter import croniter
from sqlalchemy.ext.asyncio import AsyncSession

from cronix.core.exceptions import AppError, NotFoundError
from cronix.models import Task
from cronix.utils.datetime import utc_now
from cronix.repositories import NotificationRepository, TaskRepository
from cronix.schemas import PaginatedResponse, TaskResponse, TaskSchema
from cronix.services.scheduler import SchedulerService


class TaskService:
    """任务增删改查与手动调度业务服务。

    职责：
    - 任务的业务逻辑处理（校验、计算、编排）
    - 调度器集成
    - 通知配置校验

    数据访问委托给 TaskRepository。
    """

    def __init__(self, session: AsyncSession, scheduler_service: SchedulerService) -> None:
        """初始化任务服务依赖。

        Args:
            session: 数据库会话。
            scheduler_service: 调度服务。
        """
        self._repo = TaskRepository(session)
        self._notification_repo = NotificationRepository(session)
        self._session = session
        self._scheduler_service = scheduler_service

    def _calculate_next_run_time(self, cron_expression: str) -> datetime | None:
        """计算任务下一次运行时间。"""
        try:
            cron = croniter(cron_expression, utc_now())
            return cron.get_next(datetime)
        except Exception:
            return None

    async def _assert_notifications_exist(self, notification_ids: list[int] | None) -> None:
        """校验通知配置是否全部存在。

        Args:
            notification_ids: 通知配置 ID 列表。

        Raises:
            AppError: 当部分或全部通知配置不存在时。
        """
        if not notification_ids:
            return

        if not await self._notification_repo.validate_ids_exist(notification_ids):
            raise AppError(
                message="One or more notifications not found",
                status_code=400,
                data={"notification_ids": notification_ids},
            )

    async def _get_task_or_raise(self, task_id: int) -> Task:
        """获取任务，不存在时抛出业务异常。

        Args:
            task_id: 任务 ID。

        Returns:
            任务实例。

        Raises:
            NotFoundError: 任务不存在时。
        """
        task = await self._repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task not found")
        return task

    async def list_tasks(
        self,
        page: int,
        page_size: int,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> PaginatedResponse[TaskResponse]:
        """分页查询任务列表。

        Args:
            page: 页码（从 1 开始）。
            page_size: 每页大小。
            name: 任务名称过滤（模糊匹配）。
            is_active: 任务状态过滤。

        Returns:
            分页响应数据。
        """
        tasks, total = await self._repo.list_paginated(page, page_size, name, is_active)

        return PaginatedResponse(
            items=tasks,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_task(self, task_data: TaskSchema) -> Task:
        """创建任务。

        Args:
            task_data: 任务创建数据。

        Returns:
            创建后的任务响应。
        """
        await self._assert_notifications_exist(task_data.notification_ids)

        new_task = Task(
            name=task_data.name,
            description=task_data.description,
            cron_expression=task_data.cron_expression,
            command=task_data.command,
            is_active=task_data.is_active,
            timeout=task_data.timeout,
            retry_count=task_data.retry_count,
            retry_interval=task_data.retry_interval,
            notification_ids=task_data.notification_ids,
            notify_strategy=task_data.notify_strategy,
            next_run_time=self._calculate_next_run_time(task_data.cron_expression),
        )

        created_task = await self._repo.create(new_task)

        return created_task

    async def get_task(self, task_id: int) -> Task:
        """查询单个任务。

        Args:
            task_id: 任务 ID。

        Returns:
            任务响应数据。

        Raises:
            NotFoundError: 任务不存在时。
        """
        task = await self._repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task not found")
        return task

    async def update_task(self, task_id: int, task_data: TaskSchema) -> Task:
        """更新任务。

        Args:
            task_id: 任务 ID。
            task_data: 任务更新数据。

        Returns:
            更新后的任务响应。

        Raises:
            NotFoundError: 任务不存在时。
        """
        task = await self._repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task not found")

        update_data = task_data.model_dump(exclude_unset=True, exclude={"notification_ids"})
        for key, value in update_data.items():
            setattr(task, key, value)

        if "cron_expression" in update_data:
            task.next_run_time = self._calculate_next_run_time(task_data.cron_expression)

        if task_data.notification_ids is not None:
            await self._assert_notifications_exist(task_data.notification_ids)
            task.notification_ids = task_data.notification_ids

        updated_task = await self._repo.update(task)

        return updated_task

    async def delete_task(self, task_id: int) -> None:
        """删除任务。

        Args:
            task_id: 任务 ID。

        Raises:
            NotFoundError: 任务不存在时。
        """
        task = await self._repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task not found")

        await self._repo.delete(task)

    async def cancel_task(self, task_id: int) -> None:
        """取消运行中的任务。

        Args:
            task_id: 任务 ID。

        Raises:
            NotFoundError: 任务不存在时。
            AppError: 任务当前未运行时。
        """
        task = await self._repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task not found")

        cancelled = await self._scheduler_service.cancel_task(task_id)
        if not cancelled:
            raise AppError("Task is not currently running", status_code=400)

    def list_running_tasks(self) -> list[int]:
        """获取正在运行的任务 ID 列表。"""
        return self._scheduler_service.get_running_tasks()

    async def execute_task(self, task_id: int) -> None:
        """手动触发任务执行。

        Args:
            task_id: 任务 ID。

        Raises:
            NotFoundError: 任务不存在时。
        """
        task = await self._repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task not found")

        await self._scheduler_service.execute_task_now(task_id)
