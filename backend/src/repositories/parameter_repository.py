"""
参数化配置 Repository
"""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.parameter import ParameterConfig
from src.schemas.parameter import ParameterConfigCreate, ParameterConfigUpdate
from src.repositories.base import BaseRepository


class ParameterRepository(BaseRepository[ParameterConfig]):
    """参数化配置 Repository"""

    def __init__(self, db: AsyncSession):
        super().__init__(ParameterConfig, db)

    async def get_by_name(self, name: str) -> Optional[ParameterConfig]:
        """根据名称获取参数配置"""
        result = await self.db.execute(
            select(ParameterConfig).where(ParameterConfig.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all_enabled(self) -> List[ParameterConfig]:
        """获取所有启用的参数配置"""
        result = await self.db.execute(
            select(ParameterConfig)
            .where(ParameterConfig.is_enabled == True)
            .order_by(ParameterConfig.sort_order, ParameterConfig.id)
        )
        return list(result.scalars().all())

    async def create(self, data: ParameterConfigCreate) -> ParameterConfig:
        """创建参数配置"""
        config = ParameterConfig(**data.model_dump())
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def update(self, config_id: int, data: ParameterConfigUpdate) -> Optional[ParameterConfig]:
        """更新参数配置"""
        config = await self.get_by_id(config_id)
        if not config:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def delete(self, config_id: int) -> bool:
        """删除参数配置"""
        config = await self.get_by_id(config_id)
        if not config:
            return False

        await self.db.delete(config)
        await self.db.commit()
        return True

    async def count(self) -> int:
        """获取总数"""
        result = await self.db.execute(select(func.count(ParameterConfig.id)))
        return result.scalar() or 0