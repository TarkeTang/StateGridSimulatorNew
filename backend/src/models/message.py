"""
会话消息模型

用于管理所有会话的通信消息，支持多种协议类型：
- TCP消息
- UDP消息
- WebSocket消息
- 串口消息
- Modbus消息

设计考虑扩展性，便于后续添加新的消息类型
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class SessionMessage(Base):
    """
    会话消息表

    记录所有会话的通信消息，包括发送和接收的消息
    """

    __tablename__ = "sys_session_message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联会话
    session_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="会话ID")
    session_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="会话名称（冗余存储）")

    # 消息方向
    direction: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="消息方向：send发送/receive接收/system系统"
    )

    # 消息内容
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容（文本）")
    content_hex: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="消息内容（十六进制）")
    content_length: Mapped[int] = mapped_column(Integer, default=0, comment="消息长度（字节）")

    # 消息类型
    message_type: Mapped[str] = mapped_column(
        String(20), default="data", comment="消息类型：data数据/control控制/event事件/error错误"
    )

    # 协议信息
    protocol_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="协议类型：TCP/UDP/WebSocket/Serial/Modbus等"
    )

    # 来源/目标信息
    source_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="来源地址")
    source_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="来源端口")
    target_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="目标地址")
    target_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="目标端口")

    # 处理状态
    status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="处理状态：pending待处理/processed已处理/failed失败"
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="错误信息")

    # 解析结果（JSON格式存储解析后的数据）
    parsed_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="解析后的数据JSON")

    # 扩展信息
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="扩展数据JSON")

    # 时间戳
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, comment="消息时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "session_name": self.session_name,
            "direction": self.direction,
            "content": self.content,
            "content_hex": self.content_hex,
            "content_length": self.content_length,
            "message_type": self.message_type,
            "protocol_type": self.protocol_type,
            "source_address": self.source_address,
            "source_port": self.source_port,
            "target_address": self.target_address,
            "target_port": self.target_port,
            "status": self.status,
            "error_message": self.error_message,
            "parsed_data": self.parsed_data,
            "extra_data": self.extra_data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MessageStatistics(Base):
    """
    消息统计表

    按会话统计消息数量，用于快速查询统计信息
    """

    __tablename__ = "sys_message_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联会话
    session_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, comment="会话ID")

    # 统计数据
    total_send: Mapped[int] = mapped_column(Integer, default=0, comment="发送总数")
    total_receive: Mapped[int] = mapped_column(Integer, default=0, comment="接收总数")
    total_bytes_send: Mapped[int] = mapped_column(Integer, default=0, comment="发送字节总数")
    total_bytes_receive: Mapped[int] = mapped_column(Integer, default=0, comment="接收字节总数")
    total_errors: Mapped[int] = mapped_column(Integer, default=0, comment="错误总数")

    # 时间信息
    first_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="首条消息时间"
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后消息时间"
    )

    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "total_send": self.total_send,
            "total_receive": self.total_receive,
            "total_bytes_send": self.total_bytes_send,
            "total_bytes_receive": self.total_bytes_receive,
            "total_errors": self.total_errors,
            "first_message_at": self.first_message_at.isoformat() if self.first_message_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }