"""
会话配置 Schema

定义会话配置相关的请求和响应模式
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 会话配置 Schema ====================

class SessionConfigBase(BaseModel):
    """会话配置基础模式"""

    name: str = Field(..., min_length=1, max_length=100, description="会话名称")
    description: Optional[str] = Field(None, description="会话描述")

    # 协议配置
    protocol_type: str = Field(default="TCP", max_length=20, description="协议类型")
    connection_mode: str = Field(default="client", max_length=20, description="连接模式")

    # 网络配置
    host: Optional[str] = Field(None, max_length=100, description="主机地址")
    port: Optional[int] = Field(None, ge=1, le=65535, description="端口号")
    local_host: Optional[str] = Field(None, max_length=100, description="本地绑定地址")
    local_port: Optional[int] = Field(None, ge=1, le=65535, description="本地绑定端口")

    # 串口配置
    serial_port: Optional[str] = Field(None, max_length=50, description="串口号")
    baud_rate: Optional[int] = Field(None, description="波特率")
    data_bits: Optional[int] = Field(None, ge=5, le=8, description="数据位")
    stop_bits: Optional[int] = Field(None, ge=1, le=2, description="停止位")
    parity: Optional[str] = Field(None, max_length=10, description="校验位")

    # 连接参数
    timeout: int = Field(default=30000, ge=0, description="超时时间(ms)")
    auto_reconnect: bool = Field(default=False, description="是否自动重连")
    reconnect_interval: int = Field(default=5000, ge=100, description="重连间隔(ms)")
    max_reconnect_times: int = Field(default=3, ge=0, description="最大重连次数")

    # 缓冲区配置
    buffer_size: int = Field(default=4096, ge=1024, description="接收缓冲区大小")
    send_buffer_size: int = Field(default=4096, ge=1024, description="发送缓冲区大小")

    # 编码配置
    encoding: str = Field(default="UTF-8", max_length=20, description="编码格式")
    line_ending: str = Field(default="\r\n", max_length=10, description="行结束符")

    # 扩展配置
    extra_config: Optional[str] = Field(None, description="扩展配置JSON")
    group_name: Optional[str] = Field(None, max_length=50, description="分组名称")
    tags: Optional[str] = Field(None, max_length=200, description="标签")
    sort: int = Field(default=0, description="排序")
    is_enabled: bool = Field(default=True, description="是否启用")


class SessionConfigCreate(SessionConfigBase):
    """创建会话配置请求"""

    pass


class SessionConfigUpdate(BaseModel):
    """更新会话配置请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="会话名称")
    description: Optional[str] = Field(None, description="会话描述")
    protocol_type: Optional[str] = Field(None, max_length=20, description="协议类型")
    connection_mode: Optional[str] = Field(None, max_length=20, description="连接模式")
    host: Optional[str] = Field(None, max_length=100, description="主机地址")
    port: Optional[int] = Field(None, ge=1, le=65535, description="端口号")
    local_host: Optional[str] = Field(None, max_length=100, description="本地绑定地址")
    local_port: Optional[int] = Field(None, ge=1, le=65535, description="本地绑定端口")
    serial_port: Optional[str] = Field(None, max_length=50, description="串口号")
    baud_rate: Optional[int] = Field(None, description="波特率")
    data_bits: Optional[int] = Field(None, ge=5, le=8, description="数据位")
    stop_bits: Optional[int] = Field(None, ge=1, le=2, description="停止位")
    parity: Optional[str] = Field(None, max_length=10, description="校验位")
    timeout: Optional[int] = Field(None, ge=0, description="超时时间(ms)")
    auto_reconnect: Optional[bool] = Field(None, description="是否自动重连")
    reconnect_interval: Optional[int] = Field(None, ge=100, description="重连间隔(ms)")
    max_reconnect_times: Optional[int] = Field(None, ge=0, description="最大重连次数")
    buffer_size: Optional[int] = Field(None, ge=1024, description="接收缓冲区大小")
    send_buffer_size: Optional[int] = Field(None, ge=1024, description="发送缓冲区大小")
    encoding: Optional[str] = Field(None, max_length=20, description="编码格式")
    line_ending: Optional[str] = Field(None, max_length=10, description="行结束符")
    extra_config: Optional[str] = Field(None, description="扩展配置JSON")
    group_name: Optional[str] = Field(None, max_length=50, description="分组名称")
    tags: Optional[str] = Field(None, max_length=200, description="标签")
    sort: Optional[int] = Field(None, description="排序")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class SessionConfigResponse(SessionConfigBase):
    """会话配置响应"""

    id: int = Field(description="主键ID")
    status: str = Field(description="会话状态")
    last_error: Optional[str] = Field(None, description="最后错误信息")
    last_connected_at: Optional[datetime] = Field(None, description="最后连接时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True


class SessionConfigListResponse(BaseModel):
    """会话配置列表响应"""

    items: List[SessionConfigResponse] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页数量")


class SessionStatusUpdate(BaseModel):
    """会话状态更新请求"""

    status: str = Field(..., description="会话状态")
    error_message: Optional[str] = Field(None, description="错误信息")


# ==================== 会话消息 Schema ====================

class SessionMessageBase(BaseModel):
    """会话消息基础模式"""

    session_id: int = Field(..., description="会话ID")
    direction: str = Field(..., description="消息方向")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(default="data", description="消息类型")
    protocol_type: str = Field(..., description="协议类型")


class SessionMessageCreate(SessionMessageBase):
    """创建会话消息请求"""

    session_name: Optional[str] = Field(None, description="会话名称")
    content_hex: Optional[str] = Field(None, description="消息内容十六进制")
    source_address: Optional[str] = Field(None, description="来源地址")
    source_port: Optional[int] = Field(None, description="来源端口")
    target_address: Optional[str] = Field(None, description="目标地址")
    target_port: Optional[int] = Field(None, description="目标端口")
    extra_data: Optional[str] = Field(None, description="扩展数据")


class SessionMessageResponse(SessionMessageBase):
    """会话消息响应"""

    id: int = Field(description="主键ID")
    session_name: Optional[str] = Field(None, description="会话名称")
    content_hex: Optional[str] = Field(None, description="消息内容十六进制")
    content_length: int = Field(description="消息长度")
    source_address: Optional[str] = Field(None, description="来源地址")
    source_port: Optional[int] = Field(None, description="来源端口")
    target_address: Optional[str] = Field(None, description="目标地址")
    target_port: Optional[int] = Field(None, description="目标端口")
    status: str = Field(description="处理状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    parsed_data: Optional[str] = Field(None, description="解析数据")
    extra_data: Optional[str] = Field(None, description="扩展数据")
    timestamp: datetime = Field(description="消息时间")
    created_at: datetime = Field(description="创建时间")

    class Config:
        from_attributes = True


class SessionMessageListResponse(BaseModel):
    """会话消息列表响应"""

    items: List[SessionMessageResponse] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页数量")


# ==================== WebSocket 消息 Schema ====================

class WSMessageBase(BaseModel):
    """WebSocket消息基础模式"""

    type: str = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(default_factory=dict, description="消息数据")


class WSSessionStatusMessage(WSMessageBase):
    """WebSocket会话状态消息"""

    type: str = Field(default="session_status", description="消息类型")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "session_status",
                "data": {
                    "session_id": 1,
                    "status": "connected",
                    "timestamp": "2026-03-16T15:30:00"
                }
            }
        }


class WSCommunicationMessage(WSMessageBase):
    """WebSocket通信消息"""

    type: str = Field(default="communication", description="消息类型")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "communication",
                "data": {
                    "session_id": 1,
                    "direction": "receive",
                    "content": "Hello World",
                    "timestamp": "2026-03-16T15:30:00"
                }
            }
        }