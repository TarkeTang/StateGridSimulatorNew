"""
参数替换工具

支持类似 JMeter 的参数化功能，在消息内容中使用 ${参数名} 格式
发送时自动替换为实际值
"""

from __future__ import annotations

import json
import random
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.models.parameter import ParameterConfig

# 中国时区 UTC+8
CHINA_TIMEZONE = timezone.utc


def get_now() -> datetime:
    """获取当前时间（使用系统本地时区）"""
    return datetime.now()


def get_local_timestamp_ms() -> int:
    """获取当前时间戳（毫秒）"""
    return int(get_now().timestamp() * 1000)


def get_local_timestamp_s() -> int:
    """获取当前时间戳（秒）"""
    return int(get_now().timestamp())


class ParameterResolver:
    """
    参数解析器

    支持的参数类型：
    - static: 静态值，直接返回配置的值
    - timestamp: 时间戳，支持格式化
    - random: 随机数，支持整数和小数
    - uuid: UUID
    - counter: 计数器
    - custom: 自定义函数
    """

    # 内置参数（无需配置即可使用）
    BUILTIN_PARAMS = {
        "timestamp": lambda: str(get_local_timestamp_ms()),
        "timestamp_s": lambda: str(get_local_timestamp_s()),
        "datetime": lambda: get_now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": lambda: get_now().strftime("%Y-%m-%d"),
        "time": lambda: get_now().strftime("%H:%M:%S"),
        "uuid": lambda: str(uuid.uuid4()),
        "uuid_short": lambda: str(uuid.uuid4()).replace("-", ""),
        "random_int": lambda: str(random.randint(0, 999999)),
        "random_str": lambda: "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8)),
    }

    def __init__(self, parameters: Optional[List[ParameterConfig]] = None):
        """
        初始化参数解析器

        Args:
            parameters: 参数配置列表
        """
        self.parameters = {p.name: p for p in (parameters or [])}
        self._counter_values: Dict[str, int] = {}

    def resolve(self, name: str) -> Optional[str]:
        """
        解析单个参数

        Args:
            name: 参数名称

        Returns:
            参数值
        """
        # 1. 先检查内置参数
        if name in self.BUILTIN_PARAMS:
            return self.BUILTIN_PARAMS[name]()

        # 2. 检查自定义参数
        if name not in self.parameters:
            return None

        param = self.parameters[name]
        if not param.is_enabled:
            return None

        return self._resolve_param(param)

    def _resolve_param(self, param: ParameterConfig) -> str:
        """
        根据参数类型解析参数值

        Args:
            param: 参数配置

        Returns:
            参数值
        """
        param_type = param.param_type

        if param_type == "static":
            return param.static_value or ""

        elif param_type == "timestamp":
            return self._resolve_timestamp(param)

        elif param_type == "random":
            return self._resolve_random(param)

        elif param_type == "uuid":
            return str(uuid.uuid4())

        elif param_type == "counter":
            return self._resolve_counter(param)

        elif param_type == "custom":
            return self._resolve_custom(param)

        return param.static_value or ""

    def _resolve_timestamp(self, param: ParameterConfig) -> str:
        """解析时间戳参数"""
        config = json.loads(param.config) if param.config else {}
        fmt = config.get("format", "%Y%m%d%H%M%S")
        unit = config.get("unit", "formatted")  # formatted, ms, s

        if unit == "ms":
            return str(get_local_timestamp_ms())
        elif unit == "s":
            return str(get_local_timestamp_s())
        else:
            return get_now().strftime(fmt)

    def _resolve_random(self, param: ParameterConfig) -> str:
        """解析随机数参数"""
        config = json.loads(param.config) if param.config else {}
        rand_type = config.get("type", "int")
        min_val = config.get("min", 0)
        max_val = config.get("max", 100)
        length = config.get("length", 8)

        if rand_type == "int":
            return str(random.randint(int(min_val), int(max_val)))
        elif rand_type == "float":
            return str(random.uniform(float(min_val), float(max_val)))
        elif rand_type == "string":
            chars = config.get("chars", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            return "".join(random.choices(chars, k=int(length)))
        elif rand_type == "hex":
            return "".join(random.choices("0123456789ABCDEF", k=int(length)))

        return str(random.randint(int(min_val), int(max_val)))

    def _resolve_counter(self, param: ParameterConfig) -> str:
        """解析计数器参数"""
        config = json.loads(param.config) if param.config else {}
        start = config.get("start", 1)
        increment = config.get("increment", 1)
        max_val = config.get("max", 999999)

        name = param.name
        if name not in self._counter_values:
            self._counter_values[name] = start
        else:
            self._counter_values[name] += increment
            if self._counter_values[name] > max_val:
                self._counter_values[name] = start

        return str(self._counter_values[name])

    def _resolve_custom(self, param: ParameterConfig) -> str:
        """解析自定义函数参数"""
        config = json.loads(param.config) if param.config else {}
        expression = config.get("expression", "")

        # 支持简单的表达式
        # 例如: ${timestamp}_prefix, prefix_${uuid}_suffix
        if expression:
            return self.replace_params(expression)

        return param.static_value or ""

    def replace_params(self, content: str) -> str:
        """
        替换内容中的所有参数

        Args:
            content: 原始内容

        Returns:
            替换后的内容
        """
        if not content:
            return content

        # 匹配 ${参数名} 格式
        pattern = r'\$\{([^}]+)\}'

        def replace_match(match):
            param_name = match.group(1)
            value = self.resolve(param_name)
            return value if value is not None else match.group(0)

        return re.sub(pattern, replace_match, content)


async def resolve_parameters(content: str, db_session=None) -> str:
    """
    解析内容中的参数（异步版本，从数据库加载参数配置）

    Args:
        content: 原始内容
        db_session: 数据库会话（可选）

    Returns:
        替换后的内容
    """
    # 如果没有数据库会话，只使用内置参数
    if db_session is None:
        resolver = ParameterResolver()
        return resolver.replace_params(content)

    # 从数据库加载参数配置
    from src.repositories.parameter_repository import ParameterRepository

    repo = ParameterRepository(db_session)
    parameters = await repo.get_all_enabled()

    resolver = ParameterResolver(parameters)
    return resolver.replace_params(content)


def resolve_parameters_sync(content: str, parameters: Optional[List[ParameterConfig]] = None) -> str:
    """
    解析内容中的参数（同步版本）

    Args:
        content: 原始内容
        parameters: 参数配置列表（可选）

    Returns:
        替换后的内容
    """
    resolver = ParameterResolver(parameters)
    return resolver.replace_params(content)