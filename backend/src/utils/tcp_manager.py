"""
TCP 连接管理器

管理所有 TCP 会话的连接，支持：
- TCP 客户端连接
- TCP 服务端监听
- 异步数据收发
- 自动重连
- WebSocket 消息推送
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from src.utils.logger import get_logger
from src.utils.websocket_manager import push_session_status, push_communication_message

log = get_logger("tcp_manager")


class TcpConnection:
    """TCP 连接实例"""

    def __init__(
        self,
        session_id: int,
        session_name: str,
        host: str,
        port: int,
        on_message: Optional[Callable[[int, str, str], None]] = None,
        on_status_change: Optional[Callable[[int, str, Optional[str]], None]] = None,
    ):
        self.session_id = session_id
        self.session_name = session_name
        self.host = host
        self.port = port
        self.on_message = on_message
        self.on_status_change = on_status_change

        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.status: str = "disconnected"
        self.receive_task: Optional[asyncio.Task] = None
        self.reconnect_task: Optional[asyncio.Task] = None

        # 配置
        self.auto_reconnect: bool = False
        self.reconnect_interval: int = 5000
        self.max_reconnect_times: int = 3
        self.reconnect_count: int = 0
        self.buffer_size: int = 4096
        self.encoding: str = "UTF-8"

    async def connect(self) -> bool:
        """建立 TCP 连接"""
        if self.status == "connected":
            log.warning(f"会话 {self.session_name} 已连接")
            return True

        self.status = "connecting"
        self._notify_status_change("connecting")

        try:
            log.info(f"正在连接 {self.host}:{self.port}...")
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=10.0,
            )

            self.status = "connected"
            self.reconnect_count = 0
            self._notify_status_change("connected")
            log.info(f"TCP 连接成功: {self.host}:{self.port}")

            # 启动接收任务
            self.receive_task = asyncio.create_task(self._receive_loop())

            return True

        except asyncio.TimeoutError:
            error_msg = f"连接超时: {self.host}:{self.port}"
            log.error(error_msg)
            self.status = "error"
            self._notify_status_change("error", error_msg)
            return False

        except OSError as e:
            error_msg = f"连接失败: {e.strerror or str(e)}"
            log.error(f"TCP 连接失败: {self.host}:{self.port}, 错误: {e}")
            self.status = "error"
            self._notify_status_change("error", error_msg)
            return False

        except Exception as e:
            error_msg = f"连接异常: {str(e)}"
            log.error(f"TCP 连接异常: {self.host}:{self.port}, 错误: {e}")
            self.status = "error"
            self._notify_status_change("error", error_msg)
            return False

    async def disconnect(self) -> bool:
        """断开 TCP 连接"""
        if self.status != "connected":
            self.status = "disconnected"
            return True

        try:
            # 取消接收任务
            if self.receive_task:
                self.receive_task.cancel()
                try:
                    await self.receive_task
                except asyncio.CancelledError:
                    pass
                self.receive_task = None

            # 取消重连任务
            if self.reconnect_task:
                self.reconnect_task.cancel()
                try:
                    await self.reconnect_task
                except asyncio.CancelledError:
                    pass
                self.reconnect_task = None

            # 关闭连接
            if self.writer:
                self.writer.close()
                try:
                    await self.writer.wait_closed()
                except Exception:
                    pass
                self.writer = None

            self.reader = None
            self.status = "disconnected"
            self._notify_status_change("disconnected")
            log.info(f"TCP 连接已断开: {self.host}:{self.port}")
            return True

        except Exception as e:
            log.error(f"断开连接异常: {e}")
            return False

    async def send(self, data: str) -> bool:
        """发送数据"""
        if self.status != "connected" or not self.writer:
            log.warning(f"会话 {self.session_name} 未连接，无法发送数据")
            return False

        try:
            # 编码并发送
            encoded_data = data.encode(self.encoding)
            self.writer.write(encoded_data)
            await self.writer.drain()

            log.info(f"TCP 发送数据: {self.session_name}, 长度: {len(encoded_data)}")
            
            # 通知消息回调
            if self.on_message:
                self.on_message(self.session_id, "send", data)

            return True

        except Exception as e:
            log.error(f"发送数据失败: {e}")
            # 连接可能已断开
            await self._handle_disconnect()
            return False

    async def send_bytes(self, data: bytes) -> bool:
        """发送字节数据"""
        if self.status != "connected" or not self.writer:
            log.warning(f"会话 {self.session_name} 未连接，无法发送数据")
            return False

        try:
            self.writer.write(data)
            await self.writer.drain()

            log.info(f"TCP 发送数据: {self.session_name}, 长度: {len(data)}")
            return True

        except Exception as e:
            log.error(f"发送数据失败: {e}")
            await self._handle_disconnect()
            return False

    async def _receive_loop(self):
        """接收数据循环"""
        while self.status == "connected" and self.reader:
            try:
                data = await self.reader.read(self.buffer_size)
                if not data:
                    # 连接已关闭
                    log.info(f"TCP 连接被远程关闭: {self.host}:{self.port}")
                    await self._handle_disconnect()
                    break

                # 解码数据
                try:
                    text = data.decode(self.encoding)
                except UnicodeDecodeError:
                    text = data.hex()

                log.info(f"TCP 接收数据: {self.session_name}, 长度: {len(data)}")

                # 通知消息回调
                if self.on_message:
                    self.on_message(self.session_id, "receive", text)

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"接收数据异常: {e}")
                await self._handle_disconnect()
                break

    async def _handle_disconnect(self):
        """处理连接断开"""
        if self.status != "connected":
            return

        old_status = self.status
        self.status = "disconnected"
        
        # 清理资源
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
            self.writer = None
        self.reader = None

        # 通知状态变更
        self._notify_status_change("disconnected", "连接已断开")

        # 自动重连
        if self.auto_reconnect and self.reconnect_count < self.max_reconnect_times:
            self.reconnect_task = asyncio.create_task(self._auto_reconnect())

    async def _auto_reconnect(self):
        """自动重连"""
        while (
            self.auto_reconnect
            and self.reconnect_count < self.max_reconnect_times
            and self.status != "connected"
        ):
            self.reconnect_count += 1
            log.info(
                f"尝试自动重连 ({self.reconnect_count}/{self.max_reconnect_times}): "
                f"{self.host}:{self.port}"
            )

            await asyncio.sleep(self.reconnect_interval / 1000)
            
            success = await self.connect()
            if success:
                log.info(f"自动重连成功: {self.host}:{self.port}")
                return

        log.warning(f"自动重连失败，已达最大重试次数: {self.host}:{self.port}")

    def _notify_status_change(self, status: str, error_message: Optional[str] = None):
        """通知状态变更"""
        if self.on_status_change:
            self.on_status_change(self.session_id, status, error_message)


class TcpConnectionManager:
    """TCP 连接管理器"""

    def __init__(self):
        self.connections: Dict[int, TcpConnection] = {}

    async def create_connection(
        self,
        session_id: int,
        session_name: str,
        host: str,
        port: int,
        auto_reconnect: bool = False,
        reconnect_interval: int = 5000,
        max_reconnect_times: int = 3,
        buffer_size: int = 4096,
        encoding: str = "UTF-8",
    ) -> TcpConnection:
        """创建 TCP 连接实例"""
        # 如果已存在，先断开
        if session_id in self.connections:
            await self.disconnect(session_id)

        conn = TcpConnection(
            session_id=session_id,
            session_name=session_name,
            host=host,
            port=port,
            on_message=self._on_message,
            on_status_change=self._on_status_change,
        )

        # 配置
        conn.auto_reconnect = auto_reconnect
        conn.reconnect_interval = reconnect_interval
        conn.max_reconnect_times = max_reconnect_times
        conn.buffer_size = buffer_size
        conn.encoding = encoding

        self.connections[session_id] = conn
        return conn

    async def connect(self, session_id: int) -> bool:
        """连接指定会话"""
        conn = self.connections.get(session_id)
        if not conn:
            log.error(f"会话 {session_id} 不存在")
            return False

        return await conn.connect()

    async def disconnect(self, session_id: int) -> bool:
        """断开指定会话"""
        conn = self.connections.get(session_id)
        if not conn:
            return True

        result = await conn.disconnect()
        del self.connections[session_id]
        return result

    async def disconnect_all(self):
        """断开所有连接"""
        for session_id in list(self.connections.keys()):
            await self.disconnect(session_id)

    async def send(self, session_id: int, data: str) -> bool:
        """发送数据"""
        conn = self.connections.get(session_id)
        if not conn:
            log.error(f"会话 {session_id} 不存在")
            return False

        return await conn.send(data)

    async def send_bytes(self, session_id: int, data: bytes) -> bool:
        """发送字节数据"""
        conn = self.connections.get(session_id)
        if not conn:
            log.error(f"会话 {session_id} 不存在")
            return False

        return await conn.send_bytes(data)

    def get_connection(self, session_id: int) -> Optional[TcpConnection]:
        """获取连接实例"""
        return self.connections.get(session_id)

    def get_status(self, session_id: int) -> str:
        """获取连接状态"""
        conn = self.connections.get(session_id)
        return conn.status if conn else "disconnected"

    def _on_message(self, session_id: int, direction: str, content: str):
        """消息回调 - 推送到 WebSocket"""
        log.info(f"TCP 消息回调: session={session_id}, direction={direction}")
        # 推送消息到 WebSocket
        asyncio.create_task(
            push_communication_message(
                session_id=session_id,
                direction=direction,
                content=content,
            )
        )

    def _on_status_change(self, session_id: int, status: str, error_message: Optional[str] = None):
        """状态变更回调 - 推送到 WebSocket"""
        log.info(f"TCP 状态变更回调: session={session_id}, status={status}")
        # 推送状态到 WebSocket
        asyncio.create_task(
            push_session_status(
                session_id=session_id,
                status=status,
                error_message=error_message,
            )
        )


# 全局 TCP 连接管理器实例
tcp_manager = TcpConnectionManager()