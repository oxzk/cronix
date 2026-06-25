"""基础 Repository 类。"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """基础 Repository 类，提供通用数据访问方法。

    Attributes:
        session: SQLAlchemy 异步会话。
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化 Repository。

        Args:
            session: SQLAlchemy 异步会话。
        """
        self.session = session
