"""执行上下文。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.runtime.logger import RuntimeLogger


@dataclass(frozen=True)
class ExecutionContext:
    run_id: uuid.UUID
    task_id: uuid.UUID
    task_name: str
    command: str
    logger: RuntimeLogger
