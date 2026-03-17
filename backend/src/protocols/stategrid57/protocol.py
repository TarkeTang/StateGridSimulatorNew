"""
国网57号文协议消息处理器

实现消息的打包、解包、XML解析等功能
"""

from __future__ import annotations

import binascii
import struct
import time
import xml.dom.minidom as minidom
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StateGrid57Message:
    """国网57号文消息结构"""

    # 会话信息
    send_session_num: int = 0  # 发送会话序列号
    receive_session_num: int = 0  # 接收会话序列号
    session_source: str = "request"  # 会话标识: request(00)/response(01)

    # XML 内容
    send_code: str = ""  # 发送方标识
    receive_code: str = ""  # 接收方标识
    message_type: str = ""  # 消息类型
    message_code: str = ""  # 消息编码
    message_command: str = ""  # 指令
    message_time: str = ""  # 时间
    items: List[Dict[str, Any]] = field(default_factory=list)  # 数据项列表

    # 原始数据
    raw_xml: str = ""
    raw_bytes: bytes = b""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "send_session_num": self.send_session_num,
            "receive_session_num": self.receive_session_num,
            "session_source": self.session_source,
            "send_code": self.send_code,
            "receive_code": self.receive_code,
            "message_type": self.message_type,
            "message_code": self.message_code,
            "message_command": self.message_command,
            "message_time": self.message_time,
            "items": self.items,
            "raw_xml": self.raw_xml,
        }


class StateGrid57Protocol:
    """
    国网57号文协议处理器

    实现消息的打包、解包、XML解析
    """

    # 报文头尾标识
    PACKET_HEADER = b"\xeb\x90"
    PACKET_FOOTER = b"\xeb\x90"

    # 会话标识
    SESSION_REQUEST = "00"  # 请求
    SESSION_RESPONSE = "01"  # 响应

    @classmethod
    def write_xml(
        cls,
        node_type: str,
        send_code: str,
        receive_code: str,
        message_type: str,
        message_code: str = "",
        message_command: str = "",
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        生成 XML 消息内容

        Args:
            node_type: 节点类型
            send_code: 发送方标识
            receive_code: 接收方标识
            message_type: 消息类型
            message_code: 消息编码
            message_command: 指令
            items: 数据项列表

        Returns:
            XML 字符串
        """
        dom = minidom.getDOMImplementation().createDocument(None, node_type, None)
        root = dom.documentElement

        # 添加基本元素
        elements = [
            ("SendCode", send_code),
            ("ReceiveCode", receive_code),
            ("Type", message_type),
            ("Code", message_code),
            ("Command", message_command),
            ("Time", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
        ]

        for tag, value in elements:
            element = dom.createElement(tag)
            element.appendChild(dom.createTextNode(value))
            root.appendChild(element)

        # 添加数据项
        items_element = dom.createElement("Items")
        root.appendChild(items_element)

        if items:
            for item in items:
                item_element = dom.createElement("Item")
                for k, v in item.items():
                    item_element.setAttribute(k, str(v))
                items_element.appendChild(item_element)

        # 生成 XML 字符串
        return root.toxml()

    @classmethod
    def read_xml(cls, xml_content: str) -> Dict[str, Any]:
        """
        解析 XML 消息内容

        Args:
            xml_content: XML 字符串

        Returns:
            解析后的字典
        """
        try:
            root = minidom.parseString(xml_content).documentElement

            def get_element_text(tag_name: str, default: str = "") -> str:
                elements = root.getElementsByTagName(tag_name)
                if elements and elements[0].childNodes:
                    return elements[0].childNodes[0].data
                return default

            # 解析数据项
            items = []
            items_elements = root.getElementsByTagName("Items")
            if items_elements:
                for items_element in items_elements:
                    for item in items_element.getElementsByTagName("Item"):
                        item_dict = {k: v for k, v in item.attributes.items()}
                        if item_dict:
                            items.append(item_dict)

            return {
                "node_name": root.nodeName,
                "send_code": get_element_text("SendCode"),
                "receive_code": get_element_text("ReceiveCode"),
                "message_type": get_element_text("Type"),
                "message_code": get_element_text("Code"),
                "message_command": get_element_text("Command"),
                "message_time": get_element_text("Time"),
                "items": items,
            }
        except Exception as e:
            return {"error": str(e), "raw": xml_content}

    @classmethod
    def packetize(
        cls,
        session_source: str,
        send_session_num: int,
        xml_content: str,
        receive_session_num: int = 0,
    ) -> bytes:
        """
        打包消息

        Args:
            session_source: 会话标识 (request/response)
            send_session_num: 发送会话序列号
            xml_content: XML 内容
            receive_session_num: 接收会话序列号

        Returns:
            打包后的字节流
        """
        # 会话标识（1字节）
        if session_source == "request":
            session_source_id = bytes([0x00])  # 请求
            send_num = send_session_num
            recv_num = 0
        elif session_source == "response":
            session_source_id = bytes([0x01])  # 响应
            send_num = 0
            recv_num = receive_session_num
        else:
            session_source_id = bytes([0x02])
            send_num = send_session_num
            recv_num = receive_session_num

        # 构建报文
        send_session_bytes = struct.pack("<q", send_num)  # 小端序，8字节
        receive_session_bytes = struct.pack("<q", recv_num)  # 小端序，8字节
        xml_length_bytes = struct.pack("<i", len(xml_content.encode("utf-8")))  # 小端序，4字节
        xml_bytes = xml_content.encode("utf-8")

        # 拼接报文
        message = (
            cls.PACKET_HEADER
            + send_session_bytes
            + receive_session_bytes
            + session_source_id
            + xml_length_bytes
            + xml_bytes
            + cls.PACKET_FOOTER
        )

        return message

    @classmethod
    def depacketize(cls, data: bytes) -> Optional[StateGrid57Message]:
        """
        解包消息

        Args:
            data: 报文数据（不含头尾标识）

        Returns:
            解析后的消息对象
        """
        try:
            if len(data) < 21:  # 最小长度：8+8+1+4=21
                return None

            # 解析各字段
            send_session_num = struct.unpack("<q", data[0:8])[0]
            receive_session_num = struct.unpack("<q", data[8:16])[0]
            session_source_id = data[16:17].decode()

            xml_length = struct.unpack("<i", data[17:21])[0]
            xml_bytes = data[21 : 21 + xml_length]

            try:
                xml_content = xml_bytes.decode("utf-8")
            except UnicodeDecodeError:
                xml_content = xml_bytes.decode("gbk", errors="ignore")

            # 解析 XML
            parsed = cls.read_xml(xml_content)

            # 构建消息对象
            message = StateGrid57Message(
                send_session_num=send_session_num,
                receive_session_num=receive_session_num,
                session_source="request" if session_source_id == cls.SESSION_REQUEST else "response",
                send_code=parsed.get("send_code", ""),
                receive_code=parsed.get("receive_code", ""),
                message_type=parsed.get("message_type", ""),
                message_code=parsed.get("message_code", ""),
                message_command=parsed.get("message_command", ""),
                message_time=parsed.get("message_time", ""),
                items=parsed.get("items", []),
                raw_xml=xml_content,
                raw_bytes=data,
            )

            return message

        except Exception as e:
            return None

    @classmethod
    def split_packets(cls, data: bytes) -> List[bytes]:
        """
        从数据流中分割出完整的报文

        Args:
            data: 原始数据流

        Returns:
            完整报文列表（不含头尾标识）
        """
        packets = []

        # 检查是否以 EB90 开头和结尾
        if not data.startswith(cls.PACKET_HEADER):
            return packets

        # 分割报文
        parts = data.split(cls.PACKET_HEADER)

        for part in parts:
            if not part:
                continue

            # 检查是否以 EB90 结尾
            if part.endswith(cls.PACKET_FOOTER):
                # 去掉结尾标识
                packet_data = part[: -len(cls.PACKET_FOOTER)]
                if packet_data:
                    packets.append(packet_data)

        return packets

    @classmethod
    def is_complete_packet(cls, data: bytes) -> bool:
        """
        检查是否是完整的报文

        Args:
            data: 数据

        Returns:
            是否完整
        """
        if not data.startswith(cls.PACKET_HEADER):
            return False
        if not data.endswith(cls.PACKET_FOOTER):
            return False
        return True

    @classmethod
    def format_hex_display(cls, data: bytes) -> str:
        """
        格式化十六进制显示

        Args:
            data: 字节数据

        Returns:
            格式化的十六进制字符串
        """
        return binascii.hexlify(data).decode().upper()


# 消息类型常量
class MessageType:
    """消息类型常量"""

    # 系统消息
    SYSTEM = "251"  # 注册/心跳/响应

    # 巡视设备相关
    PATROL_DEVICE_STATUS = "61"  # 巡视装置运行数据
    PATROL_DEVICE_CONTROL = "62"  # 巡视装置控制
    PATROL_DEVICE_ALARM = "63"  # 巡视装置告警

    # 无人机相关
    DRONE_STATUS = "71"  # 无人机运行数据
    DRONE_NEST_STATUS = "72"  # 无人机机巢运行数据
    DRONE_CONTROL = "73"  # 无人机控制

    # 环境数据
    WEATHER_DATA = "81"  # 气象数据
    ENV_DATA = "82"  # 环境数据

    # 监视数据
    MONITOR_DATA = "64"  # 静默监视数据

    # 算法相关
    ALGO_STATUS = "316"  # 算法状态
    ALGO_RESULT = "41"  # 算法结果


# 指令常量
class Command:
    """指令常量"""

    REGISTER = "1"  # 注册
    HEARTBEAT = "2"  # 心跳
    RESPONSE = "3"  # 响应（确认/拒绝/错误）
    RESPONSE_WITH_DATA = "4"  # 响应（带数据）


# 响应码常量
class ResponseCode:
    """响应码常量"""

    CONTINUE = "100"  # 需重发
    SUCCESS = "200"  # 成功
    REJECTED = "400"  # 拒绝
    ERROR = "500"  # 错误