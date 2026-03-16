"""
字典数据模型

用于管理系统中各类字典数据，如：
- 协议类型（TCP、UDP、WebSocket、Modbus等）
- 设备类型（PLC、RTU、传感器等）
- 通讯类型（串口、网口、无线等）
- 会话状态（已连接、未连接、连接中、错误等）

支持扩展，便于后续添加新的字典类型
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class DictType(Base):
    """
    字典类型表

    管理字典的分类，如：协议类型、设备类型、通讯类型等
    """

    __tablename__ = "sys_dict_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="字典类型编码")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="字典类型名称")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="描述")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment="状态：True启用，False禁用")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "sort": self.sort,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DictData(Base):
    """
    字典数据表

    管理具体的字典项，如：协议类型下的TCP、UDP、WebSocket等
    """

    __tablename__ = "sys_dict_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    type_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="字典类型编码")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="字典项编码")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="字典项名称")
    value: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="字典项值")
    parent_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="父级编码，支持树形结构")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="描述")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment="状态：True启用，False禁用")
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="扩展数据JSON")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type_code": self.type_code,
            "code": self.code,
            "name": self.name,
            "value": self.value,
            "parent_code": self.parent_code,
            "description": self.description,
            "sort": self.sort,
            "status": self.status,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }