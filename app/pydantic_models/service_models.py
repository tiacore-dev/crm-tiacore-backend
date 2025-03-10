from typing import Optional
from pydantic import BaseModel, Field, field_validator, UUID4
from fastapi import Query
from app.utils.validate_helpers import sanitize_input


class ServiceCreateSchema(BaseModel):
    service_name: str = Field(..., min_length=3, max_length=100)

    @field_validator("service_name")
    @classmethod
    def validate_service_name(cls, value: str) -> str:
        """Фильтрация входных данных от XSS и других инъекций"""
        return sanitize_input(value)


class ServiceResponseSchema(BaseModel):
    service_id: UUID4


class ServiceEditSchema(BaseModel):
    service_name: str = Field(..., min_length=3, max_length=100)

    @field_validator("service_name")
    @classmethod
    def validate_service_name(cls, value: str) -> str:
        """Фильтрация входных данных от XSS и других инъекций"""
        return sanitize_input(value)


def service_filter_params(
    search: Optional[str] = Query(None, description="Фильтр по названию"),
    sort_by: Optional[str] = Query(
        "service_name", description="Поле сортировки"),
    order: Optional[str] = Query(
        "asc", description="Порядок сортировки: asc/desc"),
    page: Optional[int] = Query(1, ge=1, description="Номер страницы"),
    page_size: Optional[int] = Query(
        10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "search": search,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
