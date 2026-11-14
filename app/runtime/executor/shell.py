"""Shell 执行器: asyncio 子进程, 合并 stderr, 超时/取消时杀进程组, 输出按行限长。"""

from __future__ import annotations

import asyncio
import os
import signal

from app.runtime.execution.context import ExecutionContext
from app.runtime.execution.result import ExecutorResult
from app.runtime.executor.base import BaseExecutor
from app.runtime.executor.env import sanitized_environment

MAX_LINE_BYTES = 8 * 1024


class ShellExecutor(BaseExecutor):
    kind = "shell"

    async def run(self, ctx: ExecutionContext) -> ExecutorResult:
        proc = await asyncio.create_subprocess_shell(
            ctx.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
            env=sanitized_environment(),
            limit=128 * 1024,
        )
        assert proc.stdout is not None
        try:
            buffer = b""
            while True:
                chunk = await proc.stdout.read(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    ctx.logger.info(_format_line(line))
                if len(buffer) > MAX_LINE_BYTES:
                    ctx.logger.info(f"{_format_line(buffer)} ...[truncated]")
                    buffer = b""
            if buffer:
                ctx.logger.info(_format_line(buffer))
            exit_code = await proc.wait()
        except asyncio.CancelledError:
            await self._kill(proc)
            raise
        return ExecutorResult(exit_code=exit_code)

    async def _kill(self, proc: asyncio.subprocess.Process) -> None:
        if proc.returncode is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                proc.kill()
            await proc.wait()


def _format_line(raw: bytes) -> str:
    return raw[:MAX_LINE_BYTES].decode("utf-8", errors="replace").rstrip("\r")
