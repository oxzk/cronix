from fastapi import APIRouter, Request
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
from src.utils import success_response, error_response

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/2fa")
async def get_2fa_info(request: Request) -> dict:
    """Get 2FA configuration information"""
    async for session in db.get_session():
        current_user = request.state.user

        result = await session.execute(
            select(User).where(User.username == current_user.username)
        )
        user: User | None = result.scalar_one_or_none()
        if not user:
            return error_response(message="User not found", code=404)

        secret = user.totp_secret_key or pyotp.random_base32()
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.username, issuer_name="Cronix"
        )

        return success_response(
            data={
                "totp_secret_key": secret,
                "totp_uri": totp_uri,
                "is_2fa_enabled": user.is_2fa_enabled,
            }
        )


@router.get("/notifications")
async def list_notifications(request: Request) -> dict:
    """Get all notification configurations, returned in notify_type: {id, config} format"""
    async for session in db.get_session():
        result = await session.execute(select(Notification))
        notifications = result.scalars().all()
        data = {n.notify_type: {"id": n.id, **n.config} for n in notifications}
        return success_response(data=data)


@router.put("/notifications/{notification_id}")
async def update_notification(
    notification_id: int, notification_data: NotificationSchema, request: Request
) -> dict:
    """Update notification configuration"""
    async for session in db.get_session():
        result = await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return error_response(message="Notification not found", code=404)

        # Check if notify_type conflicts with other configurations
        if notification_data.notify_type.value != notification.notify_type:
            result = await session.execute(
                select(Notification).where(
                    Notification.notify_type == notification_data.notify_type.value
                )
            )
            if result.scalar_one_or_none():
                return error_response(
                    message="Notification with this type already exists", code=400
                )

        notification.notify_type = notification_data.notify_type.value
        notification.config = notification_data.config

        await session.commit()
        await session.refresh(notification)

        notification_response = NotificationResponse(
            id=notification.id,
            notify_type=notification.notify_type,
            config=notification.config,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        )

        return success_response(
            data=notification_response, message="Notification updated successfully"
        )


@router.put("/user")
async def update_user(user_data: UserSchema, request: Request) -> dict:
    """Update user settings (password, 2FA configuration)"""
    async for session in db.get_session():
        # Get current user from request
        current_user = request.state.user

        result = await session.execute(
            select(User).where(User.username == current_user.username)
        )
        user: User | None = result.scalar_one_or_none()
        if not user:
            return error_response(message="User not found", code=404)

        updated_fields = []

        # Update password
        if user_data.password is not None:
            user.password = get_password_hash(user_data.password)
            updated_fields.append("password")

        # Update 2FA enabled status
        if user_data.is_2fa_enabled is not None:
            # If enabling 2FA, TOTP secret must be set and verified first
            if user_data.is_2fa_enabled:
                if not user.totp_secret_key:
                    return error_response(
                        message="TOTP secret must be set before enabling 2FA", code=400
                    )
                # Verify TOTP code
                if user_data.totp_code is None:
                    return error_response(
                        message="TOTP code is required to enable 2FA", code=400
                    )
                if not verify_totp(user.totp_secret_key, user_data.totp_code):
                    return error_response(message="Invalid TOTP code", code=400)
            # If disabling 2FA and currently enabled, TOTP code verification required
            elif user.is_2fa_enabled:
                if user_data.totp_code is None:
                    return error_response(
                        message="TOTP code is required to disable 2FA", code=400
                    )
                if not verify_totp(user.totp_secret_key, user_data.totp_code):
                    return error_response(message="Invalid TOTP code", code=400)

            user.is_2fa_enabled = user_data.is_2fa_enabled
            updated_fields.append("is_2fa_enabled")

        if not updated_fields:
            return error_response(message="No fields to update", code=400)

        await session.commit()

        return success_response(
            data={"updated_fields": updated_fields},
            message="User settings updated successfully",
        )
