"""Health endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查接口"""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    assert "status" in data["data"]


@pytest.mark.asyncio
async def test_liveness(client: AsyncClient):
    """测试存活检查接口"""
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness(client: AsyncClient):
    """测试就绪检查接口"""
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "ready"