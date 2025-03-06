from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi import Query


# ✅ Общая схема с alias для маппинга названий
class BaseListSchema(BaseModel):
    id: str
    name: str

    model_config = {"from_attributes": True}


class LegalEntityTypeSchema(BaseListSchema):
    id: str = Field(alias="legal_entity_type_id")
    name: str = Field(alias="entity_name")


class UserRoleSchema(BaseListSchema):
    id: str = Field(alias="role_id")
    name: str = Field(alias="role_name")


class ContractStatusSchema(BaseListSchema):
    id: str = Field(alias="contract_status_id")
    name: str = Field(alias="status_name")


# ✅ Схема для ответа с пагинацией
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[BaseListSchema]  # Возвращаем список объектов

    model_config = {"from_attributes": True}


# ✅ Схема для фильтрации и поиска
class FilterParams(BaseModel):
    search: Optional[str] = Query(None, description="Фильтр по названию")
    sort_by: Optional[str] = Query(
        "name", description="Сортировка (по умолчанию name)")
    order: Optional[str] = Query(
        "asc", description="Порядок сортировки: asc/desc")
    page: Optional[int] = Query(1, description="Номер страницы")
    page_size: Optional[int] = Query(10, description="Размер страницы")
