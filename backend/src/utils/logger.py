"""
日志系统模块

提供统一的日志记录功能，支持：
- 按时间轮转日志文件
- 自动清理过期日志
- 多级别日志输出
- 结构化日志格式

日志格式：
[2026-03-16 15:30:25.123] [INFO ] [main] [UserService:45] - 用户登录成功，ID:1001
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger


class AppLogger:
    """应用日志管理器"""

    _initialized: bool = False

    @classmethod
    def setup(
        cls,
        log_level: str = "INFO",
        log_dir: str = "logs",
        rotation: str = "00:00",
        retention: str = "30 days",
        compression: str = "zip",
        enable_console: bool = True,
        enable_file: bool = True,
        max_file_size: str = "50 MB",
    ) -> None:
        """
        初始化日志配置

        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: 日志目录路径
            rotation: 轮转时间，如 "00:00" 表示每天午夜轮转
            retention: 日志保留时间，如 "30 days"
            compression: 压缩格式 (zip, gz, tar.gz)
            enable_console: 是否启用控制台输出
            enable_file: 是否启用文件输出
            max_file_size: 单个日志文件最大大小
        """
        if cls._initialized:
            logger.warning("日志系统已初始化，跳过重复初始化")
            return

        # 移除默认处理器
        logger.remove()

        # 日志格式：[时间戳] [级别] [线程] [模块:行号] - 消息
        log_format = (
            "[{time:YYYY-MM-DD HH:mm:ss.SSS}] "
            "[{level: <5}] "
            "[{thread}] "
            "[{module}:{line}] - {message}"
        )

        # 控制台输出（带颜色）
        if enable_console:
            logger.add(
                sys.stdout,
                format=log_format,
                level=log_level,
                colorize=True,
                enqueue=True,
            )

        if enable_file:
            # 确保日志目录存在
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)

            # 主日志文件 - 按日期轮转
            logger.add(
                log_path / "app_{time:YYYY-MM-DD}.log",
                format=log_format,
                level=log_level,
                rotation=rotation,
                retention=retention,
                compression=compression,
                encoding="utf-8",
                enqueue=True,
            )

            # 错误日志单独文件
            logger.add(
                log_path / "error_{time:YYYY-MM-DD}.log",
                format=log_format,
                level="ERROR",
                rotation=rotation,
                retention=retention,
                compression=compression,
                encoding="utf-8",
                enqueue=True,
            )

            # 按大小轮转的日志（防止单文件过大）
            logger.add(
                log_path / "app_size.log",
                format=log_format,
                level=log_level,
                rotation=max_file_size,
                retention=retention,
                compression=compression,
                encoding="utf-8",
                enqueue=True,
            )

        cls._initialized = True
        logger.info(
            "日志系统初始化完成",
            extra={
                "log_level": log_level,
                "log_dir": log_dir,
                "rotation": rotation,
                "retention": retention,
            },
        )

    @classmethod
    def get_logger(cls, name: str = "app"):
        """
        获取绑定名称的日志器

        Args:
            name: 日志器名称，通常使用模块名

        Returns:
            绑定名称的 Logger 实例
        """
        return logger.bind(name=name)

    @classmethod
    def log_request(
        cls,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_ip: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> None:
        """记录 HTTP 请求日志"""
        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": f"{duration_ms:.2f}",
        }
        if client_ip:
            log_data["client_ip"] = client_ip
        if user_id:
            log_data["user_id"] = user_id

        # 格式化附加数据
        extra_str = " | " + ", ".join(f"{k}={v}" for k, v in log_data.items())

        if status_code >= 500:
            logger.error(f"HTTP请求失败{extra_str}")
        elif status_code >= 400:
            logger.warning(f"HTTP请求异常{extra_str}")
        else:
            logger.info(f"HTTP请求完成{extra_str}")

    @classmethod
    def log_exception(cls, exception: Exception, context: Optional[dict] = None) -> None:
        """
        记录异常日志

        Args:
            exception: 异常对象
            context: 上下文信息
        """
        extra_str = ""
        if context:
            extra_str = " | " + ", ".join(f"{k}={v}" for k, v in context.items())

        logger.exception(f"发生异常: {type(exception).__name__}: {str(exception)}{extra_str}")


def setup_logger(**kwargs) -> None:
    """便捷函数：初始化日志系统"""
    AppLogger.setup(**kwargs)


def get_logger(name: str = "app"):
    """便捷函数：获取日志器"""
    return AppLogger.get_logger(name)


# 创建模块级日志器
log = get_logger("app")