from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from tiacore_lib.handlers.auth_handler import get_current_user
from tortoise.expressions import Q

from app.database.models import ContractStatus
from app.pydantic_models.get_models import (
    ContractStatusListResponse,
    ContractStatusSchema,
    FilterParams,
)

get_router = APIRouter()


@get_router.get(
    "/contract-statuses/all",
    response_model=ContractStatusListResponse,
    summary="Получение списка статусов контрактов",
)
async def get_contract_statuses(
    filters: FilterParams = Depends(), _: str = Depends(get_current_user)
):
    try:
        query = ContractStatus.all()

        if filters.search:
            query = query.filter(Q(name__icontains=filters.search))

        order_by = f"{'-' if filters.order == 'desc' else ''}name"
        query = query.order_by(order_by)
        total_count = await query.count()
        statuses = (
            await query.offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
            .values("id", "name")
        )

        return ContractStatusListResponse(
            total=total_count,
            contract_statuses=[ContractStatusSchema(**status) for status in statuses],
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e
