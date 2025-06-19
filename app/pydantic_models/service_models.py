from typing import List, Optional
from uuid import UUID

from fastapi import Query
from pydantic import Field
from tiacore_lib.pydantic_models.clean_model import CleanableBaseModel


class ServiceCreateSchema(CleanableBaseModel):
    name: str = Field(..., min_length=3, max_length=100, alias="service_name")
    company_id: UUID = Field(..., alias="company")

    class Config:
        from_attributes = True
        populate_by_name = True


class ServiceResponseSchema(CleanableBaseModel):
    service_id: UUID


class ServiceSchema(CleanableBaseModel):
    id: UUID = Field(..., alias="service_id")
    name: str = Field(..., alias="service_name")
    company_id: UUID = Field(..., alias="company")

    class Config:
        from_attributes = True
        populate_by_name = True


class ServiceListResponseSchema(CleanableBaseModel):
    total: int  # 🔥 Количество услуг по фильтру
    services: List[ServiceSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class ServiceEditSchema(CleanableBaseModel):
    name: Optional[str] = Field(
        None, min_length=3, max_length=100, alias="service_name"
    )
    company_id: Optional[UUID] = Field(None, alias="company")

    class Config:
        from_attributes = True
        populate_by_name = True


def service_filter_params(
    search: Optional[str] = Query(None, description="Фильтр по названию"),
    company: Optional[UUID] = Query(None, description="Фильтр по компании"),
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
