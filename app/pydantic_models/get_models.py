from typing import List, Optional
from fastapi import Query
from app.pydantic_models.clean_model import CleanableBaseModel


class LegalEntityTypeSchema(CleanableBaseModel):
    legal_entity_type_id: str
    entity_name: str

    model_config = {"from_attributes": True}


class LegalEntityTypeListResponse(CleanableBaseModel):
    total: int
    legal_entity_types: List[LegalEntityTypeSchema]


class ContractStatusSchema(CleanableBaseModel):
    contract_status_id: str
    status_name: str

    model_config = {"from_attributes": True}


class ContractStatusListResponse(CleanableBaseModel):
    total: int
    contract_statuses: List[ContractStatusSchema]


# ✅ Фильтры и параметры поиска
class FilterParams(CleanableBaseModel):
    search: Optional[str] = Query(None, description="Фильтр по названию")
    sort_by: Optional[str] = Query(
        "name", description="Сортировка (по умолчанию name)")
    order: Optional[str] = Query(
        "asc", description="Порядок сортировки: asc/desc")
    page: Optional[int] = Query(1, description="Номер страницы")
    page_size: Optional[int] = Query(10, description="Размер страницы")
