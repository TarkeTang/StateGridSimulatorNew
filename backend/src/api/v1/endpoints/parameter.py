"""
????? API ??
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import AsyncSessionLocal
from src.repositories.parameter_repository import ParameterRepository
from src.schemas.parameter import (
    ParameterConfigCreate,
    ParameterConfigResponse,
    ParameterConfigUpdate,
    ParameterConfigListResponse,
    PARAM_TYPES,
)
from src.schemas.base import BaseResponse
from src.utils.parameter_resolver import resolve_parameters_sync

router = APIRouter(prefix="/parameters", tags=["?????"])


async def get_db():
    """???????"""
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/types", response_model=BaseResponse[dict])
async def get_param_types():
    """????????"""
    return BaseResponse(data=PARAM_TYPES)


@router.get("", response_model=BaseResponse[ParameterConfigListResponse])
async def get_parameters(
    page: int = Query(1, ge=1, description="??"),
    page_size: int = Query(20, ge=1, le=100, description="????"),
    name: Optional[str] = Query(None, description="??????????"),
    param_type: Optional[str] = Query(None, description="????"),
    is_enabled: Optional[bool] = Query(None, description="????"),
    db: AsyncSession = Depends(get_db),
):
    """????????"""
    repo = ParameterRepository(db)

    # ????
    items = await repo.get_all()

    # ??
    if name:
        items = [item for item in items if name.lower() in item.name.lower()]
    if param_type:
        items = [item for item in items if item.param_type == param_type]
    if is_enabled is not None:
        items = [item for item in items if item.is_enabled == is_enabled]

    total = len(items)

    # ??
    start = (page - 1) * page_size
    end = start + page_size
    items = items[start:end]

    return BaseResponse(
        data=ParameterConfigListResponse(
            items=[ParameterConfigResponse.model_validate(item) for item in items],
            total=total,
        )
    )


@router.get("/enabled", response_model=BaseResponse[list])
async def get_enabled_parameters(
    db: AsyncSession = Depends(get_db),
):
    """???????????"""
    repo = ParameterRepository(db)
    items = await repo.get_all_enabled()

    return BaseResponse(
        data=[ParameterConfigResponse.model_validate(item) for item in items]
    )


@router.get("/{config_id}", response_model=BaseResponse[ParameterConfigResponse])
async def get_parameter(
    config_id: int,
    db: AsyncSession = Depends(get_db),
):
    """????????"""
    repo = ParameterRepository(db)
    item = await repo.get_by_id(config_id)

    if not item:
        raise HTTPException(status_code=404, detail="???????")

    return BaseResponse(data=ParameterConfigResponse.model_validate(item))


@router.post("", response_model=BaseResponse[ParameterConfigResponse])
async def create_parameter(
    data: ParameterConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    """??????"""
    repo = ParameterRepository(db)

    # ?????????
    existing = await repo.get_by_name(data.name)
    if existing:
        raise HTTPException(status_code=400, detail="???????")

    item = await repo.create(data)
    return BaseResponse(data=ParameterConfigResponse.model_validate(item))


@router.put("/{config_id}", response_model=BaseResponse[ParameterConfigResponse])
async def update_parameter(
    config_id: int,
    data: ParameterConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """??????"""
    repo = ParameterRepository(db)

    # ??????
    existing = await repo.get_by_id(config_id)
    if not existing:
        raise HTTPException(status_code=404, detail="???????")

    # ??????????????????
    if data.name and data.name != existing.name:
        name_exists = await repo.get_by_name(data.name)
        if name_exists:
            raise HTTPException(status_code=400, detail="???????")

    item = await repo.update(config_id, data)
    return BaseResponse(data=ParameterConfigResponse.model_validate(item))


@router.delete("/{config_id}", response_model=BaseResponse[bool])
async def delete_parameter(
    config_id: int,
    db: AsyncSession = Depends(get_db),
):
    """??????"""
    repo = ParameterRepository(db)

    success = await repo.delete(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="???????")

    return BaseResponse(data=True)


@router.post("/preview", response_model=BaseResponse[str])
async def preview_parameter(
    content: str = Query(..., description="??????"),
):
    """????????"""
    result = resolve_parameters_sync(content)
    return BaseResponse(data=result)