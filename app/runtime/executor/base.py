"""执行器协议基类(留扩展点)。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.runtime.execution.context import ExecutionContext
from app.runtime.execution.result import ExecutorResult


class BaseExecutor(ABC):
    kind: ClassVar[str] = "base"

    @abstractmethod
    async def run(self, ctx: ExecutionContext) -> ExecutorResult:
        """执行一次任务, 失败/退出码非 0 由生命周期层判定。"""
