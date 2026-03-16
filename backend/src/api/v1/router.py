"""
API v1 路由汇总
"""

from fastapi import APIRouter

from src.api.v1.endpoints import health, session

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(session.router, prefix="/sessions", tags=["会话管理"])