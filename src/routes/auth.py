from fastapi import APIRouter, HTTPException, status
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

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=Token)
async def login(user_data: UserSchema) -> Token:
    # Validate required login fields
    if not user_data.username or not user_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
        )

    async for session in db.get_session():
        result = await session.execute(
            select(User).where(User.username == user_data.username)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(user_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        # Check if 2FA is enabled
        if user.is_2fa_enabled:
            if not user_data.totp_code:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="2FA verification required",
                )
            if not user.totp_secret_key or not verify_totp(
                user.totp_secret_key, user_data.totp_code
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid 2FA code",
                )

        access_token_expires = timedelta(hours=settings.access_token_expire_hours)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")
