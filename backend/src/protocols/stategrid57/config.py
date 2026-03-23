"""
国网57号文协议配置

定义国网规范57号文协议的配置参数
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DeviceMode(str, Enum):
    """设备模式"""

    SUPERIOR = "Superior"  # 上级系统
    AREA = "Area"  # 区域主机
    EDGE = "Edge"  # 边缘节点
    ROBOT = "Robot"  # 机器人
    DRONE = "Drone"  # 无人机
    ALGO = "Algo"  # 算法管理平台


class NodeType(str, Enum):
    """节点类型"""

    PATROL_HOST = "PatrolHost"  # 巡检主机
    PATROL_DEVICE = "PatrolDevice"  # 巡检设备
    CLOUD_HOST = "CloudHost"  # 云主机


class StateGrid57Config(BaseModel):
    """国网57号文协议配置"""

    # 身份标识
    send_code: str = Field(default="Device01", description="发送身份标识")
    receive_code: str = Field(default="Server01", description="接收身份标识")

    # 设备模式
    device_mode: DeviceMode = Field(default=DeviceMode.EDGE, description="设备模式")
    node_type: NodeType = Field(default=NodeType.PATROL_DEVICE, description="节点类型")

    # 心跳配置
    heart_beat_interval: int = Field(default=100000, ge=100, le=3600000, description="心跳间隔(ms)")
    auto_heartbeat: bool = Field(default=True, description="是否自动发送心跳")

    # 数据上报间隔配置
    patroldevice_run_interval: int = Field(default=300000, ge=100, le=3600000, description="巡视装置运行数据间隔(ms)")
    nest_run_interval: int = Field(default=300000, ge=100, le=3600000, description="无人机机巢运行数据间隔(ms)")
    env_interval: int = Field(default=300000, ge=100, le=3600000, description="环境数据上报间隔(ms)")

    # 自动注册
    auto_register: bool = Field(default=True, description="连接后是否自动发送注册指令")

    # 响应处理
    auto_response: bool = Field(default=True, description="是否自动响应请求消息")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "send_code": self.send_code,
            "receive_code": self.receive_code,
            "device_mode": self.device_mode.value,
            "node_type": self.node_type.value,
            "heart_beat_interval": self.heart_beat_interval,
            "auto_heartbeat": self.auto_heartbeat,
            "patroldevice_run_interval": self.patroldevice_run_interval,
            "nest_run_interval": self.nest_run_interval,
            "env_interval": self.env_interval,
            "auto_register": self.auto_register,
            "auto_response": self.auto_response,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateGrid57Config":
        """从字典创建"""
        return cls(
            send_code=data.get("send_code", "Device01"),
            receive_code=data.get("receive_code", "Server01"),
            device_mode=DeviceMode(data.get("device_mode", "Edge")),
            node_type=NodeType(data.get("node_type", "PatrolDevice")),
            heart_beat_interval=data.get("heart_beat_interval", 100000),
            auto_heartbeat=data.get("auto_heartbeat", True),
            patroldevice_run_interval=data.get("patroldevice_run_interval", 300000),
            nest_run_interval=data.get("nest_run_interval", 300000),
            env_interval=data.get("env_interval", 300000),
            auto_register=data.get("auto_register", True),
            auto_response=data.get("auto_response", True),
        )


# 设备模式与节点类型的映射关系
DEVICE_MODE_NODE_TYPE_MAP: Dict[DeviceMode, NodeType] = {
    DeviceMode.SUPERIOR: NodeType.PATROL_HOST,
    DeviceMode.AREA: NodeType.PATROL_HOST,
    DeviceMode.EDGE: NodeType.PATROL_HOST,
    DeviceMode.ROBOT: NodeType.PATROL_DEVICE,
    DeviceMode.DRONE: NodeType.PATROL_DEVICE,
    DeviceMode.ALGO: NodeType.CLOUD_HOST,
}


def get_node_type_for_device_mode(device_mode: DeviceMode) -> NodeType:
    """根据设备模式获取节点类型"""
    return DEVICE_MODE_NODE_TYPE_MAP.get(device_mode, NodeType.PATROL_DEVICE)