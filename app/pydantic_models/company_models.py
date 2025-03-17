from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, UUID4
from fastapi import Query, HTTPException
from app.utils.validate_helpers import sanitize_input


class CompanyCreateSchema(BaseModel):
    company_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, description="Описание компании")

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, value: str) -> str:
        if not value or len(value) < 3:
            raise HTTPException(
                status_code=400, detail="Название компании должно быть не менее 3 символов")
        return sanitize_input(value)


class CompanyResponseSchema(BaseModel):
    company_id: UUID4


class CompanySchema(BaseModel):
    company_id: UUID4
    company_name: str
    description: str


class CompanyListResponseSchema(BaseModel):
    total: int  # 🔥 Количество записей по фильтру
    # ✅ Используем `list`, а не `List[CompanySchema]`
    companies: List[CompanySchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


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
