from fastapi import APIRouter, Request
from sqlalchemy import select, func
from src.utils import success_response, error_response
from src.models.schemas import TaskStatsResponse
from src.models.tables import Task, TaskExecution
from src.databases import db


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/tasks/summary")
async def get_tasks_stats(request: Request):
    """Get statistics about all tasks and executions"""
    try:
        async for session in db.get_session():
            # Get total tasks count
            total_tasks_result = await session.execute(select(func.count(Task.id)))
            total_tasks = total_tasks_result.scalar() or 0

            # Get active tasks count
            active_tasks_result = await session.execute(
                select(func.count(Task.id)).where(Task.is_active == True)
            )
            active_tasks = active_tasks_result.scalar() or 0

            # Get inactive tasks count
            inactive_tasks = total_tasks - active_tasks

            # Get total executions count
            total_executions_result = await session.execute(
                select(func.count(TaskExecution.id))
            )
            total_executions = total_executions_result.scalar() or 0

            # Get success executions count
            success_executions_result = await session.execute(
                select(func.count(TaskExecution.id)).where(
                    TaskExecution.status == "success"
                )
            )
            success_executions = success_executions_result.scalar() or 0

            # Get failed executions count
            failed_executions_result = await session.execute(
                select(func.count(TaskExecution.id)).where(
                    TaskExecution.status == "failed"
                )
            )
            failed_executions = failed_executions_result.scalar() or 0

            # Get running executions count
            running_executions_result = await session.execute(
                select(func.count(TaskExecution.id)).where(
                    TaskExecution.status == "running"
                )
            )
            running_executions = running_executions_result.scalar() or 0

            # Calculate success rate
            success_rate = None
            if total_executions > 0:
                success_rate = round((success_executions / total_executions) * 100, 2)

            stats = TaskStatsResponse(
                total_tasks=total_tasks,
                active_tasks=active_tasks,
                inactive_tasks=inactive_tasks,
                total_executions=total_executions,
                success_executions=success_executions,
                failed_executions=failed_executions,
                running_executions=running_executions,
                success_rate=success_rate,
            )

            return success_response(data=stats)

    except Exception as e:
        return error_response(message=str(e), code=500)
