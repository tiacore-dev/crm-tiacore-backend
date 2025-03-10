from typing import Optional
from pydantic import BaseModel, Field
from fastapi import Query


class CompanyCreateSchema(BaseModel):
    company_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, description="Описание комании")


class CompanyResponseSchema(BaseModel):
    company_id: str


class CompanyEditSchema(BaseModel):
    company_name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, description="Описание компании")


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
