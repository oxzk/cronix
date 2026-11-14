"""仪表盘统计模式。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class NextRun(BaseModel):
    task_id: str
    task_name: str
    cron: str
    next_run_at: datetime | None


class StatsResponse(BaseModel):
    tasks_total: int
    tasks_enabled: int
    runs_running: int
    runs_24h: dict[str, int]
    next_runs: list[NextRun]
