"""
自动发送配置 API 端点

提供自动发送配置的 RESTful API 接口，包括：
- 配置的 CRUD 操作
- 自动发送任务的启动/停止
- 状态查询
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_session
from src.repositories.auto_send_repository import AutoSendConfigRepository
from src.schemas.auto_send import (
    AutoSendConfigCreate,
    AutoSendConfigUpdate,
    AutoSendConfigResponse,
    AutoSendConfigListResponse,
    AutoSendConfigBatchCreate,
    AutoSendConfigBatchUpdate,
    AutoSendConfigReorder,
)
from src.schemas.base import BaseResponse
from src.services.auto_send_service import auto_send_service
from src.utils.logger import get_logger
from src.utils.tcp_manager import tcp_manager

router = APIRouter()
log = get_logger("api.auto_send")


@router.post(
    "",
    response_model=BaseResponse[AutoSendConfigResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建自动发送配置",
    description="创建新的自动发送配置",
)
async def create_config(
    data: AutoSendConfigCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """创建自动发送配置"""
    try:
        repo = AutoSendConfigRepository(db)
        result = await repo.create(data)
        await db.commit()
        log.info(f"创建自动发送配置成功: session_id={data.session_id}")
        return BaseResponse(data=AutoSendConfigResponse.model_validate(result), message="创建成功")
    except Exception as e:
        await db.rollback()
        log.error(f"创建自动发送配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建失败",
        )


@router.get(
    "/session/{session_id}",
    response_model=BaseResponse[AutoSendConfigListResponse],
    summary="获取会话的自动发送配置列表",
    description="获取指定会话的所有自动发送配置",
)
async def get_config_list(
    session_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """获取会话的自动发送配置列表"""
    repo = AutoSendConfigRepository(db)
    items = await repo.get_by_session(session_id)
    return BaseResponse(
        data=AutoSendConfigListResponse(
            items=[AutoSendConfigResponse.model_validate(item) for item in items],
            total=len(items),
        )
    )


@router.get(
    "/{config_id}",
    response_model=BaseResponse[AutoSendConfigResponse],
    summary="获取自动发送配置详情",
    description="根据ID获取自动发送配置详情",
)
async def get_config(
    config_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """获取自动发送配置详情"""
    repo = AutoSendConfigRepository(db)
    result = await repo.get_by_id(config_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )
    return BaseResponse(data=AutoSendConfigResponse.model_validate(result))


@router.put(
    "/{config_id}",
    response_model=BaseResponse[AutoSendConfigResponse],
    summary="更新自动发送配置",
    description="更新指定ID的自动发送配置",
)
async def update_config(
    config_id: int,
    data: AutoSendConfigUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """更新自动发送配置"""
    try:
        repo = AutoSendConfigRepository(db)
        result = await repo.update(config_id, data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在",
            )
        await db.commit()
        log.info(f"更新自动发送配置成功: id={config_id}")
        return BaseResponse(data=AutoSendConfigResponse.model_validate(result), message="更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        log.error(f"更新自动发送配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败",
        )


@router.delete(
    "/{config_id}",
    response_model=BaseResponse[None],
    summary="删除自动发送配置",
    description="删除指定ID的自动发送配置",
)
async def delete_config(
    config_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """删除自动发送配置"""
    repo = AutoSendConfigRepository(db)
    success = await repo.delete(config_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )
    await db.commit()
    log.info(f"删除自动发送配置成功: id={config_id}")
    return BaseResponse(message="删除成功")


@router.post(
    "/batch",
    response_model=BaseResponse[List[AutoSendConfigResponse]],
    status_code=status.HTTP_201_CREATED,
    summary="批量创建自动发送配置",
    description="批量创建指定会话的自动发送配置",
)
async def batch_create_configs(
    data: AutoSendConfigBatchCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """批量创建自动发送配置"""
    try:
        repo = AutoSendConfigRepository(db)
        configs = [c.model_dump() for c in data.configs]
        result = await repo.batch_create(data.session_id, configs)
        await db.commit()
        log.info(f"批量创建自动发送配置成功: session_id={data.session_id}, count={len(result)}")
        return BaseResponse(
            data=[AutoSendConfigResponse.model_validate(r) for r in result],
            message=f"成功创建 {len(result)} 条配置",
        )
    except Exception as e:
        await db.rollback()
        log.error(f"批量创建自动发送配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建失败",
        )


@router.put(
    "/batch",
    response_model=BaseResponse[List[AutoSendConfigResponse]],
    summary="批量更新自动发送配置",
    description="批量更新自动发送配置",
)
async def batch_update_configs(
    data: AutoSendConfigBatchUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """批量更新自动发送配置"""
    try:
        repo = AutoSendConfigRepository(db)
        result = await repo.batch_update(data.configs)
        await db.commit()
        log.info(f"批量更新自动发送配置成功: count={len(result)}")
        return BaseResponse(
            data=[AutoSendConfigResponse.model_validate(r) for r in result],
            message=f"成功更新 {len(result)} 条配置",
        )
    except Exception as e:
        await db.rollback()
        log.error(f"批量更新自动发送配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败",
        )


@router.delete(
    "/session/{session_id}",
    response_model=BaseResponse[None],
    summary="清空会话的自动发送配置",
    description="删除指定会话的所有自动发送配置",
)
async def clear_session_configs(
    session_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """清空会话的自动发送配置"""
    repo = AutoSendConfigRepository(db)
    count = await repo.delete_by_session(session_id)
    await db.commit()
    log.info(f"清空会话自动发送配置: session_id={session_id}, count={count}")
    return BaseResponse(message=f"已删除 {count} 条配置")


@router.post(
    "/reorder",
    response_model=BaseResponse[None],
    summary="重新排序",
    description="重新排序自动发送配置",
)
async def reorder_configs(
    data: AutoSendConfigReorder,
    db: AsyncSession = Depends(get_db_session),
):
    """重新排序"""
    repo = AutoSendConfigRepository(db)
    await repo.reorder(data.ordered_ids)
    await db.commit()
    return BaseResponse(message="排序成功")


# ==================== 自动发送任务控制 ====================


async def _send_callback(session_id: int, content: str, is_auto_send: bool = True) -> bool:
    """自动发送回调函数"""
    conn = tcp_manager.get_connection(session_id)
    if not conn or conn.status != "connected":
        log.warning(f"会话 {session_id} 未连接，无法自动发送")
        return False
    return await tcp_manager.send(session_id, content, is_auto_send=is_auto_send)


# 设置自动发送回调
auto_send_service.set_send_callback(_send_callback)


@router.post(
    "/session/{session_id}/start",
    response_model=BaseResponse[Dict[str, Any]],
    summary="启动自动发送",
    description="启动指定会话的自动发送任务",
)
async def start_auto_send(
    session_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """启动自动发送"""
    # 检查会话是否已连接
    conn = tcp_manager.get_connection(session_id)
    if not conn or conn.status != "connected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="会话未连接，请先建立连接",
        )

    # 设置数据库会话工厂
    from src.api.deps import get_async_session_factory

    auto_send_service.set_db_session_factory(get_async_session_factory)

    result = await auto_send_service.start(session_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "启动失败"),
        )

    log.info(f"启动自动发送: session_id={session_id}")
    return BaseResponse(data=result, message=result.get("message", "启动成功"))


@router.post(
    "/session/{session_id}/stop",
    response_model=BaseResponse[Dict[str, Any]],
    summary="停止自动发送",
    description="停止指定会话的自动发送任务",
)
async def stop_auto_send(
    session_id: int,
):
    """停止自动发送"""
    result = await auto_send_service.stop(session_id)
    log.info(f"停止自动发送: session_id={session_id}")
    return BaseResponse(data=result, message=result.get("message", "停止成功"))


@router.get(
    "/session/{session_id}/status",
    response_model=BaseResponse[Dict[str, Any]],
    summary="获取自动发送状态",
    description="获取指定会话的自动发送状态",
)
async def get_auto_send_status(
    session_id: int,
):
    """获取自动发送状态"""
    status_data = auto_send_service.get_status(session_id)
    if not status_data:
        return BaseResponse(
            data={
                "session_id": session_id,
                "is_active": False,
                "task_count": 0,
            }
        )
    return BaseResponse(data=status_data)