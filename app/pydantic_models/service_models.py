from typing import List, Optional

from fastapi import Query
from pydantic import UUID4, Field

from app.pydantic_models.clean_model import CleanableBaseModel


class ServiceCreateSchema(CleanableBaseModel):
    service_name: str = Field(..., min_length=3, max_length=100)
    company: UUID4 = Field(...)


class ServiceResponseSchema(CleanableBaseModel):
    service_id: UUID4


class ServiceSchema(CleanableBaseModel):
    service_id: UUID4
    service_name: str
    company: UUID4


class ServiceListResponseSchema(CleanableBaseModel):
    total: int  # 🔥 Количество услуг по фильтру
    services: List[ServiceSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class ServiceEditSchema(CleanableBaseModel):
    service_name: Optional[str] = Field(None, min_length=3, max_length=100)
    company: Optional[UUID4] = Field(None)


def service_filter_params(
    search: Optional[str] = Query(None, description="Фильтр по названию"),
    company: Optional[UUID4] = Query(None, description="Фильтр по компании"),
    sort_by: Optional[str] = Query("service_name", description="Поле сортировки"),
    order: Optional[str] = Query("asc", description="Порядок сортировки: asc/desc"),
    page: Optional[int] = Query(1, ge=1, description="Номер страницы"),
    page_size: Optional[int] = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "search": search,
        "company": company,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
