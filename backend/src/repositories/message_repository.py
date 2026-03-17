"""
消息 Repository

提供消息的数据访问操作
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.message import SessionMessage
from src.schemas.session import SessionMessageCreate
from src.utils.logger import get_logger

log = get_logger("repository")


class MessageRepository:
    """消息数据访问层"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: SessionMessageCreate) -> SessionMessage:
        """创建消息记录"""
        message = SessionMessage(
            connection_id=data.connection_id,
            session_id=data.session_id,
            config_id=data.config_id,
            direction=data.direction,
            content=data.content,
            content_hex=data.content_hex,
            content_length=len(data.content.encode('utf-8')),
            message_type=data.message_type,
            protocol_type=data.protocol_type,
            source_address=data.source_address,
            source_port=data.source_port,
            target_address=data.target_address,
            target_port=data.target_port,
            extra_data=data.extra_data,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_by_id(self, message_id: int) -> Optional[SessionMessage]:
        """根据ID获取消息"""
        result = await self.db.execute(
            select(SessionMessage).where(SessionMessage.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_list_by_connection(
        self,
        connection_id: int,
        page: int = 1,
        page_size: int = 50,
        direction: Optional[str] = None,
    ) -> Tuple[List[SessionMessage], int]:
        """获取连接的消息列表"""
        query = select(SessionMessage).where(SessionMessage.connection_id == connection_id)

        if direction:
            query = query.where(SessionMessage.direction == direction)

        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        # 分页，按时间倒序
        query = query.order_by(SessionMessage.timestamp.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def get_list_by_config(
        self,
        config_id: int,
        limit: int = 50,
        direction: Optional[str] = None,
    ) -> List[SessionMessage]:
        """获取配置的消息列表（用于显示历史消息）"""
        query = select(SessionMessage).where(SessionMessage.config_id == config_id)

        if direction:
            query = query.where(SessionMessage.direction == direction)

        # 按时间倒序，取最近的消息
        query = query.order_by(desc(SessionMessage.timestamp)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent_by_config(
        self,
        config_id: int,
        limit: int = 10,
    ) -> List[SessionMessage]:
        """获取配置最近的消息（用于显示旧连接消息）"""
        query = (
            select(SessionMessage)
            .where(SessionMessage.config_id == config_id)
            .order_by(desc(SessionMessage.timestamp))
            .limit(limit)
        )
        result = await self.db.execute(query)
        # 返回时按时间正序
        messages = list(result.scalars().all())
        return messages[::-1]

    async def delete_by_connection(self, connection_id: int) -> int:
        """删除连接的所有消息"""
        result = await self.db.execute(
            select(SessionMessage).where(SessionMessage.connection_id == connection_id)
        )
        messages = result.scalars().all()
        count = len(messages)

        for msg in messages:
            await self.db.delete(msg)

        await self.db.flush()
        return count

    async def delete_by_config(self, config_id: int) -> int:
        """删除配置的所有消息"""
        result = await self.db.execute(
            select(SessionMessage).where(SessionMessage.config_id == config_id)
        )
        messages = result.scalars().all()
        count = len(messages)

        for msg in messages:
            await self.db.delete(msg)

        await self.db.flush()
        return count

    async def count_by_connection(self, connection_id: int) -> dict:
        """统计连接的消息数量"""
        result = await self.db.execute(
            select(
                SessionMessage.direction,
                func.count(SessionMessage.id).label('count')
            )
            .where(SessionMessage.connection_id == connection_id)
            .group_by(SessionMessage.direction)
        )
        counts = {'send': 0, 'receive': 0, 'system': 0}
        for row in result:
            counts[row.direction] = row.count
        return counts