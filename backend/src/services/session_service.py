"""
会话配置 Service

提供会话配置的业务逻辑处理
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.session import SessionConfig
from src.repositories.session_repository import SessionConfigRepository
from src.schemas.session import (
    SessionConfigCreate,
    SessionConfigUpdate,
    SessionConfigResponse,
    SessionConfigListResponse,
)
from src.utils.logger import get_logger

log = get_logger("service")


class SessionConfigService:
    """会话配置服务层"""

    def __init__(self, db: AsyncSession):
        self.repository = SessionConfigRepository(db)

    async def create_session(self, data: SessionConfigCreate) -> SessionConfigResponse:
        """创建会话配置"""
        # 检查名称是否重复
        existing = await self.repository.get_by_name(data.name)
        if existing:
            raise ValueError(f"会话名称已存在: {data.name}")

        config = await self.repository.create(data)
        return SessionConfigResponse.model_validate(config)

    async def get_session(self, config_id: int) -> Optional[SessionConfigResponse]:
        """获取会话配置详情"""
        config = await self.repository.get_by_id(config_id)
        if not config:
            return None
        return SessionConfigResponse.model_validate(config)

    async def get_session_list(
        self,
        page: int = 1,
        page_size: int = 20,
        protocol_type: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        is_enabled: Optional[bool] = None,
    ) -> SessionConfigListResponse:
        """获取会话配置列表"""
        items, total = await self.repository.get_list(
            page=page,
            page_size=page_size,
            protocol_type=protocol_type,
            status=status,
            keyword=keyword,
            is_enabled=is_enabled,
        )
        return SessionConfigListResponse(
            items=[SessionConfigResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_session(
        self, config_id: int, data: SessionConfigUpdate
    ) -> Optional[SessionConfigResponse]:
        """更新会话配置"""
        # 检查是否存在
        existing = await self.repository.get_by_id(config_id)
        if not existing:
            return None

        # 如果更新名称，检查是否重复
        if data.name and data.name != existing.name:
            name_exists = await self.repository.get_by_name(data.name)
            if name_exists:
                raise ValueError(f"会话名称已存在: {data.name}")

        config = await self.repository.update(config_id, data)
        if not config:
            return None
        return SessionConfigResponse.model_validate(config)

    async def update_session_status(
        self, config_id: int, status: str, error_message: Optional[str] = None
    ) -> Optional[SessionConfigResponse]:
        """更新会话状态"""
        config = await self.repository.update_status(config_id, status, error_message)
        if not config:
            return None
        return SessionConfigResponse.model_validate(config)

    async def delete_session(self, config_id: int) -> bool:
        """删除会话配置"""
        return await self.repository.delete(config_id)

    async def connect_session(self, config_id: int) -> Optional[SessionConfigResponse]:
        """连接会话"""
        config = await self.repository.get_by_id(config_id)
        if not config:
            return None

        if config.status == "connected":
            raise ValueError("会话已连接")

        # 更新状态为连接中
        await self.repository.update_status(config_id, "connecting")

        # TODO: 实际连接逻辑
        # 这里应该调用实际的连接处理程序

        # 模拟连接成功
        config = await self.repository.update_status(config_id, "connected")
        log.info(f"会话连接成功: {config.name}, ID: {config_id}")

        return SessionConfigResponse.model_validate(config)

    async def disconnect_session(self, config_id: int) -> Optional[SessionConfigResponse]:
        """断开会话"""
        config = await self.repository.get_by_id(config_id)
        if not config:
            return None

        if config.status != "connected":
            raise ValueError("会话未连接")

        # TODO: 实际断开逻辑
        # 这里应该调用实际的断开处理程序

        config = await self.repository.update_status(config_id, "disconnected")
        log.info(f"会话已断开: {config.name}, ID: {config_id}")

        return SessionConfigResponse.model_validate(config)

    async def get_all_enabled_sessions(self) -> List[SessionConfigResponse]:
        """获取所有启用的会话配置"""
        configs = await self.repository.get_all_enabled()
        return [SessionConfigResponse.model_validate(config) for config in configs]