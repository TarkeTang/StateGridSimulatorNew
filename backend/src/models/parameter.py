"""
参数化配置模型

支持类似 JMeter 的参数化功能，在消息内容中使用 ${参数名} 格式
发送时自动替换为实际值
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.session import SessionConfig


class ParameterConfig(Base, TimestampMixin):
    """
    参数化配置表

    定义可用的参数及其生成规则
    """

    __tablename__ = "sys_parameter_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 参数名称（用于 ${参数名} 引用）
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="参数名称",
    )

    # 参数类型
    param_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="static",
        comment="参数类型: static(静态值), timestamp(时间戳), random(随机数), uuid(UUID), counter(计数器), custom(自定义函数)",
    )

    # 静态值或默认值
    static_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="静态值或默认值",
    )

    # 参数配置（JSON格式）
    # timestamp: {"format": "%Y%m%d%H%M%S"}
    # random: {"min": 0, "max": 100, "type": "int"}
    # counter: {"start": 1, "increment": 1}
    # custom: {"expression": "表达式"}
    config: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="参数配置(JSON格式)",
    )

    # 描述
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="参数描述",
    )

    # 是否启用
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )

    # 排序
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序",
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "param_type": self.param_type,
            "static_value": self.static_value,
            "config": self.config,
            "description": self.description,
            "is_enabled": self.is_enabled,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }