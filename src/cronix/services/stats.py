"""统计业务服务。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from cronix.repositories import ExecutionRepository, TaskRepository
from cronix.schemas import TaskStatsResponse


class StatsService:
    """任务和执行记录统计服务。

    数据访问委托给 TaskRepository 与 ExecutionRepository。
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化统计服务。

        Args:
            session: SQLAlchemy 异步会话，由外层依赖注入并管理事务边界。
        """
        self._task_repo = TaskRepository(session)
        self._execution_repo = ExecutionRepository(session)

    async def get_tasks_stats(self) -> TaskStatsResponse:
        """统计任务和执行记录概览。

        Returns:
            任务和执行记录统计数据。
        """
        total_tasks, active_tasks = await self._task_repo.get_counts()
        inactive_tasks = total_tasks - active_tasks

        status_counts = await self._execution_repo.count_group_by_status()

        total_executions = sum(status_counts.values())
        success_executions = status_counts.get("success", 0)
        failed_executions = status_counts.get("failed", 0)
        running_executions = status_counts.get("running", 0)
        success_rate = None
        if total_executions > 0:
            success_rate = round((success_executions / total_executions) * 100, 2)

        return TaskStatsResponse(
            total_tasks=total_tasks,
            active_tasks=active_tasks,
            inactive_tasks=inactive_tasks,
            total_executions=total_executions,
            success_executions=success_executions,
            failed_executions=failed_executions,
            running_executions=running_executions,
            success_rate=success_rate,
        )
