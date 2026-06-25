"""设置路由。"""

from __future__ import annotations

from fastapi import APIRouter

from cronix.core.dependencies import CurrentUserDep, SettingsServiceDep
from cronix.schemas import (
    APIResponse,
    NotificationResponse,
    NotificationSchema,
    SettingsUserCreateSchema,
    SettingsUserResponse,
    SettingsUserUpdateSchema,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/users", response_model=APIResponse[list[SettingsUserResponse]])
async def list_users(service: SettingsServiceDep):
    """查询系统用户列表。"""
    data = await service.list_users()
    return APIResponse.ok(data)


@router.post("/users", response_model=APIResponse[SettingsUserResponse])
async def create_user(
    user_data: SettingsUserCreateSchema,
    service: SettingsServiceDep,
):
    """创建系统用户。"""
    data = await service.create_user(user_data)
    return APIResponse.ok(data, "User created successfully")


@router.put("/users/{user_id}", response_model=APIResponse[SettingsUserResponse])
async def update_user(
    user_id: int,
    user_data: SettingsUserUpdateSchema,
    service: SettingsServiceDep,
):
    """更新系统用户。"""
    data = await service.update_user(user_id, user_data)
    return APIResponse.ok(data, "User updated successfully")


@router.delete("/users/{user_id}", response_model=APIResponse[None])
async def delete_user(
    user_id: int,
    current_user: CurrentUserDep,
    service: SettingsServiceDep,
):
    """删除系统用户。"""
    await service.delete_user(user_id, current_user.id)
    return APIResponse.ok(None, "User deleted successfully")


@router.get("/notifications", response_model=APIResponse[list[NotificationResponse]])
async def list_notifications(service: SettingsServiceDep):
    """查询通知配置列表。"""
    data = await service.list_notifications()
    return APIResponse.ok(data)


@router.post("/notifications", response_model=APIResponse[NotificationResponse])
async def create_notification(
    notification_data: NotificationSchema,
    service: SettingsServiceDep,
):
    """创建通知配置。"""
    data = await service.create_notification(notification_data)
    return APIResponse.ok(data, "Notification created successfully")


@router.put(
    "/notifications/{notification_id}",
    response_model=APIResponse[NotificationResponse],
)
async def update_notification(
    notification_id: int,
    notification_data: NotificationSchema,
    service: SettingsServiceDep,
):
    """更新通知配置。"""
    data = await service.update_notification(notification_id, notification_data)
    return APIResponse.ok(data, "Notification updated successfully")
