"""
API v1 路由汇总
"""

from fastapi import APIRouter

from src.api.v1.endpoints import health

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])