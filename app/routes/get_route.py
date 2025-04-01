from fastapi import APIRouter, Depends, HTTPException
from tortoise.expressions import Q
from loguru import logger
from app.handlers.auth import get_current_user
from app.database.models import LegalEntityType, UserRole, ContractStatus
from app.pydantic_models.get_models import (
    LegalEntityTypeListResponse, UserRoleListResponse, ContractStatusListResponse,
    FilterParams
)


get_router = APIRouter()


# 📌 Обновленные эндпоинты с `PaginatedResponse`
@get_router.get(
    "/legal-entity-types/all",
    response_model=LegalEntityTypeListResponse,
    summary="Получение списка типов юридических лиц"
)
async def get_legal_entity_types(filters: FilterParams = Depends(), username: str = Depends(get_current_user)):
    try:
        query = LegalEntityType.all()

        if filters.search:
            query = query.filter(Q(entity_name__icontains=filters.search))
        # 🟢 Добавляем сортировку
        order_by = f"{'-' if filters.order == 'desc' else ''}entity_name"
        query = query.order_by(order_by)
        total_count = await query.count()
        entities = await query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

        return {
            "total": total_count,
            "legal_entity_types": [
                {
                    "legal_entity_type_id": entity.legal_entity_type_id,
                    "entity_name": entity.entity_name
                } for entity in entities
            ]
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Ошибка при получении типов юридических лиц")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@get_router.get(
    "/user-roles/all",
    response_model=UserRoleListResponse,
    summary="Получение списка ролей пользователей"
)
async def get_user_roles(filters: FilterParams = Depends(), username: str = Depends(get_current_user)):
    try:
        query = UserRole.all()

        if filters.search:
            query = query.filter(Q(role_name__icontains=filters.search))

        order_by = f"{'-' if filters.order == 'desc' else ''}role_name"
        query = query.order_by(order_by)
        total_count = await query.count()
        roles = await query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

        return {
            "total": total_count,
            "user_roles": [
                {
                    "role_id": role.role_id,
                    "role_name": role.role_name
                } for role in roles
            ]
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Ошибка при получении списка ролей пользователей")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@get_router.get(
    "/contract-statuses/all",
    response_model=ContractStatusListResponse,
    summary="Получение списка статусов контрактов"
)
async def get_contract_statuses(filters: FilterParams = Depends(), username: str = Depends(get_current_user)):
    try:
        query = ContractStatus.all()

        if filters.search:
            query = query.filter(Q(status_name__icontains=filters.search))

        order_by = f"{'-' if filters.order == 'desc' else ''}status_name"
        query = query.order_by(order_by)
        total_count = await query.count()
        statuses = await query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

        return {
            "total": total_count,
            "contract_statuses": [
                {
                    "contract_status_id": status.contract_status_id,
                    "status_name": status.status_name
                } for status in statuses
            ]
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Ошибка при получении списка статусов контрактов")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e
