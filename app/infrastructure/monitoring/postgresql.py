"""PostgreSQL 检查器: 通过 SQLAlchemy 执行 SELECT 1。"""

from __future__ import annotations

import ssl

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.infrastructure.monitoring.base import BaseChecker, CheckResult, MonitorStatus


def _asyncpg_url(url: str) -> str:
    """参考 DatabaseSettings: 将 PostgreSQL URL 前缀统一为 asyncpg 驱动。"""
    if url.startswith(("postgresql://", "postgres://")):
        return "postgresql+asyncpg://" + url.split("://", 1)[1]
    return url


class PostgresqlChecker(BaseChecker):
    kind = "postgresql"

    async def check(self, config: dict, timeout: int) -> CheckResult:
        engine: AsyncEngine | None = None
        try:
            connect_args: dict[str, object] = {"timeout": timeout}
            if config.get("ssl"):
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                connect_args["ssl"] = context
            engine = create_async_engine(
                _asyncpg_url(config["url"]), connect_args=connect_args
            )
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return CheckResult(MonitorStatus.UP)
        except Exception as exc:
            return CheckResult(
                MonitorStatus.DOWN, "driver_error", f"{type(exc).__name__}: {exc}"
            )
        finally:
            if engine is not None:
                await engine.dispose()
