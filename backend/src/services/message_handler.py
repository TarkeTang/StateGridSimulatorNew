"""
消息处理服务

统一处理会话消息的接收、发送、持久化和推送
支持消息解析、转换、过滤等扩展功能
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol

from src.db.session import AsyncSessionLocal
from src.repositories.message_repository import MessageRepository
from src.schemas.session import SessionMessageCreate
from src.utils.logger import get_logger
from src.utils.websocket_manager import push_communication_message, push_session_status

log = get_logger("message_handler")


class MessageProcessor(Protocol):
    """消息处理器协议"""

    async def process(self, content: str, direction: str, context: Dict[str, Any]) -> str:
        """处理消息内容，返回处理后的内容"""
        ...


class MessageHandler:
    """
    消息处理服务

    职责：
    1. 消息接收和发送的处理
    2. 消息持久化到数据库
    3. 通过 WebSocket 实时推送
    4. 支持消息处理器链（解析、转换、过滤）
    """

    def __init__(self):
        # 消息处理器链
        self.processors: List[MessageProcessor] = []
        # 会话信息缓存
        self._session_cache: Dict[int, Dict[str, Any]] = {}

    def add_processor(self, processor: MessageProcessor):
        """添加消息处理器"""
        self.processors.append(processor)
        log.info(f"添加消息处理器: {processor.__class__.__name__}")

    def remove_processor(self, processor: MessageProcessor):
        """移除消息处理器"""
        if processor in self.processors:
            self.processors.remove(processor)
            log.info(f"移除消息处理器: {processor.__class__.__name__}")

    def register_session(self, session_id: int, session_name: str, protocol_type: str):
        """注册会话信息到缓存"""
        self._session_cache[session_id] = {
            "session_name": session_name,
            "protocol_type": protocol_type,
            "registered_at": datetime.now().isoformat(),
        }
        log.info(f"注册会话: session_id={session_id}, name={session_name}")

    def unregister_session(self, session_id: int):
        """注销会话信息"""
        if session_id in self._session_cache:
            del self._session_cache[session_id]
            log.info(f"注销会话: session_id={session_id}")

    def get_session_info(self, session_id: int) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self._session_cache.get(session_id)

    async def handle_send(
        self,
        session_id: int,
        content: str,
        is_auto_send: bool = False,
        save_to_db: bool = True,
    ) -> Dict[str, Any]:
        """
        处理发送消息

        Args:
            session_id: 会话ID
            content: 消息内容
            is_auto_send: 是否为自动发送
            save_to_db: 是否保存到数据库

        Returns:
            处理结果
        """
        session_info = self.get_session_info(session_id)
        session_name = session_info.get("session_name", "") if session_info else ""
        protocol_type = session_info.get("protocol_type", "TCP") if session_info else "TCP"

        # 处理器链处理
        processed_content = content
        context = {"session_id": session_id, "direction": "send", "is_auto_send": is_auto_send}
        for processor in self.processors:
            try:
                processed_content = await processor.process(processed_content, "send", context)
            except Exception as e:
                log.error(f"消息处理器执行失败: {e}")

        # 构建额外数据
        extra_data = {}
        if is_auto_send:
            extra_data["is_auto_send"] = True

        # 保存到数据库
        message_record = None
        if save_to_db:
            try:
                async with AsyncSessionLocal() as db:
                    repo = MessageRepository(db)
                    message_record = await repo.create(
                        SessionMessageCreate(
                            session_id=session_id,
                            session_name=session_name,
                            direction="send",
                            content=processed_content,
                            protocol_type=protocol_type,
                            extra_data=json.dumps(extra_data) if extra_data else None,
                        )
                    )
                    await db.commit()
                    log.info(f"发送消息已保存: session_id={session_id}, length={len(processed_content)}")
            except Exception as e:
                log.error(f"保存发送消息失败: {e}")

        # 推送到 WebSocket
        log.info(f"推送发送消息到WebSocket: session_id={session_id}, content={processed_content[:50]}...")
        await push_communication_message(
            session_id=session_id,
            direction="send",
            content=processed_content,
            extra_data=extra_data,
        )

        return {
            "success": True,
            "content": processed_content,
            "message_id": message_record.id if message_record else None,
            "timestamp": datetime.now().isoformat(),
        }

    async def handle_receive(
        self,
        session_id: int,
        content: str,
        content_hex: Optional[str] = None,
        save_to_db: bool = True,
    ) -> Dict[str, Any]:
        """
        处理接收消息

        Args:
            session_id: 会话ID
            content: 消息内容
            content_hex: 十六进制内容
            save_to_db: 是否保存到数据库

        Returns:
            处理结果
        """
        session_info = self.get_session_info(session_id)
        session_name = session_info.get("session_name", "") if session_info else ""
        protocol_type = session_info.get("protocol_type", "TCP") if session_info else "TCP"

        # 处理器链处理
        processed_content = content
        context = {"session_id": session_id, "direction": "receive"}
        for processor in self.processors:
            try:
                processed_content = await processor.process(processed_content, "receive", context)
            except Exception as e:
                log.error(f"消息处理器执行失败: {e}")

        # 保存到数据库
        message_record = None
        if save_to_db:
            try:
                async with AsyncSessionLocal() as db:
                    repo = MessageRepository(db)
                    message_record = await repo.create(
                        SessionMessageCreate(
                            session_id=session_id,
                            session_name=session_name,
                            direction="receive",
                            content=processed_content,
                            content_hex=content_hex,
                            protocol_type=protocol_type,
                        )
                    )
                    await db.commit()
                    log.info(f"接收消息已保存: session_id={session_id}, length={len(processed_content)}")
            except Exception as e:
                log.error(f"保存接收消息失败: {e}")

        # 推送到 WebSocket
        log.info(f"推送接收消息到WebSocket: session_id={session_id}, content={processed_content[:50]}...")
        await push_communication_message(
            session_id=session_id,
            direction="receive",
            content=processed_content,
            content_hex=content_hex,
        )

        return {
            "success": True,
            "content": processed_content,
            "message_id": message_record.id if message_record else None,
            "timestamp": datetime.now().isoformat(),
        }

    async def handle_system(
        self,
        session_id: int,
        content: str,
        save_to_db: bool = True,
    ) -> Dict[str, Any]:
        """
        处理系统消息

        Args:
            session_id: 会话ID
            content: 消息内容
            save_to_db: 是否保存到数据库

        Returns:
            处理结果
        """
        session_info = self.get_session_info(session_id)
        session_name = session_info.get("session_name", "") if session_info else ""
        protocol_type = session_info.get("protocol_type", "TCP") if session_info else "TCP"

        # 保存到数据库
        message_record = None
        if save_to_db:
            try:
                async with AsyncSessionLocal() as db:
                    repo = MessageRepository(db)
                    message_record = await repo.create(
                        SessionMessageCreate(
                            session_id=session_id,
                            session_name=session_name,
                            direction="system",
                            content=content,
                            protocol_type=protocol_type,
                        )
                    )
                    await db.commit()
                    log.info(f"系统消息已保存: session_id={session_id}")
            except Exception as e:
                log.error(f"保存系统消息失败: {e}")

        # 推送到 WebSocket
        log.info(f"推送系统消息到WebSocket: session_id={session_id}, content={content[:50]}...")
        await push_communication_message(
            session_id=session_id,
            direction="system",
            content=content,
        )

        return {
            "success": True,
            "content": content,
            "message_id": message_record.id if message_record else None,
            "timestamp": datetime.now().isoformat(),
        }


# ==================== 内置消息处理器 ====================


class HexConverterProcessor:
    """十六进制转换处理器"""

    def __init__(self, encoding: str = "UTF-8"):
        self.encoding = encoding

    async def process(self, content: str, direction: str, context: Dict[str, Any]) -> str:
        """处理消息内容"""
        # 如果内容是有效的十六进制，尝试转换
        return content


class JsonParserProcessor:
    """JSON 解析处理器"""

    async def process(self, content: str, direction: str, context: Dict[str, Any]) -> str:
        """尝试解析 JSON，格式化输出"""
        try:
            data = json.loads(content)
            context["parsed_json"] = data
            return json.dumps(data, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            return content


class XmlParserProcessor:
    """XML 解析处理器"""

    async def process(self, content: str, direction: str, context: Dict[str, Any]) -> str:
        """尝试解析 XML，格式化输出"""
        if content.strip().startswith("<"):
            context["is_xml"] = True
        return content


class TimestampProcessor:
    """时间戳处理器"""

    async def process(self, content: str, direction: str, context: Dict[str, Any]) -> str:
        """添加时间戳信息到上下文"""
        context["processed_at"] = datetime.now().isoformat()
        return content


# ==================== 全局实例 ====================

message_handler = MessageHandler()