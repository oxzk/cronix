"""
SQLAlchemy 异步数据库连接模块。
"""

from __future__ import annotations

import ssl
from collections.abc import AsyncGenerator

import aiomysql
from sqlalchemy import TIMESTAMP, event, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator
from datetime import datetime, timezone
from pathlib import Path
from importlib import import_module

from cronix.core.config import settings
from cronix.utils.logger import logger


class UTCDateTime(TypeDecorator[datetime]):
    """统一按 UTC 读写的数据库时间类型。"""

    impl = TIMESTAMP
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: object) -> datetime | None:
        """写入数据库前统一转换为 UTC naive 时间。"""
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: object) -> datetime | None:
        """从数据库读取后统一补充 UTC 时区信息。"""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class Base(AsyncAttrs, DeclarativeBase):
    """ORM 声明式模型基类。"""


class Database:
    """
    SQLAlchemy 异步连接管理器。

    以类级状态保存 engine 与 session factory，便于 FastAPI 依赖复用连接池。
    """

    def __init__(self) -> None:
        """初始化数据库连接状态。"""
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """初始化数据库连接并创建缺失表。"""
        connect_args: dict[str, object] = {
            "charset": "utf8mb4",
            "cursorclass": aiomysql.DictCursor,
        }
        if settings.database_ssl:
            connect_args["ssl"] = self._create_ssl_context()

        self._engine = create_async_engine(
            self._normalize_database_url(settings.database_url),
            connect_args=connect_args,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            echo=bool(settings.app_debug),
        )
        event.listen(self._engine.sync_engine, "connect", self._set_utc_timezone)
        self._session_factory = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
            autoflush=False,
        )
        await self.create_tables()

    def _set_utc_timezone(self, dbapi_connection: object, connection_record: object) -> None:
        """将数据库连接会话时区固定为 UTC。"""
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SET time_zone = '+00:00'")
        finally:
            cursor.close()

    async def create_tables(self) -> None:
        """创建当前应用需要的表。"""
        if self._engine is None:
            raise RuntimeError("数据库尚未初始化")

        self._load_model_metadata()

        async with self._engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    def _normalize_database_url(self, database_url: str) -> str:
        """
        规范化数据库连接地址。

        Args:
            database_url: 原始数据库连接地址。

        Returns:
            SQLAlchemy 异步数据库连接地址。
        """
        normalized = database_url.strip()
        for sync_scheme in ("mysql://", "mysql+pymysql://", "mysql+mysqldb://"):
            if normalized.startswith(sync_scheme):
                return normalized.replace(sync_scheme, "mysql+aiomysql://", 1)
        return normalized

    def _create_ssl_context(self) -> ssl.SSLContext:
        """
        创建数据库 SSL 上下文。

        Returns:
            SSL 上下文。
        """
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    def _load_model_metadata(self) -> None:
        """
        加载 ORM 模型元数据。

        SQLAlchemy 只有在模型类被导入后才会把表注册到 Base.metadata,
        create_all 只能创建已经注册的表。
        """
        models_dir = Path(__file__).parent.parent / "models"
        for model_file in models_dir.glob("*.py"):
            if model_file.name.startswith("_"):
                continue
            module_name = f"cronix.models.{model_file.stem}"
            try:
                import_module(module_name)
            except Exception as exc:
                logger.warning("加载模型模块 %s 失败: %s", module_name, exc)

    async def close(self) -> None:
        """关闭数据库连接池。"""
        if self._engine is not None:
            await self._engine.dispose()
        self._engine = None
        self._session_factory = None

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取带事务的异步数据库会话。

        Raises:
            RuntimeError: 数据库尚未初始化。
        """
        if self._session_factory is None:
            raise RuntimeError("数据库尚未初始化")
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as exc:
                await session.rollback()
                logger.exception("数据库事务回滚, 已回滚当前请求事务: %s", exc)
                raise
            finally:
                await session.close()

    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        获取异步数据库会话工厂。

        Returns:
            异步数据库会话工厂。

        Raises:
            RuntimeError: 数据库尚未初始化。
        """
        if self._session_factory is None:
            raise RuntimeError("数据库尚未初始化")
        return self._session_factory


db = Database()
