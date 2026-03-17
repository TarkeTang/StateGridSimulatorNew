"""
连接会话模型

每次连接创建一个新的连接记录，用于：
- 追踪每次连接的历史
- 关联消息记录
- 统计发送/接收数量

设计：
- session_id 格式: {config_id}_{timestamp}，如 "1_20260317093000"
- 便于按时间范围查询消息记录
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.session import SessionConfig
    from src.models.message import SessionMessage


class ConnectionSession(Base):
    """
    连接会话表

    每次连接创建一条记录，用于追踪连接历史和关联消息
    """

    __tablename__ = "sys_connection_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联会话配置
    config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_session_config.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="会话配置ID",
    )

    # 会话标识（带时间戳）
    session_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="会话标识，格式: {config_id}_{timestamp}",
    )

    # 连接状态
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="connected",
        comment="连接状态：connected/disconnected/error",
    )

    # 连接信息
    local_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="本地地址")
    local_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="本地端口")
    remote_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="远程地址")
    remote_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="远程端口")

    # 时间信息
    connected_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        comment="连接时间",
    )
    disconnected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="断开时间",
    )

    # 统计信息
    send_count: Mapped[int] = mapped_column(Integer, default=0, comment="发送消息数")
    receive_count: Mapped[int] = mapped_column(Integer, default=0, comment="接收消息数")

    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="错误信息")

    # 备注
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    # 关系
    config: Mapped["SessionConfig"] = relationship("SessionConfig", back_populates="connections")
    messages: Mapped[List["SessionMessage"]] = relationship(
        "SessionMessage",
        back_populates="connection",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ConnectionSession(id={self.id}, session_id={self.session_id}, status={self.status})>"

    @staticmethod
    def generate_session_id(config_id: int, timestamp: Optional[datetime] = None) -> str:
        """
        生成会话ID

        Args:
            config_id: 会话配置ID
            timestamp: 时间戳，默认使用当前时间

        Returns:
            会话ID，格式: {config_id}_{YYYYMMDDHHmmss}
        """
        if timestamp is None:
            timestamp = datetime.now()
        return f"{config_id}_{timestamp.strftime('%Y%m%d%H%M%S')}"