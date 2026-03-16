"""
Pydantic 基础模式模块

提供统一的请求/响应模式定义
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """基础模式配置"""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
        },
    )


class BaseResponse(BaseSchema, Generic[T]):
    """统一响应格式"""

    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="消息")
    data: Optional[T] = Field(default=None, description="数据")


class PaginatedData(BaseSchema, Generic[T]):
    """分页数据"""

    items: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页数量")
    total_pages: int = Field(default=0, description="总页数")


class PaginatedResponse(BaseResponse[PaginatedData[T]]):
    """分页响应"""

    pass


class ErrorResponse(BaseSchema):
    """错误响应"""

    code: int = Field(description="错误码")
    message: str = Field(description="错误消息")
    data: Dict[str, Any] = Field(default_factory=dict, description="错误详情")


class HealthResponse(BaseSchema):
    """健康检查响应"""

    status: str = Field(default="healthy", description="服务状态")
    version: str = Field(description="版本号")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    components: Dict[str, str] = Field(
        default_factory=lambda: {
            "database": "unknown",
            "redis": "unknown",
        },
        description="组件状态",
    )