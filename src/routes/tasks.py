from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, Session
import json
from src.models import (
    TaskSchema,
    TaskResponse,
    TaskExecutionResponse,
    Task,
    TaskExecution,
    User,
    Notification,
    NotificationResponse,
    NotifyType,
)
from src.databases import db

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _build_task_response(task: Task, session: Session) -> TaskResponse:
    """Helper function to build TaskResponse with notifications"""
    notifications = []
    if task.notification_ids:
        result = await session.execute(
            select(Notification).where(Notification.id.in_(task.notification_ids))
        )
        notifs = result.scalars().all()
        notifications = [
            NotificationResponse(
                id=n.id,
                notify_type=NotifyType(n.notify_type),
                config=n.config,
                created_at=n.created_at,
                updated_at=n.updated_at,
            )
            for n in notifs
        ]

    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        cron_expression=task.cron_expression,
        execution_type=task.execution_type,
        command=task.command,
        is_active=task.is_active,
        timeout=task.timeout,
        retry_count=task.retry_count,
        retry_interval=task.retry_interval,
        notifications=notifications if notifications else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(request: Request) -> List[TaskResponse]:
    async for session in db.get_session():
        result = await session.execute(select(Task))
        tasks = result.scalars().all()
        return [await _build_task_response(t, session) for t in tasks]


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskSchema, request: Request) -> TaskResponse:
    async for session in db.get_session():
        # 验证通知配置是否存在
        if task_data.notification_ids:
            result = await session.execute(
                select(Notification).where(
                    Notification.id.in_(task_data.notification_ids)
                )
            )
            notifs = result.scalars().all()
            if len(notifs) != len(task_data.notification_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more notifications not found",
                )

        new_task = Task(
            name=task_data.name,
            description=task_data.description,
            cron_expression=task_data.cron_expression,
            execution_type=task_data.execution_type.value,
            command=task_data.command,
            is_active=task_data.is_active,
            timeout=task_data.timeout,
            retry_count=task_data.retry_count,
            retry_interval=task_data.retry_interval,
            notification_ids=task_data.notification_ids,
        )
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)

        return await _build_task_response(new_task, session)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, request: Request) -> TaskResponse:
    async for session in db.get_session():
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return await _build_task_response(task, session)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int, task_data: TaskSchema, request: Request
) -> TaskResponse:
    async for session in db.get_session():
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 使用 exclude_unset=True 只更新提供的字段
        update_data = task_data.model_dump(
            exclude_unset=True, exclude={"notification_ids"}
        )
        for key, value in update_data.items():
            if key == "execution_type" and value:
                setattr(task, key, value.value)
            else:
                setattr(task, key, value)

        # 如果提供了 notification_ids，则更新
        if task_data.notification_ids is not None:
            # 验证通知配置是否存在
            if task_data.notification_ids:
                result = await session.execute(
                    select(Notification).where(
                        Notification.id.in_(task_data.notification_ids)
                    )
                )
                notifs = result.scalars().all()
                if len(notifs) != len(task_data.notification_ids):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="One or more notifications not found",
                    )

            task.notification_ids = task_data.notification_ids

        await session.commit()
        await session.refresh(task)

        return await _build_task_response(task, session)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, request: Request) -> None:
    async for session in db.get_session():
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        await session.delete(task)
        await session.commit()
        return None


@router.get("/{task_id}/executions", response_model=List[TaskExecutionResponse])
async def get_task_executions(
    task_id: int, request: Request
) -> List[TaskExecutionResponse]:
    async for session in db.get_session():
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        result = await session.execute(
            select(TaskExecution)
            .where(TaskExecution.task_id == task_id)
            .order_by(TaskExecution.started_at.desc())
            .limit(50)
        )
        executions = result.scalars().all()

        return [
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


@router.post("/{task_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_task(task_id: int, request: Request) -> dict:
    """取消正在运行的任务"""
    from src.services.scheduler import scheduler

    async for session in db.get_session():
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

    cancelled = await scheduler.cancel_task(task_id)
    if cancelled:
        return {"message": f"Task {task_id} cancelled successfully"}
    else:
        raise HTTPException(status_code=400, detail="Task is not currently running")


@router.get("/running/list", response_model=List[int])
async def list_running_tasks(request: Request) -> List[int]:
    """获取所有正在运行的任务"""
    from src.services.scheduler import scheduler

    return scheduler.get_running_tasks()
