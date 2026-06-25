"""数据访问层（Repository Layer）。

Repository 层负责封装数据库访问逻辑，提供清晰的数据访问接口。
Service 层通过 Repository 访问数据，专注于业务逻辑的实现。

职责划分：
- Repository：数据查询、CRUD 操作、ORM 映射
- Service：业务逻辑、数据校验、业务编排

使用示例：
    ```python
    class TaskService:
        def __init__(self, session: AsyncSession, scheduler: SchedulerService):
            self.repo = TaskRepository(session)
            self.scheduler = scheduler

        async def get_task(self, task_id: int) -> TaskResponse:
            task = await self.repo.get_by_id(task_id)
            if not task:
                raise NotFoundError("Task not found")
            return TaskResponse.model_validate(task)
    ```
"""

from __future__ import annotations

from cronix.repositories.base import BaseRepository
from cronix.repositories.execution_repository import ExecutionRepository
from cronix.repositories.notification_repository import NotificationRepository
from cronix.repositories.task_repository import TaskRepository
from cronix.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "ExecutionRepository",
    "NotificationRepository",
    "TaskRepository",
    "UserRepository",
]
