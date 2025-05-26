from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import Query
from pydantic import Field

from app.pydantic_models.clean_model import CleanableBaseModel


class UserCompanyRelationCreateSchema(CleanableBaseModel):
    user: UUID = Field(..., description="UUID пользователя, связанного с компанией")
    company: UUID = Field(..., description="UUID компании")
    role: UUID = Field(..., description="UUID роли пользователя в компании")

    class Config:
        from_attributes = True


class UserCompanyRelationSchema(CleanableBaseModel):
    user_company_id: UUID
    user_id: UUID
    company_id: UUID
    role_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class UserCompanyRelationListResponseSchema(CleanableBaseModel):
    total: int
    relations: List[UserCompanyRelationSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class UserCompanyRelationResponseSchema(CleanableBaseModel):
    user_company_id: UUID

    class Config:
        from_attributes = True


class UserCompanyRelationEditSchema(CleanableBaseModel):
    user: Optional[UUID] = None
    company: Optional[UUID] = None
    role: Optional[UUID] = None

    class Config:
        from_attributes = True


def user_company_filter_params(
    user: Optional[UUID] = Query(None, description="Фильтр по пользователю"),
    company: Optional[UUID] = Query(None, description="Фильтр по компании"),
    role: Optional[UUID] = Query(None, description="Фильтр по роли"),
    sort_by: Optional[str] = Query("created_at", description="Поле сортировки"),
    order: Optional[str] = Query("desc", description="Порядок сортировки: asc/desc"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "user": user,
        "company": company,
        "role": role,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
