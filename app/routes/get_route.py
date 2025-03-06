from typing import Type
from fastapi import APIRouter, Depends
from tortoise.expressions import Q
from app.database.models import LegalEntityType, UserRole, ContractStatus
from app.pydantic_models.get_models import (
    LegalEntityTypeSchema, UserRoleSchema, ContractStatusSchema, FilterParams, PaginatedResponse
)


get_router = APIRouter()


# 🔍 Универсальная функция для получения данных с фильтрацией, сортировкой и пагинацией
async def get_filtered_data(model: Type, schema: Type, params: FilterParams) -> PaginatedResponse:
    query = model.all()

    # 📌 Определяем правильное поле для имени
    field_mapping = {
        "LegalEntityType": "entity_name",
        "UserRole": "role_name",
        "ContractStatus": "status_name",
    }
    model_name = model.__name__
    name_field = field_mapping.get(model_name)

    if not name_field:
        raise ValueError(
            f"Модель {model_name} не содержит корректного текстового поля для поиска")

    # 🔎 Фильтр по названию
    if params.search:
        query = query.filter(Q(**{f"{name_field}__icontains": params.search}))

    # 🔄 Сортировка
    order_by = name_field if params.order == "asc" else f"-{name_field}"
    query = query.order_by(order_by)

    # 📑 Пагинация
    total_count = await query.count()
    items = await query.offset((params.page - 1) * params.page_size).limit(params.page_size)

    return PaginatedResponse(
        total=total_count,
        page=params.page,
        page_size=params.page_size,
        items=[schema.model_validate(item, from_attributes=True)
               for item in items]
    )


# 📌 Эндпоинты с `PaginatedResponse`


@get_router.get("/legal-entity-types/", response_model=PaginatedResponse)
async def get_legal_entity_types(params: FilterParams = Depends()):
    return await get_filtered_data(LegalEntityType, LegalEntityTypeSchema, params)


@get_router.get("/user-roles/", response_model=PaginatedResponse)
async def get_user_roles(params: FilterParams = Depends()):
    return await get_filtered_data(UserRole, UserRoleSchema, params)


@get_router.get("/contract-statuses/", response_model=PaginatedResponse)
async def get_contract_statuses(params: FilterParams = Depends()):
    return await get_filtered_data(ContractStatus, ContractStatusSchema, params)
