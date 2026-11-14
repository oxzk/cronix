"""ScriptService: 脚本 CRUD + 测试运行(不落库)。"""

from __future__ import annotations

import asyncio
import os
import signal
import time
import uuid

from loguru import logger
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.infrastructure.database.models.script import Script
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.runtime.executor.env import sanitized_environment

MAX_CONTENT_BYTES = 64 * 1024
MAX_OUTPUT_CHARS = 64 * 1024
MAX_OUTPUT_BYTES = 64 * 1024
TEST_TIMEOUT_SECONDS = 15


class ScriptService:
    def __init__(self, session_factory) -> None:  # type: ignore[no-untyped-def]
        self._session_factory = session_factory

    async def list_paginated(self, page: int, page_size: int) -> tuple[list[Script], int]:
        async with UnitOfWork(self._session_factory) as uow:
            return await uow.scripts.list_paginated(page, page_size)

    async def get(self, script_id: uuid.UUID) -> Script:
        async with UnitOfWork(self._session_factory) as uow:
            script = await uow.scripts.get(script_id)
        if script is None:
            raise NotFoundError("脚本不存在")
        return script

    async def create(self, values: dict) -> Script:
        name = self._clean_name(values)
        content = self._clean_content(values)
        description = self._clean_description(values)
        script = Script(name=name, description=description, content=content)
        async with UnitOfWork(self._session_factory) as uow:
            if await uow.scripts.get_by_name(name) is not None:
                raise ConflictError("脚本名已存在")
            try:
                await uow.scripts.add(script)
            except IntegrityError as exc:
                raise ConflictError("脚本名已存在") from exc
        logger.info("脚本已创建", script_id=str(script.id), name=name)
        return script

    async def update(self, script_id: uuid.UUID, values: dict) -> Script:
        async with UnitOfWork(self._session_factory) as uow:
            script = await uow.scripts.get(script_id)
            if script is None:
                raise NotFoundError("脚本不存在")
            if "name" in values:
                name = self._clean_name(values)
                existing = await uow.scripts.get_by_name(name)
                if existing is not None and existing.id != script.id:
                    raise ConflictError("脚本名已存在")
                script.name = name
            if "description" in values:
                script.description = self._clean_description(values)
            if "content" in values:
                script.content = self._clean_content(values)
        return script

    async def delete(self, script_id: uuid.UUID) -> None:
        async with UnitOfWork(self._session_factory) as uow:
            script = await uow.scripts.get(script_id)
            if script is None:
                raise NotFoundError("脚本不存在")
            references = await uow.scripts.count_task_references(script_id)
            if references > 0:
                raise ConflictError(f"仍有 {references} 个任务引用该脚本, 无法删除")
            await uow.scripts.delete(script)
        logger.info("脚本已删除", script_id=str(script_id))

    async def test_run(self, script_id: uuid.UUID, timeout: int = TEST_TIMEOUT_SECONDS) -> dict:
        """用 sh -c 执行脚本内容, 流式读取并限制输出, 不写任何记录。"""
        script = await self.get(script_id)
        started = time.perf_counter()
        process = await asyncio.create_subprocess_shell(
            script.content,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
            env=sanitized_environment(),
        )
        assert process.stdout is not None and process.stderr is not None
        stdout_task = asyncio.create_task(self._read_capped(process.stdout, MAX_OUTPUT_BYTES))
        stderr_task = asyncio.create_task(self._read_capped(process.stderr, MAX_OUTPUT_BYTES))
        timed_out = False
        try:
            async with asyncio.timeout(timeout):
                await process.wait()
        except TimeoutError:
            timed_out = True
            await self._kill(process)
        stdout = await stdout_task
        stderr = await stderr_task
        duration_ms = int((time.perf_counter() - started) * 1000)
        return {
            "exit_code": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace")[:MAX_OUTPUT_CHARS],
            "stderr": stderr.decode("utf-8", errors="replace")[:MAX_OUTPUT_CHARS],
            "duration_ms": duration_ms,
            "timed_out": timed_out,
        }

    @staticmethod
    async def _read_capped(stream: asyncio.StreamReader, limit: int) -> bytes:
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = await stream.read(8192)
            if not chunk:
                break
            if total < limit:
                take = chunk[: limit - total]
                chunks.append(take)
                total += len(take)
            # 超出上限继续读取丢弃, 避免子进程因管道写满而阻塞
        return b"".join(chunks)

    @staticmethod
    async def _kill(process: asyncio.subprocess.Process) -> None:
        if process.returncode is None:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                process.kill()
            await process.wait()

    @staticmethod
    def _clean_name(values: dict) -> str:
        name = str(values.get("name") or "").strip()
        if not name:
            raise ValidationError("脚本名不能为空")
        if len(name) > 255:
            raise ValidationError("脚本名不能超过 255 字符")
        return name

    @staticmethod
    def _clean_description(values: dict) -> str | None:
        description = str(values.get("description") or "").strip()
        if len(description) > 500:
            raise ValidationError("脚本描述不能超过 500 字符")
        return description or None

    @staticmethod
    def _clean_content(values: dict) -> str:
        content = str(values.get("content") or "")
        if not content.strip():
            raise ValidationError("脚本内容不能为空")
        if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise ValidationError("脚本内容不能超过 64KB")
        return content
