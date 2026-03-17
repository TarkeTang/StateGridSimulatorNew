"""
国网57号文 TCP 连接管理器

扩展 TCP 连接，支持国网57号文协议：
- 自动注册
- 自动心跳
- 消息解析和响应
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from src.db.session import AsyncSessionLocal
from src.protocols.stategrid57 import (
    DeviceMode,
    MessageType,
    StateGrid57Config,
    StateGrid57Handler,
    StateGrid57Message,
    StateGrid57Protocol,
)
from src.repositories.connection_repository import ConnectionSessionRepository
from src.schemas.connection import ConnectionSessionCreate
from src.services.message_handler import message_handler
from src.utils.logger import get_logger
from src.utils.websocket_manager import push_session_status

log = get_logger("stategrid57_tcp_manager")


class StateGrid57TcpConnection:
    """
    国网57号文 TCP 连接实例

    继承 TCP 连接功能，添加国网57号文协议支持
    """

    def __init__(
        self,
        config_id: int,
        session_name: str,
        host: str,
        port: int,
        protocol_config: StateGrid57Config,
        on_message: Optional[Callable[[int, str, str], None]] = None,
        on_status_change: Optional[Callable[[int, str, Optional[str]], None]] = None,
    ):
        self.config_id = config_id
        self.session_name = session_name
        self.host = host
        self.port = port
        self.protocol_config = protocol_config
        self.on_message = on_message
        self.on_status_change = on_status_change

        # 连接会话信息
        self.connection_id: Optional[int] = None
        self.session_id: Optional[str] = None

        # TCP 连接
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.status: str = "disconnected"
        self.receive_task: Optional[asyncio.Task] = None

        # 接收缓冲区
        self._receive_buffer: bytes = b""

        # 协议处理器
        self._protocol_handler: Optional[StateGrid57Handler] = None

        # 配置
        self.buffer_size: int = 4096
        self.protocol_type: str = "STATEGRID57"

        # 自动重连配置
        self.auto_reconnect: bool = True
        self.reconnect_interval: int = 5000  # 毫秒
        self.max_reconnect_times: int = 3
        self.reconnect_count: int = 0
        self.reconnect_task: Optional[asyncio.Task] = None

    async def connect(self, is_reconnect: bool = False) -> bool:
        """建立 TCP 连接
        
        Args:
            is_reconnect: 是否为重连调用（重连时不改变状态）
        """
        if self.status == "connected":
            log.warning(f"会话 {self.session_name} 已连接")
            return True

        # 只有非重连时才更新状态为 connecting
        if not is_reconnect:
            self.status = "connecting"
            await self._notify_status_change("connecting")

        try:
            log.info(f"正在连接 {self.host}:{self.port}...")

            # 建立 TCP 连接
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=10.0,
            )

            # 创建连接会话记录
            try:
                async with AsyncSessionLocal() as db:
                    repo = ConnectionSessionRepository(db)
                    connection = await repo.create(ConnectionSessionCreate(config_id=self.config_id))
                    await db.commit()
                    self.connection_id = connection.id
                    self.session_id = connection.session_id
                    log.info(f"创建连接会话记录: connection_id={self.connection_id}, session_id={self.session_id}")
            except Exception as db_error:
                log.error(f"创建连接记录失败: {db_error}")

            # 初始化协议处理器
            self._protocol_handler = StateGrid57Handler(
                config=self.protocol_config,
                on_send=self._send_raw,
                on_message=self._on_protocol_message,
            )

            # 连接成功，重置重连计数器
            self.reconnect_count = 0
            if self.reconnect_task:
                self.reconnect_task.cancel()
                self.reconnect_task = None

            self.status = "connected"
            await self._notify_status_change("connected")
            log.info(f"TCP 连接成功: {self.host}:{self.port}")

            # 注册会话到消息处理器
            if self.connection_id:
                message_handler.register_session(
                    session_id=self.connection_id,
                    session_name=self.session_name,
                    protocol_type=self.protocol_type,
                )

            # 启动接收任务
            self.receive_task = asyncio.create_task(self._receive_loop())

            return True

        except asyncio.TimeoutError:
            error_msg = f"连接超时: {self.host}:{self.port}"
            log.error(error_msg)
            # 重连时不改变状态，由 _auto_reconnect 处理
            if not is_reconnect:
                self.status = "error"
                await self._notify_status_change("error", error_msg)
            return False

        except OSError as e:
            error_msg = f"连接失败: {e.strerror or str(e)}"
            log.error(f"TCP 连接失败: {self.host}:{self.port}, 错误: {e}")
            # 重连时不改变状态，由 _auto_reconnect 处理
            if not is_reconnect:
                self.status = "error"
                await self._notify_status_change("error", error_msg)
            return False

        except Exception as e:
            error_msg = f"连接异常: {str(e)}"
            log.error(f"TCP 连接异常: {self.host}:{self.port}, 错误: {e}")
            # 重连时不改变状态，由 _auto_reconnect 处理
            if not is_reconnect:
                self.status = "error"
                await self._notify_status_change("error", error_msg)
            return False

    async def disconnect(self) -> bool:
        """断开 TCP 连接"""
        # 禁用自动重连
        self.auto_reconnect = False

        # 取消重连任务
        if self.reconnect_task:
            self.reconnect_task.cancel()
            try:
                await self.reconnect_task
            except asyncio.CancelledError:
                pass
            self.reconnect_task = None

        if self.status != "connected":
            self.status = "disconnected"
            return True

        try:
            # 停止心跳
            if self._protocol_handler:
                await self._protocol_handler.stop_heartbeat()

            # 取消接收任务
            if self.receive_task:
                self.receive_task.cancel()
                try:
                    await self.receive_task
                except asyncio.CancelledError:
                    pass
                self.receive_task = None

            # 关闭连接
            if self.writer:
                self.writer.close()
                try:
                    await self.writer.wait_closed()
                except Exception:
                    pass
                self.writer = None

            # 更新连接记录状态
            await self._update_connection_status("disconnected")

            # 注销会话
            if self.connection_id:
                message_handler.unregister_session(self.connection_id)

            self.status = "disconnected"
            await self._notify_status_change("disconnected")
            log.info(f"TCP 连接已断开: {self.host}:{self.port}")

            return True

        except Exception as e:
            log.error(f"断开连接失败: {e}")
            return False

    async def send(self, content: str, is_auto_send: bool = False) -> bool:
        """
        发送消息

        Args:
            content: 消息内容，支持以下格式：
                - JSON格式: {"type": "61", "code": "", "command": "", "items": [...]}
                - 十六进制报文: 以 "hex:" 开头，如 "hex:EB90..."
                - 普通文本: 自动打包成协议消息
            is_auto_send: 是否为自动发送

        Returns:
            发送是否成功
        """
        # 检查连接状态
        if self.status == "disconnected":
            log.warning(f"会话 {self.session_name} 已断开，无法发送数据")
            return False

        if self.status == "reconnecting":
            log.warning(f"会话 {self.session_name} 正在重连中，无法发送数据")
            return False

        if self.status != "connected" or not self.writer:
            log.warning(f"会话 {self.session_name} 未连接，无法发送数据")
            return False

        if not self._protocol_handler:
            log.error(f"协议处理器未初始化")
            return False

        try:
            raw_data: bytes
            
            # 检查是否是十六进制报文
            if content.lower().startswith("hex:"):
                # 十六进制格式，直接转换
                hex_str = content[4:].strip()
                raw_data = bytes.fromhex(hex_str)
                log.info(f"发送十六进制报文: {hex_str[:40]}...")

            # 检查是否是 XML 格式（用户输入完整XML）
            elif content.strip().startswith("<?xml") or content.strip().startswith("<"):
                # XML 格式，直接打包成协议消息（只加 EB90 头尾）
                session_num = self._protocol_handler._get_next_session_num()
                raw_data = StateGrid57Protocol.packetize(
                    session_source="request",
                    send_session_num=session_num,
                    xml_content=content.strip(),
                )
                log.info(f"发送XML格式消息，长度: {len(content)}")

            # 尝试解析为 JSON
            elif content.strip().startswith("{"):
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        raw_data = self._build_message_from_dict(data)
                        log.info(f"发送JSON格式消息: type={data.get('type', 'unknown')}")
                    else:
                        raw_data = self._protocol_handler.create_data_message(
                            message_type="64",
                            items=[{"data": str(data)}],
                        )
                except json.JSONDecodeError:
                    # JSON解析失败，作为普通文本
                    raw_data = self._protocol_handler.create_data_message(
                        message_type="64",
                        items=[{"content": content}],
                    )

            # 普通文本，打包成协议消息
            else:
                raw_data = self._protocol_handler.create_data_message(
                    message_type="64",  # 默认使用监视数据类型
                    items=[{"content": content}],
                )
                log.info(f"发送普通文本消息，已打包成协议格式，原始内容: {content[:50]}")

            # 发送数据
            self.writer.write(raw_data)
            await self.writer.drain()

            log.info(f"国网57号文协议发送成功: 长度={len(raw_data)}, 报文头={raw_data[:4].hex().upper()}")

            # 记录消息
            if self.connection_id and self.session_id:
                await message_handler.handle_send(
                    connection_id=self.connection_id,
                    session_id=self.session_id,
                    config_id=self.config_id,
                    content=content,
                    is_auto_send=is_auto_send,
                )

            return True
        except Exception as e:
            log.error(f"发送消息失败: {e}")
            return False

    async def send_protocol_message(
        self,
        message_type: str,
        message_code: str = "",
        message_command: str = "",
        items: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        发送协议消息

        Args:
            message_type: 消息类型
            message_code: 消息编码
            message_command: 指令
            items: 数据项

        Returns:
            发送结果
        """
        if not self._protocol_handler:
            return {"success": False, "error": "协议处理器未初始化"}

        try:
            # 创建消息
            raw_data = self._protocol_handler.create_data_message(
                message_type=message_type,
                message_code=message_code,
                message_command=message_command,
                items=items,
            )

            # 发送
            if self.writer:
                self.writer.write(raw_data)
                await self.writer.drain()

            # 记录
            content = StateGrid57Protocol.read_xml(
                raw_data[21:-2].decode("utf-8", errors="ignore")
            )
            content_str = json.dumps(content, ensure_ascii=False)

            if self.connection_id and self.session_id:
                await message_handler.handle_send(
                    connection_id=self.connection_id,
                    session_id=self.session_id,
                    config_id=self.config_id,
                    content=content_str,
                )

            return {"success": True, "content": content_str}

        except Exception as e:
            log.error(f"发送协议消息失败: {e}")
            return {"success": False, "error": str(e)}

    def _build_message_from_dict(self, data: Dict[str, Any]) -> bytes:
        """从字典构建协议消息"""
        if not self._protocol_handler:
            raise ValueError("协议处理器未初始化")

        return self._protocol_handler.create_data_message(
            message_type=data.get("type", ""),
            message_code=data.get("code", ""),
            message_command=data.get("command", ""),
            items=data.get("items"),
        )

    async def _receive_loop(self):
        """接收数据循环"""
        while self.status == "connected" and self.reader:
            try:
                data = await self.reader.read(self.buffer_size)
                if not data:
                    log.info("连接被对方关闭")
                    await self._handle_disconnect()
                    break

                log.info(f"收到原始数据: 长度={len(data)}, 前20字节={data[:20].hex().upper() if len(data) >= 20 else data.hex().upper()}")

                # 添加到缓冲区
                self._receive_buffer += data

                # 处理缓冲区中的完整报文
                await self._process_buffer()

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"接收数据异常: {e}")
                await self._handle_disconnect()
                break

    async def _process_buffer(self):
        """处理接收缓冲区
        
        协议结构：
        - 起始标志符: EB90 (2字节)
        - 发送会话序列号: long (8字节)
        - 接收会话序列号: long (8字节)
        - 会话源标识: 1字节
        - XML字节长度: int (4字节)
        - XML内容: 变长
        - 结束标志符: EB90 (2字节)
        """
        while len(self._receive_buffer) >= 23:  # 最小头部长度
            # 检查是否以 EB90 开头
            if not self._receive_buffer.startswith(StateGrid57Protocol.PACKET_HEADER):
                # 尝试找到下一个 EB90 头
                idx = self._receive_buffer.find(StateGrid57Protocol.PACKET_HEADER)
                if idx == -1:
                    # 没有找到，清空缓冲区
                    log.warning(f"缓冲区数据不以EB90开头，且未找到EB90头，丢弃数据: {self._receive_buffer[:50].hex().upper()}")
                    self._receive_buffer = b""
                    return
                # 丢弃无效数据
                log.warning(f"丢弃EB90头之前的数据: {self._receive_buffer[:idx].hex().upper()}")
                self._receive_buffer = self._receive_buffer[idx:]

            # 检查是否有足够的字节读取固定头部（2 + 8 + 8 + 1 + 4 = 23字节）
            if len(self._receive_buffer) < 23:
                return

            # 读取 XML 长度（位置：2 + 8 + 8 + 1 = 19）
            import struct
            xml_length = struct.unpack("<i", self._receive_buffer[19:23])[0]

            # 计算完整报文长度：2(头) + 8 + 8 + 1 + 4 + xml_length + 2(尾)
            total_length = 2 + 8 + 8 + 1 + 4 + xml_length + 2

            # 检查是否有完整的报文
            if len(self._receive_buffer) < total_length:
                log.info(f"缓冲区数据不完整，等待更多数据，当前长度: {len(self._receive_buffer)}, 需要: {total_length}")
                return

            # 检查结尾标识
            footer_pos = total_length - 2
            if self._receive_buffer[footer_pos:footer_pos + 2] != StateGrid57Protocol.PACKET_FOOTER:
                log.warning(f"结尾标识不匹配，期望EB90，实际: {self._receive_buffer[footer_pos:footer_pos + 2].hex().upper()}")
                # 丢弃这个无效的头，继续查找
                self._receive_buffer = self._receive_buffer[2:]
                continue

            # 提取完整报文（包含头尾）
            packet = self._receive_buffer[:total_length]
            self._receive_buffer = self._receive_buffer[total_length:]
            
            log.info(f"找到完整报文: 长度={len(packet)}, XML长度={xml_length}")

            # 处理报文
            await self._handle_packet(packet)

    async def _handle_packet(self, data: bytes):
        """处理单个报文（包含头尾标识）
        
        Args:
            data: 完整报文（包含EB90头尾）
        """
        if not self._protocol_handler:
            log.warning("协议处理器未初始化，无法处理报文")
            return

        try:
            log.info(f"_handle_packet: 开始处理报文，长度={len(data)}, 前20字节={data[:20].hex().upper()}")
            
            # 去掉头尾标识后传给协议处理器
            # data 格式: EB90 + 内容 + EB90
            packet_content = data[2:-2]  # 去掉头尾各2字节
            
            # 处理接收数据
            response = await self._protocol_handler.handle_receive(packet_content)
            log.info(f"_handle_packet: 处理完成，是否有响应={response is not None}")

            # 发送响应
            if response and self.writer:
                self.writer.write(response)
                await self.writer.drain()
                log.info(f"已发送响应: 长度={len(response)}")

        except Exception as e:
            log.error(f"处理报文失败: {e}")

    async def _handle_disconnect(self):
        """处理断开连接"""
        # 停止心跳
        if self._protocol_handler:
            await self._protocol_handler.stop_heartbeat()

        # 取消接收任务
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
            self.receive_task = None

        # 关闭写入器
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
            self.writer = None
        self.reader = None

        # 注销会话
        if self.connection_id:
            message_handler.unregister_session(self.connection_id)

        # 尝试自动重连
        if self.auto_reconnect and self.reconnect_count < self.max_reconnect_times:
            self.status = "reconnecting"
            await self._notify_status_change("reconnecting", f"连接断开，正在尝试自动重连...")
            
            # 发送系统消息
            if self.connection_id and self.session_id:
                await message_handler.handle_system(
                    connection_id=self.connection_id,
                    session_id=self.session_id,
                    config_id=self.config_id,
                    content="⚠️ 连接已断开，正在尝试自动重连...",
                )
            
            self.reconnect_task = asyncio.create_task(self._auto_reconnect())
        else:
            # 更新连接记录状态
            await self._update_connection_status("disconnected", "连接已断开")
            self.status = "disconnected"
            await self._notify_status_change("disconnected", "连接已断开")
            
            # 发送系统消息
            if self.connection_id and self.session_id:
                await message_handler.handle_system(
                    connection_id=self.connection_id,
                    session_id=self.session_id,
                    config_id=self.config_id,
                    content="❌ 连接已断开",
                )

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

            # 更新状态
            self.status = "reconnecting"
            await self._notify_status_change(
                "reconnecting",
                f"连接断开，正在重连 ({self.reconnect_count}/{self.max_reconnect_times})...",
            )
            
            # 发送系统消息
            if self.connection_id and self.session_id:
                await message_handler.handle_system(
                    connection_id=self.connection_id,
                    session_id=self.session_id,
                    config_id=self.config_id,
                    content=f"🔄 正在尝试重连 ({self.reconnect_count}/{self.max_reconnect_times})...",
                )

            await asyncio.sleep(self.reconnect_interval / 1000)

            success = await self.connect(is_reconnect=True)
            if success:
                log.info(f"自动重连成功: {self.host}:{self.port}")
                self.reconnect_count = 0
                
                # 发送系统消息
                if self.connection_id and self.session_id:
                    await message_handler.handle_system(
                        connection_id=self.connection_id,
                        session_id=self.session_id,
                        config_id=self.config_id,
                        content="✅ 重连成功",
                    )
                return

        # 重连失败
        log.warning(f"自动重连失败，已达最大重试次数: {self.host}:{self.port}")
        self.status = "disconnected"
        await self._update_connection_status("disconnected", "连接已断开，自动重连失败")
        await self._notify_status_change("disconnected", "连接已断开，自动重连失败")
        
        # 发送系统消息
        if self.connection_id and self.session_id:
            await message_handler.handle_system(
                connection_id=self.connection_id,
                session_id=self.session_id,
                config_id=self.config_id,
                content="❌ 重连失败，连接已断开",
            )

    def _on_protocol_message(self, message: StateGrid57Message):
        """协议消息回调"""
        log.info(f"_on_protocol_message 被调用: connection_id={self.connection_id}, session_id={self.session_id}, config_id={self.config_id}")
        
        # 记录接收的消息
        if self.connection_id and self.session_id:
            content = json.dumps(message.to_dict(), ensure_ascii=False)
            log.info(f"准备推送接收消息: content长度={len(content)}")

            # 创建异步任务处理消息
            asyncio.create_task(
                message_handler.handle_receive(
                    connection_id=self.connection_id,
                    session_id=self.session_id,
                    config_id=self.config_id,
                    content=content,
                    content_hex=StateGrid57Protocol.format_hex_display(message.raw_bytes),
                )
            )
        else:
            log.warning(f"无法处理接收消息: connection_id={self.connection_id}, session_id={self.session_id}")

    def _send_raw(self, data: bytes):
        """发送原始数据（供协议处理器回调）"""
        if self.writer and self.status == "connected":
            self.writer.write(data)
            asyncio.create_task(self.writer.drain())

    async def _send_register(self):
        """发送注册消息"""
        if not self._protocol_handler:
            return

        try:
            register_msg = self._protocol_handler.create_register_message()
            if self.writer:
                self.writer.write(register_msg)
                await self.writer.drain()
                log.info("注册消息已发送")

                # 记录
                if self.connection_id and self.session_id:
                    await message_handler.handle_send(
                        connection_id=self.connection_id,
                        session_id=self.session_id,
                        config_id=self.config_id,
                        content="[注册消息]",
                    )

                # 启动心跳
                if self.protocol_config.auto_heartbeat:
                    await self._protocol_handler.start_heartbeat()

        except Exception as e:
            log.error(f"发送注册消息失败: {e}")

    async def _update_connection_status(self, status: str, error_message: Optional[str] = None):
        """更新连接记录状态"""
        if not self.connection_id:
            return

        try:
            async with AsyncSessionLocal() as db:
                repo = ConnectionSessionRepository(db)
                await repo.update_status(
                    self.connection_id,
                    status=status,
                    error_message=error_message,
                )
                await db.commit()
        except Exception as e:
            log.error(f"更新连接状态失败: {e}")

    async def _notify_status_change(self, status: str, error_message: Optional[str] = None):
        """通知状态变更"""
        if self.on_status_change:
            self.on_status_change(self.config_id, status, error_message)

        # 推送 WebSocket 状态
        try:
            await push_session_status(
                session_id=self.config_id,
                status=status,
                error_message=error_message,
            )
            log.info(f"状态变更已推送: config_id={self.config_id}, status={status}")
        except Exception as e:
            log.error(f"推送状态变更失败: {e}")