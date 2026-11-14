"""执行器结果。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutorResult:
    exit_code: int | None = None
