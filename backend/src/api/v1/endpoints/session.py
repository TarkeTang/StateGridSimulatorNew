"""
会话配置 API 端点

提供会话配置的 RESTful API 接口
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_session
from src.schemas.base import BaseResponse
from src.schemas.session import (
    SessionConfigCreate,
    SessionConfigUpdate,
    SessionConfigResponse,
    SessionConfigListResponse,
)
from src.services.session_service import SessionConfigService
from src.utils.logger import get_logger

router = APIRouter()
log = get_logger("api.session")


@router.post(
    "",
    response_model=BaseResponse[SessionConfigResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建会话配置",
    description="创建新的会话配置",
)
async def create_session(
    data: SessionConfigCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """创建会话配置"""
    try:
        service = SessionConfigService(db)
        result = await service.create_session(data)
        await db.commit()
        log.info(f"创建会话配置成功: {result.name}")
        return BaseResponse(data=result, message="创建成功")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()
        log.error(f"创建会话配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建失败",
        )


@router.get(
    "",
    response_model=BaseResponse[SessionConfigListResponse],
    summary="获取会话配置列表",
    description="分页获取会话配置列表，支持筛选",
)
async def get_session_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    protocol_type: Optional[str] = Query(None, description="协议类型"),
    status: Optional[str] = Query(None, description="会话状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db_session),
):
    """获取会话配置列表"""
    service = SessionConfigService(db)
    result = await service.get_session_list(
        page=page,
        page_size=page_size,
        protocol_type=protocol_type,
        status=status,
        keyword=keyword,
        is_enabled=is_enabled,
    )
    return BaseResponse(data=result)


@router.get(
    "/{config_id}",
    response_model=BaseResponse[SessionConfigResponse],
    summary="获取会话配置详情",
    description="根据ID获取会话配置详情",
)
async def get_session(
    config_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """获取会话配置详情"""
    service = SessionConfigService(db)
    result = await service.get_session(config_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话配置不存在",
        )
    return BaseResponse(data=result)


@router.put(
    "/{config_id}",
    response_model=BaseResponse[SessionConfigResponse],
    summary="更新会话配置",
    description="更新指定ID的会话配置",
)
async def update_session(
    config_id: int,
    data: SessionConfigUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """更新会话配置"""
    try:
        service = SessionConfigService(db)
        result = await service.update_session(config_id, data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话配置不存在",
            )
        await db.commit()
        log.info(f"更新会话配置成功: {result.name}")
        return BaseResponse(data=result, message="更新成功")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        log.error(f"更新会话配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败",
        )


@router.delete(
    "/{config_id}",
    response_model=BaseResponse[None],
    summary="删除会话配置",
    description="删除指定ID的会话配置",
)
async def delete_session(
    config_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """删除会话配置"""
    service = SessionConfigService(db)
    success = await service.delete_session(config_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话配置不存在",
        )
    await db.commit()
    log.info(f"删除会话配置成功: ID={config_id}")
    return BaseResponse(message="删除成功")


@router.post(
    "/{config_id}/connect",
    response_model=BaseResponse[SessionConfigResponse],
    summary="连接会话",
    description="建立指定会话的连接",
)
async def connect_session(
    config_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """连接会话"""
    try:
        service = SessionConfigService(db)
        result = await service.connect_session(config_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话配置不存在",
            )
        await db.commit()
        log.info(f"连接会话成功: {result.name}")
        return BaseResponse(data=result, message="连接成功")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        log.error(f"连接会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="连接失败",
        )


@router.post(
    "/{config_id}/disconnect",
    response_model=BaseResponse[SessionConfigResponse],
    summary="断开会话",
    description="断开指定会话的连接",
)
async def disconnect_session(
    config_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """断开会话"""
    try:
        service = SessionConfigService(db)
        result = await service.disconnect_session(config_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话配置不存在",
            )
        await db.commit()
        log.info(f"断开会话成功: {result.name}")
        return BaseResponse(data=result, message="断开成功")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        log.error(f"断开会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="断开失败",
        )


@router.post(
    "/{config_id}/send",
    response_model=BaseResponse[None],
    summary="发送消息",
    description="通过指定会话发送消息",
)
async def send_message(
    config_id: int,
    data: str,
    db: AsyncSession = Depends(get_db_session),
):
    """发送消息"""
    try:
        service = SessionConfigService(db)
        success = await service.send_message(config_id, data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="发送失败",
            )
        log.info(f"发送消息成功: config_id={config_id}")
        return BaseResponse(message="发送成功")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"发送消息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送失败",
        )