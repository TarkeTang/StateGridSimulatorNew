"""
自动发送配置 Schema

定义自动发送配置相关的请求和响应模式
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ==================== 自动发送配置 Schema ====================

class AutoSendConfigBase(BaseModel):
    """自动发送配置基础模式"""

    message_content: str = Field(..., min_length=1, description="消息内容")
    interval_ms: int = Field(default=1000, ge=100, le=86400000, description="发送间隔(毫秒)")
    is_enabled: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序顺序")
    description: Optional[str] = Field(None, max_length=200, description="描述说明")


class AutoSendConfigCreate(AutoSendConfigBase):
    """创建自动发送配置请求"""

    session_id: int = Field(..., description="会话ID")


class AutoSendConfigUpdate(BaseModel):
    """更新自动发送配置请求"""

    message_content: Optional[str] = Field(None, min_length=1, description="消息内容")
    interval_ms: Optional[int] = Field(None, ge=100, le=86400000, description="发送间隔(毫秒)")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    description: Optional[str] = Field(None, max_length=200, description="描述说明")


class AutoSendConfigResponse(AutoSendConfigBase):
    """自动发送配置响应"""

    id: int = Field(description="主键ID")
    session_id: int = Field(description="会话ID")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True


class AutoSendConfigListResponse(BaseModel):
    """自动发送配置列表响应"""

    items: List[AutoSendConfigResponse] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总数")


# ==================== 批量操作 Schema ====================

class AutoSendConfigBatchCreate(BaseModel):
    """批量创建自动发送配置请求"""

    session_id: int = Field(..., description="会话ID")
    configs: List[AutoSendConfigBase] = Field(..., description="配置列表")


class AutoSendConfigBatchUpdate(BaseModel):
    """批量更新自动发送配置请求"""

    configs: List[dict] = Field(..., description="配置列表，每项包含id和要更新的字段")


class AutoSendConfigReorder(BaseModel):
    """重新排序请求"""

    ordered_ids: List[int] = Field(..., description="按顺序排列的ID列表")


# ==================== 自动发送控制 Schema ====================

class AutoSendControl(BaseModel):
    """自动发送控制请求"""

    action: str = Field(..., description="操作：start/stop")
    session_id: int = Field(..., description="会话ID")


class AutoSendStatus(BaseModel):
    """自动发送状态响应"""

    session_id: int = Field(description="会话ID")
    is_running: bool = Field(description="是否正在运行")
    active_configs: List[int] = Field(default_factory=list, description="正在发送的配置ID列表")
    started_at: Optional[datetime] = Field(None, description="启动时间")