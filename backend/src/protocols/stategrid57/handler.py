"""
国网57号文消息处理器

处理接收到的消息，生成响应，管理心跳和注册
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Callable, Dict, List, Optional

from src.protocols.stategrid57.config import StateGrid57Config
from src.protocols.stategrid57.protocol import (
    Command,
    MessageType,
    ResponseCode,
    StateGrid57Message,
    StateGrid57Protocol,
)
from src.utils.logger import get_logger

log = get_logger("stategrid57_handler")


class StateGrid57Handler:
    """
    国网57号文消息处理器

    职责：
    1. 解析接收到的消息
    2. 生成响应消息
    3. 管理心跳和注册
    4. 处理业务逻辑
    """

    def __init__(
        self,
        config: StateGrid57Config,
        on_send: Optional[Callable[[bytes], None]] = None,
        on_message: Optional[Callable[[StateGrid57Message], None]] = None,
    ):
        self.config = config
        self.on_send = on_send
        self.on_message = on_message

        # 会话计数器
        self._session_counter = 0

        # 登录状态
        self._is_logged_in = False

        # 心跳任务
        self._heartbeat_task: Optional[asyncio.Task] = None

        # 等待响应的请求
        self._pending_requests: Dict[int, asyncio.Future] = {}

    def _get_next_session_num(self) -> int:
        """获取下一个会话序列号"""
        self._session_counter += 1
        return self._session_counter

    async def handle_receive(self, data: bytes) -> Optional[bytes]:
        """
        处理接收到的数据

        Args:
            data: 接收到的原始数据

        Returns:
            需要发送的响应数据（如果有）
        """
        # 分割报文
        packets = StateGrid57Protocol.split_packets(data)

        responses = []
        for packet in packets:
            # 解析报文
            message = StateGrid57Protocol.depacketize(packet)
            if not message:
                log.warning(f"解析报文失败: {StateGrid57Protocol.format_hex_display(packet)}")
                continue

            log.info(
                f"收到消息: type={message.message_type}, "
                f"command={message.message_command}, "
                f"session_num={message.send_session_num}"
            )

            # 回调通知
            if self.on_message:
                try:
                    self.on_message(message)
                except Exception as e:
                    log.error(f"消息回调执行失败: {e}")

            # 处理消息
            response = await self._process_message(message)
            if response:
                responses.append(response)

        # 合并响应
        if responses:
            return b"".join(responses)
        return None

    async def _process_message(self, message: StateGrid57Message) -> Optional[bytes]:
        """
        处理单条消息

        Args:
            message: 解析后的消息

        Returns:
            响应数据
        """
        # 根据会话标识处理
        if message.session_source == "request":
            # 收到请求消息，需要响应
            if self.config.auto_response:
                return await self._handle_request(message)
        elif message.session_source == "response":
            # 收到响应消息
            return await self._handle_response(message)

        return None

    async def _handle_request(self, message: StateGrid57Message) -> Optional[bytes]:
        """
        处理请求消息

        Args:
            message: 请求消息

        Returns:
            响应数据
        """
        # 验证发送方
        if message.send_code != self.config.receive_code:
            log.warning(f"发送方不匹配: 期望={self.config.receive_code}, 实际={message.send_code}")

        # 验证接收方
        if message.receive_code != self.config.send_code:
            log.warning(f"接收方不匹配: 期望={self.config.send_code}, 实际={message.receive_code}")

        # 根据消息类型处理
        if message.message_type == MessageType.SYSTEM:
            return await self._handle_system_request(message)
        else:
            # 其他消息类型，返回成功响应
            return self._create_response(
                send_session_num=message.send_session_num,
                code=ResponseCode.SUCCESS,
                command=Command.RESPONSE,
            )

    async def _handle_system_request(self, message: StateGrid57Message) -> Optional[bytes]:
        """
        处理系统消息请求

        Args:
            message: 系统消息

        Returns:
            响应数据
        """
        command = message.message_command

        if command == Command.REGISTER:
            # 注册请求
            items = self._get_register_response_items()
            return self._create_response(
                send_session_num=message.send_session_num,
                code=ResponseCode.SUCCESS,
                command=Command.RESPONSE_WITH_DATA,
                items=items,
            )

        elif command == Command.HEARTBEAT:
            # 心跳请求
            return self._create_response(
                send_session_num=message.send_session_num,
                code=ResponseCode.SUCCESS,
                command=Command.RESPONSE,
            )

        else:
            # 未知指令
            return self._create_response(
                send_session_num=message.send_session_num,
                code=ResponseCode.ERROR,
                command=Command.RESPONSE,
            )

    async def _handle_response(self, message: StateGrid57Message) -> Optional[bytes]:
        """
        处理响应消息

        Args:
            message: 响应消息

        Returns:
            无需响应
        """
        # 检查是否有等待的请求
        session_num = message.receive_session_num
        if session_num in self._pending_requests:
            future = self._pending_requests.pop(session_num)
            if not future.done():
                future.set_result(message)

        # 处理注册响应
        if message.message_type == MessageType.SYSTEM:
            if message.message_command == Command.RESPONSE_WITH_DATA:
                # 注册成功，提取配置参数
                self._handle_register_response(message)

        return None

    def _handle_register_response(self, message: StateGrid57Message):
        """处理注册响应"""
        if message.items:
            item = message.items[0]

            # 更新心跳间隔
            if "heart_beat_interval" in item:
                self.config.heart_beat_interval = int(item["heart_beat_interval"])

            # 更新其他间隔
            if "patroldevice_run_interval" in item:
                self.config.patroldevice_run_interval = int(item["patroldevice_run_interval"])

            if "nest_run_interval" in item:
                self.config.nest_run_interval = int(item["nest_run_interval"])

            if "weather_interval" in item:
                self.config.weather_interval = int(item["weather_interval"])

            if "env_interval" in item:
                self.config.env_interval = int(item["env_interval"])

            if "run_params_interval" in item:
                self.config.run_params_interval = int(item["run_params_interval"])

            # 设置登录状态
            self._is_logged_in = True
            log.info(f"注册成功，心跳间隔: {self.config.heart_beat_interval}s")

    def _get_register_response_items(self) -> List[Dict[str, Any]]:
        """获取注册响应的数据项"""
        if self.config.device_mode.value == "Algo":
            return [
                {
                    "heart_beat_interval": str(self.config.heart_beat_interval),
                    "run_params_interval": str(self.config.run_params_interval),
                }
            ]
        else:
            return [
                {
                    "heart_beat_interval": str(self.config.heart_beat_interval),
                    "patroldevice_run_interval": str(self.config.patroldevice_run_interval),
                    "nest_run_interval": str(self.config.nest_run_interval),
                    "weather_interval": str(self.config.weather_interval),
                }
            ]

    def _create_response(
        self,
        send_session_num: int,
        code: str,
        command: str,
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> bytes:
        """
        创建响应消息

        Args:
            send_session_num: 原请求的会话序列号
            code: 响应码
            command: 指令
            items: 数据项

        Returns:
            响应报文
        """
        xml_content = StateGrid57Protocol.write_xml(
            node_type=self.config.node_type.value,
            send_code=self.config.send_code,
            receive_code=self.config.receive_code,
            message_type=MessageType.SYSTEM,
            message_code=code,
            message_command=command,
            items=items,
        )

        return StateGrid57Protocol.packetize(
            session_source="response",
            send_session_num=send_session_num,
            xml_content=xml_content,
        )

    # ==================== 发送消息方法 ====================

    def create_register_message(self) -> bytes:
        """创建注册消息"""
        session_num = self._get_next_session_num()

        xml_content = StateGrid57Protocol.write_xml(
            node_type=self.config.node_type.value,
            send_code=self.config.send_code,
            receive_code=self.config.receive_code,
            message_type=MessageType.SYSTEM,
            message_command=Command.REGISTER,
        )

        return StateGrid57Protocol.packetize(
            session_source="request",
            send_session_num=session_num,
            xml_content=xml_content,
        )

    def create_heartbeat_message(self) -> bytes:
        """创建心跳消息"""
        session_num = self._get_next_session_num()

        xml_content = StateGrid57Protocol.write_xml(
            node_type=self.config.node_type.value,
            send_code=self.config.send_code,
            receive_code=self.config.receive_code,
            message_type=MessageType.SYSTEM,
            message_command=Command.HEARTBEAT,
        )

        return StateGrid57Protocol.packetize(
            session_source="request",
            send_session_num=session_num,
            xml_content=xml_content,
        )

    def create_data_message(
        self,
        message_type: str,
        message_code: str = "",
        message_command: str = "",
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> bytes:
        """
        创建数据消息

        Args:
            message_type: 消息类型
            message_code: 消息编码
            message_command: 指令
            items: 数据项

        Returns:
            报文数据
        """
        session_num = self._get_next_session_num()

        xml_content = StateGrid57Protocol.write_xml(
            node_type=self.config.node_type.value,
            send_code=self.config.send_code,
            receive_code=self.config.receive_code,
            message_type=message_type,
            message_code=message_code,
            message_command=message_command,
            items=items,
        )

        return StateGrid57Protocol.packetize(
            session_source="request",
            send_session_num=session_num,
            xml_content=xml_content,
        )

    async def send_and_wait_response(
        self,
        message: bytes,
        timeout: float = 10.0,
    ) -> Optional[StateGrid57Message]:
        """
        发送消息并等待响应

        Args:
            message: 消息数据
            timeout: 超时时间（秒）

        Returns:
            响应消息
        """
        # 获取会话序列号
        session_num = self._session_counter

        # 创建等待 Future
        future: asyncio.Future[StateGrid57Message] = asyncio.get_event_loop().create_future()
        self._pending_requests[session_num] = future

        try:
            # 发送消息
            if self.on_send:
                self.on_send(message)

            # 等待响应
            return await asyncio.wait_for(future, timeout=timeout)

        except asyncio.TimeoutError:
            self._pending_requests.pop(session_num, None)
            log.warning(f"等待响应超时: session_num={session_num}")
            return None

        except Exception as e:
            self._pending_requests.pop(session_num, None)
            log.error(f"发送消息失败: {e}")
            return None

    # ==================== 心跳管理 ====================

    async def start_heartbeat(self):
        """启动心跳任务"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            return

        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        log.info("心跳任务已启动")

    async def stop_heartbeat(self):
        """停止心跳任务"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            log.info("心跳任务已停止")

    async def _heartbeat_loop(self):
        """心跳循环"""
        while True:
            try:
                # 等待登录成功
                if self._is_logged_in:
                    await asyncio.sleep(self.config.heart_beat_interval)

                    # 发送心跳
                    heartbeat = self.create_heartbeat_message()
                    if self.on_send:
                        self.on_send(heartbeat)
                        log.debug("心跳已发送")
                else:
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"心跳发送失败: {e}")
                await asyncio.sleep(5)

    @property
    def is_logged_in(self) -> bool:
        """是否已登录"""
        return self._is_logged_in

    def reset(self):
        """重置状态"""
        self._is_logged_in = False
        self._session_counter = 0
        self._pending_requests.clear()