"""
健康检查端点

提供服务健康状态检查接口
"""

from datetime import datetime

from fastapi import APIRouter, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_session
from src.core.config import settings
from src.schemas.base import BaseResponse, HealthResponse
from src.utils.logger import get_logger

router = APIRouter()
log = get_logger("health")


@router.get(
    "",
    response_model=BaseResponse[HealthResponse],
    status_code=status.HTTP_200_OK,
    summary="健康检查",
    description="检查服务及各组件的健康状态",
)
async def health_check():
    """
    健康检查接口

    返回服务状态和各组件连接状态
    """
    components = {
        "database": "unknown",
        "redis": "unknown",
    }

    # 检查数据库连接
    try:
        async for session in get_db_session():
            await session.execute(text("SELECT 1"))
            components["database"] = "connected"
            break
    except Exception as e:
        log.error(f"数据库连接检查失败: {e}")
        components["database"] = "disconnected"

    # 检查 Redis 连接
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.redis.url)
        await client.ping()
        components["redis"] = "connected"
        await client.close()
    except Exception as e:
        log.warning(f"Redis 连接检查失败: {e}")
        components["redis"] = "disconnected"

    health_data = HealthResponse(
        status="healthy" if all(v in ["connected", "unknown"] for v in components.values()) else "unhealthy",
        version=settings.version,
        timestamp=datetime.now(),
        components=components,
    )

    return BaseResponse(data=health_data)


@router.get(
    "/live",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="存活检查",
    description="Kubernetes 存活探针",
)
async def liveness():
    """存活检查（Kubernetes liveness probe）"""
    return BaseResponse(data={"status": "alive"})


@router.get(
    "/ready",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="就绪检查",
    description="Kubernetes 就绪探针",
)
async def readiness():
    """就绪检查（Kubernetes readiness probe）"""
    # 检查数据库连接
    try:
        async for session in get_db_session():
            await session.execute(text("SELECT 1"))
            break
    except Exception as e:
        log.error(f"就绪检查失败: {e}")
        return BaseResponse(
            code=503,
            message="服务未就绪",
            data={"status": "not_ready", "reason": str(e)},
        )

    return BaseResponse(data={"status": "ready"})