from fastapi import APIRouter, HTTPException, status, Request
import pyotp
from sqlalchemy import select
from src.models import (
    NotificationSchema,
    NotificationResponse,
    Notification,
    UserSchema,
    User,
)
from src.databases import db
from src.services import get_password_hash, verify_totp

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/2fa", response_model=dict)
async def get_2fa_info(request: Request) -> dict:
    """获取2FA配置信息"""
    async for session in db.get_session():
        current_user = request.state.user

        result = await session.execute(
            select(User).where(User.username == current_user.username)
        )
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        secret = user.totp_secret_key or pyotp.random_base32()
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.username, issuer_name="Cronix"
        )

        return {
            "totp_secret_key": secret,
            "totp_uri": totp_uri,
            "is_2fa_enabled": user.is_2fa_enabled,
        }


@router.get("/notifications", response_model=dict)
async def list_notifications(request: Request) -> dict:
    """获取所有通知配置，按照 notify_type: {id, config} 格式返回"""
    async for session in db.get_session():
        result = await session.execute(select(Notification))
        notifications = result.scalars().all()
        return {n.notify_type: {"id": n.id, **n.config} for n in notifications}


@router.put("/notifications/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int, notification_data: NotificationSchema, request: Request
) -> NotificationResponse:
    """更新通知配置"""
    async for session in db.get_session():
        result = await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        # 检查notify_type是否与其他配置冲突
        if notification_data.notify_type.value != notification.notify_type:
            result = await session.execute(
                select(Notification).where(
                    Notification.notify_type == notification_data.notify_type.value
                )
            )
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Notification with this type already exists",
                )

        notification.notify_type = notification_data.notify_type.value
        notification.config = notification_data.config

        await session.commit()
        await session.refresh(notification)

        return NotificationResponse(
            id=notification.id,
            notify_type=notification.notify_type,
            config=notification.config,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        )


@router.put("/user", response_model=dict)
async def update_user(user_data: UserSchema, request: Request) -> dict:
    """更新用户设置（密码、2FA配置）"""
    async for session in db.get_session():
        # 从请求中获取当前用户
        current_user = request.state.user

        result = await session.execute(
            select(User).where(User.username == current_user.username)
        )
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        updated_fields = []

        # 更新密码
        if user_data.password is not None:
            user.password = get_password_hash(user_data.password)
            updated_fields.append("password")

        # 更新2FA启用状态
        if user_data.is_2fa_enabled is not None:
            # 如果要启用2FA，必须先设置TOTP密钥并验证
            if user_data.is_2fa_enabled:
                if not user.totp_secret_key:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="TOTP secret must be set before enabling 2FA",
                    )
                # 验证TOTP code
                if user_data.totp_code is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="TOTP code is required to enable 2FA",
                    )
                if not verify_totp(user.totp_secret_key, user_data.totp_code):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid TOTP code",
                    )
            # 如果要禁用2FA，且当前已启用，需要验证TOTP code
            elif user.is_2fa_enabled:
                if user_data.totp_code is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="TOTP code is required to disable 2FA",
                    )
                if not verify_totp(user.totp_secret_key, user_data.totp_code):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid TOTP code",
                    )

            user.is_2fa_enabled = user_data.is_2fa_enabled
            updated_fields.append("is_2fa_enabled")

        if not updated_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        await session.commit()

        return {
            "message": "User settings updated successfully",
            "updated_fields": updated_fields,
        }
