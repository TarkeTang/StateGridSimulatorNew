"""
FastAPI 应用实例模块

创建和配置 FastAPI 应用实例
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.middleware import ExceptionHandlerMiddleware, RequestLoggingMiddleware
from src.db.session import close_db, init_db
from src.utils.logger import get_logger, setup_logger

log = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时初始化
    setup_logger(
        log_level=settings.log.level,
        log_dir=settings.log.dir,
        rotation=settings.log.rotation,
        retention=settings.log.retention,
        compression=settings.log.compression,
        enable_console=settings.log.enable_console,
        enable_file=settings.log.enable_file,
    )
    log.info(f"应用启动: {settings.name} v{settings.version}")

    # 初始化数据库
    await init_db()
    log.info("数据库初始化完成")

    yield

    # 关闭时清理
    await close_db()
    log.info("应用关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title=settings.name,
        description=settings.description,
        version=settings.version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # 添加自定义中间件
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # 注册路由
    app.include_router(api_router, prefix="/api/v1")

    # 根路径
    @app.get("/", tags=["根路径"])
    async def root():
        return {
            "name": settings.name,
            "version": settings.version,
            "docs": "/docs" if settings.debug else "disabled",
        }

    return app


# 创建应用实例
app = create_app()