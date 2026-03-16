"""
WebSocket 消息推送模块

提供实时消息推送功能，支持：
- 会话状态变更推送
- 通信消息实时推送
- 系统通知推送

使用方法：
1. 前端连接 WebSocket: ws://host:port/api/v1/ws
2. 接收推送消息，消息格式：
   {
       "type": "session_status" | "communication" | "notification",
       "data": { ... }
   }
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.utils.logger import get_logger

log = get_logger("websocket")


class WSMessage(BaseModel):
    """WebSocket消息格式"""

    type: str
    data: Dict[str, Any]
    timestamp: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ConnectionManager:
    """
    WebSocket连接管理器

    管理所有WebSocket连接，支持：
    - 广播消息
    - 按会话ID分组推送
    - 按用户ID分组推送
    """

    def __init__(self):
        # 所有活跃连接
        self.active_connections: List[WebSocket] = []
        # 按会话ID分组的连接
        self.session_connections: Dict[int, Set[WebSocket]] = {}
        # 按用户ID分组的连接
        self.user_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None):
        """接受新的WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)

        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)

        log.info(f"WebSocket连接建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: Optional[int] = None):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # 从会话分组中移除
        for session_id, connections in list(self.session_connections.items()):
            connections.discard(websocket)
            if not connections:
                del self.session_connections[session_id]

        # 从用户分组中移除
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        log.info(f"WebSocket连接断开，当前连接数: {len(self.active_connections)}")

    def subscribe_session(self, websocket: WebSocket, session_id: int):
        """订阅会话消息"""
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
        self.session_connections[session_id].add(websocket)
        log.info(f"WebSocket订阅会话: {session_id}")

    def unsubscribe_session(self, websocket: WebSocket, session_id: int):
        """取消订阅会话消息"""
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(websocket)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            log.error(f"发送WebSocket消息失败: {e}")

    async def broadcast(self, message: Dict[str, Any]):
        """广播消息给所有连接"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                log.error(f"广播消息失败: {e}")

    async def broadcast_to_session(self, session_id: int, message: Dict[str, Any]):
        """广播消息给订阅指定会话的连接"""
        if session_id not in self.session_connections:
            return

        for connection in self.session_connections[session_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                log.error(f"发送会话消息失败: {e}")

    async def broadcast_to_user(self, user_id: int, message: Dict[str, Any]):
        """广播消息给指定用户的连接"""
        if user_id not in self.user_connections:
            return

        for connection in self.user_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                log.error(f"发送用户消息失败: {e}")


# 全局连接管理器实例
manager = ConnectionManager()


# ==================== 消息推送函数 ====================

async def push_session_status(
    session_id: int,
    status: str,
    error_message: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None,
):
    """
    推送会话状态变更消息

    Args:
        session_id: 会话ID
        status: 会话状态
        error_message: 错误信息
        extra_data: 额外数据
    """
    message = {
        "type": "session_status",
        "data": {
            "session_id": session_id,
            "status": status,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
            **(extra_data or {}),
        },
    }
    await manager.broadcast_to_session(session_id, message)
    log.info(f"推送会话状态: session_id={session_id}, status={status}")


async def push_communication_message(
    session_id: int,
    direction: str,
    content: str,
    content_hex: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None,
):
    """
    推送通信消息

    Args:
        session_id: 会话ID
        direction: 消息方向 (send/receive)
        content: 消息内容
        content_hex: 十六进制内容
        extra_data: 额外数据
    """
    message = {
        "type": "communication",
        "data": {
            "session_id": session_id,
            "direction": direction,
            "content": content,
            "content_hex": content_hex,
            "timestamp": datetime.now().isoformat(),
            **(extra_data or {}),
        },
    }
    await manager.broadcast_to_session(session_id, message)


async def push_notification(
    title: str,
    message: str,
    level: str = "info",
    user_id: Optional[int] = None,
):
    """
    推送系统通知

    Args:
        title: 通知标题
        message: 通知内容
        level: 通知级别 (info/warning/error/success)
        user_id: 用户ID，为None则广播给所有用户
    """
    notification = {
        "type": "notification",
        "data": {
            "title": title,
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat(),
        },
    }

    if user_id:
        await manager.broadcast_to_user(user_id, notification)
    else:
        await manager.broadcast(notification)

    log.info(f"推送通知: {title} - {message}")


# ==================== WebSocket 端点 ====================

async def websocket_endpoint(websocket: WebSocket, user_id: Optional[int] = None):
    """
    WebSocket端点处理函数

    处理客户端连接、消息接收、订阅请求等
    """
    await manager.connect(websocket, user_id)

    try:
        # 发送连接成功消息
        await manager.send_personal_message(
            {
                "type": "connected",
                "data": {"message": "WebSocket连接成功"},
            },
            websocket,
        )

        while True:
            # 接收客户端消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type")
                msg_data = message.get("data", {})

                # 处理订阅请求
                if msg_type == "subscribe":
                    session_id = msg_data.get("session_id")
                    if session_id:
                        manager.subscribe_session(websocket, session_id)
                        await manager.send_personal_message(
                            {
                                "type": "subscribed",
                                "data": {"session_id": session_id},
                            },
                            websocket,
                        )

                # 处理取消订阅请求
                elif msg_type == "unsubscribe":
                    session_id = msg_data.get("session_id")
                    if session_id:
                        manager.unsubscribe_session(websocket, session_id)
                        await manager.send_personal_message(
                            {
                                "type": "unsubscribed",
                                "data": {"session_id": session_id},
                            },
                            websocket,
                        )

                # 处理心跳
                elif msg_type == "ping":
                    await manager.send_personal_message(
                        {"type": "pong", "data": {}},
                        websocket,
                    )

                else:
                    log.warning(f"未知的WebSocket消息类型: {msg_type}")

            except json.JSONDecodeError:
                log.error(f"无效的JSON消息: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        log.error(f"WebSocket异常: {e}")
        manager.disconnect(websocket, user_id)