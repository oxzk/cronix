"""执行状态与触发方式枚举(与 task_runs 表约束一致)。"""

from __future__ import annotations

from enum import IntEnum


class ExecutionStatus(IntEnum):
    PENDING = 0
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3
    CANCELLED = 4
    TIMEOUT = 5

    @property
    def is_terminal(self) -> bool:
        return self in {self.COMPLETED, self.FAILED, self.CANCELLED, self.TIMEOUT}

    @property
    def event_name(self) -> str:
        return {
            self.COMPLETED: "run.completed",
            self.FAILED: "run.failed",
            self.CANCELLED: "run.cancelled",
            self.TIMEOUT: "run.timeout",
        }[self]

    @property
    def code(self) -> str:
        return self.name.lower()


class Trigger(IntEnum):
    MANUAL = 0
    SCHEDULE = 1
