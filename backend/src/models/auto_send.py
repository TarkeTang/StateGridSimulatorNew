"""
自动发送配置模型

用于管理会话的自动发送消息配置
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class AutoSendConfig(Base):
    """
    自动发送配置表

    管理会话的自动发送消息配置
    """

    __tablename__ = "sys_auto_send_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联会话
    session_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="会话ID")

    # 消息配置
    message_content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    interval_ms: Mapped[int] = mapped_column(Integer, default=1000, comment="发送间隔(毫秒)")

    # 状态
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序顺序")

    # 描述
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="描述说明")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_content": self.message_content,
            "interval_ms": self.interval_ms,
            "is_enabled": self.is_enabled,
            "sort_order": self.sort_order,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }