"""
字典数据 Repository

提供字典数据的数据库访问操作
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.dict import DictData, DictType
from src.utils.logger import get_logger

log = get_logger("repository")


class DictRepository:
    """字典数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_type_by_code(self, code: str) -> Optional[DictType]:
        """根据编码获取字典类型"""
        result = await self.db.execute(select(DictType).where(DictType.code == code))
        return result.scalar_one_or_none()

    async def get_all_types(self) -> List[DictType]:
        """获取所有字典类型"""
        result = await self.db.execute(select(DictType).order_by(DictType.sort))
        return list(result.scalars().all())

    async def get_data_by_type_code(
        self,
        type_code: str,
        status: Optional[bool] = None,
    ) -> List[DictData]:
        """根据类型编码获取字典数据列表"""
        query = select(DictData).where(DictData.type_code == type_code)
        if status is not None:
            query = query.where(DictData.status == status)
        query = query.order_by(DictData.sort)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_data_by_code(self, type_code: str, code: str) -> Optional[DictData]:
        """根据类型编码和字典编码获取字典数据"""
        result = await self.db.execute(
            select(DictData).where(DictData.type_code == type_code, DictData.code == code)
        )
        return result.scalar_one_or_none()

    async def create_type(self, data: DictType) -> DictType:
        """创建字典类型"""
        self.db.add(data)
        await self.db.flush()
        return data

    async def create_data(self, data: DictData) -> DictData:
        """创建字典数据"""
        self.db.add(data)
        await self.db.flush()
        return data

    async def init_default_data(self) -> None:
        """初始化默认字典数据"""
        # 检查是否已初始化
        existing = await self.get_type_by_code("protocol_type")
        if existing:
            return

        # 创建协议类型字典
        protocol_type = DictType(
            code="protocol_type",
            name="协议类型",
            description="通信协议类型字典",
            sort=1,
        )
        self.db.add(protocol_type)
        await self.db.flush()

        # 创建协议类型字典数据
        protocol_datas = [
            DictData(type_code="protocol_type", code="57StateGrid", name="国网规范57号文", sort=1),
            DictData(type_code="protocol_type", code="TCP", name="TCP协议", sort=2),
            DictData(type_code="protocol_type", code="UDP", name="UDP协议", sort=3),
            DictData(type_code="protocol_type", code="WebSocket", name="WebSocket协议", sort=4),
            DictData(type_code="protocol_type", code="Modbus", name="Modbus协议", sort=5),
            DictData(type_code="protocol_type", code="Serial", name="串口通信", sort=6),
        ]
        for data in protocol_datas:
            self.db.add(data)

        log.info("字典数据初始化完成")