"""数据库引擎: 单实例语义由 pg advisory lock 保证, 时区强制 UTC。"""

from __future__ import annotations

import asyncio
import ssl

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.config import DatabaseSettings
from app.core.exceptions import RuntimeInitializationError

ADVISORY_LOCK_ID = 19870315  # cronix 专用锁 id


class Database:
    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker | None = None
        self._lock_connection = None
        self._guard_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        connect_args: dict = {"server_settings": {"timezone": "UTC"}}
        if self._settings.ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = context
        self._engine = create_async_engine(
            self._settings.url, pool_pre_ping=True, connect_args=connect_args
        )
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

        # 持有一条长连接持有 advisory lock, 保证同库只有一个 cronix 实例
        self._lock_connection = await self._engine.connect()
        acquired = (
            await self._lock_connection.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": ADVISORY_LOCK_ID}
            )
        ).scalar()
        if not acquired:
            await self._lock_connection.close()
            self._lock_connection = None
            raise RuntimeInitializationError("另一个 cronix 实例正在运行(advisory lock 获取失败)")
        self._guard_task = asyncio.create_task(self._guard_lock(), name="cronix-lock-guard")
        logger.info("数据库初始化完成")

    async def _guard_lock(self) -> None:
        """定期探测 advisory lock 连接, 断连时尝试重连并重新加锁。"""
        while True:
            await asyncio.sleep(30)
            if self._lock_connection is None:
                return
            try:
                await self._lock_connection.execute(text("SELECT 1"))
            except Exception:
                logger.critical("advisory lock 连接异常, 尝试重连并重新获取")
                try:
                    await self._lock_connection.close()
                    self._lock_connection = await self._engine.connect()  # type: ignore[union-attr]
                    acquired = (
                        await self._lock_connection.execute(
                            text("SELECT pg_try_advisory_lock(:lock_id)"),
                            {"lock_id": ADVISORY_LOCK_ID},
                        )
                    ).scalar()
                    if not acquired:
                        logger.critical("重新获取 advisory lock 失败, 可能存在第二个实例")
                except Exception:
                    logger.exception("advisory lock 恢复失败")

    @property
    def session_factory(self) -> async_sessionmaker:
        if self._session_factory is None:
            raise RuntimeInitializationError("数据库尚未初始化")
        return self._session_factory

    async def close(self) -> None:
        if self._guard_task is not None:
            self._guard_task.cancel()
            await asyncio.gather(self._guard_task, return_exceptions=True)
            self._guard_task = None
        if self._lock_connection is not None:
            await self._lock_connection.close()
            self._lock_connection = None
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
