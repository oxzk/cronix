from fastapi import APIRouter, Depends, Request, Query
from typing import List, Optional
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from croniter import croniter
import json
from src.models import (
    TaskSchema,
    TaskResponse,
    TaskExecutionResponse,
    Task,
    TaskExecution,
    User,
    Notification,
)
from src.databases import db
from src.utils import success_response, error_response

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _calculate_next_run_time(cron_expression: str) -> datetime:
    """Calculate next run time based on cron expression"""
    try:
        cron = croniter(cron_expression, datetime.now(timezone.utc))
        return cron.get_next(datetime)
    except Exception:
        return None


async def _build_task_response(task: Task, session: Session) -> TaskResponse:
    """Helper function to build TaskResponse"""
    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        cron_expression=task.cron_expression,
        command=task.command,
        is_active=task.is_active,
        timeout=task.timeout,
        retry_count=task.retry_count,
        retry_interval=task.retry_interval,
        notification_ids=task.notification_ids,
        notify_strategy=task.notify_strategy,
        next_run_time=task.next_run_time,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("")
async def list_tasks(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    page_size: int = Query(20, ge=1, le=200, description="Items per page"),
    name: Optional[str] = Query(
        None, description="Filter by task name (partial match)"
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by task status (true=active, false=inactive)"
    ),
) -> dict:
    """Get task list with pagination support"""
    async for session in db.get_session():
        # Build query
        query = select(Task)

        # Apply filter conditions
        if name is not None:
            query = query.where(Task.name.ilike(f"%{name}%"))

        if is_active is not None:
            query = query.where(Task.is_active == is_active)

        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # Calculate pagination
        offset = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size

        # Query paginated data
        result = await session.execute(query.offset(offset).limit(page_size))
        tasks = result.scalars().all()

        items = [await _build_task_response(t, session) for t in tasks]

        return success_response(
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        )


@router.post("")
async def create_task(task_data: TaskSchema, request: Request) -> dict:
    async for session in db.get_session():
        # Verify notification configurations exist
        if task_data.notification_ids:
            result = await session.execute(
                select(Notification).where(
                    Notification.id.in_(task_data.notification_ids)
                )
            )
            notifs = result.scalars().all()
            if len(notifs) != len(task_data.notification_ids):
                return error_response(
                    message="One or more notifications not found", code=400
                )

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
            next_run_time=_calculate_next_run_time(task_data.cron_expression),
        )
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)

        task_response = await _build_task_response(new_task, session)
        return success_response(data=task_response, message="Task created successfully")


@router.get("/{task_id}")
async def get_task(task_id: int, request: Request) -> dict:
    async for session in db.get_session():
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return error_response(message="Task not found", code=404)

        task_response = await _build_task_response(task, session)
        return success_response(data=task_response)


@router.put("/{task_id}")
async def update_task(task_id: int, task_data: TaskSchema, request: Request) -> dict:
    async for session in db.get_session():
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return error_response(message="Task not found", code=404)

        # Use exclude_unset=True to only update provided fields
        update_data = task_data.model_dump(
            exclude_unset=True, exclude={"notification_ids"}
        )
        for key, value in update_data.items():
            setattr(task, key, value)

        # Update next_run_time if cron_expression changed
        if "cron_expression" in update_data:
            task.next_run_time = _calculate_next_run_time(task_data.cron_expression)

        # Update notification_ids if provided
        if task_data.notification_ids is not None:
            # Verify notification configurations exist
            if task_data.notification_ids:
                result = await session.execute(
                    select(Notification).where(
                        Notification.id.in_(task_data.notification_ids)
                    )
                )
                notifs = result.scalars().all()
                if len(notifs) != len(task_data.notification_ids):
                    return error_response(
                        message="One or more notifications not found", code=400
                    )

            task.notification_ids = task_data.notification_ids

        await session.commit()
        await session.refresh(task)

        task_response = await _build_task_response(task, session)
        return success_response(data=task_response, message="Task updated successfully")


@router.delete("/{task_id}")
async def delete_task(task_id: int, request: Request) -> dict:
    async for session in db.get_session():
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return error_response(message="Task not found", code=404)

        await session.delete(task)
        await session.commit()
        return success_response(message="Task deleted successfully")


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: int, request: Request) -> dict:
    """Cancel a running task"""
    from src.services.scheduler import scheduler

    async for session in db.get_session():
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return error_response(message="Task not found", code=404)

    cancelled = await scheduler.cancel_task(task_id)
    if cancelled:
        return success_response(message=f"Task {task_id} cancelled successfully")
    else:
        return error_response(message="Task is not currently running", code=400)


@router.get("/running/list")
async def list_running_tasks(request: Request) -> dict:
    """Get all running tasks"""
    from src.services.scheduler import scheduler

    running_tasks = scheduler.get_running_tasks()
    return success_response(data=running_tasks)


@router.post("/{task_id}/execute")
async def execute_task(task_id: int, request: Request) -> dict:
    """Manually execute a task"""
    from src.services.scheduler import scheduler

    async for session in db.get_session():
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return error_response(message="Task not found", code=404)

    # Trigger manual execution
    await scheduler.execute_task_now(task_id)
    return success_response(message=f"Task {task_id} execution triggered successfully")
