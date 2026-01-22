from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from src.config import settings
from src.models.tables import Base
from src.utils import logger


class Database:
    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def connect(self) -> None:
        """Create database engine and initialize tables"""
        if not self.engine:
            self.engine = create_async_engine(
                settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
                poolclass=NullPool,
                echo=settings.app_debug,
            )
            self.session_factory = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            # Create all tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")

    async def disconnect(self) -> None:
        """Close database engine"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database instance
db = Database()
