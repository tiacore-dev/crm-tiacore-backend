from typing import List, Optional

from fastapi import Query
from pydantic import Field
from tiacore_lib.pydantic_models.clean_model import CleanableBaseModel


class ContractStatusSchema(CleanableBaseModel):
    id: str = Field(..., alias="contract_status_id")
    name: str = Field(..., alias="status_name")

    class Config:
        from_attributes = True
        populate_by_name = True


class ContractStatusListResponse(CleanableBaseModel):
    total: int
    contract_statuses: List[ContractStatusSchema]


# ✅ Фильтры и параметры поиска
class FilterParams(CleanableBaseModel):
    search: Optional[str] = Query(None, description="Фильтр по названию")
    sort_by: str = Query("name", description="Сортировка (по умолчанию name)")
    order: str = Query("asc", description="Порядок сортировки: asc/desc")
    page: int = Query(1, description="Номер страницы")
    page_size: int = Query(10, description="Размер страницы")
