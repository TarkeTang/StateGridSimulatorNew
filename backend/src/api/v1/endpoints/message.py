"""
消息 API 端点

提供消息的 RESTful API 接口
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_session
from src.repositories.message_repository import MessageRepository
from src.schemas.base import BaseResponse
from src.schemas.session import (
    SessionMessageCreate,
    SessionMessageResponse,
    SessionMessageListResponse,
)
from src.utils.logger import get_logger

router = APIRouter()
log = get_logger("api.message")


@router.post(
    "",
    response_model=BaseResponse[SessionMessageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建消息记录",
    description="创建新的消息记录",
)
async def create_message(
    data: SessionMessageCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """创建消息记录"""
    try:
        repo = MessageRepository(db)
        result = await repo.create(data)
        await db.commit()
        return BaseResponse(data=result, message="创建成功")
    except Exception as e:
        await db.rollback()
        log.error(f"创建消息记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建失败",
        )


@router.get(
    "/config/{config_id}/recent",
    response_model=BaseResponse[List[SessionMessageResponse]],
    summary="获取配置的最近消息",
    description="获取指定配置的最近消息（用于显示旧连接消息）",
)
async def get_recent_messages(
    config_id: int,
    limit: int = Query(10, ge=1, le=50, description="限制数量"),
    db: AsyncSession = Depends(get_db_session),
):
    """获取配置的最近消息"""
    repo = MessageRepository(db)
    items = await repo.get_recent_by_config(config_id, limit)
    return BaseResponse(data=[SessionMessageResponse.model_validate(item) for item in items])


@router.get(
    "/connection/{connection_id}",
    response_model=BaseResponse[SessionMessageListResponse],
    summary="获取连接消息列表",
    description="分页获取指定连接的消息列表",
)
async def get_connection_messages(
    connection_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    direction: Optional[str] = Query(None, description="消息方向: send/receive/system"),
    db: AsyncSession = Depends(get_db_session),
):
    """获取连接消息列表"""
    repo = MessageRepository(db)
    items, total = await repo.get_list_by_connection(
        connection_id=connection_id,
        page=page,
        page_size=page_size,
        direction=direction,
    )
    return BaseResponse(
        data=SessionMessageListResponse(
            items=[SessionMessageResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get(
    "/{message_id}",
    response_model=BaseResponse[SessionMessageResponse],
    summary="获取消息详情",
    description="根据ID获取消息详情",
)
async def get_message(
    message_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """获取消息详情"""
    repo = MessageRepository(db)
    result = await repo.get_by_id(message_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在",
        )
    return BaseResponse(data=SessionMessageResponse.model_validate(result))


@router.delete(
    "/connection/{connection_id}",
    response_model=BaseResponse[None],
    summary="清空连接消息",
    description="删除指定连接的所有消息",
)
async def clear_connection_messages(
    connection_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """清空连接消息"""
    repo = MessageRepository(db)
    count = await repo.delete_by_connection(connection_id)
    await db.commit()
    log.info(f"清空连接消息: connection_id={connection_id}, count={count}")
    return BaseResponse(message=f"已删除 {count} 条消息")