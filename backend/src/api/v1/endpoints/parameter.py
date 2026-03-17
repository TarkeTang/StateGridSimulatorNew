"""
参数化配置 API 路由
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import AsyncSessionLocal
from src.repositories.parameter_repository import ParameterRepository
from src.schemas.parameter import (
    ParameterConfigCreate,
    ParameterConfigResponse,
    ParameterConfigUpdate,
    ParameterConfigListResponse,
    PARAM_TYPES,
)
from src.schemas.response import Response
from src.utils.parameter_resolver import resolve_parameters_sync

router = APIRouter(prefix="/parameters", tags=["参数化配置"])


async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/types", response_model=Response[dict])
async def get_param_types():
    """获取参数类型列表"""
    return Response(data=PARAM_TYPES)


@router.get("", response_model=Response[ParameterConfigListResponse])
async def get_parameters(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="参数名称（模糊搜索）"),
    param_type: Optional[str] = Query(None, description="参数类型"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
):
    """获取参数配置列表"""
    repo = ParameterRepository(db)

    # 构建查询条件
    filters = {}
    if param_type:
        filters["param_type"] = param_type
    if is_enabled is not None:
        filters["is_enabled"] = is_enabled

    # 获取列表
    items = await repo.get_all()
    total = len(items)

    # 过滤
    if name:
        items = [item for item in items if name.lower() in item.name.lower()]
        total = len(items)

    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    items = items[start:end]

    return Response(
        data=ParameterConfigListResponse(
            items=[ParameterConfigResponse.model_validate(item) for item in items],
            total=total,
        )
    )


@router.get("/enabled", response_model=Response[list])
async def get_enabled_parameters(
    db: AsyncSession = Depends(get_db),
):
    """获取所有启用的参数配置"""
    repo = ParameterRepository(db)
    items = await repo.get_all_enabled()

    return Response(
        data=[ParameterConfigResponse.model_validate(item) for item in items]
    )


@router.get("/{config_id}", response_model=Response[ParameterConfigResponse])
async def get_parameter(
    config_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取单个参数配置"""
    repo = ParameterRepository(db)
    item = await repo.get_by_id(config_id)

    if not item:
        raise HTTPException(status_code=404, detail="参数配置不存在")

    return Response(data=ParameterConfigResponse.model_validate(item))


@router.post("", response_model=Response[ParameterConfigResponse])
async def create_parameter(
    data: ParameterConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建参数配置"""
    repo = ParameterRepository(db)

    # 检查名称是否已存在
    existing = await repo.get_by_name(data.name)
    if existing:
        raise HTTPException(status_code=400, detail="参数名称已存在")

    item = await repo.create(data)
    return Response(data=ParameterConfigResponse.model_validate(item))


@router.put("/{config_id}", response_model=Response[ParameterConfigResponse])
async def update_parameter(
    config_id: int,
    data: ParameterConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新参数配置"""
    repo = ParameterRepository(db)

    # 检查是否存在
    existing = await repo.get_by_id(config_id)
    if not existing:
        raise HTTPException(status_code=404, detail="参数配置不存在")

    # 如果修改了名称，检查新名称是否已存在
    if data.name and data.name != existing.name:
        name_exists = await repo.get_by_name(data.name)
        if name_exists:
            raise HTTPException(status_code=400, detail="参数名称已存在")

    item = await repo.update(config_id, data)
    return Response(data=ParameterConfigResponse.model_validate(item))


@router.delete("/{config_id}", response_model=Response[bool])
async def delete_parameter(
    config_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除参数配置"""
    repo = ParameterRepository(db)

    success = await repo.delete(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="参数配置不存在")

    return Response(data=True)


@router.post("/preview", response_model=Response[str])
async def preview_parameter(
    content: str = Query(..., description="要预览的内容"),
):
    """预览参数替换结果"""
    result = resolve_parameters_sync(content)
    return Response(data=result)