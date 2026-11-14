"""检查器注册表。"""

from __future__ import annotations

from app.core.exceptions import ValidationError
from app.infrastructure.monitoring.base import BaseChecker
from app.infrastructure.monitoring.http import HttpChecker
from app.infrastructure.monitoring.mongo import MongoChecker
from app.infrastructure.monitoring.mysql import MysqlChecker
from app.infrastructure.monitoring.postgresql import PostgresqlChecker
from app.infrastructure.monitoring.rabbitmq import RabbitmqChecker
from app.infrastructure.monitoring.redis import RedisChecker

_CHECKERS: dict[str, BaseChecker] = {
    checker.kind: checker
    for checker in (
        HttpChecker(),
        RedisChecker(),
        MysqlChecker(),
        PostgresqlChecker(),
        MongoChecker(),
        RabbitmqChecker(),
    )
}


def get_checker(kind: str) -> BaseChecker:
    checker = _CHECKERS.get(kind)
    if checker is None:
        raise ValidationError(f"不支持的监控类型: {kind}")
    return checker
