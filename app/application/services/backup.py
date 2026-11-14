"""BackupService: 一致性备份(JSON.gz) / 整库恢复 / Kryva 上传下载。"""

from __future__ import annotations

import asyncio
import gzip
import json
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from loguru import logger
from sqlalchemy import text

from app.core.exceptions import NotFoundError, ValidationError
from app.core.utils import utc_now
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.infrastructure.http.kryva import KryvaClient

BACKUP_DIR = Path("data/backups")
FILENAME_PATTERN = re.compile(r"^cronix-\d{8}-\d{6}(-\d+)?\.json\.gz$")
FORMAT_VERSION = 1
# 顺序同时满足导出与导入的外键依赖(scripts → tasks → task_runs)
TABLES = ("scripts", "tasks", "task_runs", "monitors", "monitor_checks", "system_settings")
IMPORT_ORDER = TABLES
TRUNCATE_SQL = (
    "TRUNCATE TABLE monitor_checks, task_runs, monitors, tasks, scripts, system_settings CASCADE"
)
DEFAULT_KRYVA_URL = "https://kryva.oozuo.com"
DEFAULT_PLATFORM = "cronix"
FILE_MODE = 0o600

RestoreHook = Callable[[], Awaitable[None]]


class BackupService:
    def __init__(
        self,
        session_factory,  # type: ignore[no-untyped-def]
        runtime_state=None,  # type: ignore[no-untyped-def]
        before_restore: RestoreHook | None = None,
        on_restored: RestoreHook | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._runtime_state = runtime_state
        self._before_restore = before_restore
        self._on_restored = on_restored

    # ---- 本地备份 ----

    async def list_local(self) -> list[dict]:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        items: list[dict] = []
        for path in BACKUP_DIR.iterdir():
            if not path.is_file() or not FILENAME_PATTERN.match(path.name):
                continue
            stat = path.stat()
            items.append(
                {
                    "filename": path.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                }
            )
        items.sort(key=lambda item: item["created_at"], reverse=True)
        return items

    async def create(self, upload: bool = False) -> dict:
        payload = await self._dump()
        filename = self._new_filename()
        path = BACKUP_DIR / filename
        await asyncio.to_thread(self._write_file, path, payload)
        uploaded = False
        if upload:
            await self.upload(filename)
            uploaded = True
        stat = path.stat()
        logger.info("备份已创建", filename=filename, size=stat.st_size, uploaded=uploaded)
        return {
            "filename": filename,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            "uploaded": uploaded,
        }

    async def delete(self, filename: str) -> None:
        path = self._path(filename)
        path.unlink(missing_ok=True)
        logger.info("备份已删除", filename=filename)

    # ---- Kryva ----

    async def upload(self, filename: str) -> dict:
        path = self._path(filename)
        if not path.is_file():
            raise NotFoundError("备份文件不存在")
        kryva = await self._kryva_config()
        if not kryva["api_key"]:
            raise ValidationError("未配置 Kryva API Key")
        client = KryvaClient(kryva["api_url"], kryva["api_key"])
        await client.upload(kryva["platform"], filename, path)
        logger.info("备份已上传 Kryva", filename=filename, platform=kryva["platform"])
        return {"filename": filename, "platform": kryva["platform"]}

    async def restore_local(self, filename: str) -> dict:
        path = self._path(filename)
        if not path.is_file():
            raise NotFoundError("备份文件不存在")
        payload = await asyncio.to_thread(self._read, path)
        return await self._restore(payload, filename)

    async def list_remote(self, page: int = 1, page_size: int = 20) -> dict:
        kryva = await self._kryva_config()
        if not kryva["api_key"]:
            raise ValidationError("未配置 Kryva API Key")
        client = KryvaClient(kryva["api_url"], kryva["api_key"])
        data = await client.list_files(kryva["platform"], page, page_size)
        items = [
            {
                "filename": str(item.get("name") or ""),
                "size": int(item.get("size") or 0),
                "created_at": item.get("createdAt"),
            }
            for item in (data.get("files") or [])
            if item.get("name")
        ]
        return {
            "items": items,
            "total": int(data.get("total") or 0),
            "page": int(data.get("page") or page),
            "page_size": int(data.get("pageSize") or page_size),
        }

    async def restore_remote(self, filename: str) -> dict:
        self._validate_filename(filename)
        kryva = await self._kryva_config()
        if not kryva["api_key"]:
            raise ValidationError("未配置 Kryva API Key")
        temp_path = BACKUP_DIR / f".remote-{uuid.uuid4().hex}.json.gz"
        client = KryvaClient(kryva["api_url"], kryva["api_key"])
        try:
            found = await client.download(kryva["platform"], filename, temp_path)
            if not found:
                raise NotFoundError(f"Kryva 上不存在备份: {filename}")
            payload = await asyncio.to_thread(self._read, temp_path)
        finally:
            temp_path.unlink(missing_ok=True)
        return await self._restore(payload, filename)

    # ---- 内部 ----

    def _new_filename(self) -> str:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        base = f"cronix-{utc_now().strftime('%Y%m%d-%H%M%S')}"
        filename = f"{base}.json.gz"
        counter = 1
        while (BACKUP_DIR / filename).exists():
            filename = f"{base}-{counter}.json.gz"
            counter += 1
        return filename

    @staticmethod
    def _write_file(path: Path, payload: dict) -> None:
        with gzip.open(path, "wt", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False)
        os.chmod(path, FILE_MODE)

    async def _dump(self) -> dict:
        tables: dict[str, Any] = {}
        async with UnitOfWork(self._session_factory) as uow:
            # 一致性快照: 避免并发写入导致跨表引用不一致
            await uow.session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
            for table in TABLES:
                result = await uow.session.execute(
                    text(
                        f"SELECT COALESCE(json_agg(t), '[]'::json) "
                        f"FROM (SELECT * FROM {table}) t"
                    )
                )
                raw = result.scalar_one()
                tables[table] = (
                    raw
                    if isinstance(raw, list)
                    else await asyncio.to_thread(json.loads, raw or "[]")
                )
        return {
            "app": "cronix",
            "format_version": FORMAT_VERSION,
            "alembic_revision": await self._current_revision(),
            "created_at": utc_now().isoformat(),
            "tables": tables,
        }

    async def _restore(self, payload: dict, filename: str) -> dict:
        self._validate_payload(payload)
        await self._check_revision(payload)
        if self._before_restore is not None:
            await self._before_restore()
        try:
            safety = await self.create(upload=False)
            counts: dict[str, int] = {}
            async with UnitOfWork(self._session_factory) as uow:
                await uow.session.execute(text(TRUNCATE_SQL))
                for table in IMPORT_ORDER:
                    rows = payload["tables"].get(table) or []
                    counts[table] = len(rows)
                    if not rows:
                        continue
                    payload_json = await asyncio.to_thread(
                        json.dumps, rows, ensure_ascii=False
                    )
                    await uow.session.execute(
                        text(
                            f"INSERT INTO {table} SELECT * FROM "
                            f"jsonb_populate_recordset(NULL::{table}, CAST(:payload AS jsonb))"
                        ),
                        {"payload": payload_json},
                    )
            logger.warning("已从备份恢复数据", filename=filename, counts=counts)
        finally:
            if self._on_restored is not None:
                await self._on_restored()
        return {"filename": filename, "safety_backup": safety["filename"], "tables": counts}

    async def _current_revision(self) -> str | None:
        try:
            async with UnitOfWork(self._session_factory) as uow:
                result = await uow.session.execute(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                )
                return result.scalar_one_or_none()
        except Exception:
            return None

    async def _check_revision(self, payload: dict) -> None:
        backup_revision = payload.get("alembic_revision")
        if not backup_revision:
            return
        current = await self._current_revision()
        if current and backup_revision != current:
            raise ValidationError(
                f"备份版本({backup_revision})与当前数据库({current})不一致, 请先升级/回退后再恢复"
            )

    @staticmethod
    def _read(path: Path) -> dict:
        try:
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                payload = json.load(stream)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError("备份文件无法读取或已损坏") from exc
        return payload

    @staticmethod
    def _validate_payload(payload: dict) -> None:
        if (
            not isinstance(payload, dict)
            or payload.get("app") != "cronix"
            or payload.get("format_version") != FORMAT_VERSION
        ):
            raise ValidationError("备份文件格式不受支持")
        tables = payload.get("tables")
        if not isinstance(tables, dict) or any(table not in tables for table in TABLES):
            raise ValidationError("备份文件缺少数据表")
        for table in TABLES:
            if not isinstance(tables[table], list):
                raise ValidationError(f"备份文件数据表格式不正确: {table}")

    @staticmethod
    def _validate_filename(filename: str) -> None:
        if not FILENAME_PATTERN.match(filename):
            raise ValidationError("备份文件名不合法")

    def _path(self, filename: str) -> Path:
        self._validate_filename(filename)
        return BACKUP_DIR / filename

    async def _kryva_config(self) -> dict:
        async with UnitOfWork(self._session_factory) as uow:
            row = await uow.system_settings.by_key("backup", "kryva")
        value = (row.value if row else {}) or {}
        return {
            "api_url": str(value.get("api_url") or DEFAULT_KRYVA_URL).rstrip("/"),
            "api_key": str(value.get("api_key") or ""),
            "platform": str(value.get("platform") or DEFAULT_PLATFORM),
        }
