from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
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

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("/", response_model=dict)
async def list_executions(
    request: Request,
    task_id: Optional[int] = Query(None, description="按任务ID筛选"),
    status: Optional[ExecutionStatus] = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(20, ge=1, le=200, description="每页数量"),
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

        items = [
            TaskExecutionResponse(
                id=e.id,
                task_id=e.task_id,
                started_at=e.started_at,
                finished_at=e.finished_at,
                status=e.status,
                output=e.output,
                error=e.error,
                retry_attempt=e.retry_attempt,
            )
            for e in executions
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }


@router.get("/{execution_id}", response_model=TaskExecutionDetailResponse)
async def get_execution(
    execution_id: int, request: Request
) -> TaskExecutionDetailResponse:
    """Get single execution record details (including associated task information)"""
    async for session in db.get_session():
        result = await session.execute(
            select(TaskExecution).where(TaskExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found",
            )

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
                created_at=task.created_at,
                updated_at=task.updated_at,
            )

        return TaskExecutionDetailResponse(
            id=execution.id,
            task_id=execution.task_id,
            task=task_response,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            status=execution.status,
            output=execution.output,
            error=execution.error,
            retry_attempt=execution.retry_attempt,
        )
