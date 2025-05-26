from typing import List, Optional

from fastapi import HTTPException, Query
from pydantic import UUID4, Field, field_validator

from app.pydantic_models.clean_model import CleanableBaseModel
from app.utils.validate_helpers import sanitize_input


class CompanyCreateSchema(CleanableBaseModel):
    company_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, description="Описание компании")

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, value: str) -> str:
        if not value or len(value) < 3:
            raise HTTPException(
                status_code=400,
                detail="Название компании должно быть не менее 3 символов",
            )
        return sanitize_input(value)


class CompanyResponseSchema(CleanableBaseModel):
    company_id: UUID4


class CompanySchema(CleanableBaseModel):
    company_id: UUID4
    company_name: str
    description: Optional[str] = None


class CompanyListResponseSchema(CleanableBaseModel):
    total: int
    companies: List[CompanySchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class CompanyEditSchema(CleanableBaseModel):
    company_name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, description="Описание компании")


def company_filter_params(
    search: Optional[str] = Query(None, description="Фильтр по названию компании"),
    sort_by: Optional[str] = Query("company_name", description="Поле сортировки"),
    order: Optional[str] = Query("asc", description="Порядок сортировки: asc/desc"),
    page: Optional[int] = Query(1, ge=1, description="Номер страницы"),
    page_size: Optional[int] = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "search": search,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
