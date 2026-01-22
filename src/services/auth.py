import jwt
import bcrypt
import secrets
import string
import pyotp
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from src.config import settings
from src.databases import db
from src.models import User
from src.utils import logger


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Hash a password"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt


async def verify_token(token: str) -> User:
    """Verify JWT token and return user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    async for session in db.get_session():
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        return user


async def initialize_admin_user():
    """Initialize admin user with random password if not exists"""
    async for session in db.get_session():
        result = await session.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            # Generate random password
            alphabet = string.ascii_letters + string.digits + string.punctuation
            random_password = "".join(secrets.choice(alphabet) for _ in range(16))

            # Create admin user
            hashed_password = get_password_hash(random_password)
            admin_user = User(username="admin", password=hashed_password)
            session.add(admin_user)
            await session.commit()

            logger.warning("=" * 60)
            logger.warning("ADMIN USER INITIALIZED")
            logger.warning(f"Username: admin")
            logger.warning(f"Password: {random_password}")
            logger.warning("PLEASE SAVE THIS PASSWORD - IT WILL NOT BE SHOWN AGAIN")
            logger.warning("=" * 60)


def verify_totp(secret: str, code: str) -> bool:
    """Verify TOTP code against secret"""
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    except Exception as e:
        logger.error(f"TOTP verification error: {e}")
        return False
