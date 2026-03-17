"""
会话配置 Repository

提供会话配置的数据访问操作
"""

from __future__ import annotations

import json
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.session import SessionConfig
from src.schemas.session import SessionConfigCreate, SessionConfigUpdate
from src.utils.logger import get_logger

log = get_logger("repository")


class SessionConfigRepository:
    """会话配置数据访问层"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: SessionConfigCreate) -> SessionConfig:
        """创建会话配置"""
        data_dict = data.model_dump()
        
        # 处理 stategrid57_config，存储到 extra_config 中
        if "stategrid57_config" in data_dict and data_dict["stategrid57_config"]:
            extra_config = {}
            if data_dict.get("extra_config"):
                try:
                    extra_config = json.loads(data_dict["extra_config"])
                except (json.JSONDecodeError, TypeError):
                    extra_config = {}
            extra_config["stategrid57_config"] = data_dict.pop("stategrid57_config")
            data_dict["extra_config"] = json.dumps(extra_config, ensure_ascii=False)
        elif "stategrid57_config" in data_dict:
            del data_dict["stategrid57_config"]
        
        config = SessionConfig(**data_dict)
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        log.info(f"创建会话配置: {config.name}, ID: {config.id}")
        return config

    async def get_by_id(self, config_id: int) -> Optional[SessionConfig]:
        """根据ID获取会话配置"""
        result = await self.db.execute(
            select(SessionConfig).where(SessionConfig.id == config_id)
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        protocol_type: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        is_enabled: Optional[bool] = None,
    ) -> Tuple[List[SessionConfig], int]:
        """获取会话配置列表"""
        query = select(SessionConfig)

        # 筛选条件
        if protocol_type:
            query = query.where(SessionConfig.protocol_type == protocol_type)
        if status:
            query = query.where(SessionConfig.status == status)
        if is_enabled is not None:
            query = query.where(SessionConfig.is_enabled == is_enabled)
        if keyword:
            query = query.where(
                or_(
                    SessionConfig.name.contains(keyword),
                    SessionConfig.host.contains(keyword),
                    SessionConfig.description.contains(keyword),
                )
            )

        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        # 分页
        query = query.order_by(SessionConfig.sort.asc(), SessionConfig.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def update(self, config_id: int, data: SessionConfigUpdate) -> Optional[SessionConfig]:
        """更新会话配置"""
        config = await self.get_by_id(config_id)
        if not config:
            return None

        update_data = data.model_dump(exclude_unset=True)
        
        # 处理 stategrid57_config，存储到 extra_config 中
        if "stategrid57_config" in update_data and update_data["stategrid57_config"]:
            extra_config = {}
            if config.extra_config:
                try:
                    extra_config = json.loads(config.extra_config)
                except (json.JSONDecodeError, TypeError):
                    extra_config = {}
            extra_config["stategrid57_config"] = update_data.pop("stategrid57_config")
            update_data["extra_config"] = json.dumps(extra_config, ensure_ascii=False)
        elif "stategrid57_config" in update_data:
            del update_data["stategrid57_config"]
        
        for key, value in update_data.items():
            setattr(config, key, value)

        await self.db.flush()
        await self.db.refresh(config)
        log.info(f"更新会话配置: {config.name}, ID: {config.id}")
        return config

    async def update_status(
        self, config_id: int, status: str, error_message: Optional[str] = None
    ) -> Optional[SessionConfig]:
        """更新会话状态"""
        config = await self.get_by_id(config_id)
        if not config:
            return None

        config.status = status
        if error_message:
            config.last_error = error_message
        if status == "connected":
            from datetime import datetime

            config.last_connected_at = datetime.now()

        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def delete(self, config_id: int) -> bool:
        """删除会话配置"""
        config = await self.get_by_id(config_id)
        if not config:
            return False

        await self.db.delete(config)
        await self.db.flush()
        log.info(f"删除会话配置: {config.name}, ID: {config_id}")
        return True

    async def get_by_name(self, name: str) -> Optional[SessionConfig]:
        """根据名称获取会话配置"""
        result = await self.db.execute(
            select(SessionConfig).where(SessionConfig.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all_enabled(self) -> List[SessionConfig]:
        """获取所有启用的会话配置"""
        result = await self.db.execute(
            select(SessionConfig)
            .where(SessionConfig.is_enabled == True)
            .order_by(SessionConfig.sort.asc())
        )
        return list(result.scalars().all())