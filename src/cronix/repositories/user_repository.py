"""用户数据访问层。"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cronix.models import User
from cronix.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """用户数据访问层。

    负责用户表的查询、CRUD 操作和数据映射。
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化用户 Repository。

        Args:
            session: SQLAlchemy 异步会话。
        """
        super().__init__(session)

    async def get_by_id(self, user_id: int) -> User | None:
        """根据 ID 查询用户。

        Args:
            user_id: 用户 ID。

        Returns:
            用户实例，不存在时返回 None。
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """根据用户名查询用户。

        Args:
            username: 用户名。

        Returns:
            用户实例，不存在时返回 None。
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[User]:
        """查询所有用户。

        Returns:
            用户列表。
        """
        result = await self.session.execute(select(User).order_by(User.id.asc()))
        return list(result.scalars().all())

    async def count_all(self) -> int:
        """统计用户总数。

        Returns:
            用户总数。
        """
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar() or 0

    async def exists_by_username(
        self,
        username: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """检查用户名是否已存在。

        Args:
            username: 用户名。
            exclude_id: 排除的用户 ID（用于更新时检查）。

        Returns:
            True 表示存在，False 表示不存在。
        """
        query = select(User.id).where(User.username == username)
        if exclude_id is not None:
            query = query.where(User.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def create(self, user: User) -> User:
        """创建用户。

        Args:
            user: 用户实例。

        Returns:
            已保存的用户实例。
        """
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """更新用户。

        Args:
            user: 用户实例。

        Returns:
            更新后的用户实例。
        """
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """删除用户。

        Args:
            user: 用户实例。
        """
        await self.session.delete(user)
        await self.session.flush()
