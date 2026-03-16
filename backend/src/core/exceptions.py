"""
自定义异常模块

定义应用级别的异常类，提供统一的错误处理机制
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class AppException(Exception):
    """
    应用基础异常类

    所有自定义异常应继承此类
    """

    def __init__(
        self,
        code: int = 500,
        message: str = "服务器内部错误",
        data: Optional[dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data,
        }


class ValidationError(AppException):
    """数据验证错误"""

    def __init__(self, message: str = "数据验证失败", data: Optional[dict] = None):
        super().__init__(code=422, message=message, data=data)


class NotFoundError(AppException):
    """资源不存在错误"""

    def __init__(self, message: str = "资源不存在", data: Optional[dict] = None):
        super().__init__(code=404, message=message, data=data)


class UnauthorizedError(AppException):
    """未认证错误"""

    def __init__(self, message: str = "未授权访问", data: Optional[dict] = None):
        super().__init__(code=401, message=message, data=data)


class ForbiddenError(AppException):
    """权限不足错误"""

    def __init__(self, message: str = "权限不足", data: Optional[dict] = None):
        super().__init__(code=403, message=message, data=data)


class ConflictError(AppException):
    """资源冲突错误"""

    def __init__(self, message: str = "资源冲突", data: Optional[dict] = None):
        super().__init__(code=409, message=message, data=data)


class DatabaseError(AppException):
    """数据库错误"""

    def __init__(self, message: str = "数据库操作失败", data: Optional[dict] = None):
        super().__init__(code=500, message=message, data=data)


class CacheError(AppException):
    """缓存错误"""

    def __init__(self, message: str = "缓存操作失败", data: Optional[dict] = None):
        super().__init__(code=500, message=message, data=data)


class ExternalServiceError(AppException):
    """外部服务错误"""

    def __init__(self, message: str = "外部服务调用失败", data: Optional[dict] = None):
        super().__init__(code=503, message=message, data=data)