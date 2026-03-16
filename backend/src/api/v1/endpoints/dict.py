"""
字典数据 API 端点

提供字典数据的 RESTful API 接口
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_session
from src.schemas.base import BaseResponse
from src.schemas.dict import DictDataListResponse, DictDataResponse, DictTypeResponse
from src.repositories.dict_repository import DictRepository
from src.utils.logger import get_logger

router = APIRouter()
log = get_logger("api.dict")


@router.get(
    "/types",
    response_model=BaseResponse[list[DictTypeResponse]],
    summary="获取字典类型列表",
    description="获取所有字典类型",
)
async def get_dict_types(db: AsyncSession = Depends(get_db_session)):
    """获取字典类型列表"""
    repo = DictRepository(db)
    types = await repo.get_all_types()
    return BaseResponse(data=[DictTypeResponse.model_validate(t) for t in types])


@router.get(
    "/data/{type_code}",
    response_model=BaseResponse[list[DictDataResponse]],
    summary="获取字典数据列表",
    description="根据类型编码获取字典数据列表",
)
async def get_dict_data(
    type_code: str,
    status: Optional[bool] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db_session),
):
    """获取字典数据列表"""
    repo = DictRepository(db)
    data = await repo.get_data_by_type_code(type_code, status)
    return BaseResponse(data=[DictDataResponse.model_validate(d) for d in data])


@router.get(
    "/data/{type_code}/{code}",
    response_model=BaseResponse[DictDataResponse],
    summary="获取字典数据详情",
    description="根据类型编码和字典编码获取字典数据",
)
async def get_dict_data_by_code(
    type_code: str,
    code: str,
    db: AsyncSession = Depends(get_db_session),
):
    """获取字典数据详情"""
    repo = DictRepository(db)
    data = await repo.get_data_by_code(type_code, code)
    if not data:
        return BaseResponse(code=404, message="字典数据不存在")
    return BaseResponse(data=DictDataResponse.model_validate(data))