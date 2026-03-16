"""
数据库会话管理模块

提供异步数据库连接和会话管理
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.utils.logger import get_logger

log = get_logger("db")

# SQLite 不支持连接池，需要特殊处理
is_sqlite = settings.database.driver == "sqlite"

if is_sqlite:
    # 确保 SQLite 数据目录存在
    sqlite_path = Path(settings.database.sqlite_file)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    
    # SQLite 引擎配置
    engine = create_async_engine(
        settings.database.async_url,
        echo=settings.debug,
        poolclass=NullPool,  # SQLite 必须使用 NullPool
    )
else:
    # PostgreSQL/MySQL 引擎配置
    engine = create_async_engine(
        settings.database.async_url,
        echo=settings.debug,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_timeout=settings.database.pool_timeout,
        pool_recycle=settings.database.pool_recycle,
        poolclass=None if not settings.debug else NullPool,
    )

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（依赖注入）

    Yields:
        AsyncSession: 数据库会话实例
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            log.error(f"数据库会话异常: {e}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话上下文管理器

    用于非依赖注入场景

    Yields:
        AsyncSession: 数据库会话实例
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            log.error(f"数据库会话异常: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库（创建所有表）"""
    # 导入所有模型，确保 SQLAlchemy 能够创建对应的表
    from src.models.base import Base
    from src.models.dict import DictType, DictData
    from src.models.session import SessionConfig
    from src.models.message import SessionMessage, MessageStatistics

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("数据库表初始化完成")


async def close_db() -> None:
    """关闭数据库连接"""
    await engine.dispose()
    log.info("数据库连接已关闭")