"""
自动发送服务

管理会话的自动发送任务，支持：
- 每条消息独立定时器
- 与会话连接状态联动
- 启动/停止控制
- 状态推送
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.db.session import AsyncSessionLocal
from src.repositories.auto_send_repository import AutoSendConfigRepository
from src.schemas.auto_send import AutoSendConfigResponse
from src.utils.logger import get_logger
from src.utils.websocket_manager import push_notification

log = get_logger("auto_send_service")


@dataclass
class AutoSendTask:
    """自动发送任务"""

    config_id: int
    session_id: int
    message_content: str
    interval_ms: int
    task: Optional[asyncio.Task] = None
    is_running: bool = False
    send_count: int = 0
    last_send_at: Optional[datetime] = None


@dataclass
class SessionAutoSendManager:
    """会话自动发送管理器"""

    session_id: int
    tasks: Dict[int, AutoSendTask] = field(default_factory=dict)
    is_active: bool = False
    started_at: Optional[datetime] = None


class AutoSendService:
    """
    自动发送服务

    职责：
    1. 管理所有会话的自动发送任务
    2. 每条消息独立定时器执行
    3. 与会话连接状态联动
    4. 支持启动/停止/暂停/恢复
    """

    def __init__(self):
        # 会话自动发送管理器
        self._session_managers: Dict[int, SessionAutoSendManager] = {}
        # 发送回调函数
        self._send_callback: Optional[callable] = None

    def set_send_callback(self, callback: callable):
        """
        设置发送回调函数

        Args:
            callback: 异步回调函数，签名为 async (session_id: int, content: str) -> bool
        """
        self._send_callback = callback
        log.info("设置自动发送回调函数")

    async def load_configs(self, session_id: int) -> List[AutoSendConfigResponse]:
        """加载会话的自动发送配置"""
        async with AsyncSessionLocal() as db:
            repo = AutoSendConfigRepository(db)
            configs = await repo.get_by_session(session_id)
            return [AutoSendConfigResponse.model_validate(c) for c in configs]

    async def start(self, session_id: int) -> Dict[str, Any]:
        """
        启动会话的自动发送

        Args:
            session_id: 会话ID

        Returns:
            启动结果
        """
        # 检查是否已启动
        if session_id in self._session_managers and self._session_managers[session_id].is_active:
            log.warning(f"会话 {session_id} 的自动发送已在运行")
            return {
                "success": False,
                "message": "自动发送已在运行",
                "session_id": session_id,
            }

        # 加载配置
        configs = await self.load_configs(session_id)
        enabled_configs = [c for c in configs if c.is_enabled and c.message_content.strip()]

        if not enabled_configs:
            log.warning(f"会话 {session_id} 没有启用的自动发送配置")
            return {
                "success": False,
                "message": "没有启用的自动发送配置",
                "session_id": session_id,
            }

        # 创建会话管理器
        manager = SessionAutoSendManager(session_id=session_id)
        manager.started_at = datetime.now()

        # 为每条配置创建独立任务
        for config in enabled_configs:
            task = AutoSendTask(
                config_id=config.id,
                session_id=session_id,
                message_content=config.message_content,
                interval_ms=config.interval_ms if config.interval_ms >= 100 else 1000,
            )
            task.task = asyncio.create_task(
                self._run_task(session_id, task),
                name=f"auto_send_{session_id}_{config.id}",
            )
            task.is_running = True
            manager.tasks[config.id] = task

        manager.is_active = True
        self._session_managers[session_id] = manager

        log.info(f"启动自动发送: session_id={session_id}, 任务数={len(enabled_configs)}")

        # 推送通知
        await push_notification(
            title="自动发送",
            message=f"已启动 {len(enabled_configs)} 条自动发送任务",
            level="info",
        )

        return {
            "success": True,
            "message": f"已启动 {len(enabled_configs)} 条自动发送任务",
            "session_id": session_id,
            "task_count": len(enabled_configs),
            "started_at": manager.started_at.isoformat(),
        }

    async def stop(self, session_id: int) -> Dict[str, Any]:
        """
        停止会话的自动发送

        Args:
            session_id: 会话ID

        Returns:
            停止结果
        """
        if session_id not in self._session_managers:
            return {
                "success": True,
                "message": "自动发送未运行",
                "session_id": session_id,
            }

        manager = self._session_managers[session_id]
        stopped_count = 0

        # 取消所有任务
        for task_id, task in manager.tasks.items():
            if task.task and not task.task.done():
                task.task.cancel()
                try:
                    await task.task
                except asyncio.CancelledError:
                    pass
                task.is_running = False
                stopped_count += 1

        manager.is_active = False
        manager.tasks.clear()
        del self._session_managers[session_id]

        log.info(f"停止自动发送: session_id={session_id}, 已停止任务数={stopped_count}")

        # 推送通知
        await push_notification(
            title="自动发送",
            message=f"已停止 {stopped_count} 条自动发送任务",
            level="info",
        )

        return {
            "success": True,
            "message": f"已停止 {stopped_count} 条自动发送任务",
            "session_id": session_id,
            "stopped_count": stopped_count,
        }

    async def stop_all(self):
        """停止所有自动发送任务"""
        session_ids = list(self._session_managers.keys())
        for session_id in session_ids:
            await self.stop(session_id)
        log.info(f"已停止所有自动发送任务，共 {len(session_ids)} 个会话")

    def is_active(self, session_id: int) -> bool:
        """检查会话的自动发送是否在运行"""
        if session_id not in self._session_managers:
            return False
        return self._session_managers[session_id].is_active

    def get_status(self, session_id: int) -> Optional[Dict[str, Any]]:
        """获取会话自动发送状态"""
        if session_id not in self._session_managers:
            return None

        manager = self._session_managers[session_id]
        return {
            "session_id": session_id,
            "is_active": manager.is_active,
            "task_count": len(manager.tasks),
            "started_at": manager.started_at.isoformat() if manager.started_at else None,
            "tasks": [
                {
                    "config_id": task.config_id,
                    "is_running": task.is_running,
                    "send_count": task.send_count,
                    "last_send_at": task.last_send_at.isoformat() if task.last_send_at else None,
                }
                for task in manager.tasks.values()
            ],
        }

    async def _run_task(self, session_id: int, task: AutoSendTask):
        """
        运行单个自动发送任务

        Args:
            session_id: 会话ID
            task: 自动发送任务
        """
        interval_sec = task.interval_ms / 1000.0

        log.info(
            f"自动发送任务启动: session_id={session_id}, config_id={task.config_id}, "
            f"interval={task.interval_ms}ms"
        )

        try:
            while task.is_running:
                # 执行发送
                if self._send_callback:
                    try:
                        success = await self._send_callback(session_id, task.message_content, is_auto_send=True)
                        if success:
                            task.send_count += 1
                            task.last_send_at = datetime.now()
                    except Exception as e:
                        log.error(f"自动发送失败: {e}")

                # 等待间隔
                await asyncio.sleep(interval_sec)

        except asyncio.CancelledError:
            log.info(f"自动发送任务被取消: session_id={session_id}, config_id={task.config_id}")
        except Exception as e:
            log.error(f"自动发送任务异常: session_id={session_id}, config_id={task.config_id}, error={e}")
        finally:
            task.is_running = False

    async def reload_configs(self, session_id: int):
        """
        重新加载会话的自动发送配置

        如果自动发送正在运行，会先停止再重新启动
        """
        was_active = self.is_active(session_id)
        if was_active:
            await self.stop(session_id)
            await self.start(session_id)
            log.info(f"重新加载自动发送配置: session_id={session_id}")


# ==================== 全局实例 ====================

auto_send_service = AutoSendService()