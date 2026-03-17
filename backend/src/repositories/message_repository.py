"""
消息 Repository

提供消息的数据访问操作
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.message import SessionMessage, MessageStatistics
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
            session_id=data.session_id,
            session_name=data.session_name,
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

        # 更新统计
        await self._update_statistics(data.session_id, data.direction, len(data.content.encode('utf-8')))

        return message

    async def get_by_id(self, message_id: int) -> Optional[SessionMessage]:
        """根据ID获取消息"""
        result = await self.db.execute(
            select(SessionMessage).where(SessionMessage.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        session_id: int,
        page: int = 1,
        page_size: int = 50,
        direction: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Tuple[List[SessionMessage], int]:
        """获取消息列表"""
        query = select(SessionMessage).where(SessionMessage.session_id == session_id)

        # 筛选条件
        if direction:
            query = query.where(SessionMessage.direction == direction)
        if start_time:
            query = query.where(SessionMessage.timestamp >= start_time)
        if end_time:
            query = query.where(SessionMessage.timestamp <= end_time)

        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        # 分页，按时间倒序
        query = query.order_by(SessionMessage.timestamp.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def delete_by_session(self, session_id: int) -> int:
        """删除会话的所有消息"""
        result = await self.db.execute(
            select(SessionMessage).where(SessionMessage.session_id == session_id)
        )
        messages = result.scalars().all()
        count = len(messages)

        for msg in messages:
            await self.db.delete(msg)

        await self.db.flush()

        # 重置统计
        stats = await self.get_statistics(session_id)
        if stats:
            stats.total_send = 0
            stats.total_receive = 0
            stats.total_bytes_send = 0
            stats.total_bytes_receive = 0
            stats.first_message_at = None
            stats.last_message_at = None

        return count

    async def get_statistics(self, session_id: int) -> Optional[MessageStatistics]:
        """获取会话消息统计"""
        result = await self.db.execute(
            select(MessageStatistics).where(MessageStatistics.session_id == session_id)
        )
        stats = result.scalar_one_or_none()

        if not stats:
            # 创建统计记录
            stats = MessageStatistics(session_id=session_id)
            self.db.add(stats)
            await self.db.flush()
            await self.db.refresh(stats)

        return stats

    async def _update_statistics(self, session_id: int, direction: str, bytes_count: int):
        """更新消息统计"""
        stats = await self.get_statistics(session_id)
        now = datetime.now()

        if direction == "send":
            stats.total_send += 1
            stats.total_bytes_send += bytes_count
        elif direction == "receive":
            stats.total_receive += 1
            stats.total_bytes_receive += bytes_count

        if not stats.first_message_at:
            stats.first_message_at = now
        stats.last_message_at = now

        await self.db.flush()