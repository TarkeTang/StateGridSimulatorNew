"""
连接会话 Repository

提供连接会话的数据库操作
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.connection import ConnectionSession
from src.schemas.connection import ConnectionSessionCreate
from src.utils.logger import get_logger

log = get_logger("connection_repository")


class ConnectionSessionRepository:
    """连接会话仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ConnectionSessionCreate) -> ConnectionSession:
        """
        创建连接会话

        Args:
            data: 创建数据

        Returns:
            创建的连接会话
        """
        # 生成会话ID
        session_id = ConnectionSession.generate_session_id(data.config_id)

        connection = ConnectionSession(
            config_id=data.config_id,
            session_id=session_id,
            status="connected",
            connected_at=datetime.now(),
        )
        self.db.add(connection)
        await self.db.flush()
        await self.db.refresh(connection)
        log.info(f"创建连接会话: id={connection.id}, session_id={session_id}")
        return connection

    async def get_by_id(self, connection_id: int) -> Optional[ConnectionSession]:
        """
        根据ID获取连接会话

        Args:
            connection_id: 连接会话ID

        Returns:
            连接会话或None
        """
        result = await self.db.execute(
            select(ConnectionSession).where(ConnectionSession.id == connection_id)
        )
        return result.scalar_one_or_none()

    async def get_by_session_id(self, session_id: str) -> Optional[ConnectionSession]:
        """
        根据会话标识获取连接会话

        Args:
            session_id: 会话标识

        Returns:
            连接会话或None
        """
        result = await self.db.execute(
            select(ConnectionSession).where(ConnectionSession.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_config(self, config_id: int) -> Optional[ConnectionSession]:
        """
        获取配置的当前活跃连接

        Args:
            config_id: 会话配置ID

        Returns:
            活跃的连接会话或None
        """
        result = await self.db.execute(
            select(ConnectionSession)
            .where(ConnectionSession.config_id == config_id)
            .where(ConnectionSession.status == "connected")
            .order_by(desc(ConnectionSession.connected_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_list_by_config(
        self,
        config_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ConnectionSession]:
        """
        获取配置的连接历史列表

        Args:
            config_id: 会话配置ID
            limit: 限制数量
            offset: 偏移量

        Returns:
            连接会话列表
        """
        result = await self.db.execute(
            select(ConnectionSession)
            .where(ConnectionSession.config_id == config_id)
            .order_by(desc(ConnectionSession.connected_at))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_config(self, config_id: int) -> int:
        """
        统计配置的连接数量

        Args:
            config_id: 会话配置ID

        Returns:
            连接数量
        """
        result = await self.db.execute(
            select(func.count(ConnectionSession.id)).where(
                ConnectionSession.config_id == config_id
            )
        )
        return result.scalar() or 0

    async def update_status(
        self,
        connection_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[ConnectionSession]:
        """
        更新连接状态

        Args:
            connection_id: 连接会话ID
            status: 新状态
            error_message: 错误信息

        Returns:
            更新后的连接会话或None
        """
        connection = await self.get_by_id(connection_id)
        if connection:
            connection.status = status
            if error_message:
                connection.error_message = error_message
            if status == "disconnected":
                connection.disconnected_at = datetime.now()
            await self.db.flush()
            log.info(f"更新连接状态: id={connection_id}, status={status}")
        return connection

    async def increment_send_count(self, connection_id: int) -> None:
        """
        增加发送计数

        Args:
            connection_id: 连接会话ID
        """
        connection = await self.get_by_id(connection_id)
        if connection:
            connection.send_count += 1
            await self.db.flush()

    async def increment_receive_count(self, connection_id: int) -> None:
        """
        增加接收计数

        Args:
            connection_id: 连接会话ID
        """
        connection = await self.get_by_id(connection_id)
        if connection:
            connection.receive_count += 1
            await self.db.flush()

    async def delete(self, connection_id: int) -> bool:
        """
        删除连接会话

        Args:
            connection_id: 连接会话ID

        Returns:
            是否删除成功
        """
        connection = await self.get_by_id(connection_id)
        if connection:
            await self.db.delete(connection)
            await self.db.flush()
            log.info(f"删除连接会话: id={connection_id}")
            return True
        return False

    async def delete_by_config(self, config_id: int) -> int:
        """
        删除配置的所有连接会话

        Args:
            config_id: 会话配置ID

        Returns:
            删除的数量
        """
        result = await self.db.execute(
            select(ConnectionSession).where(ConnectionSession.config_id == config_id)
        )
        connections = result.scalars().all()
        count = 0
        for connection in connections:
            await self.db.delete(connection)
            count += 1
        await self.db.flush()
        log.info(f"删除配置的所有连接会话: config_id={config_id}, count={count}")
        return count