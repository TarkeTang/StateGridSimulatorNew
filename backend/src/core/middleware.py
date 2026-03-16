"""
中间件模块

提供请求处理中间件：
- 请求日志记录
- 请求计时
- 异常处理
- CORS 处理
"""

import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.exceptions import AppException
from src.utils.logger import AppLogger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录请求开始时间
        start_time = time.time()

        # 获取客户端信息
        client_ip = request.client.host if request.client else None
        user_id = getattr(request.state, "user_id", None)

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        duration_ms = (time.time() - start_time) * 1000

        # 记录请求日志
        AppLogger.log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
            user_id=user_id,
        )

        return response


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """异常处理中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except AppException as e:
            AppLogger.log_exception(e, {"path": request.url.path})
            return JSONResponse(
                status_code=e.code,
                content=e.to_dict(),
            )
        except Exception as e:
            AppLogger.log_exception(e, {"path": request.url.path})
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": "服务器内部错误",
                    "data": {},
                },
            )