"""通知配置数据访问层。"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cronix.models import Notification
from cronix.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """通知配置数据访问层。

    负责通知配置表的查询、CRUD 操作和数据映射。
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化通知配置 Repository。

        Args:
            session: SQLAlchemy 异步会话。
        """
        super().__init__(session)

    async def get_by_id(self, notification_id: int) -> Notification | None:
        """根据 ID 查询通知配置。

        Args:
            notification_id: 通知配置 ID。

        Returns:
            通知配置实例，不存在时返回 None。
        """
        result = await self.session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def get_by_type(self, notify_type: str) -> Notification | None:
        """根据通知类型查询配置。

        Args:
            notify_type: 通知类型。

        Returns:
            通知配置实例，不存在时返回 None。
        """
        result = await self.session.execute(
            select(Notification).where(Notification.notify_type == notify_type)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, notification_ids: list[int]) -> list[Notification]:
        """根据 ID 列表批量查询通知配置。

        Args:
            notification_ids: 通知配置 ID 列表。

        Returns:
            通知配置列表。
        """
        if not notification_ids:
            return []

        result = await self.session.execute(
            select(Notification).where(Notification.id.in_(notification_ids))
        )
        return list(result.scalars().all())

    async def validate_ids_exist(self, notification_ids: list[int]) -> bool:
        """校验通知配置 ID 是否全部存在。

        Args:
            notification_ids: 通知配置 ID 列表。

        Returns:
            True 表示全部存在，False 表示部分或全部不存在。
        """
        if not notification_ids:
            return True

        notifications = await self.get_by_ids(notification_ids)
        return len(notifications) == len(notification_ids)

    async def list_all(self) -> list[Notification]:
        """查询所有通知配置。

        Returns:
            通知配置列表。
        """
        result = await self.session.execute(
            select(Notification).order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, notification: Notification) -> Notification:
        """创建通知配置。

        Args:
            notification: 通知配置实例。

        Returns:
            已保存的通知配置实例。
        """
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def update(self, notification: Notification) -> Notification:
        """更新通知配置。

        Args:
            notification: 通知配置实例。

        Returns:
            更新后的通知配置实例。
        """
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def delete(self, notification: Notification) -> None:
        """删除通知配置。

        Args:
            notification: 通知配置实例。
        """
        await self.session.delete(notification)
        await self.session.flush()

    async def exists_by_type(self, notify_type: str, exclude_id: Optional[int] = None) -> bool:
        """检查指定类型的通知配置是否存在。

        Args:
            notify_type: 通知类型。
            exclude_id: 排除的通知配置 ID（用于更新时检查）。

        Returns:
            True 表示存在，False 表示不存在。
        """
        query = select(Notification).where(Notification.notify_type == notify_type)

        if exclude_id is not None:
            query = query.where(Notification.id != exclude_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
