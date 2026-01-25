from fastapi import APIRouter, Depends, Request, Query
from typing import List, Optional
from sqlalchemy import select, func
from src.models import (
    TaskExecutionResponse,
    TaskExecutionDetailResponse,
    TaskExecution,
    Task,
    ExecutionStatus,
    NotificationResponse,
    Notification,
    NotifyType,
    TaskResponse,
)
from src.databases import db
from src.utils import success_response, error_response

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("")
async def list_executions(
    request: Request,
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    status: Optional[ExecutionStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    page_size: int = Query(20, ge=1, le=200, description="Items per page"),
) -> dict:
    """Get task execution history with multi-condition filtering and pagination support"""
    async for session in db.get_session():
        # Build query
        query = select(TaskExecution)

        # Apply filter conditions
        if task_id is not None:
            query = query.where(TaskExecution.task_id == task_id)

        if status is not None:
            query = query.where(TaskExecution.status == status.value)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # Calculate pagination
        offset = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size

        # Sort and paginate
        query = (
            query.order_by(TaskExecution.started_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(query)
        executions = result.scalars().all()

        # Get all unique task IDs
        task_ids = list(set(e.task_id for e in executions))

        # Fetch all related tasks in one query
        tasks_result = await session.execute(select(Task).where(Task.id.in_(task_ids)))
        tasks = {task.id: task for task in tasks_result.scalars().all()}

        # Build response with task information
        items = []
        for e in executions:
            task = tasks.get(e.task_id)
            task_response = None
            if task:
                task_response = TaskResponse(
                    id=task.id,
                    name=task.name,
                    description=task.description,
                    cron_expression=task.cron_expression,
                    command=task.command,
                    is_active=task.is_active,
                    timeout=task.timeout,
                    retry_count=task.retry_count,
                    retry_interval=task.retry_interval,
                    next_run_time=task.next_run_time,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                )

            items.append(
                TaskExecutionDetailResponse(
                    id=e.id,
                    task_id=e.task_id,
                    task=task_response,
                    started_at=e.started_at,
                    finished_at=e.finished_at,
                    status=e.status,
                    output=None,  # Don't include output in list view
                    error=None,  # Don't include error in list view
                    retry_attempt=e.retry_attempt,
                    duration=e.duration,
                )
            )

        return success_response(
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        )


@router.get("/{execution_id}")
async def get_execution(execution_id: int, request: Request) -> dict:
    """Get single execution record details (including associated task information)"""
    async for session in db.get_session():
        result = await session.execute(
            select(TaskExecution).where(TaskExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        if not execution:
            return error_response(message="Execution not found", code=404)

        # Get associated task information
        task_result = await session.execute(
            select(Task).where(Task.id == execution.task_id)
        )
        task = task_result.scalar_one_or_none()

        task_response = None
        if task:
            task_response = TaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                cron_expression=task.cron_expression,
                command=task.command,
                is_active=task.is_active,
                timeout=task.timeout,
                retry_count=task.retry_count,
                retry_interval=task.retry_interval,
                next_run_time=task.next_run_time,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )

        execution_detail = TaskExecutionDetailResponse(
            id=execution.id,
            task_id=execution.task_id,
            task=task_response,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            status=execution.status,
            output=execution.output,
            error=execution.error,
            retry_attempt=execution.retry_attempt,
            duration=execution.duration,
        )

        return success_response(data=execution_detail)
