"""
自动发送配置 Repository

提供自动发送配置的数据访问操作
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.auto_send import AutoSendConfig
from src.schemas.auto_send import AutoSendConfigCreate, AutoSendConfigUpdate
from src.utils.logger import get_logger

log = get_logger("repository")


class AutoSendConfigRepository:
    """自动发送配置数据访问层"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: AutoSendConfigCreate) -> AutoSendConfig:
        """创建自动发送配置"""
        config = AutoSendConfig(**data.model_dump())
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        log.info(f"创建自动发送配置: session_id={config.session_id}, id={config.id}")
        return config

    async def get_by_id(self, config_id: int) -> Optional[AutoSendConfig]:
        """根据ID获取自动发送配置"""
        result = await self.db.execute(
            select(AutoSendConfig).where(AutoSendConfig.id == config_id)
        )
        return result.scalar_one_or_none()

    async def get_by_session(self, session_id: int) -> List[AutoSendConfig]:
        """根据会话ID获取所有自动发送配置"""
        result = await self.db.execute(
            select(AutoSendConfig)
            .where(AutoSendConfig.session_id == session_id)
            .order_by(AutoSendConfig.sort_order.asc(), AutoSendConfig.id.asc())
        )
        return list(result.scalars().all())

    async def get_enabled_by_session(self, session_id: int) -> List[AutoSendConfig]:
        """根据会话ID获取启用的自动发送配置"""
        result = await self.db.execute(
            select(AutoSendConfig)
            .where(AutoSendConfig.session_id == session_id)
            .where(AutoSendConfig.is_enabled == True)
            .order_by(AutoSendConfig.sort_order.asc(), AutoSendConfig.id.asc())
        )
        return list(result.scalars().all())

    async def update(self, config_id: int, data: AutoSendConfigUpdate) -> Optional[AutoSendConfig]:
        """更新自动发送配置"""
        config = await self.get_by_id(config_id)
        if not config:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        await self.db.flush()
        await self.db.refresh(config)
        log.info(f"更新自动发送配置: id={config_id}")
        return config

    async def delete(self, config_id: int) -> bool:
        """删除自动发送配置"""
        config = await self.get_by_id(config_id)
        if not config:
            return False

        await self.db.delete(config)
        await self.db.flush()
        log.info(f"删除自动发送配置: id={config_id}")
        return True

    async def delete_by_session(self, session_id: int) -> int:
        """删除会话的所有自动发送配置"""
        configs = await self.get_by_session(session_id)
        count = len(configs)

        for config in configs:
            await self.db.delete(config)

        await self.db.flush()
        return count

    async def batch_create(self, session_id: int, configs: List[dict]) -> List[AutoSendConfig]:
        """批量创建自动发送配置"""
        created = []
        for i, config_data in enumerate(configs):
            config = AutoSendConfig(
                session_id=session_id,
                message_content=config_data.get("message_content", ""),
                interval_ms=config_data.get("interval_ms", 1000),
                is_enabled=config_data.get("is_enabled", True),
                sort_order=config_data.get("sort_order", i),
                description=config_data.get("description"),
            )
            self.db.add(config)
            created.append(config)

        await self.db.flush()
        for config in created:
            await self.db.refresh(config)

        log.info(f"批量创建自动发送配置: session_id={session_id}, count={len(created)}")
        return created

    async def batch_update(self, configs: List[dict]) -> List[AutoSendConfig]:
        """批量更新自动发送配置"""
        updated = []
        for config_data in configs:
            config_id = config_data.get("id")
            if not config_id:
                continue

            config = await self.get_by_id(config_id)
            if config:
                for key, value in config_data.items():
                    if key != "id" and hasattr(config, key):
                        setattr(config, key, value)
                updated.append(config)

        await self.db.flush()
        for config in updated:
            await self.db.refresh(config)

        log.info(f"批量更新自动发送配置: count={len(updated)}")
        return updated

    async def reorder(self, ordered_ids: List[int]) -> bool:
        """重新排序"""
        for i, config_id in enumerate(ordered_ids):
            config = await self.get_by_id(config_id)
            if config:
                config.sort_order = i

        await self.db.flush()
        log.info(f"重新排序自动发送配置: {ordered_ids}")
        return True