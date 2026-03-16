"""
消息 API 端点

提供消息的 RESTful API 接口
"""

from datetime import datetime
from typing import Optional

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
    "/session/{session_id}",
    response_model=BaseResponse[SessionMessageListResponse],
    summary="获取会话消息列表",
    description="分页获取指定会话的消息列表",
)
async def get_message_list(
    session_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    direction: Optional[str] = Query(None, description="消息方向: send/receive/system"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: AsyncSession = Depends(get_db_session),
):
    """获取会话消息列表"""
    repo = MessageRepository(db)
    items, total = await repo.get_list(
        session_id=session_id,
        page=page,
        page_size=page_size,
        direction=direction,
        start_time=start_time,
        end_time=end_time,
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
    "/session/{session_id}",
    response_model=BaseResponse[None],
    summary="清空会话消息",
    description="删除指定会话的所有消息",
)
async def clear_session_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """清空会话消息"""
    repo = MessageRepository(db)
    count = await repo.delete_by_session(session_id)
    await db.commit()
    log.info(f"清空会话消息: session_id={session_id}, count={count}")
    return BaseResponse(message=f"已删除 {count} 条消息")


@router.get(
    "/session/{session_id}/statistics",
    response_model=BaseResponse[dict],
    summary="获取会话消息统计",
    description="获取指定会话的消息统计信息",
)
async def get_message_statistics(
    session_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """获取会话消息统计"""
    repo = MessageRepository(db)
    stats = await repo.get_statistics(session_id)
    return BaseResponse(data=stats.to_dict() if stats else None)