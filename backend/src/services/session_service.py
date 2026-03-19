"""
会话配置 Service

提供会话配置的业务逻辑处理
"""

from __future__ import annotations

import json
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.session import SessionConfig
from src.protocols.stategrid57 import StateGrid57Config, StateGrid57TcpConnection
from src.repositories.session_repository import SessionConfigRepository
from src.schemas.session import (
    SessionConfigCreate,
    SessionConfigUpdate,
    SessionConfigResponse,
    SessionConfigListResponse,
)
from src.utils.logger import get_logger
from src.utils.tcp_manager import tcp_manager

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
        return SessionConfigResponse.model_validate(config.to_dict())

    async def get_session(self, config_id: int) -> Optional[SessionConfigResponse]:
        """获取会话配置详情"""
        config = await self.repository.get_by_id(config_id)
        if not config:
            return None
        return SessionConfigResponse.model_validate(config.to_dict())

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
            items=[SessionConfigResponse.model_validate(item.to_dict()) for item in items],
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
        return SessionConfigResponse.model_validate(config.to_dict())

    async def update_session_status(
        self, config_id: int, status: str, error_message: Optional[str] = None
    ) -> Optional[SessionConfigResponse]:
        """更新会话状态"""
        config = await self.repository.update_status(config_id, status, error_message)
        if not config:
            return None
        return SessionConfigResponse.model_validate(config.to_dict())

    async def delete_session(self, config_id: int) -> bool:
        """删除会话配置"""
        # 先断开连接
        await tcp_manager.disconnect(config_id)
        return await self.repository.delete(config_id)

    async def connect_session(self, config_id: int) -> SessionConfigResponse:
        """连接会话"""
        config = await self.repository.get_by_id(config_id)
        if not config:
            raise ValueError("会话配置不存在")

        if config.status == "connected":
            raise ValueError("会话已连接")

        if not config.host or not config.port:
            raise ValueError("会话配置缺少主机地址或端口")

        # 更新状态为连接中
        await self.repository.update_status(config_id, "connecting")

        try:
            # 根据协议类型创建连接
            if config.protocol_type in ("STATEGRID57", "57StateGrid"):
                # 国网57号文协议
                success = await self._connect_stategrid57(config)
            else:
                # 普通 TCP 连接
                success = await self._connect_tcp(config)

            if success:
                # 更新数据库状态
                config = await self.repository.update_status(config_id, "connected")
                log.info(f"会话连接成功: {config.name}, {config.host}:{config.port}")
            else:
                # 更新数据库状态为错误
                config = await self.repository.update_status(
                    config_id, "error", "连接失败"
                )
                raise ValueError("连接失败")

            return SessionConfigResponse.model_validate(config.to_dict())

        except Exception as e:
            # 更新数据库状态为错误
            await self.repository.update_status(config_id, "error", str(e))
            raise

    async def _connect_tcp(self, config: SessionConfig) -> bool:
        """创建普通 TCP 连接"""
        conn = await tcp_manager.create_connection(
            config_id=config.id,
            session_name=config.name,
            host=config.host,
            port=config.port,
            auto_reconnect=config.auto_reconnect,
            reconnect_interval=config.reconnect_interval,
            max_reconnect_times=config.max_reconnect_times,
            buffer_size=config.buffer_size,
            encoding=config.encoding,
        )
        return await conn.connect()

    async def _connect_stategrid57(self, config: SessionConfig) -> bool:
        """创建国网57号文协议连接"""
        # 解析协议配置
        protocol_config = self._parse_stategrid57_config(config.extra_config)

        # 创建国网57号文连接
        conn = StateGrid57TcpConnection(
            config_id=config.id,
            session_name=config.name,
            host=config.host,
            port=config.port,
            protocol_config=protocol_config,
        )

        # 注册到 TCP 管理器
        tcp_manager.connections[config.id] = conn

        return await conn.connect()

    def _parse_stategrid57_config(self, extra_config: Optional[str]) -> StateGrid57Config:
        """解析国网57号文协议配置"""
        if not extra_config:
            return StateGrid57Config()

        try:
            extra = json.loads(extra_config)
            if "stategrid57_config" in extra:
                return StateGrid57Config.from_dict(extra["stategrid57_config"])
        except (json.JSONDecodeError, TypeError):
            pass

        return StateGrid57Config()

    async def disconnect_session(self, config_id: int) -> SessionConfigResponse:
        """断开会话"""
        config = await self.repository.get_by_id(config_id)
        if not config:
            raise ValueError("会话配置不存在")

        # 断开 TCP 连接
        await tcp_manager.disconnect(config_id)

        # 更新数据库状态
        config = await self.repository.update_status(config_id, "disconnected")
        log.info(f"会话已断开: {config.name}")

        return SessionConfigResponse.model_validate(config.to_dict())

    async def send_message(self, config_id: int, data: str) -> bool:
        """发送消息（支持参数替换）"""
        # 检查 TCP 连接是否存在且已连接
        conn = tcp_manager.get_connection(config_id)
        if not conn or conn.status != "connected":
            raise ValueError("会话未连接，请先建立连接")

        # 参数替换
        from src.utils.parameter_resolver import resolve_parameters_sync
        from src.repositories.parameter_repository import ParameterRepository

        # 获取所有启用的参数配置
        repo = ParameterRepository(self.repository.db)
        parameters = await repo.get_all_enabled()

        # 执行参数替换
        processed_data = resolve_parameters_sync(data, parameters)

        log.info(f"发送消息: 原始长度={len(data)}, 替换后长度={len(processed_data)}")

        return await tcp_manager.send(config_id, processed_data)

    async def get_all_enabled_sessions(self) -> List[SessionConfigResponse]:
        """获取所有启用的会话配置"""
        configs = await self.repository.get_all_enabled()
        return [SessionConfigResponse.model_validate(config.to_dict()) for config in configs]