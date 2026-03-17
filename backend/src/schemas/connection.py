"""
连接会话 Schema

用于 API 请求和响应的数据验证
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ConnectionSessionBase(BaseModel):
    """连接会话基础模型"""

    config_id: int = Field(..., description="会话配置ID")
    session_id: str = Field(..., description="会话标识")
    status: str = Field(default="connected", description="连接状态")
    local_address: Optional[str] = Field(None, description="本地地址")
    local_port: Optional[int] = Field(None, description="本地端口")
    remote_address: Optional[str] = Field(None, description="远程地址")
    remote_port: Optional[int] = Field(None, description="远程端口")
    remark: Optional[str] = Field(None, description="备注")


class ConnectionSessionCreate(BaseModel):
    """创建连接会话"""

    config_id: int = Field(..., description="会话配置ID")


class ConnectionSessionResponse(BaseModel):
    """连接会话响应"""

    id: int = Field(..., description="主键ID")
    config_id: int = Field(..., description="会话配置ID")
    session_id: str = Field(..., description="会话标识")
    status: str = Field(..., description="连接状态")
    local_address: Optional[str] = Field(None, description="本地地址")
    local_port: Optional[int] = Field(None, description="本地端口")
    remote_address: Optional[str] = Field(None, description="远程地址")
    remote_port: Optional[int] = Field(None, description="远程端口")
    connected_at: datetime = Field(..., description="连接时间")
    disconnected_at: Optional[datetime] = Field(None, description="断开时间")
    send_count: int = Field(default=0, description="发送消息数")
    receive_count: int = Field(default=0, description="接收消息数")
    error_message: Optional[str] = Field(None, description="错误信息")
    remark: Optional[str] = Field(None, description="备注")

    model_config = {"from_attributes": True}


class ConnectionSessionListResponse(BaseModel):
    """连接会话列表响应"""

    items: List[ConnectionSessionResponse] = Field(default_factory=list, description="连接会话列表")
    total: int = Field(default=0, description="总数")


class ConnectionSessionBrief(BaseModel):
    """连接会话简要信息"""

    id: int = Field(..., description="主键ID")
    session_id: str = Field(..., description="会话标识")
    status: str = Field(..., description="连接状态")
    connected_at: datetime = Field(..., description="连接时间")
    send_count: int = Field(default=0, description="发送消息数")
    receive_count: int = Field(default=0, description="接收消息数")

    model_config = {"from_attributes": True}