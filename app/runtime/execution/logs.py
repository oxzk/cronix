"""运行日志内存缓冲: 每个活动 run 一个有界 deque, 终态弹出快照入库。"""

from __future__ import annotations

from collections import OrderedDict, deque

from app.core.utils import utc_now

MAX_RUNS = 256
MAX_LINES = 1000


class RunLogBuffer:
    def __init__(self, max_runs: int = MAX_RUNS, max_lines: int = MAX_LINES) -> None:
        self._max_runs = max_runs
        self._max_lines = max_lines
        self._buffers: OrderedDict[str, deque[dict]] = OrderedDict()

    def append(self, run_id: str, level: str, message: str) -> None:
        buffer = self._buffers.get(run_id)
        if buffer is None:
            if len(self._buffers) >= self._max_runs:
                self._buffers.popitem(last=False)  # 淘汰最久未活动的 run
            buffer = deque(maxlen=self._max_lines)
            self._buffers[run_id] = buffer
        self._buffers.move_to_end(run_id)
        buffer.append({"timestamp": utc_now().isoformat(), "level": level.upper(), "message": message})

    def snapshot(self, run_id: str) -> list[dict]:
        buffer = self._buffers.get(run_id)
        return list(buffer) if buffer else []

    def pop(self, run_id: str) -> list[dict]:
        buffer = self._buffers.pop(run_id, None)
        return list(buffer) if buffer else []
