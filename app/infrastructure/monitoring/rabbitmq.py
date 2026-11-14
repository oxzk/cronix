"""RabbitMQ 检查器: 使用连接 URL 建立连接并开 channel。"""

from __future__ import annotations

import aio_pika

from app.infrastructure.monitoring.base import BaseChecker, CheckResult, MonitorStatus


class RabbitmqChecker(BaseChecker):
    kind = "rabbitmq"

    async def check(self, config: dict, timeout: int) -> CheckResult:
        connection = None
        try:
            connection = await aio_pika.connect(config["url"], timeout=timeout)
            channel = await connection.channel()
            await channel.close()
            return CheckResult(MonitorStatus.UP)
        except Exception as exc:
            return CheckResult(
                MonitorStatus.DOWN, "driver_error", f"{type(exc).__name__}: {exc}"
            )
        finally:
            if connection is not None:
                await connection.close()
