"""备份路由: 本地备份/上传 Kryva/恢复(恢复需再认证)。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, Response

from app.api.cookies import set_auth_cookies
from app.api.dependencies import Container, CurrentUser
from app.api.schemas.backup import (
    BackupCreate,
    BackupCreateResult,
    BackupInfo,
    BackupRestoreAuth,
    BackupRestoreResult,
    BackupUploadResult,
    KryvaBackupInfo,
    RemoteRestoreRequest,
)
from app.api.schemas.response import PageResponse, SuccessResponse
from app.application.pagination import parse_pagination

router = APIRouter(prefix="/backups", tags=["backups"])


@router.get("", response_model=SuccessResponse[list[BackupInfo]])
async def list_backups(container: Container) -> Any:
    items = await container.backups.list_local()
    return SuccessResponse(data=[BackupInfo.model_validate(item) for item in items])


@router.post("", response_model=SuccessResponse[BackupCreateResult], status_code=201)
async def create_backup(body: BackupCreate, container: Container) -> Any:
    data = await container.backups.create(upload=body.upload)
    return SuccessResponse(data=BackupCreateResult(**data))


@router.get("/kryva", response_model=SuccessResponse[PageResponse[KryvaBackupInfo]])
async def list_kryva_backups(container: Container, page: int = 1, page_size: int = 20) -> Any:
    page, page_size = parse_pagination(page, page_size)
    data = await container.backups.list_remote(page, page_size)
    return SuccessResponse(
        data=PageResponse(
            items=[KryvaBackupInfo.model_validate(item) for item in data["items"]],
            total=data["total"],
            page=data["page"],
            page_size=data["page_size"],
        )
    )


@router.post("/restore-remote", response_model=SuccessResponse[BackupRestoreResult])
async def restore_remote(
    body: RemoteRestoreRequest,
    container: Container,
    current_user: CurrentUser,
    request: Request,
    response: Response,
) -> Any:
    await container.auth.verify_reauth(body.password, body.code)
    data = await container.backups.restore_remote(body.filename)
    # 恢复会替换 auth 配置(含 token_version), 为当前会话换发新令牌
    tokens = await container.auth.issue(current_user.username)
    set_auth_cookies(request, response, tokens, container.settings.jwt)
    return SuccessResponse(data=BackupRestoreResult(**data))


@router.post("/{filename}/upload", response_model=SuccessResponse[BackupUploadResult])
async def upload_backup(filename: str, container: Container) -> Any:
    data = await container.backups.upload(filename)
    return SuccessResponse(data=BackupUploadResult(**data))


@router.post("/{filename}/restore", response_model=SuccessResponse[BackupRestoreResult])
async def restore_backup(
    filename: str,
    body: BackupRestoreAuth,
    container: Container,
    current_user: CurrentUser,
    request: Request,
    response: Response,
) -> Any:
    await container.auth.verify_reauth(body.password, body.code)
    data = await container.backups.restore_local(filename)
    tokens = await container.auth.issue(current_user.username)
    set_auth_cookies(request, response, tokens, container.settings.jwt)
    return SuccessResponse(data=BackupRestoreResult(**data))


@router.delete("/{filename}", response_model=SuccessResponse[bool])
async def delete_backup(filename: str, container: Container) -> Any:
    await container.backups.delete(filename)
    return SuccessResponse(data=True)
