"""
会话配置模型

用于管理所有会话配置信息，支持多种协议类型：
- TCP客户端/服务端
- UDP
- WebSocket
- 串口通信
- Modbus

设计考虑扩展性，便于后续添加新的会话类型
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.connection import ConnectionSession


class SessionConfig(Base):
    """
    会话配置表

    管理所有通信会话的配置信息
    """

    __tablename__ = "sys_session_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="会话名称")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="会话描述")

    # 协议配置
    protocol_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="TCP", comment="协议类型：TCP/UDP/WebSocket/Serial/Modbus等"
    )
    connection_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="client", comment="连接模式：client客户端/server服务端"
    )

    # 网络配置（TCP/UDP/WebSocket）
    host: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="主机地址")
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="端口号")
    local_host: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="本地绑定地址")
    local_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="本地绑定端口")

    # 串口配置（Serial）
    serial_port: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="串口号：COM1/COM2等")
    baud_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="波特率")
    data_bits: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="数据位")
    stop_bits: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="停止位")
    parity: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="校验位：none/odd/even")

    # 连接参数
    timeout: Mapped[int] = mapped_column(Integer, default=30000, comment="超时时间(ms)")
    auto_reconnect: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否自动重连")
    reconnect_interval: Mapped[int] = mapped_column(Integer, default=5000, comment="重连间隔(ms)")
    max_reconnect_times: Mapped[int] = mapped_column(Integer, default=3, comment="最大重连次数，0表示无限")

    # 缓冲区配置
    buffer_size: Mapped[int] = mapped_column(Integer, default=4096, comment="接收缓冲区大小")
    send_buffer_size: Mapped[int] = mapped_column(Integer, default=4096, comment="发送缓冲区大小")

    # 编码配置
    encoding: Mapped[str] = mapped_column(String(20), default="UTF-8", comment="编码格式")
    line_ending: Mapped[str] = mapped_column(String(10), default="\r\n", comment="行结束符")

    # 状态
    status: Mapped[str] = mapped_column(
        String(20), default="disconnected", comment="会话状态：disconnected/connected/connecting/error"
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="最后错误信息")
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后连接时间"
    )

    # 扩展配置（JSON格式存储额外参数）
    extra_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="扩展配置JSON")

    # 分组和标签
    group_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="分组名称")
    tags: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="标签，逗号分隔")

    # 排序和状态
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关系
    connections: Mapped[List["ConnectionSession"]] = relationship(
        "ConnectionSession",
        back_populates="config",
        cascade="all, delete-orphan",
        order_by="desc(ConnectionSession.connected_at)",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "protocol_type": self.protocol_type,
            "connection_mode": self.connection_mode,
            "host": self.host,
            "port": self.port,
            "local_host": self.local_host,
            "local_port": self.local_port,
            "serial_port": self.serial_port,
            "baud_rate": self.baud_rate,
            "data_bits": self.data_bits,
            "stop_bits": self.stop_bits,
            "parity": self.parity,
            "timeout": self.timeout,
            "auto_reconnect": self.auto_reconnect,
            "reconnect_interval": self.reconnect_interval,
            "max_reconnect_times": self.max_reconnect_times,
            "buffer_size": self.buffer_size,
            "send_buffer_size": self.send_buffer_size,
            "encoding": self.encoding,
            "line_ending": self.line_ending,
            "status": self.status,
            "last_error": self.last_error,
            "last_connected_at": self.last_connected_at.isoformat() if self.last_connected_at else None,
            "extra_config": self.extra_config,
            "group_name": self.group_name,
            "tags": self.tags,
            "sort": self.sort,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }