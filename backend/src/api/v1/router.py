"""
API v1 路由汇总
"""

from fastapi import APIRouter

from src.api.v1.endpoints import dict, health, session, message, auto_send

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(dict.router, prefix="/dict", tags=["字典管理"])
api_router.include_router(session.router, prefix="/sessions", tags=["会话管理"])
api_router.include_router(message.router, prefix="/messages", tags=["消息管理"])
api_router.include_router(auto_send.router, prefix="/auto-send", tags=["自动发送配置"])