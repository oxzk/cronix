"""MongoDB 检查器: 使用连接 URL 执行 admin ping。"""

from __future__ import annotations

from pymongo import AsyncMongoClient

from app.infrastructure.monitoring.base import BaseChecker, CheckResult, MonitorStatus


class MongoChecker(BaseChecker):
    kind = "mongo"

    async def check(self, config: dict, timeout: int) -> CheckResult:
        client = None
        try:
            client = AsyncMongoClient(
                config["url"],
                serverSelectionTimeoutMS=timeout * 1000,
                connectTimeoutMS=timeout * 1000,
            )
            await client.admin.command("ping")
            return CheckResult(MonitorStatus.UP)
        except Exception as exc:
            return CheckResult(
                MonitorStatus.DOWN, "driver_error", f"{type(exc).__name__}: {exc}"
            )
        finally:
            if client is not None:
                await client.close()
