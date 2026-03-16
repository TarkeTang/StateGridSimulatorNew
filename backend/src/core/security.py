"""
安全模块

提供认证和授权相关的功能：
- JWT Token 生成和验证
- 密码哈希和验证
- 权限检查
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings
from src.core.exceptions import UnauthorizedError

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordManager:
    """密码管理器"""

    @staticmethod
    def hash_password(password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)


class TokenManager:
    """Token 管理器"""

    @staticmethod
    def create_access_token(
        subject: Union[str, int],
        expires_delta: Optional[timedelta] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        创建访问令牌

        Args:
            subject: 令牌主体（通常是用户ID）
            expires_delta: 过期时间增量
            extra_data: 额外数据

        Returns:
            JWT 令牌字符串
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.jwt.access_token_expire_minutes
            )

        to_encode = {
            "sub": str(subject),
            "exp": expire,
            "type": "access",
        }
        if extra_data:
            to_encode.update(extra_data)

        return jwt.encode(
            to_encode,
            settings.jwt.secret_key,
            algorithm=settings.jwt.algorithm,
        )

    @staticmethod
    def create_refresh_token(
        subject: Union[str, int],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        创建刷新令牌

        Args:
            subject: 令牌主体
            expires_delta: 过期时间增量

        Returns:
            JWT 刷新令牌
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.jwt.refresh_token_expire_days
            )

        to_encode = {
            "sub": str(subject),
            "exp": expire,
            "type": "refresh",
        }

        return jwt.encode(
            to_encode,
            settings.jwt.secret_key,
            algorithm=settings.jwt.algorithm,
        )

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        解码并验证令牌

        Args:
            token: JWT 令牌

        Returns:
            解码后的载荷

        Raises:
            UnauthorizedError: 令牌无效或过期
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt.secret_key,
                algorithms=[settings.jwt.algorithm],
            )
            return payload
        except JWTError as e:
            raise UnauthorizedError(message="令牌无效或已过期", data={"error": str(e)})

    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """验证访问令牌"""
        payload = TokenManager.decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedError(message="无效的访问令牌")
        return payload

    @staticmethod
    def verify_refresh_token(token: str) -> Dict[str, Any]:
        """验证刷新令牌"""
        payload = TokenManager.decode_token(token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError(message="无效的刷新令牌")
        return payload