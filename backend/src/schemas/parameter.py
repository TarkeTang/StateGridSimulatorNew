"""
参数化配置 Schema
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ParameterConfigBase(BaseModel):
    """参数化配置基类"""

    name: str = Field(..., min_length=1, max_length=100, description="参数名称")
    param_type: str = Field(default="static", description="参数类型")
    static_value: Optional[str] = Field(None, description="静态值或默认值")
    config: Optional[str] = Field(None, description="参数配置(JSON格式)")
    description: Optional[str] = Field(None, max_length=500, description="参数描述")
    is_enabled: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序")


class ParameterConfigCreate(ParameterConfigBase):
    """创建参数化配置"""

    pass


class ParameterConfigUpdate(BaseModel):
    """更新参数化配置"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="参数名称")
    param_type: Optional[str] = Field(None, description="参数类型")
    static_value: Optional[str] = Field(None, description="静态值或默认值")
    config: Optional[str] = Field(None, description="参数配置(JSON格式)")
    description: Optional[str] = Field(None, max_length=500, description="参数描述")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序")


class ParameterConfigResponse(ParameterConfigBase):
    """参数化配置响应"""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ParameterConfigListResponse(BaseModel):
    """参数化配置列表响应"""

    items: List[ParameterConfigResponse]
    total: int


# 参数类型枚举
PARAM_TYPES = {
    "static": "静态值",
    "timestamp": "时间戳",
    "random": "随机数",
    "uuid": "UUID",
    "counter": "计数器",
    "custom": "自定义函数",
}