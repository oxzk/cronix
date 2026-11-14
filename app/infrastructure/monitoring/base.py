"""监控检查器基类与结果。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar


class MonitorStatus(IntEnum):
    UNKNOWN = 0
    UP = 1
    DOWN = 2


@dataclass(frozen=True)
class CheckResult:
    status: MonitorStatus
    error_code: str | None = None
    error_message: str | None = None


class BaseChecker(ABC):
    kind: ClassVar[str] = "base"

    @abstractmethod
    async def check(self, config: dict, timeout: int) -> CheckResult:
        """执行一次连通性检查, 业务异常由检查器自行映射为 DOWN。"""
