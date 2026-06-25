"""认证业务服务。"""

from __future__ import annotations

import secrets
import string

from sqlalchemy.ext.asyncio import AsyncSession

from cronix.core.config import settings
from cronix.core.database import db
from cronix.core.exceptions import AppError
from cronix.core.security import Security
from cronix.models import User
from cronix.repositories import UserRepository
from cronix.schemas import LoginSchema, TokenResponse, UserResponse
from cronix.utils.logger import logger

DEFAULT_ADMIN_USERNAME = "admin"


class AuthService:
    """用户认证业务服务。

    职责：
    - 用户名密码校验
    - 签发 JWT 访问令牌

    数据访问委托给 UserRepository。
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化认证服务。

        Args:
            session: SQLAlchemy 异步会话，由外层依赖注入并管理事务边界。
        """
        self._repo = UserRepository(session)
        self._session = session

    async def login(self, login_data: LoginSchema) -> TokenResponse:
        """校验用户名密码并签发访问令牌。

        Args:
            login_data: 登录请求数据。

        Returns:
            包含访问令牌与用户信息的响应。

        Raises:
            AppError: 用户名或密码错误。
        """
        user = await self._repo.get_by_username(login_data.username)
        if not user or not Security.verify_password(login_data.password, user.password):
            raise AppError("Incorrect username or password", status_code=401)

        token = Security.create_access_token(user.username)
        return TokenResponse(
            access_token=token,
            expires_in=settings.jwt_expire_hours * 3600,
            user=UserResponse.model_validate(user),
        )


async def initialize_admin_user() -> None:
    """启动时初始化管理员账户。

    若 ``admin`` 用户不存在，则使用随机密码创建并在日志中打印一次，
    提示运营人员妥善保存。
    """
    async for session in db.get_session():
        repo = UserRepository(session)
        if await repo.exists_by_username(DEFAULT_ADMIN_USERNAME):
            return

        alphabet = string.ascii_letters + string.digits
        random_password = "".join(secrets.choice(alphabet) for _ in range(16))

        await repo.create(
            User(
                username=DEFAULT_ADMIN_USERNAME,
                password=Security.hash_password(random_password),
            )
        )

        logger.warning("=" * 60)
        logger.warning("ADMIN USER INITIALIZED")
        logger.warning("Username: %s", DEFAULT_ADMIN_USERNAME)
        logger.warning("Password: %s", random_password)
        logger.warning("PLEASE SAVE THIS PASSWORD - IT WILL NOT BE SHOWN AGAIN")
        logger.warning("=" * 60)

