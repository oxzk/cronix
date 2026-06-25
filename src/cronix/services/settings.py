"""设置业务服务。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from cronix.core.exceptions import AppError, NotFoundError
from cronix.core.security import Security
from cronix.models import Notification, User
from cronix.repositories import NotificationRepository, UserRepository
from cronix.schemas import (
    NotificationSchema,
    SettingsUserCreateSchema,
    SettingsUserUpdateSchema,
)


class SettingsService:
    """系统设置业务服务。

    数据访问委托给 UserRepository 与 NotificationRepository。
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化设置服务。

        Args:
            session: SQLAlchemy 异步会话，由外层依赖注入并管理事务边界。
        """
        self._repo = NotificationRepository(session)
        self._user_repo = UserRepository(session)
        self._session = session

    async def list_users(self) -> list[User]:
        """查询系统用户列表。

        Returns:
            用户列表。
        """
        return await self._user_repo.list_all()

    async def create_user(self, user_data: SettingsUserCreateSchema) -> User:
        """创建系统用户。

        Args:
            user_data: 用户创建数据。

        Returns:
            已创建的用户。

        Raises:
            AppError: 用户名已存在。
        """
        if await self._user_repo.exists_by_username(user_data.username):
            raise AppError("User with this username already exists", status_code=400)

        return await self._user_repo.create(
            User(
                username=user_data.username,
                password=Security.hash_password(user_data.password),
            )
        )

    async def update_user(
        self,
        user_id: int,
        user_data: SettingsUserUpdateSchema,
    ) -> User:
        """更新系统用户。

        Args:
            user_id: 用户 ID。
            user_data: 用户更新数据。

        Returns:
            更新后的用户。

        Raises:
            NotFoundError: 用户不存在。
            AppError: 用户名已存在或未提供更新内容。
        """
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        if user_data.username is None and user_data.password is None:
            raise AppError("No user setting changes provided", status_code=400)

        if user_data.username is not None and user_data.username != user.username:
            if await self._user_repo.exists_by_username(
                user_data.username,
                exclude_id=user_id,
            ):
                raise AppError(
                    "User with this username already exists",
                    status_code=400,
                )
            user.username = user_data.username

        if user_data.password is not None:
            user.password = Security.hash_password(user_data.password)

        return await self._user_repo.update(user)

    async def delete_user(self, user_id: int, current_user_id: int) -> None:
        """删除系统用户。

        Args:
            user_id: 待删除用户 ID。
            current_user_id: 当前登录用户 ID。

        Raises:
            NotFoundError: 用户不存在。
            AppError: 删除当前用户或最后一个用户。
        """
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        if user.id == current_user_id:
            raise AppError("Current user cannot be deleted", status_code=400)

        if await self._user_repo.count_all() <= 1:
            raise AppError("At least one user must remain", status_code=400)

        await self._user_repo.delete(user)

    async def list_notifications(self) -> list[Notification]:
        """查询所有通知配置。

        Returns:
            通知配置列表。
        """
        return await self._repo.list_all()

    async def create_notification(
        self,
        notification_data: NotificationSchema,
    ) -> Notification:
        """创建通知配置。

        Args:
            notification_data: 通知配置数据。

        Returns:
            已创建的通知配置。

        Raises:
            AppError: 通知类型已存在。
        """
        if await self._repo.exists_by_type(notification_data.notify_type.value):
            raise AppError(
                message="Notification with this type already exists",
                status_code=400,
            )

        return await self._repo.create(
            Notification(
                notify_type=notification_data.notify_type.value,
                config=notification_data.config,
            )
        )

    async def update_notification(
        self,
        notification_id: int,
        notification_data: NotificationSchema,
    ) -> Notification:
        """更新通知配置。

        Args:
            notification_id: 通知配置 ID。
            notification_data: 更新数据。

        Returns:
            更新后的通知配置。

        Raises:
            NotFoundError: 通知配置不存在。
            AppError: 通知类型已存在。
        """
        notification = await self._repo.get_by_id(notification_id)
        if not notification:
            raise NotFoundError("Notification not found")

        if notification_data.notify_type.value != notification.notify_type:
            if await self._repo.exists_by_type(
                notification_data.notify_type.value, exclude_id=notification_id
            ):
                raise AppError(
                    message="Notification with this type already exists",
                    status_code=400,
                )

        notification.notify_type = notification_data.notify_type.value
        notification.config = notification_data.config

        return await self._repo.update(notification)
