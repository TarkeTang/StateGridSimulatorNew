"""
字典 Schema

定义字典相关的 Pydantic 模型
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DictDataBase(BaseModel):
    """字典数据基础模型"""

    type_code: str = Field(..., description="字典类型编码")
    code: str = Field(..., description="字典项编码")
    name: str = Field(..., description="字典项名称")
    value: Optional[str] = Field(None, description="字典项值")
    parent_code: Optional[str] = Field(None, description="父级编码")
    description: Optional[str] = Field(None, description="描述")
    sort: int = Field(0, description="排序")
    status: bool = Field(True, description="状态")
    extra_data: Optional[str] = Field(None, description="扩展数据JSON")


class DictDataResponse(DictDataBase):
    """字典数据响应模型"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DictTypeBase(BaseModel):
    """字典类型基础模型"""

    code: str = Field(..., description="字典类型编码")
    name: str = Field(..., description="字典类型名称")
    description: Optional[str] = Field(None, description="描述")
    sort: int = Field(0, description="排序")
    status: bool = Field(True, description="状态")


class DictTypeResponse(DictTypeBase):
    """字典类型响应模型"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DictDataListResponse(BaseModel):
    """字典数据列表响应"""

    items: List[DictDataResponse]
    total: int