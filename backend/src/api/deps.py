"""
API 依赖注入模块

提供通用的依赖注入函数
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import UnauthorizedError
from src.core.security import TokenManager
from src.db.session import AsyncSessionLocal

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[int]:
    """
    获取当前用户ID（可选）

    Returns:
        用户ID或None
    """
    if not credentials:
        return None

    try:
        payload = TokenManager.verify_access_token(credentials.credentials)
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except Exception:
        return None


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> int:
    """
    要求用户认证（必须）

    Returns:
        用户ID

    Raises:
        UnauthorizedError: 未认证
    """
    if not credentials:
        raise UnauthorizedError(message="请先登录")

    payload = TokenManager.verify_access_token(credentials.credentials)
    user_id = payload.get("sub")

    if not user_id:
        raise UnauthorizedError(message="无效的认证信息")

    return int(user_id)