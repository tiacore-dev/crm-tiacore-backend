from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from tortoise.expressions import Q

from app.database.models import ContractStatus, LegalEntityType
from app.handlers.auth import get_current_user
from app.pydantic_models.get_models import (
    ContractStatusListResponse,
    FilterParams,
    LegalEntityTypeListResponse,
)

get_router = APIRouter()


# 📌 Обновленные эндпоинты с `PaginatedResponse`
@get_router.get(
    "/legal-entity-types/all",
    response_model=LegalEntityTypeListResponse,
    summary="Получение списка типов юридических лиц",
)
async def get_legal_entity_types(
    filters: FilterParams = Depends(), username: str = Depends(get_current_user)
):
    try:
        query = LegalEntityType.all()

        if filters.search:
            query = query.filter(Q(entity_name__icontains=filters.search))
        # 🟢 Добавляем сортировку
        order_by = f"{'-' if filters.order == 'desc' else ''}entity_name"
        query = query.order_by(order_by)
        total_count = await query.count()
        entities = await query.offset((filters.page - 1) * filters.page_size).limit(
            filters.page_size
        )

        return {
            "total": total_count,
            "legal_entity_types": [
                {
                    "legal_entity_type_id": entity.legal_entity_type_id,
                    "entity_name": entity.entity_name,
                }
                for entity in entities
            ],
        }

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@get_router.get(
    "/contract-statuses/all",
    response_model=ContractStatusListResponse,
    summary="Получение списка статусов контрактов",
)
async def get_contract_statuses(
    filters: FilterParams = Depends(), username: str = Depends(get_current_user)
):
    try:
        query = ContractStatus.all()

        if filters.search:
            query = query.filter(Q(status_name__icontains=filters.search))

        order_by = f"{'-' if filters.order == 'desc' else ''}status_name"
        query = query.order_by(order_by)
        total_count = await query.count()
        statuses = await query.offset((filters.page - 1) * filters.page_size).limit(
            filters.page_size
        )

        return {
            "total": total_count,
            "contract_statuses": [
                {
                    "contract_status_id": status.contract_status_id,
                    "status_name": status.status_name,
                }
                for status in statuses
            ],
        }

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e
