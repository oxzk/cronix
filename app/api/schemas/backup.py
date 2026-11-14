"""备份相关模式。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class BackupInfo(BaseModel):
    filename: str
    size: int
    created_at: datetime


class BackupCreate(BaseModel):
    upload: bool = False


class BackupCreateResult(BackupInfo):
    uploaded: bool = False


class BackupUploadResult(BaseModel):
    filename: str
    platform: str


class KryvaBackupInfo(BaseModel):
    filename: str
    size: int
    created_at: datetime


class BackupRestoreAuth(BaseModel):
    password: str
    code: str | None = None


class RemoteRestoreRequest(BackupRestoreAuth):
    filename: str


class BackupRestoreResult(BaseModel):
    filename: str
    safety_backup: str
    tables: dict[str, int]
