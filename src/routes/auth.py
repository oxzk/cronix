from fastapi import APIRouter
from datetime import timedelta
from sqlalchemy import select
from src.models import UserSchema, Token, User
from src.services import (
    get_password_hash,
    verify_password,
    create_access_token,
    verify_totp,
)
from src.databases import db
from src.config import settings
from src.utils import success_response, error_response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(user_data: UserSchema) -> dict:
    # Validate required login fields
    if not user_data.username or not user_data.password:
        return error_response(message="Username and password are required", code=400)

    async for session in db.get_session():
        result = await session.execute(
            select(User).where(User.username == user_data.username)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(user_data.password, user.password):
            return error_response(message="Incorrect username or password", code=401)

        # Check if 2FA is enabled
        if user.is_2fa_enabled:
            if not user_data.totp_code:
                return error_response(message="2FA verification required", code=403)
            if not user.totp_secret_key or not verify_totp(
                user.totp_secret_key, user_data.totp_code
            ):
                return error_response(message="Invalid 2FA code", code=401)

        access_token_expires = timedelta(hours=settings.access_token_expire_hours)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return success_response(
            data={"access_token": access_token, "token_type": "bearer"},
            message="Login successful",
        )
