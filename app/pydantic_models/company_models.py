from typing import Optional
from pydantic import BaseModel, Field, field_validator, UUID4
from fastapi import Query
from app.utils.validate_helpers import sanitize_input


class CompanyCreateSchema(BaseModel):
    company_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, description="Описание компании")

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, value: str) -> str:
        """Фильтрация входных данных от XSS и других инъекций"""
        return sanitize_input(value)


class CompanyResponseSchema(BaseModel):
    company_id: UUID4


class CompanyEditSchema(BaseModel):
    company_name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, description="Описание компании")

    @field_validator("company_name", mode="before")
    @classmethod
    def validate_company_name(cls, value: Optional[str]) -> Optional[str]:
        """Фильтрация только если передано новое значение"""
        if value:
            return sanitize_input(value)
        return value


def company_filter_params(
    search: Optional[str] = Query(
        None, description="Фильтр по названию компании"),
    sort_by: Optional[str] = Query(
        "company_name", description="Поле сортировки"),
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
