from typing import List, Optional
from pydantic import BaseModel
from fastapi import Query


class LegalEntityTypeSchema(BaseModel):
    legal_entity_type_id: str
    entity_name: str

    model_config = {"from_attributes": True}


class LegalEntityTypeListResponse(BaseModel):
    total: int
    legal_entity_types: List[LegalEntityTypeSchema]


class UserRoleSchema(BaseModel):
    role_id: str
    role_name: str

    model_config = {"from_attributes": True}


class UserRoleListResponse(BaseModel):
    total: int
    user_roles: List[UserRoleSchema]


class ContractStatusSchema(BaseModel):
    contract_status_id: str
    status_name: str

    model_config = {"from_attributes": True}


class ContractStatusListResponse(BaseModel):
    total: int
    contract_statuses: List[ContractStatusSchema]


# ✅ Фильтры и параметры поиска
class FilterParams(BaseModel):
    search: Optional[str] = Query(None, description="Фильтр по названию")
    sort_by: Optional[str] = Query(
        "name", description="Сортировка (по умолчанию name)")
    order: Optional[str] = Query(
        "asc", description="Порядок сортировки: asc/desc")
    page: Optional[int] = Query(1, description="Номер страницы")
    page_size: Optional[int] = Query(10, description="Размер страницы")
